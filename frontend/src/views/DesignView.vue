<template>
  <main class="shell">
    <section class="hero-card">
      <div>
        <p class="eyebrow">Phase 3</p>
        <h1>设计方案自动生成</h1>
        <p class="lead">基于 Phase 2 结构化需求，支持快速/深度两种模式流式生成架构方案，并支持 Mermaid 图形/代码切换。</p>
      </div>
      <div class="hero-actions">
        <router-link class="ghost-link" to="/requirements">返回需求分析</router-link>
        <router-link class="ghost-link" to="/">返回工作台</router-link>
      </div>
    </section>

    <section class="layout" :class="{ collapsed: sidebarCollapsed }">
      <article class="panel control-panel sidebar-panel" :class="{ collapsed: sidebarCollapsed }">
        <div class="panel-head" :class="{ collapsed: sidebarCollapsed }">
          <template v-if="!sidebarCollapsed">
            <h2>设计生成控制台</h2>
            <div class="panel-head-actions">
              <span class="tag" v-if="workspace.requirementResult">已检测到需求结果</span>
              <button class="collapse-button" type="button" @click="sidebarCollapsed = true">收起</button>
            </div>
          </template>
          <template v-else>
            <button class="collapsed-rail" type="button" @click="sidebarCollapsed = false">
              <span class="collapsed-rail-icon">›</span>
              <span class="collapsed-rail-text">设计生成控制台</span>
            </button>
          </template>
        </div>

        <template v-if="!sidebarCollapsed">
        <div v-if="!workspace.requirementResult" class="placeholder small">
          请先在需求分析页完成 Phase 2。
        </div>

        <template v-else>
          <div class="mode-switcher">
            <button class="mode-button" :class="{ selected: selectedMode === 'fast' }" :disabled="loading" @click="selectMode('fast')">快速模式</button>
            <button class="mode-button" :class="{ selected: selectedMode === 'deep' }" :disabled="loading" @click="selectMode('deep')">深度模式</button>
          </div>

          <p class="mode-tip">
            {{ selectedMode === 'fast' ? '快速模式更适合先得到架构草案与关键模块。' : '深度模式会开启 thinking，更适合产出更细的模块边界与接口设计。' }}
          </p>

          <section class="summary-card">
            <h3>需求摘要</h3>
            <p>{{ workspace.requirementResult.summary }}</p>
          </section>

          <section class="summary-card">
            <h3>功能数</h3>
            <p>{{ workspace.requirementResult.functional_requirements.length }} 个</p>
          </section>

        <div class="actions-row">
          <button class="primary" :disabled="loading" @click="handleGenerate">
            {{ loading ? '流式生成中...' : '生成设计方案' }}
          </button>
          <router-link class="primary outline-primary" to="/codegen">进入代码生成阶段</router-link>
        </div>

          <div class="loading-panel" v-if="loading">
            <div class="spinner"></div>
            <div>
              <strong>实时状态</strong>
              <p>{{ workspace.designProgressMessage }}</p>
            </div>
          </div>
        </template>
        </template>
      </article>

      <article class="panel result-panel">
        <div class="panel-head">
          <h2>设计方案结果</h2>
          <div class="toolbar" v-if="design">
            <button class="secondary action-pill strong-pill" @click="toggleEdit">{{ editing ? '取消编辑' : '编辑结果' }}</button>
            <button class="secondary action-pill" @click="exportDesignJson">导出 JSON</button>
            <button class="secondary action-pill" @click="exportDesignMarkdown">导出 Markdown</button>
          </div>
          <div class="status-badges" v-if="design">
            <span class="tag edited-tag" v-if="isDesignEdited">当前为编辑后版本</span>
            <span class="tag draft-tag" v-if="workspace.designEditDraft && !editing">存在未保存草稿</span>
            <span class="tag active" v-if="design && !editing">已生成</span>
            <span class="tag active stream" v-else-if="loading">流式输出中</span>
            <span class="tag active edit-tag" v-else-if="editing">编辑中</span>
          </div>
        </div>

        <div v-if="!design && !loading" class="placeholder">
          还没有设计结果。请先生成需求分析结果，再执行设计方案生成。
        </div>

        <template v-if="loading">
          <section class="result-block">
            <h3>进度提示</h3>
            <p>{{ workspace.designProgressMessage }}</p>
          </section>
          <section class="result-block" v-if="workspace.designStreamingReasoning">
            <h3>实时推理流</h3>
            <pre>{{ workspace.designStreamingReasoning }}</pre>
          </section>
          <section class="result-block" v-if="workspace.designStreamingContent">
            <h3>实时回答流</h3>
            <pre>{{ workspace.designStreamingContent }}</pre>
          </section>
        </template>

        <template v-if="design && !editing">
          <section class="result-block">
            <h3>架构风格</h3>
            <p class="architecture">{{ design.architecture_style }}</p>
            <p>{{ design.architecture_rationale }}</p>
          </section>

          <section class="result-block">
            <h3>模块划分</h3>
            <ul class="cards">
              <li v-for="item in design.modules" :key="item.name">
                <strong>{{ item.name }}</strong>
                <p>{{ item.responsibility }}</p>
                <small>输入：{{ item.inputs.join('、') || '无' }}</small>
                <small>输出：{{ item.outputs.join('、') || '无' }}</small>
              </li>
            </ul>
          </section>

          <section class="double-grid">
            <div class="result-block compact">
              <h3>接口定义</h3>
              <ul>
                <li v-for="api in design.apis" :key="`${api.method}-${api.path}`">
                  <strong>{{ api.method }} {{ api.path }}</strong>
                  <p>{{ api.name }}：{{ api.description }}</p>
                </li>
              </ul>
            </div>
            <div class="result-block compact">
              <h3>数据实体</h3>
              <ul>
                <li v-for="entity in design.data_entities" :key="entity.name">
                  <strong>{{ entity.name }}</strong>
                  <p>{{ entity.fields.join('、') }}</p>
                </li>
              </ul>
            </div>
          </section>

          <section class="result-block">
            <div class="result-head-inline">
              <h3>Mermaid 图描述</h3>
              <div class="view-switcher">
                <button class="view-button" :class="{ selected: mermaidView === 'diagram' }" @click="mermaidView = 'diagram'">图形视图</button>
                <button class="view-button" :class="{ selected: mermaidView === 'code' }" @click="mermaidView = 'code'">代码视图</button>
                <button class="view-button copy-button" @click="copyMermaidCode">复制 Mermaid</button>
              </div>
            </div>
            <div v-if="mermaidView === 'diagram'" class="mermaid-stage">
              <div v-if="mermaidError" class="mermaid-error">{{ mermaidError }}</div>
              <div v-else class="mermaid-diagram" v-html="mermaidSvg"></div>
            </div>
            <pre v-else>{{ design.mermaid }}</pre>
          </section>

          <section class="result-block">
            <h3>模型原始输出</h3>
            <pre>{{ design.raw_model_output }}</pre>
          </section>

          <section class="result-block" v-if="design.reasoning_content">
            <h3>思考内容</h3>
            <pre>{{ design.reasoning_content }}</pre>
          </section>
        </template>

        <template v-if="editing && editableDesign">
          <section class="editor-shell">
            <div class="inline-toast success-toast floating-toast" v-if="toastMessage">{{ toastMessage }}</div>
            <div class="inline-banner" v-if="draftRecovered">已恢复上次未保存的草稿，你可以继续编辑或恢复原始结果。</div>
            <div class="editor-hero">
              <div>
                <p class="editor-kicker">Design Editor</p>
                <h3>可视化编辑设计方案</h3>
                <p>你可以直接修改架构风格、模块、接口、实体与 Mermaid 图描述，再保存回当前工作区结果。</p>
              </div>
              <div class="edit-actions floating-actions">
                <button class="ghost-button" @click="restoreOriginal">恢复原始结果</button>
                <button class="primary strong-primary" @click="saveEdit">保存修改</button>
                <button class="secondary action-pill" @click="toggleEdit">取消编辑</button>
              </div>
            </div>

            <section class="editor-grid top-grid">
              <div class="editor-card spotlight-card">
                <label class="field-label">架构风格</label>
                <input v-model="editableDesign.architecture_style" class="field-input" />
                <label class="field-label">架构说明</label>
                <textarea v-model="editableDesign.architecture_rationale" class="field-area short" />
              </div>
              <div class="editor-card mermaid-editor-card">
                <div class="section-head compact-head">
                  <h3>Mermaid 设计图</h3>
                  <button class="secondary action-pill mini-pill success-pill" @click="copyMermaidCode">复制 Mermaid</button>
                </div>
                <textarea v-model="editableDesign.mermaid" class="field-area mermaid-editor" />
              </div>
            </section>

            <section class="editor-card full-span-card glass-strong-card">
              <div class="section-head">
                <h3>模块划分</h3>
                <button class="secondary action-pill mini-pill" @click="addModule">新增模块</button>
              </div>
              <div class="entity-grid">
                <div class="edit-card module-card" v-for="(item, index) in editableDesign.modules" :key="`module-${index}`">
                  <div class="mini-head">
                    <span>模块 {{ index + 1 }}</span>
                    <button class="danger-button" @click="removeModule(index)">删除</button>
                  </div>
                  <input v-model="item.name" class="field-input" placeholder="模块名称" />
                  <textarea v-model="item.responsibility" class="field-area short" placeholder="职责说明" />
                  <div class="sub-grid">
                    <div>
                      <label class="field-label">输入（每行一项）</label>
                      <textarea v-model="moduleInputs[index]" class="field-area short" />
                    </div>
                    <div>
                      <label class="field-label">输出（每行一项）</label>
                      <textarea v-model="moduleOutputs[index]" class="field-area short" />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section class="editor-grid bottom-grid">
              <div class="editor-card soft-card">
                <div class="section-head">
                  <h3>接口定义</h3>
                  <button class="secondary action-pill mini-pill" @click="addApi">新增接口</button>
                </div>
                <div class="stack-list">
                  <div class="edit-card compact-card" v-for="(api, index) in editableDesign.apis" :key="`api-${index}`">
                    <div class="mini-head">
                      <span>接口 {{ index + 1 }}</span>
                      <button class="danger-button" @click="removeApi(index)">删除</button>
                    </div>
                    <input v-model="api.name" class="field-input" placeholder="接口名称" />
                    <div class="sub-grid slim-grid">
                      <input v-model="api.method" class="field-input" placeholder="HTTP Method" />
                      <input v-model="api.path" class="field-input" placeholder="接口路径" />
                    </div>
                    <textarea v-model="api.description" class="field-area short" placeholder="接口说明" />
                  </div>
                </div>
              </div>

              <div class="editor-card soft-card">
                <div class="section-head">
                  <h3>数据实体</h3>
                  <button class="secondary action-pill mini-pill" @click="addEntity">新增实体</button>
                </div>
                <div class="stack-list">
                  <div class="edit-card compact-card" v-for="(entity, index) in editableDesign.data_entities" :key="`entity-${index}`">
                    <div class="mini-head">
                      <span>实体 {{ index + 1 }}</span>
                      <button class="danger-button" @click="removeEntity(index)">删除</button>
                    </div>
                    <input v-model="entity.name" class="field-input" placeholder="实体名称" />
                    <label class="field-label">字段（每行一项）</label>
                    <textarea v-model="entityFields[index]" class="field-area short" />
                  </div>
                </div>
              </div>
            </section>

            <section class="editor-grid bottom-grid compact-bottom-grid">
              <div class="editor-card note-card">
                <div class="section-head compact-head">
                  <h3>编辑提示</h3>
                  <span class="auto-save-badge">自动保存草稿</span>
                </div>
                <p class="editor-note">当前编辑内容会自动保存到本地草稿。刷新页面后再次点击“编辑结果”，会优先恢复你上次未保存的内容。</p>
              </div>
              <div class="editor-card toast-card" v-if="toastMessage">
                <div class="toast-inline">{{ toastMessage }}</div>
              </div>
            </section>
          </section>
        </template>
      </article>
    </section>
  </main>
</template>

<script setup lang="ts">
import mermaid from 'mermaid'
import { computed, nextTick, ref, watch } from 'vue'
import { streamGenerateDesign, type DesignGenerateResponse, type DesignStreamEvent } from '../api/design'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const loading = ref(false)
const editing = ref(false)
const sidebarCollapsed = ref(false)
const draftRecovered = ref(false)
const toastMessage = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null
const design = computed(() => workspace.designResult)
const selectedMode = computed(() => workspace.designMode)
const isDesignEdited = computed(() => {
  if (!workspace.designResult || !workspace.designOriginalResult) return false
  return JSON.stringify(workspace.designResult) !== JSON.stringify(workspace.designOriginalResult)
})
const mermaidView = ref<'diagram' | 'code'>('diagram')
const mermaidSvg = ref('')
const mermaidError = ref('')
const editableDesign = ref<DesignGenerateResponse | null>(null)
const moduleInputs = ref<string[]>([])
const moduleOutputs = ref<string[]>([])
const entityFields = ref<string[]>([])

watch(
  () => editableDesign.value,
  (value) => {
    if (editing.value) {
      workspace.saveDesignEditDraft(value)
    }
  },
  { deep: true },
)

mermaid.initialize({ startOnLoad: false, securityLevel: 'loose', theme: 'dark' })

watch(
  () => design.value?.mermaid,
  async (value) => {
    if (!value) {
      mermaidSvg.value = ''
      mermaidError.value = ''
      return
    }
    await renderMermaid(value)
  },
  { immediate: true },
)

watch(mermaidView, async (value) => {
  if (value === 'diagram' && design.value?.mermaid) {
    await renderMermaid(design.value.mermaid)
  }
})

function selectMode(mode: 'fast' | 'deep') {
  workspace.setDesignMode(mode)
}

async function renderMermaid(source: string) {
  mermaidError.value = ''
  try {
    await nextTick()
    const { svg } = await mermaid.render(`mermaid-${Date.now()}`, source)
    mermaidSvg.value = svg
  } catch (error) {
    console.error(error)
    mermaidSvg.value = ''
    mermaidError.value = 'Mermaid 图渲染失败，请切换到代码视图检查语法。'
  }
}

function handleStreamEvent(event: DesignStreamEvent) {
  if (event.type === 'status') workspace.setDesignProgressMessage(event.content)
  else if (event.type === 'reasoning') {
    workspace.appendDesignReasoning(event.content)
    workspace.setDesignProgressMessage('正在输出架构推理内容...')
  } else if (event.type === 'content') {
    workspace.appendDesignContent(event.content)
    workspace.setDesignProgressMessage('正在生成结构化设计结果...')
  } else if (event.type === 'result' && event.result) {
    workspace.setDesignResult(event.result, true)
    workspace.setDesignProgressMessage('结构化设计方案已生成')
  } else if (event.type === 'done') workspace.setDesignProgressMessage(event.content || '设计方案生成完成')
  else if (event.type === 'error') workspace.setDesignProgressMessage(event.content || '设计方案生成失败')
}

async function handleGenerate() {
  if (!workspace.requirementResult) {
    alert('请先完成需求分析。')
    return
  }
  loading.value = true
  editing.value = false
  workspace.clearDesignEditDraft()
  workspace.setDesignResult(null)
  workspace.resetDesignStreamState()
  workspace.setDesignProgressMessage(selectedMode.value === 'deep' ? '深度模式已启动，准备流式生成设计方案...' : '快速模式已启动，准备流式生成设计草案...')
  try {
    await streamGenerateDesign(workspace.requirementResult, selectedMode.value, handleStreamEvent)
  } catch (error) {
    console.error(error)
    workspace.setDesignProgressMessage('设计方案生成失败，请检查后端服务或网络连接。')
    alert('设计方案生成失败，请检查后端服务或模型配置。')
  } finally {
    loading.value = false
  }
}

function toggleEdit() {
  if (!design.value) return
  if (editing.value) {
    editing.value = false
    draftRecovered.value = false
    return
  }
  draftRecovered.value = !!workspace.designEditDraft
  editableDesign.value = workspace.designEditDraft
    ? JSON.parse(JSON.stringify(workspace.designEditDraft))
    : JSON.parse(JSON.stringify(design.value))
  syncEditLists()
  editing.value = true
}

function syncEditLists() {
  if (!editableDesign.value) return
  moduleInputs.value = editableDesign.value.modules.map((item) => item.inputs.join('\n'))
  moduleOutputs.value = editableDesign.value.modules.map((item) => item.outputs.join('\n'))
  entityFields.value = editableDesign.value.data_entities.map((item) => item.fields.join('\n'))
}

function toList(text: string) {
  return text.split('\n').map((item) => item.trim()).filter(Boolean)
}

function saveEdit() {
  if (!editableDesign.value) return
  editableDesign.value.modules = editableDesign.value.modules.map((item, index) => ({
    ...item,
    inputs: toList(moduleInputs.value[index] || ''),
    outputs: toList(moduleOutputs.value[index] || ''),
  }))
  editableDesign.value.data_entities = editableDesign.value.data_entities.map((item, index) => ({
    ...item,
    fields: toList(entityFields.value[index] || ''),
  }))
  workspace.setDesignResult(JSON.parse(JSON.stringify(editableDesign.value)))
  workspace.clearDesignEditDraft()
  editing.value = false
  draftRecovered.value = false
  showToast('设计结果已保存')
}

function restoreOriginal() {
  workspace.restoreDesignOriginal()
  editableDesign.value = workspace.designOriginalResult ? JSON.parse(JSON.stringify(workspace.designOriginalResult)) : null
  syncEditLists()
  draftRecovered.value = false
  showToast('已恢复原始结果')
}

function addModule() {
  editableDesign.value?.modules.push({ name: '', responsibility: '', inputs: [], outputs: [] })
  moduleInputs.value.push('')
  moduleOutputs.value.push('')
}

function removeModule(index: number) {
  editableDesign.value?.modules.splice(index, 1)
  moduleInputs.value.splice(index, 1)
  moduleOutputs.value.splice(index, 1)
}

function addApi() {
  editableDesign.value?.apis.push({ name: '', method: 'GET', path: '', description: '' })
}

function removeApi(index: number) {
  editableDesign.value?.apis.splice(index, 1)
}

function addEntity() {
  editableDesign.value?.data_entities.push({ name: '', fields: [] })
  entityFields.value.push('')
}

function removeEntity(index: number) {
  editableDesign.value?.data_entities.splice(index, 1)
  entityFields.value.splice(index, 1)
}

async function copyMermaidCode() {
  if (!design.value?.mermaid) return
  try {
    await navigator.clipboard.writeText(design.value.mermaid)
    showToast('Mermaid 代码复制成功')
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

function timestampedName(prefix: string, extension: string) {
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  return `${prefix}-${stamp}.${extension}`
}

function downloadFile(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function exportDesignJson() {
  if (!design.value) return
  downloadFile(timestampedName('design-result', 'json'), JSON.stringify(design.value, null, 2), 'application/json')
}

function exportDesignMarkdown() {
  if (!design.value) return
  const markdown = `# 设计方案结果\n\n## 架构风格\n${design.value.architecture_style}\n\n## 架构说明\n${design.value.architecture_rationale}\n\n## 模块划分\n${design.value.modules.map((item) => `- **${item.name}**：${item.responsibility}\n  - 输入：${item.inputs.join('、') || '无'}\n  - 输出：${item.outputs.join('、') || '无'}`).join('\n')}\n\n## 接口定义\n${design.value.apis.map((api) => `- **${api.method} ${api.path}** ${api.name}：${api.description}`).join('\n')}\n\n## 数据实体\n${design.value.data_entities.map((entity) => `- **${entity.name}**：${entity.fields.join('、')}`).join('\n')}\n\n## Mermaid\n\n\`\`\`mermaid\n${design.value.mermaid}\n\`\`\``
  downloadFile(timestampedName('design-result', 'md'), markdown, 'text/markdown;charset=utf-8')
}
</script>

<style scoped>
.shell { min-height: 100vh; padding: 32px; color: #f4efe8; background: radial-gradient(circle at top left, rgba(16,185,129,.18), transparent 28%), radial-gradient(circle at top right, rgba(59,130,246,.18), transparent 24%), linear-gradient(135deg, #0b1118 0%, #111827 48%, #1b1022 100%); font-family: 'Book Antiqua', Georgia, serif; }
.hero-card,.panel,.result-block,.summary-card { border: 1px solid rgba(244,238,232,.12); border-radius: 24px; background: rgba(17,24,39,.62); backdrop-filter: blur(14px); box-shadow: 0 18px 50px rgba(0,0,0,.24); }
.hero-card { display: flex; justify-content: space-between; gap: 24px; padding: 28px 30px; margin-bottom: 24px; }
.hero-actions,.mode-switcher,.view-switcher,.panel-head-actions { display: flex; gap: 10px; }
.eyebrow { margin: 0 0 10px; letter-spacing: .2em; text-transform: uppercase; color: #34d399; font-size: 12px; }
h1 { margin: 0; font-size: 42px; }
.lead { max-width: 760px; color: rgba(244,238,232,.78); line-height: 1.9; }
.ghost-link,.primary,.mode-button,.view-button { display: inline-flex; align-items: center; justify-content: center; padding: 10px 16px; border-radius: 999px; text-decoration: none; font-weight: 700; }
.ghost-link { border: 1px solid rgba(244,238,232,.2); color: #f4efe8; }
.primary { border: none; background: linear-gradient(135deg, #34d399, #60a5fa); color: #08111d; cursor: pointer; }
.outline-primary { background: rgba(255,255,255,.06); color: #d9fff2; border: 1px solid rgba(52,211,153,.24); }
.mode-button,.view-button { border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.05); color: #f4efe8; cursor: pointer; }
.mode-button.selected,.view-button.selected { background: linear-gradient(135deg, #34d399, #60a5fa); color: #08111d; }
.primary:disabled,.mode-button:disabled { opacity: .6; cursor: not-allowed; }
.actions-row { display: flex; gap: 12px; flex-wrap: wrap; }
.layout { display: grid; grid-template-columns: 360px 1fr; gap: 24px; align-items: start; }
.layout.collapsed { grid-template-columns: 64px minmax(0, 1fr); }
.panel { padding: 24px; }
.sidebar-panel.collapsed { padding: 12px 10px; }
.result-panel { min-width: 0; }
.panel-head,.result-head-inline { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 16px; }
.panel-head.collapsed { margin: 0; justify-content: center; }
.mode-tip { margin: 0 0 16px; color: rgba(244,238,232,.74); line-height: 1.8; }
.toolbar { display: flex; gap: 10px; flex-wrap: wrap; }
.status-badges { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.action-pill { border: 1px solid rgba(255,255,255,.08); background: linear-gradient(180deg, rgba(255,255,255,.1), rgba(255,255,255,.04)); box-shadow: 0 8px 24px rgba(0,0,0,.15); }
.strong-pill { background: linear-gradient(135deg, rgba(52,211,153,.24), rgba(96,165,250,.2)); color: #ddfff3; }
.mini-pill { padding: 8px 14px; font-size: 13px; }
.success-pill { background: linear-gradient(135deg, rgba(16,185,129,.2), rgba(34,197,94,.16)); }
.ghost-button { border: 1px solid rgba(96,165,250,.28); border-radius: 999px; padding: 11px 18px; font-weight: 700; cursor: pointer; color: #dbeafe; background: rgba(96,165,250,.1); }
.strong-primary { box-shadow: 0 12px 30px rgba(52,211,153,.18); }
.edit-tag { background: rgba(251,191,36,.18); color: #fde68a; }
.edited-tag { background: rgba(251, 191, 36, 0.18); color: #fde68a; }
.draft-tag { background: rgba(96, 165, 250, 0.18); color: #bfdbfe; }
.inline-banner { margin-bottom: 14px; padding: 12px 14px; border-radius: 16px; background: rgba(96,165,250,.12); color: #dbeafe; line-height: 1.7; }
.inline-toast { margin-bottom: 14px; padding: 12px 14px; border-radius: 16px; font-weight: 700; }
.success-toast { background: rgba(34,197,94,.16); color: #bbf7d0; }
.floating-toast { box-shadow: 0 12px 30px rgba(34,197,94,.12); }
.collapse-button { border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.04); color: #dbeafe; border-radius: 999px; padding: 8px 14px; cursor: pointer; font-weight: 700; }
.collapsed-rail { position: relative; width: 100%; min-height: 320px; border: 1px solid rgba(96,165,250,.18); border-radius: 20px; background: linear-gradient(180deg, rgba(15,23,42,.96), rgba(2,6,23,.98)); color: #dbeafe; display: flex; align-items: center; justify-content: center; gap: 10px; padding: 12px 8px; cursor: pointer; overflow: hidden; }
.collapsed-rail::before { content: ''; position: absolute; inset: 8px; border-radius: 14px; border: 1px solid rgba(255,255,255,.05); background: linear-gradient(180deg, rgba(52,211,153,.08), rgba(255,255,255,.01)); }
.collapsed-rail::after { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 3px; border-radius: 999px; background: linear-gradient(180deg, #34d399, #60a5fa); box-shadow: 0 0 18px rgba(52,211,153,.4); }
.collapsed-rail-icon,.collapsed-rail-text { position: relative; z-index: 1; }
.collapsed-rail-icon { font-size: 18px; line-height: 1; color: #93c5fd; }
.collapsed-rail-text { font-weight: 700; writing-mode: vertical-rl; text-orientation: mixed; letter-spacing: .18em; text-transform: uppercase; }
.field-label { display: block; margin: 14px 0 8px; color: #93c5fd; font-weight: 700; }
.field-area,.field-input { width: 100%; border: 1px solid rgba(244,238,232,.12); border-radius: 18px; background: rgba(8,17,29,.8); color: #f4efe8; padding: 14px 16px; font: inherit; }
.field-area { min-height: 120px; resize: vertical; }
.field-area.short { min-height: 86px; }
.field-area.tall-area { min-height: 220px; }
.field-area.mermaid-editor { min-height: 300px; font-family: 'Consolas', 'Courier New', monospace; }
.field-input { min-height: 48px; }
.editor-shell { display: grid; gap: 18px; }
.editor-hero,.editor-card { border: 1px solid rgba(255,255,255,.08); border-radius: 22px; background: rgba(10,18,30,.76); padding: 18px 20px; }
.editor-hero { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; background: linear-gradient(135deg, rgba(52,211,153,.12), rgba(96,165,250,.1)); }
.editor-kicker { margin: 0 0 8px; color: #34d399; text-transform: uppercase; letter-spacing: .18em; font-size: 12px; }
.editor-grid { display: grid; gap: 18px; }
.top-grid { grid-template-columns: 1.15fr .85fr; }
.bottom-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.compact-bottom-grid { grid-template-columns: 1.2fr .8fr; }
.full-span-card { grid-column: 1 / -1; }
.entity-grid,.stack-list { display: grid; gap: 14px; }
.sub-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.slim-grid { grid-template-columns: 140px 1fr; }
.edit-card { padding: 16px; border-radius: 18px; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.05); }
.module-card { background: linear-gradient(180deg, rgba(15,23,42,.92), rgba(17,24,39,.72)); }
.compact-card { background: rgba(15,23,42,.78); }
.soft-card { background: linear-gradient(180deg, rgba(15,23,42,.85), rgba(30,41,59,.62)); }
.glass-strong-card { background: linear-gradient(180deg, rgba(8,47,73,.42), rgba(15,23,42,.88)); }
.note-card,.toast-card { min-height: 120px; display: flex; flex-direction: column; justify-content: center; }
.editor-note { margin: 0; line-height: 1.8; color: rgba(244,238,232,.76); }
.auto-save-badge { padding: 6px 10px; border-radius: 999px; background: rgba(52,211,153,.16); color: #bbf7d0; font-size: 12px; }
.toast-inline { padding: 14px 16px; border-radius: 16px; background: rgba(16,185,129,.18); color: #d1fae5; font-weight: 700; }
.mini-head,.section-head,.edit-actions,.compact-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.mini-head { margin-bottom: 12px; color: #cbd5e1; font-size: 13px; }
.floating-actions { align-self: flex-start; }
.danger-button { border: none; border-radius: 999px; padding: 11px 18px; font-weight: 700; cursor: pointer; background: rgba(239,68,68,.18); color: #fecaca; }
.copy-button { background: rgba(52,211,153,.12); color: #c7f9e9; }
.tag { padding: 6px 10px; border-radius: 999px; background: rgba(255,255,255,.08); color: rgba(244,238,232,.72); font-size: 12px; }
.tag.active { background: rgba(16,185,129,.18); color: #a7f3d0; }
.tag.stream { background: rgba(59,130,246,.2); color: #93c5fd; }
.summary-card,.result-block { padding: 18px 20px; }
.summary-card + .summary-card { margin-top: 14px; }
.placeholder { min-height: 240px; display: grid; place-items: center; color: rgba(244,238,232,.56); border: 1px dashed rgba(244,238,232,.14); border-radius: 20px; }
.placeholder.small { min-height: 160px; margin-bottom: 16px; }
.loading-panel { margin-top: 18px; display: flex; align-items: center; gap: 14px; border-radius: 18px; padding: 14px 16px; background: rgba(59,130,246,.12); }
.spinner { width: 18px; height: 18px; border-radius: 50%; border: 3px solid rgba(255,255,255,.18); border-top-color: #60a5fa; animation: spin .8s linear infinite; }
.result-panel { display: flex; flex-direction: column; gap: 18px; }
.architecture { font-size: 22px; font-weight: 700; color: #86efac; }
.cards { list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; }
.cards li { padding: 14px 16px; border-radius: 18px; background: rgba(255,255,255,.04); }
.cards small { display: block; margin-top: 8px; color: rgba(244,238,232,.7); }
.double-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.compact ul { margin: 0; padding-left: 18px; line-height: 1.8; }
.mermaid-stage { border-radius: 20px; background: rgba(8,17,29,.72); padding: 18px; overflow: auto; }
.mermaid-diagram :deep(svg) { max-width: 100%; height: auto; }
.mermaid-error { color: #fca5a5; }
pre { white-space: pre-wrap; word-break: break-word; line-height: 1.7; color: #f3eadb; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 1100px) { .layout,.double-grid,.top-grid,.bottom-grid,.sub-grid { grid-template-columns: 1fr; } .layout.collapsed { grid-template-columns: 52px minmax(0, 1fr); } .collapsed-rail { min-height: 240px; } }
@media (max-width: 720px) { .shell { padding: 16px; } .hero-card,.panel-head,.result-head-inline,.editor-hero,.compact-head,.section-head,.status-badges { flex-direction: column; align-items: flex-start; } .hero-actions,.mode-switcher,.view-switcher,.toolbar,.panel-head-actions { flex-wrap: wrap; } h1 { font-size: 32px; } }
</style>
