<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="panel-title">变更执行动作</div>
      <el-table :data="actions" height="680">
        <el-table-column prop="action_no" label="ECA 编号" width="210" fixed />
        <el-table-column prop="change_no" label="来源 ECR" width="180" />
        <el-table-column prop="product_model" label="型号" width="130" />
        <el-table-column prop="action_type" label="动作类型" width="100" />
        <el-table-column prop="target_object" label="对象" min-width="180" />
        <el-table-column prop="department" label="部门" width="110" />
        <el-table-column prop="owner" label="负责人" width="90" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="due_date" label="截止日期" width="120" />
      </el-table>
    </div>
    <div class="panel">
      <div class="toolbar">
        <div class="panel-title">ERP / MES / QMS 同步队列</div>
        <el-button size="small" @click="load">刷新</el-button>
      </div>
      <div class="integration-summary">
        <div>
          <span>全部</span>
          <strong>{{ summary.total || 0 }}</strong>
        </div>
        <div>
          <span>等待</span>
          <strong>{{ summary.waiting || 0 }}</strong>
        </div>
        <div>
          <span>处理中</span>
          <strong>{{ summary.processing || 0 }}</strong>
        </div>
        <div>
          <span>失败</span>
          <strong>{{ summary.failed || 0 }}</strong>
        </div>
        <div>
          <span>成功</span>
          <strong>{{ summary.success || 0 }}</strong>
        </div>
      </div>
      <div class="integration-filters">
        <el-select v-model="filters.target_system" clearable placeholder="系统" size="small">
          <el-option label="ERP" value="ERP" />
          <el-option label="MES" value="MES" />
          <el-option label="QMS" value="QMS" />
        </el-select>
        <el-select v-model="filters.status" clearable placeholder="状态" size="small">
          <el-option label="等待" value="等待" />
          <el-option label="处理中" value="处理中" />
          <el-option label="失败" value="失败" />
          <el-option label="成功" value="成功" />
        </el-select>
        <el-input v-model="filters.keyword" clearable placeholder="对象编号 / 型号 / 作业号" size="small" />
        <el-button size="small" type="primary" @click="load">查询</el-button>
        <el-button size="small" @click="resetFilters">重置</el-button>
      </div>
      <div class="integration-list">
        <div v-for="job in jobs" :key="job.id" class="integration-item">
          <div class="toolbar">
            <strong>{{ job.target_system }} · {{ job.object_type }}</strong>
            <el-tag size="small" :type="job.status === '成功' ? 'success' : job.status === '失败' ? 'danger' : 'warning'">
              {{ job.status }}
            </el-tag>
          </div>
          <div class="integration-meta">
            <span>{{ job.product_model }}</span>
            <button type="button" @click="traceObject(job.object_no)">{{ job.object_no }}</button>
            <span>{{ job.direction }}</span>
          </div>
          <div class="muted">{{ job.triggered_by }} · {{ job.triggered_at }}</div>
          <div class="stage-blocker">{{ job.message }}</div>
          <div class="integration-log">
            <span>尝试 {{ job.attempt_count || 0 }} 次</span>
            <span>最近同步 {{ job.last_sync_at || '-' }}</span>
            <span>下游编号 {{ job.external_id || '-' }}</span>
          </div>
          <div v-if="job.response_message" class="integration-response">{{ job.response_message }}</div>
          <div class="integration-actions">
            <el-button size="small" :disabled="!can('integration') || job.status === '成功' || job.status === '处理中'" @click="start(job)">开始</el-button>
            <el-button size="small" type="primary" :disabled="!can('integration') || job.status === '成功'" @click="complete(job)">成功</el-button>
            <el-button size="small" :disabled="!can('integration') || job.status === '成功'" @click="fail(job)">失败</el-button>
            <el-button size="small" :disabled="!can('integration') || job.status === '成功'" @click="retry(job)">重试</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  completeIntegrationJob,
  failIntegrationJob,
  getChangeActions,
  getIntegrationJobs,
  getIntegrationSummary,
  retryIntegrationJob,
  startIntegrationJob,
} from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const actions = ref<any[]>([])
const jobs = ref<any[]>([])
const summary = ref<any>({})
const filters = reactive({
  target_system: '',
  status: '',
  keyword: '',
})
const { can, currentUser, refreshSession } = useAuth()

function actor() {
  return currentUser.value?.display_name || '系统用户'
}

async function load() {
  loading.value = true
  const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value))
  const [actionRows, jobRows, summaryData] = await Promise.all([getChangeActions({ page: 1, page_size: 1000 }), getIntegrationJobs(params), getIntegrationSummary()])
  actions.value = actionRows.items ?? actionRows
  jobs.value = jobRows.items ?? jobRows
  summary.value = summaryData
  loading.value = false
}

async function resetFilters() {
  filters.target_system = ''
  filters.status = ''
  filters.keyword = ''
  await load()
}

async function traceObject(objectNo: string) {
  filters.keyword = objectNo
  await load()
}

async function start(row: any) {
  if (!can('integration') || row.status === '成功' || row.status === '处理中') return
  await startIntegrationJob(row.id, { acted_by: actor(), response_message: `${actor()} 已发起 ${row.target_system} 同步` })
  ElMessage.success('同步作业已进入处理中')
  await load()
}

async function complete(row: any) {
  if (!can('integration') || row.status === '成功') return
  const { value } = await ElMessageBox.prompt('请输入下游系统返回编号', '标记同步成功', {
    inputValue: row.external_id || `${row.target_system}-${row.object_no}`,
    confirmButtonText: '确认',
    cancelButtonText: '取消',
  })
  await completeIntegrationJob(row.id, {
    acted_by: actor(),
    external_id: value,
    response_message: `${row.target_system} 已确认接收，编号 ${value}`,
  })
  ElMessage.success('同步作业已标记成功')
  await load()
}

async function fail(row: any) {
  if (!can('integration') || row.status === '成功') return
  const { value } = await ElMessageBox.prompt('请输入失败原因或接口返回信息', '标记同步失败', {
    inputValue: row.response_message || '接口返回校验失败',
    confirmButtonText: '确认',
    cancelButtonText: '取消',
  })
  await failIntegrationJob(row.id, { acted_by: actor(), response_message: value })
  ElMessage.warning('同步作业已标记失败')
  await load()
}

async function retry(row: any) {
  if (!can('integration') || row.status === '成功') return
  await retryIntegrationJob(row.id, { acted_by: actor(), response_message: `${actor()} 已加入重试队列` })
  ElMessage.success('已加入重试队列')
  await load()
}

onMounted(async () => {
  await refreshSession()
  await load()
})
</script>
