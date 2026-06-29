<template>
  <a-layout class="app-shell arco-shell">
    <a-layout-sider class="sidebar arco-sidebar" :width="212" collapsible :collapsed="collapsed" @collapse="collapsed = $event">
      <div class="brand" :class="{ collapsed }">
        <div class="brand-mark">S</div>
        <div v-if="!collapsed" class="brand-copy">
          <strong>SemiPLM</strong>
          <span>芯片制造 PLM</span>
        </div>
      </div>

      <a-menu
        class="nav-menu arco-nav"
        :selected-keys="[$route.path]"
        :default-open-keys="['work', 'base', 'master', 'docs', 'bom', 'process', 'change', 'project', 'quality']"
        @menu-item-click="navigate"
      >
        <a-sub-menu v-for="group in visibleMenuGroups" :key="group.key">
          <template #icon><component :is="group.icon" /></template>
          <template #title>{{ group.title }}</template>
          <a-menu-item v-for="item in group.children" :key="item.path">{{ item.title }}</a-menu-item>
        </a-sub-menu>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="topbar arco-topbar">
        <div class="page-heading">
          <div class="page-title">{{ $route.meta.title }}</div>
          <div class="page-subtitle">光电芯片制造 PLM · 研发、工艺、质量、制造数据闭环</div>
        </div>

        <div class="top-actions">
          <a-input-search class="search" placeholder="输入内容查询" allow-clear />
          <a-button shape="circle"><template #icon><IconNotification /></template></a-button>
          <a-dropdown position="br">
            <a-button>
              {{ session?.user?.display_name || '系统管理员' }}
              <template #icon><IconDown /></template>
            </a-button>
            <template #content>
              <a-doption disabled>{{ session?.role?.name || '系统管理员' }}</a-doption>
              <a-doption v-for="user in users" :key="user.id" @click="switchUser(user.username)">
                切换：{{ user.display_name }}
              </a-doption>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <a-layout-content class="content arco-content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAdminUsers } from './api'
import { useAuth } from './auth'
import {
  IconBarChart as IconDashboard,
  IconBranch,
  IconDown,
  IconFolder,
  IconLayers,
  IconNotification,
  IconSettings,
  IconSync
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const collapsed = ref(false)
const users = ref<any[]>([])
const { can, refreshSession, session, setCurrentUser } = useAuth()

const menuGroups = [
  {
    key: 'work',
    title: '工作台',
    icon: IconDashboard,
    children: [
      { path: '/dashboard', title: '研发驾驶舱', permission: 'dashboard' },
      { path: '/workbench', title: '我的待办', permission: 'approval' }
    ]
  },
  {
    key: 'base',
    title: '基础平台',
    icon: IconSettings,
    children: [
      { path: '/admin/organizations', title: '组织管理', permission: 'organization' },
      { path: '/admin/users', title: '用户管理', permission: 'user' },
      { path: '/admin/roles', title: '角色管理', permission: 'role' },
      { path: '/admin/foundation', title: '基础配置', permission: 'system' },
      { path: '/admin/workflows', title: '流程配置', permission: 'workflow' }
    ]
  },
  {
    key: 'master',
    title: '主数据中心',
    icon: IconLayers,
    children: [
      { path: '/products', title: '产品库', permission: 'product' },
      { path: '/requirements', title: '需求规格', permission: 'requirement' },
      { path: '/materials', title: '物料库', permission: 'material' },
      { path: '/substitutes', title: '替代料管理', permission: 'material' },
      { path: '/suppliers', title: '供应商/制造商', permission: 'material' }
    ]
  },
  {
    key: 'docs',
    title: '文档与资料',
    icon: IconFolder,
    children: [
      { path: '/documents', title: '文档库', permission: 'document' }
    ]
  },
  {
    key: 'bom',
    title: 'BOM 管理',
    icon: IconBranch,
    children: [
      { path: '/boms', title: '设计 BOM', permission: 'bom' },
      { path: '/baselines', title: 'BOM 基线', permission: 'product' }
    ]
  },
  {
    key: 'process',
    title: '工艺管理',
    icon: IconFolder,
    children: [
      { path: '/process', title: '工艺路线', permission: 'process' },
      { path: '/process-parameters', title: '工艺参数库', permission: 'process' }
    ],
  },
  {
    key: 'change',
    title: '工程变更',
    icon: IconSync,
    children: [
      { path: '/problem-reports', title: 'PR 问题报告', permission: 'change' },
      { path: '/changes', title: 'ECR 变更申请', permission: 'change' }
    ]
  },
  {
    key: 'project',
    title: '项目管理',
    icon: IconLayers,
    children: [
      { path: '/projects', title: '项目库', permission: 'project' }
    ]
  },
  {
    key: 'quality',
    title: '质量闭环',
    icon: IconFolder,
    children: [
      { path: '/quality', title: '质量问题', permission: 'quality' }
    ]
  },
  {
    key: 'integration',
    title: '集成中心',
    icon: IconBranch,
    children: [
      { path: '/integrations', title: '同步队列', permission: 'integration' },
      { path: '/admin/integrations', title: '接口配置', permission: 'integration' },
      { path: '/admin/audit-logs', title: '操作日志', permission: 'system' }
    ]
  }
]

const visibleMenuGroups = computed(() => menuGroups
  .map((group) => ({
    ...group,
    children: group.children.filter((item) => item.permission === 'dashboard' || can(item.permission))
  }))
  .filter((group) => group.children.length))

async function loadSession() {
  const [, userRows] = await Promise.all([refreshSession(), getAdminUsers()])
  users.value = userRows
}

async function switchUser(username: string) {
  setCurrentUser(username)
  await loadSession()
  const visiblePaths = visibleMenuGroups.value.flatMap((group) => group.children.map((item) => item.path))
  if (!visiblePaths.includes(router.currentRoute.value.path)) {
    router.push(visiblePaths[0] || '/dashboard')
  }
}

function navigate(path: string) {
  if (path !== router.currentRoute.value.path) router.push(path)
}

onMounted(loadSession)
</script>
