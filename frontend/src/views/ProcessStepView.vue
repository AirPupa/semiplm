<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>标准工序</strong><span class="muted"> · 独立主控工序，被工艺流程 Seq 引用</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterState" placeholder="状态" clearable style="width: 110px" @change="onSearch">
          <el-option label="有效" value="Active" />
          <el-option label="失效" value="Inactive" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索工序名称/描述" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('process')" type="primary" :icon="Plus" @click="openCreate">新增工序</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="process_step_name" label="工序名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="process_step_version" label="版本" width="80" />
        <el-table-column prop="process_step_type" label="类型" width="90">
          <template #default="{ row }">{{ typeLabel(row.process_step_type) }}</template>
        </el-table-column>
        <el-table-column prop="process_stage_name" label="所属阶段" width="120" />
        <el-table-column prop="process_capability_name" label="制程能力" width="130" />
        <el-table-column prop="recipe_name" label="配方" min-width="160" show-overflow-tooltip />
        <el-table-column prop="key_process" label="关键工序" width="100" />
        <el-table-column prop="owner" label="负责人" width="100" />
        <el-table-column prop="process_step_state" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.process_step_state === 'Active' ? 'success' : 'info'" size="small">{{ row.process_step_state === 'Active' ? '有效' : '失效' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑工序' : '新增工序'" width="820px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <div class="form-grid">
          <el-form-item label="工序名称" prop="process_step_name"><el-input v-model="form.process_step_name" :disabled="!!editingId" /></el-form-item>
          <el-form-item label="版本" prop="process_step_version"><el-input v-model="form.process_step_version" :disabled="!!editingId" /></el-form-item>
          <el-form-item label="工序类型">
            <el-select v-model="form.process_step_type">
              <el-option label="工艺" value="Process" />
              <el-option label="量测" value="Metrology" />
              <el-option label="分选" value="Sort" />
              <el-option label="存储" value="Storage" />
              <el-option label="搬运" value="Transport" />
            </el-select>
          </el-form-item>
          <el-form-item label="详细类型">
            <el-select v-model="form.detail_process_step_type">
              <el-option label="普通" value="Normal" />
              <el-option label="炉管工艺" value="FurnaceProcess" />
            </el-select>
          </el-form-item>
          <el-form-item label="所属阶段">
            <el-select v-model="form.process_stage_name" filterable clearable>
              <el-option v-for="s in stageOptions" :key="s.process_stage_name" :label="s.process_stage_name" :value="s.process_stage_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="制程能力">
            <el-select v-model="form.process_capability_name" filterable clearable>
              <el-option v-for="c in capOptions" :key="c.process_capability_name" :label="c.process_capability_name" :value="c.process_capability_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="配方名称"><el-input v-model="form.recipe_name" /></el-form-item>
          <el-form-item label="分段"><el-input v-model="form.process_group1" /></el-form-item>
          <el-form-item label="工艺层"><el-input v-model="form.process_group2" /></el-form-item>
          <el-form-item label="关键工序"><el-input v-model="form.key_process" /></el-form-item>
          <el-form-item label="Bank名称"><el-input v-model="form.bank_name" /></el-form-item>
          <el-form-item label="成本中心阶段"><el-input v-model="form.cost_center_stage" /></el-form-item>
          <el-form-item label="抽样用户组"><el-input v-model="form.sampling_user_group" /></el-form-item>
          <el-form-item label="归属组"><el-input v-model="form.owner_group_name" /></el-form-item>
          <el-form-item label="负责人"><el-input v-model="form.owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.process_step_state">
              <el-option label="有效" value="Active" />
              <el-option label="失效" value="Inactive" />
            </el-select>
          </el-form-item>
          <el-form-item label="允许跳过"><el-switch v-model="form.is_skip_allowed" /></el-form-item>
          <el-form-item label="必经工序"><el-switch v-model="form.is_mandatory_step" /></el-form-item>
          <el-form-item label="翻转"><el-switch v-model="form.is_flip" /></el-form-item>
          <el-form-item label="描述" class="form-wide"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  createProcessStep,
  deleteProcessStep,
  getProcessCapabilities,
  getProcessStages,
  getProcessSteps,
  updateProcessStep,
} from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'

const { can } = useAuth()
const filterState = ref('')
const stageOptions = ref<any[]>([])
const capOptions = ref<any[]>([])
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(
  (params) => getProcessSteps({ ...params, state: filterState.value }),
)
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const emptyForm = {
  process_step_name: '', process_step_version: '001', description: '', process_step_state: 'Active',
  process_step_type: 'Process', process_stage_name: '', process_group1: '', process_group2: '',
  key_process: '', bank_name: '', process_capability_name: '', recipe_name: '',
  is_skip_allowed: false, is_mandatory_step: false, sampling_user_group: '', owner_group_name: '',
  owner: '', cost_center_stage: '', is_flip: false, detail_process_step_type: 'Normal',
}
const form = ref<any>({ ...emptyForm })
const rules: FormRules = {
  process_step_name: [{ required: true, message: '请输入工序名称', trigger: 'blur' }],
  process_step_version: [{ required: true, message: '请输入版本', trigger: 'blur' }],
}

const TYPE_MAP: Record<string, string> = {
  Process: '工艺', Metrology: '量测', Sort: '分选', Storage: '存储', Transport: '搬运',
}
function typeLabel(v: string) {
  return TYPE_MAP[v] || v
}

async function loadOptions() {
  const [stageRes, capRes] = await Promise.all([getProcessStages(), getProcessCapabilities()])
  stageOptions.value = stageRes.items ?? []
  capOptions.value = capRes.items ?? []
}
function openCreate() {
  editingId.value = null
  form.value = { ...emptyForm }
  dialogVisible.value = true
}
function openEdit(row: any) {
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}
async function save() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      editingId.value ? await updateProcessStep(editingId.value, form.value) : await createProcessStep(form.value)
      ElMessage.success('已保存')
      dialogVisible.value = false
      await loadData()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}
async function remove(row: any) {
  await ElMessageBox.confirm('确认删除此工序？', '删除确认', { type: 'warning' })
  try {
    await deleteProcessStep(row.id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
onMounted(async () => {
  await Promise.all([loadData(), loadOptions()])
})
</script>
