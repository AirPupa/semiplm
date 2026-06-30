<template>
  <div class="panel lifecycle-template-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>生命周期</strong>
        <span class="muted"> · 维护业务对象生命周期模板和状态流转</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索模板编码/名称" :prefix-icon="Search" clearable style="width:220px" @keyup.enter="onSearch" @clear="onSearch" />
        <el-button type="primary" :icon="Plus" @click="openCreate">新增模板</el-button>
      </div>
    </div>

    <div class="lifecycle-template-table-wrap">
      <el-table :data="items" row-key="id" height="100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="nested-grid">
              <div class="toolbar compact-toolbar">
                <strong>{{ row.name }} 状态流转</strong>
                <el-button size="small" :icon="Plus" @click="openStateCreate(row)">新增状态</el-button>
              </div>
              <el-table :data="row.states || []" size="small" border>
                <el-table-column prop="sequence" label="序号" width="70" />
                <el-table-column prop="name" label="状态" width="120" />
                <el-table-column prop="state_type" label="类型" width="110" />
                <el-table-column prop="allow_edit" label="允许编辑" width="100" />
                <el-table-column prop="require_workflow" label="需流程" width="90" />
                <el-table-column prop="next_states" label="可流转到" min-width="180" />
                <el-table-column label="操作" width="150">
                  <template #default="{ row: state }">
                    <div class="row-actions">
                      <el-button size="small" @click="openStateEdit(row, state)">编辑</el-button>
                      <el-button size="small" type="danger" @click="removeState(state)">删除</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="object_type" label="对象" width="120" fixed />
        <el-table-column prop="code" label="模板编码" width="170" />
        <el-table-column prop="name" label="模板名称" width="170" />
        <el-table-column prop="description" label="说明" min-width="260" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }"><el-tag size="small" :type="row.status === '启用' ? 'success' : 'info'">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="onSizeChange"
        @current-change="onPageChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑模板' : '新增模板'" width="760px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="模板编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="模板名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="对象"><el-input v-model="form.object_type" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="说明"><el-input v-model="form.description" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="stateDialogVisible" :title="stateEditingId ? '编辑状态' : '新增状态'" width="680px">
      <el-form :model="stateForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="排序"><el-input-number v-model="stateForm.sequence" :min="1" /></el-form-item>
          <el-form-item label="状态名"><el-input v-model="stateForm.name" /></el-form-item>
          <el-form-item label="状态类型"><el-input v-model="stateForm.state_type" /></el-form-item>
          <el-form-item label="允许编辑"><el-select v-model="stateForm.allow_edit"><el-option label="是" value="是" /><el-option label="否" value="否" /></el-select></el-form-item>
          <el-form-item label="需流程"><el-select v-model="stateForm.require_workflow"><el-option label="是" value="是" /><el-option label="否" value="否" /></el-select></el-form-item>
          <el-form-item label="可流转到"><el-input v-model="stateForm.next_states" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="stateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveState">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  createLifecycleState,
  createLifecycleTemplate,
  deleteLifecycleState,
  deleteLifecycleTemplate,
  getLifecycleTemplates,
  updateLifecycleState,
  updateLifecycleTemplate,
} from '../api'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage<any>(getLifecycleTemplates)
const dialogVisible = ref(false)
const stateDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const stateEditingId = ref<number | null>(null)
const parentRow = ref<any | null>(null)
const emptyForm = { code: '', name: '', object_type: '', status: '启用', description: '' }
const emptyStateForm = { sequence: 1, name: '', state_type: '中间态', allow_edit: '是', require_workflow: '否', next_states: '' }
const form = ref<any>({ ...emptyForm })
const stateForm = ref<any>({ ...emptyStateForm })

function openCreate() {
  editingId.value = null
  form.value = { ...emptyForm }
  dialogVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = { ...row }
  delete form.value.states
  dialogVisible.value = true
}

async function save() {
  editingId.value ? await updateLifecycleTemplate(editingId.value, form.value) : await createLifecycleTemplate(form.value)
  ElMessage.success('模板已保存')
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除模板 ${row.name || row.code}？`, '删除确认', { type: 'warning' })
    await deleteLifecycleTemplate(row.id)
    ElMessage.success('模板已删除')
    await loadData()
  } catch {
    // 用户取消
  }
}

function openStateCreate(row: any) {
  parentRow.value = row
  stateEditingId.value = null
  stateForm.value = { ...emptyStateForm }
  stateDialogVisible.value = true
}

function openStateEdit(row: any, child: any) {
  parentRow.value = row
  stateEditingId.value = child.id
  stateForm.value = { ...child }
  stateDialogVisible.value = true
}

async function saveState() {
  if (!parentRow.value) return
  stateEditingId.value ? await updateLifecycleState(stateEditingId.value, stateForm.value) : await createLifecycleState(parentRow.value.id, stateForm.value)
  ElMessage.success('状态已保存')
  stateDialogVisible.value = false
  await loadData()
}

async function removeState(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除状态 ${row.name}？`, '删除确认', { type: 'warning' })
    await deleteLifecycleState(row.id)
    ElMessage.success('状态已删除')
    await loadData()
  } catch {
    // 用户取消
  }
}

onMounted(loadData)
</script>

<style scoped>
.lifecycle-template-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 82px);
}

.lifecycle-template-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0;
}
</style>
