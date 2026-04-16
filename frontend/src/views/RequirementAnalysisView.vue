<template>
  <main class="page">
    <section class="hero">
      <div>
        <p class="eyebrow">Phase 2</p>
        <h1>需求智能分析工作台</h1>
        <p class="lead">支持快速/深度模式切换，并通过流式输出展示进度与结构化结果。</p>
      </div>
      <router-link class="ghost" to="/">返回工作台</router-link>
    </section>

    <section class="layout" :class="{ collapsed: sidebarCollapsed }">
      <article class="panel sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="panel-head" :class="{ collapsed: sidebarCollapsed }">
          <template v-if="!sidebarCollapsed">
            <h2>原始需求输入</h2>
            <div class="head-actions">
              <span class="tag">支持一句话或更短需求</span>
              <button class="ghost small" @click="sidebarCollapsed = true">收起</button>
            </div>
          </template>
          <button v-else class="rail" @click="sidebarCollapsed = false">
            <span>›</span>
            <span>原始需求输入</span>
          </button>
        </div>

        <template v-if="!sidebarCollapsed">
          <div class="switcher">
            <button class="pill" :class="{ active: selectedMode === 'fast' }" :disabled="loading" @click="selectMode('fast')">快速模式</button>
            <button class="pill" :class="{ active: selectedMode === 'deep' }" :disabled="loading" @click="selectMode('deep')">深度模式</button>
          </div>
          <p class="tip">{{ selectedMode === 'fast' ? '快速模式更适合快速抽取核心需求。' : '深度模式更适合识别约束、模糊点与复杂分析。' }}</p>
          <textarea v-model="draft" class="editor" placeholder="例如：开发一个高校图书管理系统，支持学生借阅、归还、库存查询、管理员录入图书和统计分析……" />
          <div class="actions">
            <button class="primary" :disabled="loading" @click="submitAnalysis">{{ loading ? '流式分析中...' : '开始智能分析' }}</button>
            <button class="ghost" :disabled="loading" @click="fillDemo">填入示例需求</button>
            <router-link class="ghost" to="/design">前往设计方案页</router-link>
          </div>
          <div v-if="loading" class="loading-box">
            <strong>实时状态</strong>
            <p>{{ workspace.progressMessage }}</p>
          </div>
        </template>
      </article>

      <article class="panel result-panel">
        <div class="panel-head">
          <h2>结构化分析结果</h2>
          <div class="head-actions" v-if="result">
            <button class="ghost small" @click="exportRequirementJson">导出 JSON</button>
            <button class="ghost small" @click="exportRequirementMarkdown">导出 Markdown</button>
          </div>
        </div>

        <div v-if="!result && !loading" class="empty">还没有分析结果。请先在左侧输入需求并发起分析。</div>

        <template v-if="loading">
          <section class="block"><h3>进度提示</h3><p>{{ workspace.progressMessage }}</p></section>
          <section class="block" v-if="workspace.streamingReasoning"><h3>实时推理流</h3><pre>{{ workspace.streamingReasoning }}</pre></section>
          <section class="block" v-if="workspace.streamingContent"><h3>实时回答流</h3><pre>{{ workspace.streamingContent }}</pre></section>
        </template>

        <template v-if="result">
          <section class="block"><h3>需求摘要</h3><p>{{ result.summary }}</p></section>
          <section class="block">
            <h3>功能需求</h3>
            <ul class="cards">
              <li v-for="item in result.functional_requirements" :key="`${item.name}-${item.priority}`">
                <strong>{{ item.name }}</strong>
                <span class="priority">优先级：{{ item.priority || '未标注' }}</span>
                <p>{{ item.description }}</p>
              </li>
            </ul>
          </section>
          <section class="grid3">
            <div class="block compact"><h3>非功能需求</h3><ul><li v-for="item in result.non_functional_requirements" :key="item">{{ item }}</li></ul></div>
            <div class="block compact"><h3>约束条件</h3><ul><li v-for="item in result.constraints" :key="item">{{ item }}</li></ul></div>
            <div class="block compact"><h3>用户角色</h3><ul><li v-for="item in result.actors" :key="item">{{ item }}</li></ul></div>
          </section>
          <section class="grid2">
            <div class="block compact warn"><h3>模糊点</h3><ul><li v-for="item in result.ambiguities" :key="item">{{ item }}</li></ul></div>
            <div class="block compact danger"><h3>冲突点</h3><ul><li v-for="item in result.conflicts" :key="item">{{ item }}</li></ul></div>
          </section>
          <section class="block"><h3>待确认问题</h3><ul><li v-for="item in result.questions_for_user" :key="item">{{ item }}</li></ul></section>
          <section class="block"><h3>模型原始输出</h3><pre>{{ result.raw_model_output }}</pre></section>
          <section class="block" v-if="result.reasoning_content"><h3>思考内容</h3><pre>{{ result.reasoning_content }}</pre></section>
        </template>
      </article>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { streamAnalyzeRequirement, type RequirementStreamEvent } from '../api/requirement'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const loading = ref(false)
const sidebarCollapsed = ref(false)
const draft = ref(workspace.latestRequirement || '')
const result = computed(() => workspace.requirementResult)
const selectedMode = computed(() => workspace.requirementMode)

function fillDemo() {
  draft.value = '开发一个高校图书管理系统，支持学生注册登录、图书借阅与归还、库存查询、管理员录入图书、超期提醒和借阅统计分析，要求界面简洁、支持并发访问，并兼容网页端。'
}

function selectMode(mode: 'fast' | 'deep') {
  workspace.setRequirementMode(mode)
}

function handleStreamEvent(event: RequirementStreamEvent) {
  if (event.type === 'status') workspace.setProgressMessage(event.content)
  else if (event.type === 'reasoning') {
    workspace.appendReasoning(event.content)
    workspace.setProgressMessage('正在输出推理内容...')
  } else if (event.type === 'content') {
    workspace.appendContent(event.content)
    workspace.setProgressMessage('正在生成结构化结果...')
  } else if (event.type === 'result' && event.result) {
    workspace.setRequirementResult(event.result, true)
    workspace.setProgressMessage('结构化需求结果已生成')
  } else if (event.type === 'done') workspace.setProgressMessage(event.content || '需求分析完成')
  else if (event.type === 'error') workspace.setProgressMessage(event.content || '需求分析失败')
}

async function submitAnalysis() {
  if (!draft.value.trim()) return alert('请输入需求内容后再分析。')
  loading.value = true
  workspace.setRequirementDraft(draft.value)
  workspace.setRequirementResult(null)
  workspace.resetStreamState()
  workspace.setProgressMessage(selectedMode.value === 'deep' ? '深度模式已启动，准备流式分析...' : '快速模式已启动，准备流式分析...')
  try {
    await streamAnalyzeRequirement(draft.value, selectedMode.value, handleStreamEvent)
  } catch (error) {
    console.error(error)
    workspace.setProgressMessage('需求分析失败，请检查后端服务或网络连接。')
    alert('需求分析失败，请检查后端服务或模型配置。')
  } finally {
    loading.value = false
  }
}

function timestampedName(prefix: string, extension: string) {
  return `${prefix}-${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}.${extension}`
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

function exportRequirementJson() {
  if (!result.value) return
  downloadFile(timestampedName('requirement-result', 'json'), JSON.stringify(result.value, null, 2), 'application/json')
}

function exportRequirementMarkdown() {
  if (!result.value) return
  const markdown = `# 需求分析结果\n\n## 需求摘要\n${result.value.summary}\n\n## 功能需求\n${result.value.functional_requirements.map((item) => `- **${item.name}**（优先级：${item.priority || '未标注'}）：${item.description}`).join('\n')}\n\n## 非功能需求\n${result.value.non_functional_requirements.map((item) => `- ${item}`).join('\n')}\n\n## 约束条件\n${result.value.constraints.map((item) => `- ${item}`).join('\n')}\n\n## 用户角色\n${result.value.actors.map((item) => `- ${item}`).join('\n')}\n\n## 模糊点\n${result.value.ambiguities.map((item) => `- ${item}`).join('\n')}\n\n## 冲突点\n${result.value.conflicts.map((item) => `- ${item}`).join('\n')}\n\n## 待确认问题\n${result.value.questions_for_user.map((item) => `- ${item}`).join('\n')}`
  downloadFile(timestampedName('requirement-result', 'md'), markdown, 'text/markdown;charset=utf-8')
}
</script>

<style scoped>
.page{min-height:100vh;padding:32px;color:#f7f1e8;background:radial-gradient(circle at 0% 0%,rgba(249,115,22,.18),transparent 28%),radial-gradient(circle at 100% 0%,rgba(34,197,94,.15),transparent 24%),linear-gradient(145deg,#110d12 0%,#171224 50%,#081521 100%);font-family:'Palatino Linotype',Georgia,serif}.hero,.panel,.block{border:1px solid rgba(255,244,230,.12);border-radius:24px;background:rgba(14,16,26,.66);backdrop-filter:blur(14px);box-shadow:0 18px 50px rgba(0,0,0,.25)}.hero{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;padding:28px 30px;margin-bottom:24px}.eyebrow{margin:0 0 10px;letter-spacing:.2em;text-transform:uppercase;color:#fb923c;font-size:12px}h1{margin:0;font-size:42px}.lead{max-width:760px;color:rgba(247,241,232,.78);line-height:1.9}.layout{display:grid;grid-template-columns:420px 1fr;gap:24px;align-items:start}.layout.collapsed{grid-template-columns:64px minmax(0,1fr)}.panel{padding:24px}.sidebar.collapsed{padding:12px 10px}.result-panel{min-width:0;display:flex;flex-direction:column;gap:18px}.panel-head,.head-actions,.switcher,.actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.panel-head{justify-content:space-between;margin-bottom:16px}.panel-head.collapsed{justify-content:center;margin-bottom:0}.ghost,.pill,.primary{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:10px 16px;font-weight:700;text-decoration:none}.ghost,.pill{border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);color:#f7f1e8}.ghost.small{padding:8px 14px}.pill.active,.primary{border:none;background:linear-gradient(135deg,#fb923c,#facc15);color:#23140c}.tip,.nav-hint,pre,.compact ul{line-height:1.8}.tip{margin:0 0 16px;color:rgba(247,241,232,.72)}.tag{padding:6px 10px;border-radius:999px;background:rgba(255,255,255,.08);color:rgba(247,241,232,.72);font-size:12px}.rail{position:relative;width:100%;min-height:320px;border:1px solid rgba(251,146,60,.18);border-radius:20px;background:linear-gradient(180deg,rgba(20,15,25,.96),rgba(7,10,18,.98));color:#f7f1e8;display:flex;align-items:center;justify-content:center;gap:10px;padding:12px 8px;cursor:pointer;overflow:hidden}.rail::before{content:'';position:absolute;inset:8px;border-radius:14px;border:1px solid rgba(255,255,255,.05);background:linear-gradient(180deg,rgba(249,115,22,.08),rgba(255,255,255,.01))}.rail::after{content:'';position:absolute;left:0;top:18px;bottom:18px;width:3px;border-radius:999px;background:linear-gradient(180deg,#fb923c,#facc15);box-shadow:0 0 18px rgba(251,146,60,.4)}.rail span{position:relative;z-index:1}.rail span:first-child{font-size:18px;color:#fdba74}.rail span:last-child{font-weight:700;writing-mode:vertical-rl;text-orientation:mixed;letter-spacing:.18em;text-transform:uppercase}.editor,.field-area,.field-input{width:100%;border:1px solid rgba(247,241,232,.12);border-radius:18px;background:rgba(7,10,18,.8);color:#f7f1e8;padding:14px 16px;font:inherit}.editor{min-height:360px;resize:vertical;padding:18px}.field-area{min-height:120px;resize:vertical}.field-area.short{min-height:86px}.field-input{min-height:48px}.loading-box,.edit-card,.empty,.cards li{border-radius:18px}.loading-box{margin-top:18px;padding:14px 16px;background:rgba(59,130,246,.12)}.empty{min-height:240px;display:grid;place-items:center;color:rgba(247,241,232,.56);border:1px dashed rgba(247,241,232,.14)}.cards{list-style:none;margin:0;padding:0;display:grid;gap:14px}.cards li,.edit-card{padding:14px 16px;background:rgba(255,255,255,.04)}.priority{display:inline-block;margin-left:10px;font-size:12px;color:#fcd34d}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.compact ul{margin:0;padding-left:18px}.warn{background:rgba(245,158,11,.08)}.danger{background:rgba(239,68,68,.08)}pre{white-space:pre-wrap;word-break:break-word;color:#f3eadb}@media (max-width:1100px){.layout,.grid3,.grid2{grid-template-columns:1fr}.layout.collapsed{grid-template-columns:52px minmax(0,1fr)}.rail{min-height:240px}}@media (max-width:720px){.page{padding:16px}.hero,.panel-head,.section-head,.edit-actions{flex-direction:column;align-items:flex-start}h1{font-size:32px}}
</style>
