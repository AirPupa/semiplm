<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel list-panel">
      <div class="toolbar">
        <div><strong>流程模板</strong><span class="muted"> · 按对象和项目类型配置审批流程</span></div>
        <div class="toolbar-actions">
          <el-input v-model="keyword" placeholder="搜索编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
          <el-button type="primary" :icon="Plus" @click="openCreate">新增模板</el-button>
        </div>
      </div>
      <div class="list-table-wrap">
        <el-table :data="items" highlight-current-row @current-change="selected = $event" height="100%">
          <el-table-column prop="code" label="编码" width="150" fixed />
          <el-table-column prop="name" label="名称" min-width="180" />
          <el-table-column prop="object_type" label="对象" width="100" />
          <el-table-column prop="project_type" label="项目类型" width="120" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column label="操作" width="150" fixed="right" class-name="table-actions-cell">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button size="small" @click.stop="openEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" @click.stop="removeTemplate(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
      </div>
    </div>
    <div class="panel detail-panel">
      <div class="toolbar">
        <div>
          <strong>{{ selected?.name || '流程节点' }}</strong>
          <span v-if="selected" class="muted"> · {{ selected.object_type }} / {{ selected.project_type || '通用' }}</span>
        </div>
        <el-button :icon="Plus" :disabled="!selected" @click="openNodeCreate">新增节点</el-button>
      </div>
      <el-table :data="selected?.nodes || []" size="small">
        <el-table-column prop="sequence" label="序号" width="70" />
        <el-table-column prop="name" label="节点" min-width="130" />
        <el-table-column prop="role_name" label="角色" width="130" />
        <el-table-column prop="action_type" label="动作" width="100" />
        <el-table-column prop="sla_hours" label="SLA(h)" width="90" />
        <el-table-column label="操作" width="150" fixed="right" class-name="table-actions-cell">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" @click="openNodeEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeNode(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑流程模板' : '新增流程模板'" width="680px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="对象类型"><el-input v-model="form.object_type" /></el-form-item>
          <el-form-item label="项目类型"><el-input v-model="form.project_type" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="nodeDialog" :title="editingNodeId ? '编辑流程节点' : '新增流程节点'" width="560px">
      <el-form :model="nodeForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="序号"><el-input-number v-model="nodeForm.sequence" :min="1" /></el-form-item>
          <el-form-item label="节点"><el-input v-model="nodeForm.name" /></el-form-item>
          <el-form-item label="角色"><el-select v-model="nodeForm.role_name"><el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.name" /></el-select></el-form-item>
          <el-form-item label="动作"><el-input v-model="nodeForm.action_type" /></el-form-item>
          <el-form-item label="SLA小时"><el-input-number v-model="nodeForm.sla_hours" :min="1" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="nodeDialog = false">取消</el-button><el-button type="primary" @click="saveNode">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  createWorkflowNode,
  createWorkflowTemplate,
  deleteWorkflowNode,
  deleteWorkflowTemplate,
  getAdminRoles,
  getWorkflowTemplates,
  updateWorkflowNode,
  updateWorkflowTemplate,
} from '../api'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getWorkflowTemplates)
const roles = ref<any[]>([])
const selected = ref<any>()
const dialogVisible = ref(false)
const nodeDialog = ref(false)
const editingId = ref<number | null>(null)
const editingNodeId = ref<number | null>(null)
const emptyForm = { code: '', name: '', object_type: '', project_type: '', status: '启用', description: '' }
const emptyNode = { sequence: 1, name: '', role_name: '', action_type: '审批', sla_hours: 24 }
const form = ref<any>({ ...emptyForm })
const nodeForm = ref<any>({ ...emptyNode })

async function loadRows() {
  await loadData()
  const roleRes = await getAdminRoles()
  roles.value = roleRes.items ?? roleRes
  selected.value = (items.value || []).find((item) => item.id === selected.value?.id) || (items.value || [])[0]
}
function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  const row = editingId.value ? await updateWorkflowTemplate(editingId.value, form.value) : await createWorkflowTemplate(form.value)
  selected.value = row
  ElMessage.success('流程模板已保存')
  dialogVisible.value = false
  await loadRows()
}
async function removeTemplate(row: any) {
  await ElMessageBox.confirm(`确认删除流程模板 ${row.code}？关联节点会一并删除。`, '删除确认', { type: 'warning' })
  await deleteWorkflowTemplate(row.id)
  ElMessage.success('流程模板已删除')
  if (selected.value?.id === row.id) selected.value = undefined
  await loadRows()
}
function openNodeCreate() {
  if (!selected.value) return
  editingNodeId.value = null
  nodeForm.value = { ...emptyNode, sequence: (selected.value?.nodes?.length || 0) + 1, role_name: roles.value[0]?.name }
  nodeDialog.value = true
}
function openNodeEdit(row: any) {
  editingNodeId.value = row.id
  nodeForm.value = { ...row }
  nodeDialog.value = true
}
async function saveNode() {
  if (!selected.value) return
  if (editingNodeId.value) {
    await updateWorkflowNode(editingNodeId.value, nodeForm.value)
  } else {
    await createWorkflowNode(selected.value.id, nodeForm.value)
  }
  ElMessage.success('流程节点已保存')
  nodeDialog.value = false
  await loadRows()
}
async function removeNode(row: any) {
  await ElMessageBox.confirm(`确认删除流程节点 ${row.sequence}. ${row.name}？`, '删除确认', { type: 'warning' })
  await deleteWorkflowNode(row.id)
  ElMessage.success('流程节点已删除')
  await loadRows()
}
onMounted(async () => { await loadRows() })
</script>
