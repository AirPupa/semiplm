<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>工艺配方</strong><span class="muted"> · 配方命名+生命周期，不含物理参数（物理参数在 MES 设备侧）</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterCapability" placeholder="制程能力" clearable filterable style="width: 180px" @change="onSearch">
          <el-option v-for="c in capOptions" :key="c.process_capability_name" :label="c.process_capability_name" :value="c.process_capability_name" />
        </el-select>
        <el-select v-model="filterState" placeholder="状态" clearable style="width: 110px" @change="onSearch">
          <el-option label="有效" value="Valid" />
          <el-option label="失效" value="Invalid" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索配方名称/描述" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('process')" type="primary" :icon="Plus" @click="openCreate">新增配方</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="recipe_name" label="配方名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="process_capability_name" label="制程能力" width="150" />
        <el-table-column prop="object_owner" label="归属" width="110" />
        <el-table-column prop="effective_time" label="生效时间(h)" width="110" />
        <el-table-column prop="expir_alarm_id" label="过期告警" width="120" />
        <el-table-column prop="recipe_state" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.recipe_state === 'Valid' ? 'success' : 'info'" size="small">{{ row.recipe_state === 'Valid' ? '有效' : '失效' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑制程配方' : '新增制程配方'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <div class="form-grid">
          <el-form-item label="制程能力" prop="process_capability_name">
            <el-select v-model="form.process_capability_name" filterable :disabled="!!editingId">
              <el-option v-for="c in capOptions" :key="c.process_capability_name" :label="c.process_capability_name" :value="c.process_capability_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="配方名称" prop="recipe_name"><el-input v-model="form.recipe_name" :disabled="!!editingId" /></el-form-item>
          <el-form-item label="归属"><el-input v-model="form.object_owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.recipe_state">
              <el-option label="有效" value="Valid" />
              <el-option label="失效" value="Invalid" />
            </el-select>
          </el-form-item>
          <el-form-item label="生效时间(h)"><el-input-number v-model="form.effective_time" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="过期告警ID"><el-input v-model="form.expir_alarm_id" /></el-form-item>
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
import { createRecipe, deleteRecipe, getProcessCapabilities, getRecipes, updateRecipe } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'

const { can } = useAuth()
const filterState = ref('')
const filterCapability = ref('')
const capOptions = ref<any[]>([])
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(
  (params) => getRecipes({ ...params, state: filterState.value, capability: filterCapability.value }),
)
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const emptyForm = {
  process_capability_name: '', recipe_name: '', description: '', object_owner: '',
  recipe_state: 'Valid', effective_time: null, expir_alarm_id: '',
}
const form = ref<any>({ ...emptyForm })
const rules: FormRules = {
  process_capability_name: [{ required: true, message: '请选择制程能力', trigger: 'change' }],
  recipe_name: [{ required: true, message: '请输入配方名称', trigger: 'blur' }],
}

async function loadCapOptions() {
  const res = await getProcessCapabilities()
  capOptions.value = res.items ?? []
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
      editingId.value ? await updateRecipe(editingId.value, form.value) : await createRecipe(form.value)
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
  await ElMessageBox.confirm('确认删除此制程配方？', '删除确认', { type: 'warning' })
  try {
    await deleteRecipe(row.id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
onMounted(async () => {
  await Promise.all([loadData(), loadCapOptions()])
})
</script>
