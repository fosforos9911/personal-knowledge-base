import { createApp } from 'vue'
import './style.css'

const modules = [
  { key: 'dashboard', label: '工作台', route: '/' },
  { key: 'documents', label: '文档库', route: '/documents' },
  { key: 'search', label: '全局检索', route: '/search' },
  { key: 'chat', label: 'AI 问答', route: '/chat' },
  { key: 'notes', label: '个人笔记', route: '/notes' },
  { key: 'graph', label: '知识图谱', route: '/graph', enabled: false },
  { key: 'projects', label: '项目空间', route: '/projects', enabled: false },
  { key: 'settings', label: '设置', route: '/settings' },
]

const App = {
  data: () => ({ modules }),
  template: `
    <div class="shell">
      <aside class="sidebar">
        <div class="brand">PKB <span>个人知识库</span></div>
        <nav>
          <a v-for="module in modules" v-if="module.enabled !== false" :key="module.key" :href="module.route">
            {{ module.label }}
          </a>
        </nav>
      </aside>
      <main class="content">
        <p class="eyebrow">PERSONAL FDE KNOWLEDGE BASE</p>
        <h1>把资料变成可行动的工程知识</h1>
        <p class="intro">Level 0 工程骨架已就绪。后续将逐步接入文档导入、全文检索和有引用的 AI 问答。</p>
        <section class="cards">
          <article><strong>文档库</strong><span>等待导入第一份行业资料</span></article>
          <article><strong>检索</strong><span>全文检索模块将在 Level 2 开启</span></article>
          <article><strong>AI 问答</strong><span>回答将始终关联原文依据</span></article>
        </section>
      </main>
    </div>
  `,
}

createApp(App).mount('#app')
