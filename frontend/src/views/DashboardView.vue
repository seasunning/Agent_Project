<template>
  <main class="shell">
    <section class="hero-card">
      <p class="eyebrow">SD Multi Agents System</p>
      <h1>多智能体软件开发系统</h1>
      <p class="lead">
        当前已进入 Phase 4：代码生成原型阶段。系统已支持从结构化需求自动生成架构风格、模块划分、接口定义、Mermaid 设计图，并进一步生成可运行的代码原型建议。
      </p>
    </section>

    <section class="grid">
      <article class="panel accent">
        <h2>当前阶段</h2>
        <p>{{ workspace.currentPhase }}</p>
      </article>

      <article class="panel">
        <h2>模型接入策略</h2>
        <p>{{ workspace.selectedModelMode }}</p>
      </article>

      <article class="panel">
        <h2>后端状态</h2>
        <p>{{ workspace.backendStatus }}</p>
        <button class="action" @click="checkHealth">检测后端</button>
      </article>
    </section>

    <section class="panel workspace">
      <div>
        <h2>Phase 4 已落地能力</h2>
        <ul>
          <li>需求文本输入</li>
          <li>DeepSeek 结构化需求分析</li>
          <li>设计方案自动生成</li>
          <li>架构风格、模块划分、接口定义与数据实体抽取</li>
          <li>Mermaid 设计图描述生成</li>
          <li>代码文件树与关键源码原型生成</li>
        </ul>
      </div>

      <div>
        <h2>下一步入口</h2>
        <ul>
          <li>进入需求分析页发起真实分析</li>
          <li>进入设计方案页生成架构设计</li>
          <li>进入代码生成页输出文件树与原型代码</li>
          <li>后续扩展 LangGraph 工作流与多智能体协作</li>
        </ul>
        <div class="entry-actions">
          <router-link class="entry-link" to="/requirements">进入需求分析页面</router-link>
          <router-link class="entry-link secondary-link" to="/design">进入设计方案页面</router-link>
          <router-link class="entry-link tertiary-link" to="/codegen">进入代码生成页面</router-link>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import api from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
workspace.currentPhase = 'Phase 4：代码生成原型阶段'

async function checkHealth() {
  try {
    const { data } = await api.get('/health')
    workspace.setBackendStatus(`${data.status} · ${data.environment}`)
  } catch {
    workspace.setBackendStatus('连接失败')
  }
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  padding: 40px;
  color: #f4efe6;
  background:
    radial-gradient(circle at top left, rgba(251, 191, 36, 0.18), transparent 32%),
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.16), transparent 24%),
    linear-gradient(135deg, #16110f 0%, #221816 45%, #0b1220 100%);
  font-family: Georgia, 'Times New Roman', serif;
}

.hero-card,
.panel {
  border: 1px solid rgba(244, 239, 230, 0.12);
  border-radius: 24px;
  background: rgba(18, 18, 24, 0.58);
  backdrop-filter: blur(14px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.28);
}

.hero-card {
  padding: 32px;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 12px;
  color: #f6c453;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 12px;
}

h1 {
  margin: 0;
  font-size: 48px;
}

.lead {
  margin-top: 16px;
  max-width: 760px;
  color: rgba(244, 239, 230, 0.78);
  line-height: 1.8;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.panel {
  padding: 24px;
}

.accent {
  background: linear-gradient(160deg, rgba(246, 196, 83, 0.18), rgba(18, 18, 24, 0.58));
}

.workspace {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.action,
.entry-link {
  margin-top: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border: none;
  border-radius: 999px;
  background: #f6c453;
  color: #1b130f;
  cursor: pointer;
  font-weight: 700;
  text-decoration: none;
}

.entry-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}

.secondary-link {
  background: rgba(244, 239, 230, 0.12);
  color: #f4efe6;
}

.tertiary-link {
  background: rgba(56, 189, 248, 0.16);
  color: #d9f6ff;
}

ul {
  padding-left: 20px;
  line-height: 1.8;
  color: rgba(244, 239, 230, 0.84);
}

@media (max-width: 900px) {
  .grid,
  .workspace {
    grid-template-columns: 1fr;
  }

  .shell {
    padding: 20px;
  }

  h1 {
    font-size: 34px;
  }
}
</style>
