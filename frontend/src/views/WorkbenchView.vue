<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>工作台</strong>
          <span class="muted"> · {{ currentUser?.display_name || '系统用户' }} 的待办、申请、任务和消息</span>
        </div>
        <el-button @click="loadData">刷新</el-button>
      </div>
      <el-tabs class="compact-tabs">
        <el-tab-pane :label="`流程待办 (${pendingTasks.length})`">
          <el-table :data="pendingTasks" height="520" size="small">
            <el-table-column prop="object_type" label="对象" width="80" fixed />
            <el-table-column prop="object_no" label="对象编号" width="170" show-overflow-tooltip />
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="node_name" label="当前节点" width="110" />
            <el-table-column prop="role_name" label="处理角色" width="110" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }"><el-tag size="small" :type="row.status === '待处理' ? 'warning' : 'info'">{{ row.status }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="210" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" :disabled="!can('approval') || row.status !== '待处理'" @click="approve(row)">通过</el-button>
                <el-button size="small" :disabled="!can('approval') || row.status !== '待处理'" @click="reject(row)">驳回</el-button>
                <el-button size="small" :disabled="!can('approval') || row.status !== '待处理'" @click="transfer(row)">转办</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane :label="`我的变更 (${workbench.my_changes?.length || 0})`">
          <el-table :data="workbench.my_changes || []" height="520" size="small">
            <el-table-column prop="change_no" label="变更单号" width="170" />
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="product_model" label="型号" width="120" />
            <el-table-column prop="priority" label="优先级" width="80" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.status === '已关闭' ? 'success' : row.status === '执行中' ? 'warning' : 'info'">{{ row.status }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="submitted_at" label="提交日期" width="110" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane :label="`我的项目 (${workbench.my_projects?.length || 0})`">
          <el-table :data="workbench.my_projects || []" height="520" size="small">
            <el-table-column prop="project_no" label="项目编号" width="140" />
            <el-table-column prop="name" label="项目名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="product_model" label="型号" width="120" />
            <el-table-column prop="phase" label="阶段" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.phase === '量产导入' ? 'success' : 'primary'">{{ row.phase }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="140">
              <template #default="{ row }"><el-progress :percentage="row.progress" :stroke-width="6" /></template>
            </el-table-column>
            <el-table-column prop="risk_level" label="风险" width="70" />
            <el-table-column prop="end_date" label="计划完成" width="100" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane :label="`我的任务 (${workbench.my_tasks?.length || 0})`">
          <el-table :data="workbench.my_tasks || []" height="520" size="small">
            <el-table-column prop="name" label="任务" min-width="200" show-overflow-tooltip />
            <el-table-column prop="project_no" label="所属项目" width="140" />
            <el-table-column prop="phase" label="阶段" width="90" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }"><el-tag size="small" :type="row.status === '已完成' ? 'success' : row.status === '进行中' ? 'warning' : 'info'">{{ row.status }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="due_date" label="截止日期" width="110" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane :label="`我的质量问题 (${workbench.my_quality_issues?.length || 0})`">
          <el-table :data="workbench.my_quality_issues || []" height="520" size="small">
            <el-table-column prop="issue_no" label="问题编号" width="110" />
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="product_model" label="型号" width="120" />
            <el-table-column prop="severity" label="严重度" width="80">
              <template #default="{ row }"><el-tag size="small" :type="row.severity === '高' ? 'danger' : row.severity === '中' ? 'warning' : 'info'">{{ row.severity }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }"><el-tag size="small" :type="row.status === '已关闭' ? 'success' : row.status === 'CAPA 执行中' ? 'warning' : 'danger'">{{ row.status }}</el-tag></template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="阶段门风险">
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
        </el-tab-pane>
        <el-tab-pane label="近期动态">
          <el-timeline>
            <el-timeline-item v-for="item in workbench.recent_changes || []" :key="item.id" :timestamp="item.submitted_at || ''" placement="top">
              <el-card shadow="never" class="compact-card">
                <div class="toolbar">
                  <strong>{{ item.change_no }}</strong>
                  <el-tag size="small" :type="item.status === '已关闭' ? 'success' : item.status === '执行中' ? 'warning' : 'info'">{{ item.status }}</el-tag>
                </div>
                <p class="muted">{{ item.title }}</p>
                <p class="muted">产品 {{ item.product_model }} · 优先级 {{ item.priority }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-tab-pane>
        <el-tab-pane :label="`任务日历 (${calendarSummary.total})`">
          <div class="calendar-toolbar">
            <el-button size="small" @click="prevMonth">上月</el-button>
            <strong>{{ calendarMonth }}</strong>
            <el-button size="small" @click="nextMonth">下月</el-button>
            <el-button size="small" @click="goToday">今天</el-button>
            <span class="muted" style="margin-left:16px">
              共 {{ calendarSummary.total }} 项 · 逾期 {{ calendarSummary.overdue }}
              <span v-for="t in calendarSummary.by_type" :key="t.name" :style="{ marginLeft: '8px', color: typeColor(t.name) }">{{ t.name }} {{ t.value }}</span>
            </span>
          </div>
          <el-calendar v-model="calendarDate" v-loading="calendarLoading">
            <template #date-cell="{ data }">
              <div class="cal-cell" :class="{ today: data.isSelected }">
                <div class="cal-day">{{ data.day.split('-').slice(2).join('') }}</div>
                <div class="cal-items">
                  <div
                    v-for="it in itemsByDate(data.day)"
                    :key="it.type + it.no + data.day"
                    class="cal-item"
                    :style="{ borderLeftColor: typeColor(it.type) }"
                    :class="{ overdue: isOverdue(it, data.day) }"
                  >
                    <span class="cal-item-type">{{ it.type }}</span>
                    <span class="cal-item-title" :title="it.title">{{ it.title }}</span>
                  </div>
                </div>
              </div>
            </template>
          </el-calendar>
        </el-tab-pane>
        <el-tab-pane :label="`消息通知 (${notifications.total})`">
          <div class="toolbar">
            <el-select v-model="notifyFilter" clearable placeholder="按动作筛选" style="width:140px" @change="loadNotifications">
              <el-option label="发布" value="发布" />
              <el-option label="关闭" value="关闭" />
              <el-option label="提交" value="提交" />
              <el-option label="驳回" value="驳回" />
              <el-option label="删除" value="删除" />
              <el-option label="新增" value="新增" />
              <el-option label="编辑" value="编辑" />
            </el-select>
            <el-button size="small" @click="loadNotifications">刷新</el-button>
            <span class="muted" style="margin-left:16px">
              <span v-for="a in notifications.by_action" :key="a.name" style="margin-right:12px">{{ a.name }} {{ a.value }}</span>
            </span>
          </div>
          <el-table :data="notifications.items || []" height="520" size="small">
            <el-table-column prop="operated_at" label="时间" width="160" />
            <el-table-column prop="action" label="动作" width="90">
              <template #default="{ row }"><el-tag size="small" :type="notifyTagType(row.level)">{{ row.action }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="object_type" label="对象" width="100" />
            <el-table-column prop="object_no" label="对象编号" width="170" show-overflow-tooltip />
            <el-table-column prop="summary" label="摘要" min-width="280" show-overflow-tooltip />
            <el-table-column prop="operated_by" label="操作人" width="110" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import { approveWorkflowTask, getWorkbench, getWorkbenchCalendar, getWorkbenchNotifications, getWorkflowTasks, rejectWorkflowTask, transferWorkflowTask } from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const workbench = ref<any>({})
const tasks = ref<any[]>([])
const { can, currentUser, refreshSession } = useAuth()

const pendingTasks = computed(() => tasks.value.filter((item) => item.status === '待处理'))

// 任务日历
const calendarDate = ref(new Date())
const calendarLoading = ref(false)
const calendarData = ref<any>({ items: [], summary: { total: 0, overdue: 0, by_type: [], by_status: [] } })
const calendarMonth = computed(() => {
  const d = calendarDate.value
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})
const calendarSummary = computed(() => calendarData.value?.summary || { total: 0, overdue: 0, by_type: [], by_status: [] })

function itemsByDate(day: string) {
  return (calendarData.value?.items || []).filter((it: any) => it.due_date === day)
}

function isOverdue(it: any, day: string): boolean {
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  return day < todayStr && it.status !== '已完成' && it.status !== '已关闭'
}

function typeColor(type: string): string {
  if (type === '项目任务') return '#409eff'
  if (type === 'ECA动作') return '#e6a23c'
  if (type === '项目交付物') return '#67c23a'
  return '#909399'
}

async function loadCalendar() {
  calendarLoading.value = true
  try {
    calendarData.value = await getWorkbenchCalendar(calendarMonth.value)
  } finally {
    calendarLoading.value = false
  }
}

function prevMonth() {
  const d = new Date(calendarDate.value)
  d.setMonth(d.getMonth() - 1)
  calendarDate.value = d
}
function nextMonth() {
  const d = new Date(calendarDate.value)
  d.setMonth(d.getMonth() + 1)
  calendarDate.value = d
}
function goToday() {
  calendarDate.value = new Date()
}

watch(calendarMonth, () => { loadCalendar() })

// 消息通知
const notifications = ref<any>({ items: [], total: 0, by_action: [] })
const notifyFilter = ref('')

async function loadNotifications() {
  notifications.value = await getWorkbenchNotifications({ action: notifyFilter.value || undefined, limit: 100 })
}

function notifyTagType(level: string): any {
  if (level === 'danger') return 'danger'
  if (level === 'warning') return 'warning'
  if (level === 'success') return 'success'
  return 'info'
}

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
  await Promise.all([loadCalendar(), loadNotifications()])
  loading.value = false
})
</script>

<style scoped>
.stage-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
  max-height: 520px;
  overflow-y: auto;
}
.stage-item {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  padding: 12px;
  background: var(--el-bg-color);
}
.stage-blocker {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.compact-card {
  margin-bottom: 4px;
}
.compact-card :deep(.el-card__body) {
  padding: 8px 12px;
}
.calendar-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.cal-cell {
  height: 100%;
  display: flex;
  flex-direction: column;
  font-size: 12px;
}
.cal-day {
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 2px;
}
.cal-items {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.cal-item {
  border-left: 3px solid #909399;
  padding: 1px 4px;
  background: var(--el-fill-color-light);
  border-radius: 2px;
  font-size: 11px;
  line-height: 1.4;
  overflow: hidden;
}
.cal-item.overdue {
  background: var(--el-color-danger-light-9);
}
.cal-item-type {
  color: var(--el-text-color-secondary);
  margin-right: 4px;
}
.cal-item-title {
  color: var(--el-text-color-primary);
}
:deep(.el-calendar-day) {
  height: 92px;
  padding: 4px;
}
</style>
