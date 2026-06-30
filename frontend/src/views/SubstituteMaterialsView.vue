<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>替代料管理</strong><span class="muted"> · 替代策略、风险等级、有效期</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 100px" @change="onFilterChange">
          <el-option v-for="o in commonStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索物料编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('material')" type="primary" :icon="Plus" @click="openCreate">新增替代料</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="filteredItems" height="100%">
        <el-table-column prop="material_code" label="主物料编码" width="140" />
        <el-table-column prop="material_name" label="主物料名称" min-width="160" />
        <el-table-column prop="substitute_code" label="替代物料编码" width="140" />
        <el-table-column prop="substitute_name" label="替代物料名称" min-width="160" />
        <el-table-column prop="substitute_type" label="替代类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.substitute_type === '功能替代' ? 'primary' : row.substitute_type === '参数替代' ? 'warning' : 'info'">{{ row.substitute_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strategy" label="策略" width="100" />
        <el-table-column prop="risk_level" label="风险" width="80">
          <template #default="{ row }">
            <el-tag :type="row.risk_level === '高' ? 'danger' : row.risk_level === '中' ? 'warning' : 'success'" size="small">{{ row.risk_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="effective_date" label="生效日" width="110" />
        <el-table-column prop="expiry_date" label="失效日" width="110" />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑替代料' : '新增替代料'" width="620px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <div class="form-grid">
          <el-form-item label="主物料" prop="material_code">
            <el-select v-model="materialSelect" filterable placeholder="请选择主物料" style="width: 100%" @change="onMaterialChange">
              <el-option v-for="m in materials" :key="m.code" :label="`${m.code} - ${m.name}`" :value="m.code" />
            </el-select>
          </el-form-item>
          <el-form-item label="替代物料" prop="substitute_code">
            <el-select v-model="substituteSelect" filterable placeholder="请选择替代物料" style="width: 100%" @change="onSubstituteChange">
              <el-option v-for="m in materials" :key="m.code" :label="`${m.code} - ${m.name}`" :value="m.code" :disabled="m.code === materialSelect" />
            </el-select>
          </el-form-item>
          <el-form-item label="替代类型" prop="substitute_type">
            <el-select v-model="form.substitute_type">
              <el-option v-for="o in substituteTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="策略" prop="strategy">
            <el-select v-model="form.strategy">
              <el-option v-for="o in substituteStrategyOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="风险等级"><el-select v-model="form.risk_level"><el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option v-for="o in commonStatusOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="生效日期">
            <el-date-picker v-model="form.effective_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" :disabled-date="disabledEffective" />
          </el-form-item>
          <el-form-item label="失效日期">
            <el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width: 100%" :disabled-date="disabledExpiry" />
          </el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
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
import { computed, onMounted, ref } from 'vue'
import { createSubstituteMaterial, deleteSubstituteMaterial, getMaterials, getSubstituteMaterials, updateSubstituteMaterial } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const { can } = useAuth()
const substituteTypeOptions = useDictionary('DICT_SUBSTITUTE_TYPE').options
const substituteStrategyOptions = useDictionary('DICT_SUBSTITUTE_STRATEGY').options
const riskLevelOptions = useDictionary('DICT_RISK_LEVEL').options
const commonStatusOptions = useDictionary('DICT_COMMON_STATUS').options
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getSubstituteMaterials)
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const materials = ref<any[]>([])
const materialSelect = ref('')
const substituteSelect = ref('')
const filterStatus = ref('')
const emptyForm = { material_code: '', material_name: '', material_id: null as number | null, substitute_code: '', substitute_name: '', substitute_material_id: null as number | null, substitute_type: '功能替代', strategy: '一对一', risk_level: '中', status: '启用', effective_date: '', expiry_date: '', description: '' }
const form = ref<any>({ ...emptyForm })

const rules: FormRules = {
  material_code: [{ required: true, message: '请选择主物料', trigger: 'change' }],
  substitute_code: [{ required: true, message: '请选择替代物料', trigger: 'change' }],
  substitute_type: [{ required: true, message: '请选择替代类型', trigger: 'change' }],
  strategy: [{ required: true, message: '请选择策略', trigger: 'change' }],
}

const filteredItems = computed(() => {
  if (!filterStatus.value) return items.value || []
  return (items.value || []).filter((r: any) => r.status === filterStatus.value)
})

function onFilterChange() {
  // 前端筛选，不需要重新请求
}

function disabledEffective(date: Date) {
  if (!form.value.expiry_date) return false
  return date > new Date(form.value.expiry_date)
}

function disabledExpiry(date: Date) {
  if (!form.value.effective_date) return false
  return date < new Date(form.value.effective_date)
}

function onMaterialChange(val: string) {
  const m = materials.value.find((x: any) => x.code === val)
  if (m) {
    form.value.material_code = m.code
    form.value.material_name = m.name
    form.value.material_id = m.id
  }
  if (val === substituteSelect.value) {
    substituteSelect.value = ''
    form.value.substitute_code = ''
    form.value.substitute_name = ''
    form.value.substitute_material_id = null
  }
}
function onSubstituteChange(val: string) {
  const m = materials.value.find((x: any) => x.code === val)
  if (m) {
    form.value.substitute_code = m.code
    form.value.substitute_name = m.name
    form.value.substitute_material_id = m.id
  }
}
function openCreate() {
  editingId.value = null
  form.value = { ...emptyForm }
  materialSelect.value = ''
  substituteSelect.value = ''
  dialogVisible.value = true
}
function openEdit(row: any) {
  editingId.value = row.id
  form.value = { ...row }
  materialSelect.value = row.material_code || ''
  substituteSelect.value = row.substitute_code || ''
  dialogVisible.value = true
}
async function save() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (form.value.material_code === form.value.substitute_code) {
      ElMessage.warning('主物料和替代物料不能相同')
      return
    }
    saving.value = true
    try {
      editingId.value ? await updateSubstituteMaterial(editingId.value, form.value) : await createSubstituteMaterial(form.value)
      ElMessage.success('替代料已保存')
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
  await ElMessageBox.confirm('确认删除此替代料关系？', '删除确认', { type: 'warning' })
  try {
    await deleteSubstituteMaterial(row.id)
    ElMessage.success('替代料已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
onMounted(async () => {
  materials.value = (await getMaterials({ page_size: 1000 })).items
  await loadData()
})
</script>
