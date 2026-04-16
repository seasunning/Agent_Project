<template>
  <main class="shell">
    <section class="hero-card">
      <div>
        <p class="eyebrow">Phase 4</p>
        <h1>代码原型自动生成</h1>
        <p class="lead">基于 Phase 3 的设计方案，自动生成项目摘要、技术栈、文件树、关键文件源码与启动步骤，帮助你快速进入实现阶段。</p>
      </div>
      <div class="hero-actions">
        <router-link class="ghost-link" to="/design">返回设计方案</router-link>
        <router-link class="ghost-link" to="/">返回工作台</router-link>
      </div>
    </section>

    <section class="layout" :class="{ collapsed: sidebarCollapsed }">
      <article class="panel control-panel sidebar-panel" :class="{ collapsed: sidebarCollapsed }">
        <div class="panel-head" :class="{ collapsed: sidebarCollapsed }">
          <template v-if="!sidebarCollapsed">
            <h2>代码生成控制台</h2>
            <div class="panel-head-actions">
              <span class="tag" v-if="workspace.designResult">已检测到设计结果</span>
              <button class="collapse-button" type="button" @click="sidebarCollapsed = true">收起</button>
            </div>
          </template>
          <template v-else>
            <button class="collapsed-rail" type="button" @click="sidebarCollapsed = false">
              <span class="collapsed-rail-icon">›</span>
              <span class="collapsed-rail-text">代码生成控制台</span>
            </button>
          </template>
        </div>

        <template v-if="!sidebarCollapsed">
        <div v-if="!workspace.designResult" class="placeholder small">
          请先在设计方案页完成 Phase 3。
        </div>

        <template v-else>
          <div class="mode-switcher">
            <button class="mode-button" :class="{ selected: selectedMode === 'fast' }" :disabled="loading || previewing" @click="selectMode('fast')">快速模式</button>
            <button class="mode-button" :class="{ selected: selectedMode === 'deep' }" :disabled="loading || previewing" @click="selectMode('deep')">深度模式</button>
            <button class="mode-button test-button" :disabled="loading || previewing" @click="handlePreviewTest">{{ previewing ? '测试预览中...' : '测试按钮' }}</button>
          </div>

          <p class="mode-tip">{{ selectedMode === 'fast' ? '快速模式优先给出核心目录结构与关键骨架文件。' : '深度模式会给出更完整的文件树、代码原型与启动说明。' }}</p>

          <section class="summary-card">
            <h3>架构风格</h3>
            <p>{{ workspace.designResult.architecture_style }}</p>
          </section>

          <section class="summary-card">
            <h3>模块数</h3>
            <p>{{ workspace.designResult.modules.length }} 个</p>
          </section>

          <section class="selector-card">
            <div class="selector-head">
              <h3>技术选型</h3>
              <div class="selector-actions">
                <button class="secondary" :disabled="loading || selecting" @click="smartSelect">智能选型</button>
                <span class="tag pick-tag">{{ workspace.codegenAutoSelected ? '已智能选型' : '生成前必选' }}</span>
              </div>
            </div>

            <div class="mini-stream-box" v-if="selecting || workspace.codegenSuggestStream">
              <div class="mini-stream-head">
                <strong>智能选型输出</strong>
                <span>{{ selecting ? '流式输出中' : '已完成' }}</span>
              </div>
              <pre>{{ workspace.codegenSuggestStream || '等待模型输出...' }}</pre>
            </div>

            <label class="field-label">编程语言</label>
            <div class="chip-row">
              <button v-for="item in languages" :key="item" class="chip-button" :class="{ selected: codegenOptions.language === item }" @click="setLanguage(item)">{{ item }}</button>
            </div>
            <input v-model="customLanguage" class="field-input" placeholder="或输入自定义语言，例如 Go / Rust / Kotlin" @blur="applyCustomLanguage" />

            <label class="field-label">后端框架</label>
            <div v-if="!codegenOptions.language" class="hint-box">请先选择编程语言，再选择对应的后端框架。</div>
            <template v-else>
              <div class="chip-row">
                <button v-for="item in currentBackendFrameworks" :key="item" class="chip-button" :class="{ selected: codegenOptions.backend_framework === item }" @click="setBackendFramework(item)">{{ item }}</button>
              </div>
              <input v-model="customBackendFramework" class="field-input" placeholder="或输入自定义后端框架" @blur="applyCustomBackendFramework" />
            </template>

            <label class="field-label">前端框架</label>
            <div class="chip-row">
              <button v-for="item in frontendFrameworks" :key="item" class="chip-button" :class="{ selected: codegenOptions.frontend_framework === item }" @click="setFrontendFramework(item)">{{ item }}</button>
            </div>
            <input v-model="customFrontendFramework" class="field-input" placeholder="或输入自定义前端框架" @blur="applyCustomFrontendFramework" />

            <label class="field-label">数据库</label>
            <div class="chip-row">
              <button v-for="item in databases" :key="item" class="chip-button" :class="{ selected: codegenOptions.database === item }" @click="setDatabase(item)">{{ item }}</button>
            </div>
            <input v-model="customDatabase" class="field-input" placeholder="或输入自定义数据库，例如 MongoDB / Redis / TiDB" @blur="applyCustomDatabase" />

            <div class="selection-preview">
              <strong>当前选择：</strong>
              <p>{{ selectionSummary }}</p>
            </div>

            <label class="field-label">项目名称</label>
            <input v-model="projectName" class="field-input" placeholder="可自定义项目名；留空则自动提取“...系统”名称" />
            <div class="hint-box">覆盖策略固定为“另存为新目录”，若重名将自动追加 (1)、(2)...</div>
          </section>

          <button class="primary" :disabled="loading" @click="handleGenerate">
            {{ loading ? '流式生成中...' : '生成代码原型' }}
          </button>

          <div class="loading-panel" v-if="loading">
            <div class="spinner"></div>
            <div>
              <strong>实时状态</strong>
              <p>{{ workspace.codegenProgressMessage }}</p>
            </div>
          </div>
        </template>
        </template>
      </article>

      <article class="panel result-panel">
        <div class="panel-head">
          <h2>代码原型结果</h2>
          <div class="toolbar" v-if="result">
            <button class="secondary" :disabled="persisting" @click="handlePersistProject">{{ persisting ? '工程落盘中...' : 'Phase 5：落盘工程' }}</button>
            <button class="secondary" @click="exportCodegenJson">下载 JSON</button>
            <button class="secondary" @click="exportCodegenMarkdown">下载 Markdown</button>
            <button class="secondary" :disabled="persisting" @click="handleDownloadArchive">下载压缩包</button>
          </div>
          <span class="tag active" v-if="result">已生成</span>
          <span class="tag active stream" v-else-if="loading">流式输出中</span>
        </div>

        <div v-if="!result && !loading" class="placeholder">
          还没有代码原型结果。请先完成技术选型，再执行代码生成。
        </div>

        <template v-if="loading">
          <section class="result-block">
            <h3>进度提示</h3>
            <p>{{ workspace.codegenProgressMessage }}</p>
          </section>
          <section class="result-block" v-if="workspace.codegenStreamingReasoning">
            <h3>实时推理流</h3>
            <pre>{{ workspace.codegenStreamingReasoning }}</pre>
          </section>
          <section class="result-block" v-if="workspace.codegenStreamingContent">
            <h3>实时回答流</h3>
            <pre>{{ workspace.codegenStreamingContent }}</pre>
          </section>
        </template>

        <template v-if="result">
          <section class="result-block">
            <h3>项目摘要</h3>
            <p>{{ result.project_summary }}</p>
          </section>

          <section class="result-block" v-if="persistResult">
            <div class="result-head-inline">
              <h3>Phase 5：工程落地结果</h3>
              <span class="tag active">已落盘</span>
            </div>
            <p><strong>工程目录：</strong>{{ persistResult.output_path }}</p>
            <p><strong>项目名称：</strong>{{ persistResult.project_name }}</p>
            <p><strong>写入文件数：</strong>{{ persistResult.written_files.length }}</p>
            <p v-if="persistResult.startup_script"><strong>启动说明文件：</strong>{{ persistResult.startup_script }}</p>
            <p v-if="persistResult.archive_name"><strong>压缩包：</strong>{{ persistResult.archive_name }}</p>
          </section>

          <section class="double-grid">
            <div class="result-block compact tech-stack-panel">
              <h3>技术栈</h3>
              <ul v-if="result.tech_stack.length">
                <li v-for="item in result.tech_stack" :key="item">{{ item }}</li>
              </ul>
              <p v-else class="empty-tip">暂无技术栈数据</p>
            </div>
            <div class="result-block compact">
              <h3>启动步骤</h3>
              <ol>
                <li v-for="item in result.startup_steps" :key="item">{{ item }}</li>
              </ol>
            </div>
          </section>

          <section class="result-block">
            <div class="result-head-inline">
              <h3>项目文件树</h3>
              <button class="secondary copy-button" @click="copyText(result.file_tree, '文件树已复制')">复制文件树</button>
            </div>
            <pre class="tree-view">{{ result.file_tree }}</pre>
          </section>

          <section class="result-block ide-block">
            <div class="result-head-inline ide-section-head">
              <div>
                <h3>关键源码文件</h3>
                <p class="section-subtitle">像通用 IDE 一样切换文件与预览代码</p>
              </div>
              <span class="tag files-tag">{{ result.files.length }} 个文件</span>
            </div>
            <div class="ide-layout" v-if="result.files.length">
              <aside class="ide-sidebar">
                <div class="ide-sidebar-head">
                  <span class="traffic traffic-red"></span>
                  <span class="traffic traffic-amber"></span>
                  <span class="traffic traffic-green"></span>
                  <strong>EXPLORER</strong>
                </div>
                <div class="explorer-caption">PROJECT</div>
                <div class="ide-tree">
                  <button
                    v-for="row in explorerRows"
                    :key="row.path"
                    class="ide-tree-row"
                    :class="[row.kind, { active: row.filePath === activeFile?.path }]"
                    :style="{ paddingLeft: `${14 + row.depth * 16}px` }"
                    :disabled="!row.filePath"
                    @click="row.filePath && (activeFilePath = row.filePath)"
                  >
                    <span class="tree-node-icon">{{ row.kind === 'folder' ? '▸' : '•' }}</span>
                    <span class="tree-node-name">{{ row.name }}</span>
                    <span v-if="row.kind === 'file' && row.language" class="tree-node-meta">{{ row.language }}</span>
                  </button>
                </div>
              </aside>
              <section class="ide-preview" v-if="activeFile">
                <div class="ide-preview-chrome">
                  <div class="ide-preview-tabs">
                    <button class="preview-tab active">{{ activeFile.path.split('/').pop() }}</button>
                  </div>
                  <button class="secondary copy-button" @click="copyText(activeFile.content, `${activeFile.path} 已复制`)">复制代码</button>
                </div>
                <div class="ide-preview-head">
                  <div>
                    <strong>{{ activeFile.path }}</strong>
                    <p>{{ activeFile.description }}</p>
                  </div>
                  <div class="ide-preview-actions">
                    <span class="file-lang">{{ activeFile.language }}</span>
                  </div>
                </div>
                <div class="ide-breadcrumbs">
                  <span v-for="(crumb, index) in activeFileCrumbs" :key="`${crumb}-${index}`">
                    {{ crumb }}<em v-if="index < activeFileCrumbs.length - 1">/</em>
                  </span>
                </div>
                <div class="code-frame">
                  <div class="code-gutter">
                    <span v-for="(_, index) in activeFileLineEntries" :key="`line-${index}`">{{ index + 1 }}</span>
                  </div>
                  <div class="code-view" aria-label="源码预览">
                    <div v-for="(line, index) in activeFileLineEntries" :key="`code-${index}`" class="code-line">{{ line || ' ' }}</div>
                  </div>
                </div>
              </section>
            </div>
            <p v-else class="empty-tip">暂无关键源码文件</p>
          </section>

          <section class="result-block">
            <h3>模型原始输出</h3>
            <pre>{{ result.raw_model_output }}</pre>
          </section>

          <section class="result-block" v-if="result.reasoning_content">
            <h3>思考内容</h3>
            <pre>{{ result.reasoning_content }}</pre>
          </section>
        </template>
      </article>
    </section>

    <transition name="toast-fade">
      <div v-if="toastMessage" class="toast">{{ toastMessage }}</div>
    </transition>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  downloadCodeArchive,
  persistCodeProject,
  previewCodegen,
  streamGenerateCode,
  streamSuggestCodegenOptions,
  type CodePersistResponse,
  type CodeStreamEvent,
  type CodeSuggestStreamEvent,
  type CodegenOptions,
} from '../api/codegen'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const loading = ref(false)
const selecting = ref(false)
const previewing = ref(false)
const persisting = ref(false)
const sidebarCollapsed = ref(false)
const toastMessage = ref('')
const customLanguage = ref('')
const customBackendFramework = ref('')
const customFrontendFramework = ref('')
const customDatabase = ref('')
const projectName = ref('')
const activeFilePath = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null
const result = computed(() => workspace.codegenResult)
const persistResult = computed(() => workspace.codegenPersistResult)
const selectedMode = computed(() => workspace.codegenMode)
const codegenOptions = computed(() => workspace.codegenOptions)
const languages = ['Java', 'Python', 'C#', 'C++']
const frontendFrameworks = ['Vue 3', 'React', 'Angular', 'Thymeleaf', 'Qt']
const databases = ['MySQL', 'SQLite', 'PostgreSQL', '不需要']
const backendFrameworkMap: Record<string, string[]> = {
  Java: ['Spring Boot', 'Spring Cloud', 'Jakarta EE'],
  Python: ['FastAPI', 'Django', 'Flask'],
  'C#': ['.NET', 'ASP.NET Core'],
  'C++': ['Qt', 'Crow', 'Drogon'],
}
const currentBackendFrameworks = computed(() => backendFrameworkMap[codegenOptions.value.language] || [])
const selectionSummary = computed(() => {
  const { language, backend_framework, frontend_framework, database } = codegenOptions.value
  return `${language || '未选择语言'} / ${backend_framework || '未选择后端框架'} / ${frontend_framework || '未选择前端框架'} / ${database || '未选择数据库'}`
})
const explorerRows = computed(() => buildExplorerRows(result.value?.files ?? []))
const activeFile = computed(() => result.value?.files.find((file) => file.path === activeFilePath.value) ?? result.value?.files[0] ?? null)
const activeFileLineEntries = computed(() => normalizeCodeLines(activeFile.value?.content || ''))
const activeFileCrumbs = computed(() => activeFile.value?.path.split('/') ?? [])

function normalizeCodeLines(content: string) {
  const normalized = content.replace(/\r\n/g, '\n')
  const lines = normalized.split('\n')
  return lines.length ? lines : ['']
}

type ExplorerRow = {
  path: string
  name: string
  depth: number
  kind: 'folder' | 'file'
  filePath: string | null
  language?: string
}

function buildExplorerRows(files: { path: string; language: string }[]): ExplorerRow[] {
  const rows: ExplorerRow[] = []
  const seenFolders = new Set<string>()

  for (const file of files) {
    const parts = file.path.split('/').filter(Boolean)
    let currentPath = ''

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const isFile = index === parts.length - 1

      if (isFile) {
        rows.push({
          path: currentPath,
          name: part,
          depth: index,
          kind: 'file',
          filePath: file.path,
          language: file.language,
        })
        return
      }

      if (!seenFolders.has(currentPath)) {
        seenFolders.add(currentPath)
        rows.push({
          path: currentPath,
          name: part,
          depth: index,
          kind: 'folder',
          filePath: null,
        })
      }
    })
  }

  return rows
}

function selectMode(mode: 'fast' | 'deep') {
  workspace.setCodegenMode(mode)
}

function updateOptions(partial: Partial<CodegenOptions>) {
  workspace.setCodegenOptions({ ...codegenOptions.value, ...partial })
  workspace.setCodegenAutoSelected(false)
}

function setLanguage(value: string) {
  customLanguage.value = ''
  customBackendFramework.value = ''
  updateOptions({ language: value, backend_framework: '' })
}

function setBackendFramework(value: string) {
  customBackendFramework.value = ''
  updateOptions({ backend_framework: value })
}

function setFrontendFramework(value: string) {
  customFrontendFramework.value = ''
  updateOptions({ frontend_framework: value })
}

function setDatabase(value: string) {
  customDatabase.value = ''
  updateOptions({ database: value })
}

function applyCustomLanguage() {
  if (customLanguage.value.trim()) {
    updateOptions({ language: customLanguage.value.trim(), backend_framework: '' })
  }
}

function applyCustomBackendFramework() {
  if (customBackendFramework.value.trim()) updateOptions({ backend_framework: customBackendFramework.value.trim() })
}

function applyCustomFrontendFramework() {
  if (customFrontendFramework.value.trim()) updateOptions({ frontend_framework: customFrontendFramework.value.trim() })
}

function applyCustomDatabase() {
  if (customDatabase.value.trim()) updateOptions({ database: customDatabase.value.trim() })
}

function handleSuggestEvent(event: CodeSuggestStreamEvent) {
  if (event.type === 'status' || event.type === 'content') {
    workspace.appendCodegenSuggestStream(event.content)
  } else if (event.type === 'result' && event.result) {
    workspace.setCodegenOptions(event.result.options)
    workspace.setCodegenAutoSelected(true)
    customLanguage.value = ''
    customBackendFramework.value = ''
    customFrontendFramework.value = ''
    customDatabase.value = ''
  }
}

async function smartSelect() {
  const design = workspace.designResult
  if (!design) {
    showToast('请先完成设计方案生成。')
    return
  }
  selecting.value = true
  workspace.resetCodegenSuggestStream()
  try {
    await streamSuggestCodegenOptions(design, handleSuggestEvent)
    showToast('已通过模型完成智能选型。')
  } catch (error) {
    console.error(error)
    showToast('智能选型失败，请稍后重试或手动选择。')
  } finally {
    selecting.value = false
  }
}

function isSelectionComplete() {
  const { language, backend_framework, frontend_framework, database } = codegenOptions.value
  return Boolean(language.trim() && backend_framework.trim() && frontend_framework.trim() && database.trim())
}

function handleStreamEvent(event: CodeStreamEvent) {
  if (event.type === 'status') workspace.setCodegenProgressMessage(event.content)
  else if (event.type === 'reasoning') {
    workspace.appendCodegenReasoning(event.content)
    workspace.setCodegenProgressMessage('正在输出代码推理内容...')
  } else if (event.type === 'content') {
    workspace.appendCodegenContent(event.content)
    workspace.setCodegenProgressMessage('正在流式输出两阶段生成内容...')
  } else if (event.type === 'result' && event.result) {
    workspace.setCodegenResult(event.result)
    workspace.setCodegenProgressMessage('代码原型结果已生成')
  } else if (event.type === 'done') workspace.setCodegenProgressMessage(event.content || '代码原型生成完成')
  else if (event.type === 'error') workspace.setCodegenProgressMessage(event.content || '代码原型生成失败')
}

async function handleGenerate() {
  if (!workspace.designResult) {
    alert('请先完成设计方案生成。')
    return
  }
  applyCustomLanguage()
  applyCustomBackendFramework()
  applyCustomFrontendFramework()
  applyCustomDatabase()
  if (!isSelectionComplete()) {
    showToast('请先选择编程语言、前后端框架和数据库后再生成代码原型。')
    return
  }
  loading.value = true
  workspace.setCodegenResult(null)
  workspace.setCodegenPersistResult(null)
  activeFilePath.value = ''
  workspace.resetCodegenStreamState()
  workspace.setCodegenProgressMessage(selectedMode.value === 'deep' ? '深度模式已启动，准备流式生成代码原型...' : '快速模式已启动，准备流式生成代码骨架...')
  try {
    await streamGenerateCode(workspace.designResult, codegenOptions.value, selectedMode.value, handleStreamEvent)
  } catch (error) {
    console.error(error)
    workspace.setCodegenProgressMessage('代码原型生成失败，请检查后端服务或网络连接。')
    alert('代码原型生成失败，请检查后端服务或模型配置。')
  } finally {
    loading.value = false
  }
}

async function handlePersistProject() {
  if (!result.value) return persistResult.value
  persisting.value = true
  try {
    const response: CodePersistResponse = await persistCodeProject(result.value, projectName.value.trim(), codegenOptions.value)
    workspace.setCodegenPersistResult(response)
    if (!projectName.value.trim()) projectName.value = response.project_name
    showToast(`工程已写入 ${response.output_path}`)
    return response
  } catch (error) {
    console.error(error)
    showToast('工程落盘失败，请检查后端权限或路径配置。')
    return null
  } finally {
    persisting.value = false
  }
}

async function handlePreviewTest() {
  if (!workspace.designResult) {
    showToast('请先完成设计方案生成。')
    return
  }
  applyCustomLanguage()
  applyCustomBackendFramework()
  applyCustomFrontendFramework()
  applyCustomDatabase()
  if (!isSelectionComplete()) {
    showToast('请先完成技术选型后再执行测试预览。')
    return
  }
  previewing.value = true
  workspace.setCodegenPersistResult(null)
  workspace.setCodegenProgressMessage('正在生成测试预览...')
  try {
    const previewResult = await previewCodegen(workspace.designResult, codegenOptions.value, selectedMode.value)
    workspace.setCodegenResult(previewResult)
    activeFilePath.value = ''
    workspace.setCodegenProgressMessage('测试预览完成：仅生成文件树与一句话文件占位，不落盘。')
    showToast('测试预览完成，不会保存落地。')
  } catch (error) {
    console.error(error)
    showToast('测试预览失败，请稍后重试。')
  } finally {
    previewing.value = false
  }
}

async function handleDownloadArchive() {
  const persisted = await handlePersistProject()
  const archiveName = persisted?.archive_name || persistResult.value?.archive_name
  if (!archiveName) return
  try {
    const blob = await downloadCodeArchive(archiveName)
    downloadBlob(archiveName, blob)
    showToast('压缩包已开始下载')
  } catch (error) {
    console.error(error)
    showToast('压缩包下载失败，请稍后重试。')
  }
}

function timestampedName(prefix: string, extension: string) {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  return `${prefix}-${stamp}.${extension}`
}

function downloadFile(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type })
  downloadBlob(filename, blob)
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function exportCodegenJson() {
  if (!result.value) return
  downloadFile(timestampedName('codegen-result', 'json'), JSON.stringify(result.value, null, 2), 'application/json')
}

function exportCodegenMarkdown() {
  if (!result.value) return
  const markdown = `# 代码原型结果\n\n## 项目摘要\n${result.value.project_summary}\n\n## 技术栈\n${result.value.tech_stack.map((item) => `- ${item}`).join('\n')}\n\n## 启动步骤\n${result.value.startup_steps.map((item, index) => `${index + 1}. ${item}`).join('\n')}\n\n## 项目文件树\n\n\`\`\`\n${result.value.file_tree}\n\`\`\`\n\n## 关键源码文件\n${result.value.files.map((file) => `### ${file.path}\n- 语言：${file.language}\n- 说明：${file.description}\n\n\`\`\`\n${file.content}\n\`\`\``).join('\n\n')}`
  downloadFile(timestampedName('codegen-result', 'md'), markdown, 'text/markdown;charset=utf-8')
}

async function copyText(text: string, message: string) {
  try {
    await navigator.clipboard.writeText(text)
    showToast(message)
  } catch (error) {
    console.error(error)
    showToast('复制失败，请手动复制。')
  }
}

function showToast(message: string) {
  toastMessage.value = message
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toastMessage.value = ''
  }, 2200)
}
</script>

<style scoped>
.shell { min-height: 100vh; padding: 32px; color: #f4efe8; background: radial-gradient(circle at left top, rgba(14,165,233,.2), transparent 28%), radial-gradient(circle at right top, rgba(251,191,36,.18), transparent 24%), linear-gradient(135deg, #07111b 0%, #111827 48%, #1e1530 100%); font-family: 'Cambria', 'Times New Roman', serif; }
.hero-card,.panel,.result-block,.summary-card,.selector-card { border: 1px solid rgba(244,238,232,.12); border-radius: 24px; background: rgba(17,24,39,.62); backdrop-filter: blur(14px); box-shadow: 0 18px 50px rgba(0,0,0,.24); }
.hero-card { display: flex; justify-content: space-between; gap: 24px; padding: 28px 30px; margin-bottom: 24px; }
.hero-actions,.mode-switcher,.chip-row,.selector-actions,.toolbar,.ide-preview-actions,.panel-head-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.ide-accent { color: #7dd3fc; }
.eyebrow { margin: 0 0 10px; letter-spacing: .2em; text-transform: uppercase; color: #38bdf8; font-size: 12px; }
h1 { margin: 0; font-size: 42px; }
.lead { max-width: 760px; color: rgba(244,238,232,.78); line-height: 1.9; }
.ghost-link,.primary,.mode-button,.secondary,.chip-button { display: inline-flex; align-items: center; justify-content: center; padding: 10px 16px; border-radius: 999px; text-decoration: none; font-weight: 700; }
.ghost-link { border: 1px solid rgba(244,238,232,.2); color: #f4efe8; }
.primary { border: none; background: linear-gradient(135deg, #38bdf8, #facc15); color: #08111d; cursor: pointer; }
.mode-button,.secondary,.chip-button { border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.05); color: #f4efe8; cursor: pointer; }
.mode-button.selected,.chip-button.selected { background: linear-gradient(135deg, #38bdf8, #facc15); color: #08111d; }
.primary:disabled,.mode-button:disabled,.secondary:disabled { opacity: .6; cursor: not-allowed; }
.layout { display: grid; grid-template-columns: 420px 1fr; gap: 24px; align-items: start; }
.layout.collapsed { grid-template-columns: 64px minmax(0, 1fr); }
.panel { padding: 24px; }
.sidebar-panel.collapsed { padding: 12px 10px; }
.result-panel { min-width: 0; }
.panel-head,.result-head-inline,.file-head,.selector-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 16px; }
.panel-head.collapsed { margin: 0; justify-content: center; }
.mode-tip { margin: 0 0 16px; color: rgba(244,238,232,.74); line-height: 1.8; }
.tag { padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,.08); color: rgba(244,238,232,.72); font-size: 12px; }
.tag.active { background: rgba(16,185,129,.18); color: #a7f3d0; }
.tag.stream { background: rgba(59,130,246,.2); color: #93c5fd; }
.files-tag,.pick-tag { background: rgba(56,189,248,.16); color: #bae6fd; }
.summary-card,.result-block,.selector-card { padding: 18px 20px; }
.summary-card + .summary-card,.selector-card { margin-top: 14px; }
.field-label { display: block; margin: 14px 0 8px; color: #c7e8ff; font-weight: 700; }
.field-input { width: 100%; min-height: 48px; border: 1px solid rgba(244,238,232,.12); border-radius: 16px; background: rgba(8,17,29,.8); color: #f4efe8; padding: 12px 14px; font: inherit; }
.selection-preview,.hint-box,.mini-stream-box { margin-top: 16px; padding: 14px 16px; border-radius: 18px; background: rgba(56,189,248,.08); }
.selection-preview p,.hint-box,.empty-tip { margin: 8px 0 0; color: rgba(244,238,232,.78); line-height: 1.8; }
.collapse-button { border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.04); color: #dbeafe; border-radius: 999px; padding: 8px 14px; cursor: pointer; font-weight: 700; }
.collapsed-rail { position: relative; width: 100%; min-height: 320px; border: 1px solid rgba(125,211,252,.18); border-radius: 20px; background: linear-gradient(180deg, rgba(15,23,42,.96), rgba(2,6,23,.98)); color: #dbeafe; display: flex; align-items: center; justify-content: center; gap: 10px; padding: 12px 8px; cursor: pointer; overflow: hidden; }
.collapsed-rail::before { content: ''; position: absolute; inset: 8px; border-radius: 14px; border: 1px solid rgba(255,255,255,.05); background: linear-gradient(180deg, rgba(56,189,248,.08), rgba(255,255,255,.01)); }
.collapsed-rail::after { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 3px; border-radius: 999px; background: linear-gradient(180deg, #38bdf8, #facc15); box-shadow: 0 0 18px rgba(56,189,248,.4); }
.collapsed-rail-icon,.collapsed-rail-text { position: relative; z-index: 1; }
.collapsed-rail-icon { font-size: 18px; line-height: 1; color: #7dd3fc; }
.collapsed-rail-text { font-weight: 700; writing-mode: vertical-rl; text-orientation: mixed; letter-spacing: .18em; text-transform: uppercase; }
.mini-stream-box { height: 180px; overflow: hidden; }
.mini-stream-head { display: flex; justify-content: space-between; margin-bottom: 10px; color: #c7e8ff; }
.mini-stream-box pre { height: 120px; overflow: auto; background: rgba(3, 7, 18, 0.45); border-radius: 12px; padding: 12px; }
.placeholder { min-height: 240px; display: grid; place-items: center; color: rgba(244,238,232,.56); border: 1px dashed rgba(244,238,232,.14); border-radius: 20px; }
.placeholder.small { min-height: 160px; margin-bottom: 16px; }
.loading-panel { margin-top: 18px; display: flex; align-items: center; gap: 14px; border-radius: 18px; padding: 14px 16px; background: rgba(59,130,246,.12); }
.spinner { width: 18px; height: 18px; border-radius: 50%; border: 3px solid rgba(255,255,255,.18); border-top-color: #38bdf8; animation: spin .8s linear infinite; }
.result-panel { display: flex; flex-direction: column; gap: 18px; }
.double-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.compact ul,.compact ol { margin: 0; padding-left: 18px; line-height: 1.8; }
.tech-stack-panel { min-height: 220px; }
.ide-block { padding: 0; overflow: hidden; background: linear-gradient(180deg, rgba(8, 15, 29, 0.96), rgba(12, 20, 35, 0.92)); border: 1px solid rgba(125, 211, 252, 0.12); }
.ide-section-head { padding: 20px 22px 0; margin-bottom: 0; }
.section-subtitle { margin: 8px 0 0; color: rgba(244,238,232,.56); font-size: 13px; }
.ide-layout { display: grid; grid-template-columns: 300px 1fr; min-height: 560px; margin-top: 16px; }
.ide-sidebar { background: linear-gradient(180deg, rgba(3, 7, 18, 0.96), rgba(8, 15, 29, 0.98)); border-right: 1px solid rgba(255,255,255,.08); padding: 14px; display: flex; flex-direction: column; gap: 12px; }
.ide-sidebar-head { display: flex; align-items: center; gap: 8px; padding: 8px 10px 6px; color: #9cc8ff; font-size: 12px; letter-spacing: .12em; }
.explorer-caption { padding: 0 10px 10px; color: rgba(148, 163, 184, 0.85); font-size: 11px; letter-spacing: .16em; text-transform: uppercase; }
.ide-tree { display: grid; gap: 4px; overflow: auto; padding-right: 4px; }
.ide-tree-row { width: 100%; min-height: 34px; border-radius: 10px; border: 1px solid transparent; background: transparent; color: #dbeafe; display: grid; grid-template-columns: 14px minmax(0, 1fr) auto; align-items: center; gap: 8px; padding: 0 10px; text-align: left; cursor: pointer; transition: background .18s ease, border-color .18s ease, color .18s ease; }
.ide-tree-row:hover:not(:disabled) { background: rgba(56,189,248,.08); border-color: rgba(125,211,252,.14); }
.ide-tree-row.active { background: linear-gradient(135deg, rgba(56,189,248,.18), rgba(250,204,21,.14)); border-color: rgba(125,211,252,.22); color: #f8fafc; }
.ide-tree-row.folder { color: #94a3b8; cursor: default; }
.ide-tree-row.folder:hover { background: transparent; border-color: transparent; }
.ide-tree-row:disabled { opacity: 1; }
.tree-node-icon { color: #7dd3fc; font-size: 12px; }
.tree-node-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-node-meta { font-size: 10px; padding: 2px 8px; border-radius: 999px; background: rgba(255,255,255,.08); color: rgba(226,232,240,.9); }
.ide-preview { padding: 0; display: flex; flex-direction: column; min-width: 0; background: linear-gradient(180deg, rgba(5, 10, 20, 0.55), rgba(10, 18, 31, 0.78)); }
.ide-preview-chrome { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 14px 18px; border-bottom: 1px solid rgba(255,255,255,.08); background: rgba(255,255,255,.02); }
.ide-preview-tabs { display: flex; gap: 8px; overflow: auto; }
.preview-tab { border: 1px solid rgba(255,255,255,.08); background: rgba(255,255,255,.04); color: #dbeafe; border-radius: 12px 12px 0 0; padding: 10px 14px; font-weight: 700; }
.preview-tab.active { background: rgba(14,165,233,.14); border-color: rgba(125,211,252,.2); }
.ide-preview-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 18px 20px 12px; margin-bottom: 0; }
.ide-preview-head p { margin: 8px 0 0; color: rgba(244,238,232,.72); line-height: 1.7; }
.ide-breadcrumbs { padding: 0 20px 14px; color: rgba(148, 163, 184, 0.92); font-size: 12px; display: flex; gap: 6px; flex-wrap: wrap; }
.ide-breadcrumbs em { margin-left: 6px; font-style: normal; opacity: .55; }
.code-frame { display: grid; grid-template-columns: 64px minmax(0, 1fr); flex: 1; min-height: 0; border-top: 1px solid rgba(255,255,255,.06); }
.code-gutter { background: rgba(255,255,255,.02); border-right: 1px solid rgba(255,255,255,.06); padding: 18px 10px; color: rgba(148,163,184,.75); font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; line-height: 1.8; text-align: right; user-select: none; }
.code-gutter span { display: block; height: 1.8em; }
.file-lang { display: inline-block; margin-bottom: 10px; padding: 4px 10px; border-radius: 999px; background: rgba(56,189,248,.12); color: #bae6fd; font-size: 12px; }
.copy-button { background: rgba(56,189,248,.12); color: #d8f6ff; }
pre { margin: 0; white-space: pre-wrap; word-break: break-word; line-height: 1.7; color: #f3eadb; }
.tree-view { white-space: pre; overflow: auto; font-family: 'Consolas', 'Courier New', monospace; background: rgba(3, 7, 18, 0.45); padding: 16px; border-radius: 16px; }
.code-view { overflow: auto; font-family: 'Consolas', 'Courier New', monospace; background: linear-gradient(180deg, rgba(2,6,23,.35), rgba(15,23,42,.1)); padding: 18px 20px; line-height: 1.8; min-height: 420px; white-space: pre; }
.code-line { min-height: 1.8em; }
.toast { position: fixed; right: 24px; bottom: 24px; z-index: 40; padding: 14px 16px; border-radius: 16px; background: rgba(14,165,233,.18); border: 1px solid rgba(125,211,252,.18); color: #e0f2fe; box-shadow: 0 20px 40px rgba(0,0,0,.2); }
.toast-fade-enter-active,.toast-fade-leave-active { transition: opacity .2s ease, transform .2s ease; }
.toast-fade-enter-from,.toast-fade-leave-to { opacity: 0; transform: translateY(8px); }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 1100px) { .layout,.double-grid,.ide-layout { grid-template-columns: 1fr; } .layout.collapsed { grid-template-columns: 52px minmax(0, 1fr); } .ide-sidebar { max-height: 280px; } .code-frame { grid-template-columns: 52px minmax(0, 1fr); } .collapsed-rail { min-height: 240px; } }
@media (max-width: 720px) { .shell { padding: 16px; } .hero-card,.panel-head,.result-head-inline,.selector-head,.ide-preview-head,.ide-preview-chrome { flex-direction: column; align-items: flex-start; } .hero-actions,.mode-switcher,.chip-row,.selector-actions,.toolbar,.ide-preview-actions,.panel-head-actions { flex-wrap: wrap; } h1 { font-size: 32px; } }
</style>
