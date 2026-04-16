import api from './client'
import type { RequirementAnalyzeResponse } from './requirement'

export interface ModuleDesign {
  name: string
  responsibility: string
  inputs: string[]
  outputs: string[]
}

export interface ApiDesign {
  name: string
  method: string
  path: string
  description: string
}

export interface DataEntity {
  name: string
  fields: string[]
}

export interface DesignGenerateResponse {
  architecture_style: string
  architecture_rationale: string
  modules: ModuleDesign[]
  apis: ApiDesign[]
  data_entities: DataEntity[]
  mermaid: string
  raw_model_output: string
  reasoning_content?: string | null
  mode: 'fast' | 'deep'
}

export interface DesignStreamEvent {
  type: 'status' | 'reasoning' | 'content' | 'result' | 'error' | 'done'
  content: string
  mode?: 'fast' | 'deep'
  result?: DesignGenerateResponse | null
}

export async function generateDesign(requirement: RequirementAnalyzeResponse, mode: 'fast' | 'deep') {
  const { data } = await api.post<DesignGenerateResponse>('/design/generate', { requirement, mode })
  return data
}

export async function streamGenerateDesign(
  requirement: RequirementAnalyzeResponse,
  mode: 'fast' | 'deep',
  onEvent: (event: DesignStreamEvent) => void,
) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/design/generate/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ requirement, mode }),
  })

  if (!response.ok || !response.body) {
    throw new Error('流式设计生成失败')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data: ')) continue
      const payload = line.slice(6)
      onEvent(JSON.parse(payload) as DesignStreamEvent)
    }
  }
}
