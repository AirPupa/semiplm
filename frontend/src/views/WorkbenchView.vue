<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>我的流程待办</strong>
          <span class="muted"> · 文档、BOM、变更、项目阶段门统一流程任务</span>
        </div>
        <el-button @click="loadData">刷新</el-button>
      </div>
      <el-table :data="pendingTasks" stripe height="680">
        <el-table-column prop="object_type" label="对象" width="90" fixed />
        <el-table-column prop="object_no" label="对象编号" width="180" />
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="product_model" label="型号" width="130" />
        <el-table-column prop="template_name" label="流程" width="150" />
        <el-table-column prop="node_name" label="当前节点" width="120" />
        <el-table-column prop="role_name" label="处理角色" width="120" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }"><el-tag size="small" :type="row.status === '待处理' ? 'warning' : 'info'">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="assignee" label="转办给" width="100" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" :disabled="!can('approval') || row.status !== '待处理'" @click="approve(row)">通过</el-button>
            <el-button size="small" :disabled="!can('approval') || row.status !== '待处理'" @click="reject(row)">驳回</el-button>
            <el-button size="small" :disabled="!can('approval') || row.status !== '待处理'" @click="transfer(row)">转办</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="panel">
      <div class="panel-title">阶段门风险</div>
      <div class="stage-list">
        <div v-for="item in workbench.stage_gates || []" :key="item.id" class="stage-item">
          <div class="toolbar">
            <strong>{{ item.model }}</strong>
            <el-tag size="small">{{ item.lifecycle }}</el-tag>
          </div>
          <div class="muted">{{ item.owner }} · 下一关卡：{{ item.next_gate }}</div>
          <el-progress :percentage="item.readiness" :stroke-width="8" />
          <div class="stage-blocker">{{ item.blocker }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { approveWorkflowTask, getWorkbench, getWorkflowTasks, rejectWorkflowTask, transferWorkflowTask } from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const workbench = ref<any>({})
const tasks = ref<any[]>([])
const { can, currentUser, refreshSession } = useAuth()

const pendingTasks = computed(() => tasks.value.filter((item) => item.status === '待处理'))

async function loadData() {
  const [workbenchData, taskRows] = await Promise.all([getWorkbench(), getWorkflowTasks()])
  workbench.value = workbenchData
  tasks.value = taskRows
}

async function approve(row: any) {
  if (!can('approval')) return
  await ElMessageBox.prompt('请输入审批意见', `通过 ${row.node_name}`, {
    inputValue: '同意',
    confirmButtonText: '通过',
    cancelButtonText: '取消'
  })
    .then(async ({ value }) => {
      await approveWorkflowTask(row.id, { acted_by: currentUser.value?.display_name || '系统用户', comment: value })
      ElMessage.success('流程任务已通过')
      await loadData()
    })
}

async function reject(row: any) {
  if (!can('approval')) return
  await ElMessageBox.prompt('请输入驳回原因', `驳回 ${row.node_name}`, {
    inputValue: '退回修改',
    confirmButtonText: '驳回',
    cancelButtonText: '取消'
  })
    .then(async ({ value }) => {
      await rejectWorkflowTask(row.id, { acted_by: currentUser.value?.display_name || '系统用户', comment: value })
      ElMessage.success('流程任务已驳回')
      await loadData()
    })
}

async function transfer(row: any) {
  if (!can('approval')) return
  await ElMessageBox.prompt('请输入转办人', `转办 ${row.node_name}`, {
    inputValue: row.assignee || '',
    confirmButtonText: '转办',
    cancelButtonText: '取消'
  })
    .then(async ({ value }) => {
      await transferWorkflowTask(row.id, { acted_by: currentUser.value?.display_name || '系统用户', assignee: value, comment: `转办给 ${value}` })
      ElMessage.success('流程任务已转办')
      await loadData()
    })
}

onMounted(async () => {
  await refreshSession()
  await loadData()
  loading.value = false
})
</script>
