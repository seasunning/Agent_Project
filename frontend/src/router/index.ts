import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import RequirementAnalysisView from '../views/RequirementAnalysisView.vue'
import DesignView from '../views/DesignView.vue'
import CodegenView from '../views/CodegenView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
    },
    {
      path: '/requirements',
      name: 'requirements',
      component: RequirementAnalysisView,
    },
    {
      path: '/design',
      name: 'design',
      component: DesignView,
    },
    {
      path: '/codegen',
      name: 'codegen',
      component: CodegenView,
    },
  ],
})

export default router
