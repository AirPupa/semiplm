<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>项目管理</strong><span class="muted"> · 项目计划、阶段门、交付物、风险登记</span></div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索项目编号/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('project')" type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
        <el-button v-if="can('project')" type="default" @click="showTemplateDialog = true">项目模板</el-button>
      </div>
    </div>

    <div class="list-table-wrap">
    <el-table :data="items" row-key="id" height="100%">
      <el-table-column type="expand">
        <template #default="{ row }">
          <el-tabs class="compact-tabs">
            <el-tab-pane label="阶段任务">
              <div style="margin-bottom:8px" v-if="can('project')">
                <el-button size="small" type="primary" @click="openCreateTask(row)">新增任务</el-button>
                <el-button size="small" type="success" @click="advancePhase(row)" :disabled="row.phase === '量产导入'">推进阶段门</el-button>
              </div>
              <el-table :data="row.tasks" size="small">
                <el-table-column prop="name" label="任务" min-width="180" />
                <el-table-column prop="phase" label="阶段" width="100" />
                <el-table-column prop="owner" label="负责人" width="110" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row: t }">
                    <el-tag size="small" :type="t.status === '已完成' ? 'success' : t.status === '进行中' ? 'warning' : 'info'">{{ t.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="due_date" label="截止日期" width="120" />
                <el-table-column label="操作" width="130" v-if="can('project')">
                  <template #default="{ row: t }">
                    <el-button size="small" @click="openEditTask(row, t)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeTask(t)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="交付物">
              <el-table :data="row.deliverables" size="small">
                <el-table-column prop="name" label="交付物" min-width="160" />
                <el-table-column prop="deliverable_type" label="类型" width="100" />
                <el-table-column prop="phase" label="阶段" width="100" />
                <el-table-column prop="owner" label="负责人" width="100" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row: d }">
                    <el-tag size="small" :type="d.status === '已完成' ? 'success' : d.status === '已关闭' ? 'info' : d.status === '进行中' ? 'warning' : 'info'">{{ d.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="due_date" label="截止日" width="100" />
                <el-table-column label="操作" width="100" v-if="can('project')">
                  <template #default="{ row: d }">
                    <el-button size="small" @click="openEditDeliverable(row, d)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeDeliverable(d)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-button v-if="can('project')" size="small" type="primary" @click="openCreateDeliverable(row)" style="margin-top:8px">新增交付物</el-button>
            </el-tab-pane>
            <el-tab-pane label="风险登记">
              <el-table :data="row.risks" size="small">
                <el-table-column prop="risk_type" label="类型" width="100" />
                <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
                <el-table-column prop="impact" label="影响" width="80" />
                <el-table-column prop="probability" label="概率" width="80" />
                <el-table-column prop="severity" label="严重度" width="80" />
                <el-table-column prop="owner" label="负责人" width="100" />
                <el-table-column prop="status" label="状态" width="100" />
                <el-table-column prop="mitigation" label="缓解措施" min-width="200" show-overflow-tooltip />
                <el-table-column label="操作" width="100" v-if="can('project')">
                  <template #default="{ row: r }">
                    <el-button size="small" @click="openEditRisk(row, r)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeRisk(r)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-button v-if="can('project')" size="small" type="primary" @click="openCreateRisk(row)" style="margin-top:8px">新增风险</el-button>
            </el-tab-pane>
          </el-tabs>
        </template>
      </el-table-column>
      <el-table-column prop="project_no" label="项目编号" width="150" />
      <el-table-column prop="name" label="项目名称" min-width="200" />
      <el-table-column prop="product_model" label="产品型号" width="130" />
      <el-table-column prop="phase" label="阶段" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.phase === '量产导入' ? 'success' : 'primary'">{{ row.phase }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="160">
        <template #default="{ row }"><el-progress :percentage="row.progress" :status="row.progress >= 100 ? 'success' : undefined" /></template>
      </el-table-column>
      <el-table-column prop="owner" label="负责人" width="100" />
      <el-table-column prop="risk_level" label="风险" width="80" />
      <el-table-column prop="end_date" label="计划完成" width="110" />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="can('project')" size="small" type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <!-- Project Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑项目' : '新建项目'" width="640px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="项目编号"><el-input v-model="form.project_no" /></el-form-item>
          <el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="产品型号">
            <el-select v-model="form.product_model" filterable clearable placeholder="选择产品">
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.model" />
            </el-select>
          </el-form-item>
          <el-form-item label="阶段"><el-select v-model="form.phase"><el-option label="概念" value="概念" /><el-option label="设计" value="设计" /><el-option label="流片" value="流片" /><el-option label="验证" value="验证" /><el-option label="试产" value="试产" /><el-option label="量产导入" value="量产导入" /></el-select></el-form-item>
          <el-form-item label="进度"><el-input-number v-model="form.progress" :min="0" :max="100" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="开始日期"><el-input v-model="form.start_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="计划完成"><el-input v-model="form.end_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="风险等级"><el-select v-model="form.risk_level"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- Task Dialog -->
    <el-dialog v-model="taskDialog" :title="taskEditingId ? '编辑任务' : '新增任务'" width="540px">
      <el-form :model="taskForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="任务名称" class="form-wide"><el-input v-model="taskForm.name" /></el-form-item>
          <el-form-item label="阶段"><el-select v-model="taskForm.phase"><el-option label="概念" value="概念" /><el-option label="设计" value="设计" /><el-option label="流片" value="流片" /><el-option label="验证" value="验证" /><el-option label="试产" value="试产" /><el-option label="量产导入" value="量产导入" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="taskForm.owner" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="taskForm.status"><el-option label="待处理" value="待处理" /><el-option label="进行中" value="进行中" /><el-option label="已完成" value="已完成" /></el-select></el-form-item>
          <el-form-item label="截止日期"><el-input v-model="taskForm.due_date" placeholder="YYYY-MM-DD" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="taskDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>

    <!-- Deliverable Dialog -->
    <el-dialog v-model="deliverableDialog" title="交付物" width="640px">
      <el-form :model="deliverableForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="名称"><el-input v-model="deliverableForm.name" /></el-form-item>
          <el-form-item label="类型"><el-input v-model="deliverableForm.deliverable_type" /></el-form-item>
          <el-form-item label="阶段"><el-select v-model="deliverableForm.phase"><el-option label="概念" value="概念" /><el-option label="设计" value="设计" /><el-option label="流片" value="流片" /><el-option label="验证" value="验证" /><el-option label="试产" value="试产" /><el-option label="量产导入" value="量产导入" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="deliverableForm.owner" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="deliverableForm.status"><el-option label="待处理" value="待处理" /><el-option label="进行中" value="进行中" /><el-option label="已完成" value="已完成" /><el-option label="已关闭" value="已关闭" /></el-select></el-form-item>
          <el-form-item label="截止日期"><el-input v-model="deliverableForm.due_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="关联对象类型">
            <el-select v-model="deliverableForm.object_type" clearable placeholder="可选" @change="onObjectTypeChange">
              <el-option label="BOM" value="BOM" />
              <el-option label="文档" value="文档" />
              <el-option label="工艺路线" value="工艺路线" />
            </el-select>
          </el-form-item>
          <el-form-item label="关联对象">
            <el-select v-model="deliverableForm.object_id" filterable clearable placeholder="选择关联对象" :disabled="!deliverableForm.object_type">
              <el-option v-for="obj in linkableObjects" :key="obj.id" :label="obj.label" :value="obj.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="deliverableForm.description" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="deliverableDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDeliverable">保存</el-button>
      </template>
    </el-dialog>

    <!-- Risk Dialog -->
    <el-dialog v-model="riskDialog" title="风险登记" width="600px">
      <el-form :model="riskForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="风险类型"><el-input v-model="riskForm.risk_type" /></el-form-item>
          <el-form-item label="描述"><el-input v-model="riskForm.description" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="影响"><el-select v-model="riskForm.impact"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item>
          <el-form-item label="概率"><el-select v-model="riskForm.probability"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item>
          <el-form-item label="严重度"><el-select v-model="riskForm.severity"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="riskForm.owner" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="riskForm.status"><el-option label="待处理" value="待处理" /><el-option label="已识别" value="已识别" /><el-option label="已关闭" value="已关闭" /></el-select></el-form-item>
          <el-form-item label="缓解措施" class="form-wide"><el-input v-model="riskForm.mitigation" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="riskDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRisk">保存</el-button>
      </template>
    </el-dialog>

    <!-- Template Dialog -->
    <el-dialog v-model="showTemplateDialog" title="项目模板管理" width="760px">
      <div class="toolbar">
        <el-button v-if="can('project')" size="small" type="primary" @click="openCreateTemplate">新增模板</el-button>
      </div>
      <el-table :data="templates">
        <el-table-column prop="code" label="编码" width="140" />
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="stages" label="阶段定义" min-width="280" />
        <el-table-column prop="status" label="状态" width="80" />
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button size="small" @click="openEditTemplate(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeTemplate(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  advanceProjectPhase, createProject, createProjectDeliverable, createProjectRisk, createProjectTask, createProjectTemplate, deleteProject, deleteProjectDeliverable,
  deleteProjectRisk, deleteProjectTask, deleteProjectTemplate, getBoms, getDocuments, getProducts, getProjects, getProjectTemplates, getRoutes, updateProject, updateProjectDeliverable,
  updateProjectRisk, updateProjectTask, updateProjectTemplate,
} from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import { useListPage } from '../composables/useListPage'

const { can, currentUser } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getProjects)
const products = ref<any[]>([])
const templates = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = ref<any>({ project_no: '', name: '', product_model: '', phase: '概念', progress: 0, owner: '', start_date: '', end_date: '', risk_level: '低' })

const taskDialog = ref(false)
const taskProjectId = ref<number>(0)
const taskEditingId = ref<number | null>(null)
const taskForm = ref<any>({ name: '', phase: '概念', owner: '', status: '待处理', due_date: '' })

const deliverableDialog = ref(false)
const deliverableProjectId = ref<number>(0)
const deliverableEditingId = ref<number | null>(null)
const deliverableForm = ref<any>({ name: '', deliverable_type: '', phase: '', owner: '', status: '待处理', due_date: '', description: '', object_type: '', object_id: undefined })
const linkableObjects = ref<any[]>([])
const bomList = ref<any[]>([])
const documentList = ref<any[]>([])
const routeList = ref<any[]>([])

const riskDialog = ref(false)
const riskProjectId = ref<number>(0)
const riskEditingId = ref<number | null>(null)
const riskForm = ref<any>({ risk_type: '技术', description: '', impact: '中', probability: '中', severity: '中', owner: '', status: '待处理', mitigation: '' })

const showTemplateDialog = ref(false)
const templateDialogVisible = ref(false)
const templateEditingId = ref<number | null>(null)
const templateForm = ref<any>({ code: '', name: '', description: '', stages: '["概念","设计","流片","验证","试产"]', status: '启用' })

async function load() {
  await loadData()
  const tRes = await getProjectTemplates()
  templates.value = tRes.items ?? tRes
}

function openCreate() {
  editingId.value = null
  form.value = { project_no: '', name: '', product_model: '', phase: '概念', progress: 0, owner: currentUser.value?.display_name || '', start_date: '', end_date: '', risk_level: '低' }
  dialogVisible.value = true
}
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateProject(editingId.value, form.value) : await createProject(form.value)
  ElMessage.success('项目已保存')
  dialogVisible.value = false
  await load()
}
async function remove(row: any) {
  await ElMessageBox.confirm('确认删除此项目？', '删除确认', { type: 'warning' })
  await deleteProject(row.id)
  ElMessage.success('项目已删除')
  await load()
}

function openCreateTask(project: any) {
  taskProjectId.value = project.id
  taskEditingId.value = null
  taskForm.value = { name: '', phase: project.phase || '概念', owner: currentUser.value?.display_name || '', status: '待处理', due_date: '' }
  taskDialog.value = true
}
function openEditTask(project: any, t: any) {
  taskProjectId.value = project.id
  taskEditingId.value = t.id
  taskForm.value = { ...t }
  taskDialog.value = true
}
async function saveTask() {
  taskEditingId.value ? await updateProjectTask(taskEditingId.value, taskForm.value) : await createProjectTask(taskProjectId.value, taskForm.value)
  ElMessage.success('任务已保存')
  taskDialog.value = false
  await load()
}
async function removeTask(t: any) {
  await ElMessageBox.confirm('确认删除此任务？', '删除确认', { type: 'warning' })
  await deleteProjectTask(t.id)
  ElMessage.success('任务已删除')
  await load()
}

async function advancePhase(row: any) {
  await ElMessageBox.confirm(`确认将项目「${row.name}」从「${row.phase}」阶段推进到下一阶段？\n当前阶段交付物必须全部完成。`, '阶段门推进', { type: 'warning' })
  const res = await advanceProjectPhase(row.id, { acted_by: currentUser.value?.display_name || '系统用户', comment: '' })
  ElMessage.success(res.message || '阶段门已推进')
  await load()
}

function openCreateDeliverable(project: any) {
  deliverableProjectId.value = project.id
  deliverableEditingId.value = null
  deliverableForm.value = { name: '', deliverable_type: '', phase: project.phase || '', owner: currentUser.value?.display_name || '', status: '待处理', due_date: '', description: '', object_type: '', object_id: undefined }
  updateLinkableObjects('')
  deliverableDialog.value = true
}
function openEditDeliverable(project: any, d: any) { deliverableProjectId.value = project.id; deliverableEditingId.value = d.id; deliverableForm.value = { ...d, object_id: d.object_id || undefined }; updateLinkableObjects(d.object_type || ''); deliverableDialog.value = true }

function onObjectTypeChange() {
  deliverableForm.value.object_id = undefined
  updateLinkableObjects(deliverableForm.value.object_type || '')
}

function updateLinkableObjects(objectType: string) {
  if (objectType === 'BOM') {
    linkableObjects.value = bomList.value.map((b: any) => ({ id: b.id, label: `${b.bom_type}-${b.product_model}-${b.version}` }))
  } else if (objectType === '文档') {
    linkableObjects.value = documentList.value.map((d: any) => ({ id: d.id, label: `${d.doc_no} · ${d.title}` }))
  } else if (objectType === '工艺路线') {
    linkableObjects.value = routeList.value.map((r: any) => ({ id: r.id, label: `${r.route_no} · ${r.name}` }))
  } else {
    linkableObjects.value = []
  }
}
async function saveDeliverable() {
  deliverableEditingId.value ? await updateProjectDeliverable(deliverableEditingId.value, deliverableForm.value) : await createProjectDeliverable(deliverableProjectId.value, deliverableForm.value)
  ElMessage.success('交付物已保存')
  deliverableDialog.value = false
  await load()
}
async function removeDeliverable(d: any) {
  await ElMessageBox.confirm('确认删除此交付物？', '删除确认', { type: 'warning' })
  await deleteProjectDeliverable(d.id)
  ElMessage.success('交付物已删除')
  await load()
}

function openCreateRisk(project: any) {
  riskProjectId.value = project.id
  riskEditingId.value = null
  riskForm.value = { risk_type: '技术', description: '', impact: '中', probability: '中', severity: '中', owner: currentUser.value?.display_name || '', status: '待处理', mitigation: '' }
  riskDialog.value = true
}
function openEditRisk(project: any, r: any) { riskProjectId.value = project.id; riskEditingId.value = r.id; riskForm.value = { ...r }; riskDialog.value = true }
async function saveRisk() {
  riskEditingId.value ? await updateProjectRisk(riskEditingId.value, riskForm.value) : await createProjectRisk(riskProjectId.value, riskForm.value)
  ElMessage.success('风险已保存')
  riskDialog.value = false
  await load()
}
async function removeRisk(r: any) {
  await ElMessageBox.confirm('确认删除此风险记录？', '删除确认', { type: 'warning' })
  await deleteProjectRisk(r.id)
  ElMessage.success('风险已删除')
  await load()
}

function openCreateTemplate() { templateEditingId.value = null; templateForm.value = { code: '', name: '', description: '', stages: '["概念","设计","流片","验证","试产"]', status: '启用' }; templateDialogVisible.value = true }
function openEditTemplate(row: any) { templateEditingId.value = row.id; templateForm.value = { ...row }; templateDialogVisible.value = true }
async function saveTemplate() {
  templateEditingId.value ? await updateProjectTemplate(templateEditingId.value, templateForm.value) : await createProjectTemplate(templateForm.value)
  ElMessage.success('模板已保存')
  templateDialogVisible.value = false
  await load()
}
async function removeTemplate(row: any) {
  await ElMessageBox.confirm('确认删除此模板？', '删除确认', { type: 'warning' })
  await deleteProjectTemplate(row.id)
  ElMessage.success('模板已删除')
  await load()
}

onMounted(async () => {
  const pRes = await getProducts()
  products.value = pRes.items ?? pRes
  const [bomRes, docRes, routeRes] = await Promise.all([
    getBoms({ page: 1, page_size: 1000 }),
    getDocuments({ page: 1, page_size: 1000 }),
    getRoutes({ page: 1, page_size: 1000 }),
  ])
  bomList.value = bomRes.items ?? bomRes
  documentList.value = docRes.items ?? docRes
  routeList.value = routeRes.items ?? routeRes
  await load()
})
</script>
