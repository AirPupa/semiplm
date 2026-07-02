<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>工艺阶段</strong><span class="muted"> · 工艺分段与工艺层定义</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterState" placeholder="状态" clearable style="width: 110px" @change="loadData">
          <el-option label="有效" value="Valid" />
          <el-option label="失效" value="Invalid" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索阶段名称/描述" :prefix-icon="Search" clearable @keyup.enter="loadData" @clear="loadData" />
        <el-button v-if="can('process')" type="primary" :icon="Plus" @click="openCreate">新增阶段</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="idx" label="序号" width="80" sortable />
        <el-table-column prop="process_stage_name" label="阶段名称" min-width="140" />
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column prop="process_group1" label="分段" width="120" />
        <el-table-column prop="process_group2" label="工艺层" width="120" />
        <el-table-column prop="key_process" label="关键工序" width="120" />
        <el-table-column prop="process_stage_state" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.process_stage_state === 'Valid' ? 'success' : 'info'" size="small">{{ row.process_stage_state === 'Valid' ? '有效' : '失效' }}</el-tag>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑制程阶段' : '新增制程阶段'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <div class="form-grid">
          <el-form-item label="序号" prop="idx"><el-input-number v-model="form.idx" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="阶段名称" prop="process_stage_name"><el-input v-model="form.process_stage_name" :disabled="!!editingId" /></el-form-item>
          <el-form-item label="分段"><el-input v-model="form.process_group1" placeholder="如前段/中段/后段" /></el-form-item>
          <el-form-item label="工艺层"><el-input v-model="form.process_group2" placeholder="如光刻/刻蚀/薄膜" /></el-form-item>
          <el-form-item label="关键工序"><el-input v-model="form.key_process" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.process_stage_state">
              <el-option label="有效" value="Valid" />
              <el-option label="失效" value="Invalid" />
            </el-select>
          </el-form-item>
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
import { createProcessStage, deleteProcessStage, getProcessStages, updateProcessStage } from '../api'
import { useAuth } from '../auth'

const { can } = useAuth()
const items = ref<any[]>([])
const loading = ref(true)
const keyword = ref('')
const filterState = ref('')
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const emptyForm = { idx: 0, process_stage_name: '', description: '', process_group1: '', process_group2: '', key_process: '', process_stage_state: 'Valid' }
const form = ref<any>({ ...emptyForm })
const rules: FormRules = {
  process_stage_name: [{ required: true, message: '请输入阶段名称', trigger: 'blur' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await getProcessStages({ keyword: keyword.value.trim(), state: filterState.value })
    items.value = res.items ?? []
  } finally {
    loading.value = false
  }
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
      editingId.value ? await updateProcessStage(editingId.value, form.value) : await createProcessStage(form.value)
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
  await ElMessageBox.confirm('确认删除此制程阶段？', '删除确认', { type: 'warning' })
  try {
    await deleteProcessStage(row.id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
onMounted(loadData)
</script>
