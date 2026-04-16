import api from './client'
import type { DesignGenerateResponse } from './design'

export interface CodegenOptions {
  language: string
  backend_framework: string
  frontend_framework: string
  database: string
}

export interface CodeSuggestResponse {
  options: CodegenOptions
  reasoning?: string | null
  raw_model_output: string
}

export interface CodeSuggestStreamEvent {
  type: 'status' | 'content' | 'result' | 'error' | 'done'
  content: string
  result?: CodeSuggestResponse | null
}

export interface CodeFile {
  path: string
  language: string
  description: string
  content: string
}

export interface CodeGenerateResponse {
  project_summary: string
  tech_stack: string[]
  file_tree: string
  files: CodeFile[]
  startup_steps: string[]
  raw_model_output: string
  reasoning_content?: string | null
  mode: 'fast' | 'deep'
}

export interface CodeStreamEvent {
  type: 'status' | 'reasoning' | 'content' | 'result' | 'error' | 'done'
  content: string
  mode?: 'fast' | 'deep'
  result?: CodeGenerateResponse | null
}

export interface CodePersistResponse {
  project_name: string
  output_path: string
  written_files: string[]
  startup_script?: string | null
  archive_name?: string | null
}

export async function suggestCodegenOptions(design: DesignGenerateResponse) {
  const { data } = await api.post<CodeSuggestResponse>('/codegen/suggest', { design })
  return data
}

export async function streamSuggestCodegenOptions(
  design: DesignGenerateResponse,
  onEvent: (event: CodeSuggestStreamEvent) => void,
) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/codegen/suggest/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ design }),
  })

  if (!response.ok || !response.body) {
    throw new Error('流式智能选型失败')
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
      onEvent(JSON.parse(payload) as CodeSuggestStreamEvent)
    }
  }
}

export async function streamGenerateCode(
  design: DesignGenerateResponse,
  options: CodegenOptions,
  mode: 'fast' | 'deep',
  onEvent: (event: CodeStreamEvent) => void,
) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/codegen/generate/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ design, options, mode }),
  })

  if (!response.ok || !response.body) {
    throw new Error('流式代码生成失败')
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
      onEvent(JSON.parse(payload) as CodeStreamEvent)
    }
  }
}

export async function persistCodeProject(result: CodeGenerateResponse, projectName: string, options: CodegenOptions) {
  const { data } = await api.post<CodePersistResponse>('/codegen/persist', {
    result,
    options,
    project_name: projectName,
  })
  return data
}

export async function previewCodegen(design: DesignGenerateResponse, options: CodegenOptions, mode: 'fast' | 'deep') {
  const { data } = await api.post<CodeGenerateResponse>('/codegen/preview', {
    design,
    options,
    mode,
  })
  return data
}

export async function downloadCodeArchive(archiveName: string) {
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/codegen/archive/${encodeURIComponent(archiveName)}`)
  if (!response.ok) throw new Error('压缩包下载失败')
  return await response.blob()
}
