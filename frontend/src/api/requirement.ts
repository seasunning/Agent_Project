import api from './client'

export interface RequirementItem {
  name: string
  description: string
  priority?: string | null
}

export interface RequirementAnalyzeResponse {
  summary: string
  functional_requirements: RequirementItem[]
  non_functional_requirements: string[]
  constraints: string[]
  actors: string[]
  ambiguities: string[]
  conflicts: string[]
  questions_for_user: string[]
  raw_model_output: string
  reasoning_content?: string | null
  mode: 'fast' | 'deep'
}

export interface RequirementStreamEvent {
  type: 'status' | 'reasoning' | 'content' | 'result' | 'error' | 'done'
  content: string
  mode?: 'fast' | 'deep'
  result?: RequirementAnalyzeResponse | null
}

export async function analyzeRequirement(text: string, mode: 'fast' | 'deep') {
  const { data } = await api.post<RequirementAnalyzeResponse>('/requirements/analyze', { text, mode })
  return data
}

export async function streamAnalyzeRequirement(
  text: string,
  mode: 'fast' | 'deep',
  onEvent: (event: RequirementStreamEvent) => void,
) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/requirements/analyze/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, mode }),
  })

  if (!response.ok || !response.body) {
    throw new Error('流式需求分析失败')
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
      onEvent(JSON.parse(payload) as RequirementStreamEvent)
    }
  }
}
