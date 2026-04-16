import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CodeGenerateResponse, CodePersistResponse, CodegenOptions } from '../api/codegen'
import type { DesignGenerateResponse } from '../api/design'
import type { RequirementAnalyzeResponse } from '../api/requirement'

const STORAGE_KEYS = {
  requirementEditDraft: 'sdmas.requirement.editDraft',
  designEditDraft: 'sdmas.design.editDraft',
}

function loadStored<T>(key: string): T | null {
  if (typeof window === 'undefined') return null
  const raw = window.localStorage.getItem(key)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

function saveStored(key: string, value: unknown) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(key, JSON.stringify(value))
}

function removeStored(key: string) {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(key)
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const currentPhase = ref('Phase 3：设计方案自动生成阶段')
  const selectedModelMode = ref('deepseek-chat + 顶层 thinking')
  const backendStatus = ref('未检测')
  const latestRequirement = ref('')
  const requirementMode = ref<'fast' | 'deep'>('fast')
  const requirementResult = ref<RequirementAnalyzeResponse | null>(null)
  const requirementOriginalResult = ref<RequirementAnalyzeResponse | null>(null)
  const requirementEditDraft = ref<RequirementAnalyzeResponse | null>(loadStored<RequirementAnalyzeResponse>(STORAGE_KEYS.requirementEditDraft))
  const designMode = ref<'fast' | 'deep'>('fast')
  const designResult = ref<DesignGenerateResponse | null>(null)
  const designOriginalResult = ref<DesignGenerateResponse | null>(null)
  const designEditDraft = ref<DesignGenerateResponse | null>(loadStored<DesignGenerateResponse>(STORAGE_KEYS.designEditDraft))
  const codegenMode = ref<'fast' | 'deep'>('fast')
  const codegenOptions = ref<CodegenOptions>({
    language: '',
    backend_framework: '',
    frontend_framework: '',
    database: '',
  })
  const codegenAutoSelected = ref(false)
  const codegenResult = ref<CodeGenerateResponse | null>(null)
  const codegenPersistResult = ref<CodePersistResponse | null>(null)
  const codegenStreamingReasoning = ref('')
  const codegenStreamingContent = ref('')
  const codegenProgressMessage = ref('等待开始')
  const codegenSuggestStream = ref('')
  const streamingReasoning = ref('')
  const streamingContent = ref('')
  const progressMessage = ref('等待开始')
  const designStreamingReasoning = ref('')
  const designStreamingContent = ref('')
  const designProgressMessage = ref('等待开始')

  function setBackendStatus(status: string) {
    backendStatus.value = status
  }

  function setRequirementDraft(text: string) {
    latestRequirement.value = text
  }

  function setRequirementMode(mode: 'fast' | 'deep') {
    requirementMode.value = mode
  }

  function setRequirementResult(result: RequirementAnalyzeResponse | null, markAsOriginal = false) {
    requirementResult.value = result
    if (markAsOriginal) {
      requirementOriginalResult.value = result ? JSON.parse(JSON.stringify(result)) : null
      clearRequirementEditDraft()
    }
  }

  function restoreRequirementOriginal() {
    if (!requirementOriginalResult.value) return
    requirementResult.value = JSON.parse(JSON.stringify(requirementOriginalResult.value))
    clearRequirementEditDraft()
  }

  function saveRequirementEditDraft(result: RequirementAnalyzeResponse | null) {
    requirementEditDraft.value = result ? JSON.parse(JSON.stringify(result)) : null
    if (result) saveStored(STORAGE_KEYS.requirementEditDraft, requirementEditDraft.value)
    else removeStored(STORAGE_KEYS.requirementEditDraft)
  }

  function clearRequirementEditDraft() {
    requirementEditDraft.value = null
    removeStored(STORAGE_KEYS.requirementEditDraft)
  }

  function setDesignMode(mode: 'fast' | 'deep') {
    designMode.value = mode
  }

  function setCodegenMode(mode: 'fast' | 'deep') {
    codegenMode.value = mode
  }

  function setCodegenOptions(options: CodegenOptions) {
    codegenOptions.value = options
  }

  function setCodegenAutoSelected(value: boolean) {
    codegenAutoSelected.value = value
  }

  function setCodegenResult(result: CodeGenerateResponse | null) {
    codegenResult.value = result
  }

  function setCodegenPersistResult(result: CodePersistResponse | null) {
    codegenPersistResult.value = result
  }

  function resetCodegenStreamState() {
    codegenStreamingReasoning.value = ''
    codegenStreamingContent.value = ''
    codegenProgressMessage.value = '已重置，等待开始'
  }

  function appendCodegenReasoning(content: string) {
    codegenStreamingReasoning.value += content
  }

  function appendCodegenContent(content: string) {
    codegenStreamingContent.value += content
  }

  function setCodegenProgressMessage(message: string) {
    codegenProgressMessage.value = message
  }

  function resetCodegenSuggestStream() {
    codegenSuggestStream.value = ''
  }

  function appendCodegenSuggestStream(content: string) {
    codegenSuggestStream.value += content
  }

  function setDesignResult(result: DesignGenerateResponse | null, markAsOriginal = false) {
    designResult.value = result
    if (markAsOriginal) {
      designOriginalResult.value = result ? JSON.parse(JSON.stringify(result)) : null
      clearDesignEditDraft()
    }
  }

  function restoreDesignOriginal() {
    if (!designOriginalResult.value) return
    designResult.value = JSON.parse(JSON.stringify(designOriginalResult.value))
    clearDesignEditDraft()
  }

  function saveDesignEditDraft(result: DesignGenerateResponse | null) {
    designEditDraft.value = result ? JSON.parse(JSON.stringify(result)) : null
    if (result) saveStored(STORAGE_KEYS.designEditDraft, designEditDraft.value)
    else removeStored(STORAGE_KEYS.designEditDraft)
  }

  function clearDesignEditDraft() {
    designEditDraft.value = null
    removeStored(STORAGE_KEYS.designEditDraft)
  }

  function resetStreamState() {
    streamingReasoning.value = ''
    streamingContent.value = ''
    progressMessage.value = '已重置，等待开始'
  }

  function appendReasoning(content: string) {
    streamingReasoning.value += content
  }

  function appendContent(content: string) {
    streamingContent.value += content
  }

  function setProgressMessage(message: string) {
    progressMessage.value = message
  }

  function resetDesignStreamState() {
    designStreamingReasoning.value = ''
    designStreamingContent.value = ''
    designProgressMessage.value = '已重置，等待开始'
  }

  function appendDesignReasoning(content: string) {
    designStreamingReasoning.value += content
  }

  function appendDesignContent(content: string) {
    designStreamingContent.value += content
  }

  function setDesignProgressMessage(message: string) {
    designProgressMessage.value = message
  }

  return {
    currentPhase,
    selectedModelMode,
    backendStatus,
    latestRequirement,
    requirementMode,
    requirementResult,
    requirementOriginalResult,
    requirementEditDraft,
    designMode,
    designResult,
    designOriginalResult,
    designEditDraft,
    codegenMode,
    codegenOptions,
    codegenAutoSelected,
    codegenResult,
    codegenPersistResult,
    codegenStreamingReasoning,
    codegenStreamingContent,
    codegenProgressMessage,
    codegenSuggestStream,
    streamingReasoning,
    streamingContent,
    progressMessage,
    designStreamingReasoning,
    designStreamingContent,
    designProgressMessage,
    setBackendStatus,
    setRequirementDraft,
    setRequirementMode,
    setRequirementResult,
    restoreRequirementOriginal,
    saveRequirementEditDraft,
    clearRequirementEditDraft,
    setDesignMode,
    setCodegenMode,
    setCodegenOptions,
    setCodegenAutoSelected,
    setCodegenResult,
    setCodegenPersistResult,
    resetCodegenStreamState,
    appendCodegenReasoning,
    appendCodegenContent,
    setCodegenProgressMessage,
    resetCodegenSuggestStream,
    appendCodegenSuggestStream,
    setDesignResult,
    restoreDesignOriginal,
    saveDesignEditDraft,
    clearDesignEditDraft,
    resetStreamState,
    appendReasoning,
    appendContent,
    setProgressMessage,
    resetDesignStreamState,
    appendDesignReasoning,
    appendDesignContent,
    setDesignProgressMessage,
  }
})
