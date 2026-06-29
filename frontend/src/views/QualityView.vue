<template>
  <div v-loading="loading">
    <div class="toolbar">
      <div><strong>质量闭环管理</strong><span class="muted"> · Lot 追溯、缺陷问题、CAPA 纠正预防</span></div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索 Lot/问题编号" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" style="width:240px" />
      </div>
    </div>
    <el-tabs class="panel">
      <el-tab-pane label="Lot / Wafer 追溯">
        <el-table :data="quality.lots || []" height="600">
          <el-table-column prop="product_model" label="型号" width="130" />
          <el-table-column prop="lot_no" label="Lot" width="190" />
          <el-table-column prop="wafer_id" label="Wafer ID" width="110" />
          <el-table-column prop="stage" label="阶段" width="90" />
          <el-table-column prop="cp_yield" label="CP 良率" width="100" />
          <el-table-column prop="ft_yield" label="FT 良率" width="100" />
          <el-table-column prop="bin1_rate" label="Bin1" width="80" />
          <el-table-column prop="issue_count" label="问题数" width="80" />
          <el-table-column prop="status" label="状态" width="110" />
          <el-table-column prop="tested_at" label="测试日期" width="110" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="质量问题">
        <div class="toolbar">
          <el-button v-if="can('quality')" type="primary" :icon="Plus" @click="openCreateIssue">新增问题</el-button>
        </div>
        <el-table :data="quality.issues || []" height="560">
          <el-table-column prop="issue_no" label="问题编号" width="120" fixed />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="product_model" label="型号" width="120" />
          <el-table-column prop="lot_no" label="Lot" width="140" show-overflow-tooltip />
          <el-table-column prop="severity" label="严重度" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.severity === '高' ? 'danger' : row.severity === '中' ? 'warning' : 'info'">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="owner" label="负责人" width="100" />
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === '已关闭' ? 'success' : row.status === 'CAPA 执行中' ? 'warning' : row.status === '已触发 ECR' ? 'primary' : 'danger'">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEditIssue(row)" :disabled="!can('quality') || row.status === '已关闭'">编辑</el-button>
              <el-button size="small" type="primary" @click="createCAPA(row)" :disabled="!can('quality') || row.status === 'CAPA 执行中' || row.status === '已关闭'">发起 CAPA</el-button>
              <el-button size="small" type="warning" @click="triggerEcr(row)" :disabled="!can('quality') || row.status === '已关闭' || row.status === '已触发 ECR'">触发 ECR</el-button>
              <el-button size="small" type="danger" @click="removeIssue(row)" :disabled="!can('quality') || ['CAPA 执行中', '已关闭', '已触发 ECR'].includes(row.status)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="CAPA 管理">
        <div class="toolbar">
          <el-button v-if="can('quality')" type="primary" :icon="Plus" @click="openCreateCAPA">新增 CAPA</el-button>
        </div>
        <el-table :data="capas" height="580">
          <el-table-column prop="capa_no" label="CAPA 编号" width="130" />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column prop="owner" label="负责人" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><el-tag :type="row.status === '已关闭' ? 'success' : row.status === '执行中' ? 'warning' : 'info'" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="due_date" label="截止日期" width="110" />
          <el-table-column prop="closed_at" label="关闭日期" width="110" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEditCAPA(row)" :disabled="!can('quality') || row.status === '已关闭'">编辑</el-button>
              <el-button size="small" type="success" @click="closeCAPA(row)" :disabled="!can('quality') || row.status === '已关闭'">关闭</el-button>
              <el-button size="small" type="danger" @click="removeCAPA(row)" :disabled="!can('quality') || row.status === '已关闭'">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="质量报告归档">
        <div class="toolbar">
          <el-button v-if="can('quality')" type="primary" :icon="Plus" @click="openCreateReport">新增报告</el-button>
          <el-button v-if="can('quality')" type="success" @click="openArchiveDialog">从已关闭问题归档</el-button>
        </div>
        <el-table :data="reports" height="560">
          <el-table-column prop="report_no" label="报告编号" width="120" fixed />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="report_type" label="类型" width="120" />
          <el-table-column prop="product_model" label="型号" width="130" />
          <el-table-column prop="issue_nos" label="关联问题" min-width="140" show-overflow-tooltip />
          <el-table-column prop="capa_nos" label="关联 CAPA" min-width="140" show-overflow-tooltip />
          <el-table-column prop="owner" label="负责人" width="100" />
          <el-table-column prop="archived_at" label="归档日期" width="110" />
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }"><el-tag size="small" :type="row.status === '已归档' ? 'success' : 'info'">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEditReport(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeReport(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Issue Dialog -->
    <el-dialog v-model="issueDialog" :title="issueEditingId ? '编辑质量问题' : '新增质量问题'" width="680px">
      <el-form :model="issueForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="问题编号"><el-input v-model="issueForm.issue_no" placeholder="留空自动生成" /></el-form-item>
          <el-form-item label="标题" class="form-wide"><el-input v-model="issueForm.title" /></el-form-item>
          <el-form-item label="产品型号"><el-input v-model="issueForm.product_model" placeholder="输入产品型号" /></el-form-item>
          <el-form-item label="Lot 编号"><el-input v-model="issueForm.lot_no" /></el-form-item>
          <el-form-item label="严重度"><el-select v-model="issueForm.severity"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="issueForm.owner" /></el-form-item>
          <el-form-item label="根因分析" class="form-wide"><el-input v-model="issueForm.root_cause" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="纠正措施" class="form-wide"><el-input v-model="issueForm.corrective_action" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="issueDialog = false">取消</el-button>
        <el-button type="primary" @click="saveIssue">保存</el-button>
      </template>
    </el-dialog>

    <!-- CAPA Dialog -->
    <el-dialog v-model="capaDialog" :title="capaEditingId ? '编辑 CAPA' : '新增 CAPA'" width="680px">
      <el-form :model="capaForm" label-width="110px">
        <el-form-item label="CAPA 编号"><el-input v-model="capaForm.capa_no" :disabled="!!capaEditingId" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="capaForm.title" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="capaForm.source" /></el-form-item>
        <el-form-item label="负责人"><UserSelect v-model="capaForm.owner" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="capaForm.status"><el-option label="待处理" value="待处理" /><el-option label="执行中" value="执行中" /><el-option label="已关闭" value="已关闭" /></el-select></el-form-item>
        <el-form-item label="截止日期"><el-input v-model="capaForm.due_date" placeholder="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="根因分析"><el-input v-model="capaForm.root_cause" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="纠正措施"><el-input v-model="capaForm.corrective_action" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="预防措施"><el-input v-model="capaForm.preventive_action" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="关闭结论"><el-input v-model="capaForm.result" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="capaDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCAPA">保存</el-button>
      </template>
    </el-dialog>

    <!-- Report Dialog -->
    <el-dialog v-model="reportDialog" :title="reportEditingId ? '编辑质量报告' : '新增质量报告'" width="720px">
      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="报告编号"><el-input v-model="reportForm.report_no" placeholder="留空自动生成" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="reportForm.title" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="reportForm.report_type" /></el-form-item>
        <el-form-item label="产品型号"><el-input v-model="reportForm.product_model" /></el-form-item>
        <el-form-item label="关联问题"><el-input v-model="reportForm.issue_nos" placeholder="多个用顿号分隔" /></el-form-item>
        <el-form-item label="关联 CAPA"><el-input v-model="reportForm.capa_nos" placeholder="多个用顿号分隔" /></el-form-item>
        <el-form-item label="负责人"><UserSelect v-model="reportForm.owner" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="reportForm.status"><el-option label="已归档" value="已归档" /><el-option label="草稿" value="草稿" /></el-select></el-form-item>
        <el-form-item label="摘要"><el-input v-model="reportForm.summary" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="根因分析"><el-input v-model="reportForm.root_cause" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="纠正措施"><el-input v-model="reportForm.corrective_action" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="预防措施"><el-input v-model="reportForm.preventive_action" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportDialog = false">取消</el-button>
        <el-button type="primary" @click="saveReport">保存</el-button>
      </template>
    </el-dialog>

    <!-- Archive from Issues Dialog -->
    <el-dialog v-model="archiveDialog" title="从已关闭问题归档" width="640px">
      <el-form label-width="100px">
        <el-form-item label="报告标题"><el-input v-model="archiveForm.title" placeholder="留空自动生成" /></el-form-item>
        <el-form-item label="负责人"><UserSelect v-model="archiveForm.owner" /></el-form-item>
        <el-form-item label="选择问题">
          <el-table :data="closedIssues" size="small" max-height="320" @selection-change="onArchiveSelection">
            <el-table-column type="selection" width="40" />
            <el-table-column prop="issue_no" label="编号" width="100" />
            <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
            <el-table-column prop="product_model" label="型号" width="100" />
            <el-table-column prop="severity" label="严重度" width="70" />
          </el-table>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="archiveDialog = false">取消</el-button>
        <el-button type="primary" @click="doArchive" :disabled="!archiveForm.issue_ids.length">确认归档</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  archiveQualityReportFromIssues, closeQualityCAPA, closeQualityIssue, createCAPAFromIssue, createQualityCAPA, createQualityIssue, createQualityReport, deleteQualityCAPA, deleteQualityIssue,
  deleteQualityReport, getQuality, getQualityCAPAs, getQualityReports, triggerEcrFromIssue, updateQualityCAPA, updateQualityIssue, updateQualityReport,
} from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'

const loading = ref(true)
const { can, currentUser } = useAuth()
const quality = ref<any>({})
const capas = ref<any[]>([])
const reports = ref<any[]>([])
const keyword = ref('')

const issueDialog = ref(false)
const issueEditingId = ref<number | null>(null)
const issueForm = ref<any>({ issue_no: '', product_model: '', lot_no: '', title: '', severity: '中', status: '新建', owner: '', root_cause: '', corrective_action: '' })

const capaDialog = ref(false)
const capaEditingId = ref<number | null>(null)
const capaForm = ref<any>({ capa_no: '', title: '', source: '质量问题', owner: '', status: '待处理', due_date: '', root_cause: '', corrective_action: '', preventive_action: '', result: '' })

const reportDialog = ref(false)
const reportEditingId = ref<number | null>(null)
const reportForm = ref<any>({ report_no: '', title: '', report_type: '质量归档', product_model: '', issue_nos: '', capa_nos: '', summary: '', root_cause: '', corrective_action: '', preventive_action: '', owner: '', status: '已归档' })

const archiveDialog = ref(false)
const archiveForm = ref<any>({ title: '', owner: '', issue_ids: [] as number[] })
const closedIssues = ref<any[]>([])

async function load() {
  quality.value = await getQuality({ page: 1, page_size: 1000, keyword: keyword.value.trim() })
  const capaRes = await getQualityCAPAs({ page: 1, page_size: 1000 })
  capas.value = capaRes.items ?? capaRes
  const reportRes = await getQualityReports({ page: 1, page_size: 1000 })
  reports.value = reportRes.items ?? reportRes
}

function onSearch() { load() }

function openCreateIssue() {
  issueEditingId.value = null
  issueForm.value = { issue_no: '', product_model: '', lot_no: '', title: '', severity: '中', status: '新建', owner: currentUser.value?.display_name || '', root_cause: '', corrective_action: '' }
  issueDialog.value = true
}
function openEditIssue(row: any) {
  issueEditingId.value = row.id
  issueForm.value = { ...row }
  issueDialog.value = true
}
async function saveIssue() {
  issueEditingId.value ? await updateQualityIssue(issueEditingId.value, issueForm.value) : await createQualityIssue(issueForm.value)
  ElMessage.success('质量问题已保存')
  issueDialog.value = false
  await load()
}
async function removeIssue(row: any) {
  await ElMessageBox.confirm(`确认删除质量问题 ${row.issue_no}？`, '删除确认', { type: 'warning' })
  await deleteQualityIssue(row.id)
  ElMessage.success('问题已删除')
  await load()
}

async function createCAPA(issue: any) {
  await ElMessageBox.confirm(`为 ${issue.issue_no} 创建 CAPA？`, '发起 CAPA', { type: 'info' })
  await createCAPAFromIssue(issue.id)
  ElMessage.success('CAPA 已创建')
  await load()
}

async function triggerEcr(issue: any) {
  await ElMessageBox.confirm(`从质量问题 ${issue.issue_no} 触发 ECR 变更？\n将自动创建关联产品的变更单草稿。`, '触发 ECR', { type: 'warning' })
  const res = await triggerEcrFromIssue(issue.id)
  ElMessage.success(`ECR 已创建：${res.change_no}`)
  await load()
}

function openCreateCAPA() {
  capaEditingId.value = null
  capaForm.value = { capa_no: '', title: '', source: '质量问题', owner: currentUser.value?.display_name || '', status: '待处理', due_date: '', root_cause: '', corrective_action: '', preventive_action: '', result: '' }
  capaDialog.value = true
}
function openEditCAPA(row: any) {
  capaEditingId.value = row.id
  capaForm.value = { ...row }
  capaDialog.value = true
}
async function saveCAPA() {
  capaEditingId.value ? await updateQualityCAPA(capaEditingId.value, capaForm.value) : await createQualityCAPA(capaForm.value)
  ElMessage.success('CAPA 已保存')
  capaDialog.value = false
  await load()
}
async function closeCAPA(row: any) {
  const { value } = await ElMessageBox.prompt('请输入关闭结论', '关闭 CAPA', {
    inputValue: row.result || '已完成并验证',
    confirmButtonText: '确认关闭',
    cancelButtonText: '取消',
  })
  const res = await closeQualityCAPA(row.id, { acted_by: currentUser.value?.display_name || '系统用户', comment: value })
  ElMessage.success(res.issue_closed ? 'CAPA 已关闭，关联质量问题已联动关闭' : 'CAPA 已关闭')
  await load()
}
async function removeCAPA(row: any) {
  await ElMessageBox.confirm('确认删除此 CAPA？', '删除确认', { type: 'warning' })
  await deleteQualityCAPA(row.id)
  ElMessage.success('CAPA 已删除')
  await load()
}

function openCreateReport() {
  reportEditingId.value = null
  reportForm.value = { report_no: '', title: '', report_type: '质量归档', product_model: '', issue_nos: '', capa_nos: '', summary: '', root_cause: '', corrective_action: '', preventive_action: '', owner: currentUser.value?.display_name || '', status: '已归档' }
  reportDialog.value = true
}
function openEditReport(row: any) {
  reportEditingId.value = row.id
  reportForm.value = { ...row }
  reportDialog.value = true
}
async function saveReport() {
  reportEditingId.value ? await updateQualityReport(reportEditingId.value, reportForm.value) : await createQualityReport(reportForm.value)
  ElMessage.success('报告已保存')
  reportDialog.value = false
  await load()
}
async function removeReport(row: any) {
  await ElMessageBox.confirm('确认删除此报告？', '删除确认', { type: 'warning' })
  await deleteQualityReport(row.id)
  ElMessage.success('报告已删除')
  await load()
}

function openArchiveDialog() {
  closedIssues.value = (quality.value.issues || []).filter((i: any) => i.status === '已关闭')
  if (!closedIssues.value.length) {
    ElMessage.warning('暂无已关闭的质量问题可归档')
    return
  }
  archiveForm.value = { title: '', owner: currentUser.value?.display_name || '', issue_ids: [] }
  archiveDialog.value = true
}
function onArchiveSelection(rows: any[]) {
  archiveForm.value.issue_ids = rows.map((r) => r.id)
}
async function doArchive() {
  if (!archiveForm.value.issue_ids.length) {
    ElMessage.warning('请选择要归档的问题')
    return
  }
  const res = await archiveQualityReportFromIssues({ issue_ids: archiveForm.value.issue_ids, title: archiveForm.value.title, owner: archiveForm.value.owner })
  ElMessage.success(`归档报告已生成：${res.report_no}`)
  archiveDialog.value = false
  await load()
}

onMounted(async () => { await load(); loading.value = false })
</script>
