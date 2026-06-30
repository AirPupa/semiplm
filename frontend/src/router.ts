import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: () => import('./views/LoginView.vue'), meta: { title: '登录', public: true } },
    { path: '/dashboard', component: () => import('./views/DashboardView.vue'), meta: { title: '研发驾驶舱' } },
    { path: '/workbench', component: () => import('./views/WorkbenchView.vue'), meta: { title: '我的待办' } },
    { path: '/closure-check', component: () => import('./views/ClosureCheckView.vue'), meta: { title: '闭环验证' } },
    { path: '/products', component: () => import('./views/ProductsView.vue'), meta: { title: '产品库' } },
    { path: '/products/:id', component: () => import('./views/ProductDetailView.vue'), meta: { title: '产品详情' } },
    { path: '/requirements', component: () => import('./views/RequirementsView.vue'), meta: { title: '需求规格管理' } },
    { path: '/materials', component: () => import('./views/MaterialsView.vue'), meta: { title: '物料库' } },
    { path: '/substitutes', component: () => import('./views/SubstituteMaterialsView.vue'), meta: { title: '替代料管理' } },
    { path: '/suppliers', component: () => import('./views/SuppliersView.vue'), meta: { title: '供应商管理' } },
    { path: '/boms', component: () => import('./views/BomView.vue'), meta: { title: '设计 BOM' } },
    { path: '/baselines', component: () => import('./views/BaselinesView.vue'), meta: { title: 'BOM 基线' } },
    { path: '/documents', component: () => import('./views/DocumentsView.vue'), meta: { title: '文档库' } },
    { path: '/process', component: () => import('./views/ProcessView.vue'), meta: { title: '工艺路线' } },
    { path: '/process-parameters', component: () => import('./views/ProcessParametersView.vue'), meta: { title: '工艺参数库' } },
    { path: '/problem-reports', component: () => import('./views/PRProblemView.vue'), meta: { title: 'PR 问题报告' } },
    { path: '/changes', component: () => import('./views/ChangesView.vue'), meta: { title: 'ECR 变更申请' } },
    { path: '/integrations', component: () => import('./views/IntegrationsView.vue'), meta: { title: '研产集成' } },
    { path: '/projects', component: () => import('./views/ProjectsView.vue'), meta: { title: '项目管理' } },
    { path: '/quality', component: () => import('./views/QualityView.vue'), meta: { title: '质量问题' } },
    { path: '/admin', redirect: '/admin/organizations' },
    { path: '/admin/organizations', component: () => import('./views/OrganizationManagementView.vue'), meta: { title: '组织管理' } },
    { path: '/admin/users', component: () => import('./views/UserManagementView.vue'), meta: { title: '用户管理' } },
    { path: '/admin/roles', component: () => import('./views/RoleManagementView.vue'), meta: { title: '角色管理' } },
    { path: '/admin/coding-rules', component: () => import('./views/CodingRulesView.vue'), meta: { title: '编码规则' } },
    { path: '/admin/category-templates', component: () => import('./views/CategoryTemplatesView.vue'), meta: { title: '分类属性' } },
    { path: '/admin/lifecycle-templates', component: () => import('./views/LifecycleTemplatesView.vue'), meta: { title: '生命周期' } },
    { path: '/admin/dictionaries', component: () => import('./views/DictionaryView.vue'), meta: { title: '数据字典' } },
    { path: '/admin/system-parameters', component: () => import('./views/SystemParametersView.vue'), meta: { title: '系统参数' } },
    { path: '/admin/workflows', component: () => import('./views/WorkflowConfigView.vue'), meta: { title: '流程配置' } },
    { path: '/admin/integrations', component: () => import('./views/IntegrationConfigView.vue'), meta: { title: '接口端点' } },
    { path: '/admin/audit-logs', component: () => import('./views/AuditLogView.vue'), meta: { title: '操作日志' } },
    { path: '/reports', component: () => import('./views/ReportsView.vue'), meta: { title: '报表中心' } }
  ]
})

router.beforeEach((to) => {
  const loggedIn = !!localStorage.getItem('semiplm.currentUser')
  if (!to.meta.public && !loggedIn) return '/login'
  if (to.path === '/login' && loggedIn) return '/dashboard'
  return true
})

export default router
