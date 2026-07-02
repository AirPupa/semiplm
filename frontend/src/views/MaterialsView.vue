<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>物料库</strong>
        <span class="muted"> · ConsumableDef 技术规格，现场库存与告警留 MES 主控</span>
      </div>
      <div class="toolbar-actions">
        <el-select v-model="filterType" placeholder="物料类型" clearable style="width: 140px">
          <el-option v-for="item in materialTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索名称/描述/规格" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('material')" type="primary" :icon="Plus" @click="openCreate">新增物料</el-button>
      </div>
    </div>

    <div class="list-table-wrap">
      <el-table :data="filteredItems" height="100%">
        <el-table-column prop="consumable_def_name" label="物料名称" width="170" fixed />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="consumable_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.consumable_type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fab_product_name" label="Fab 产品" width="130" />
        <el-table-column prop="primary_unit_name" label="主单位" width="100" />
        <el-table-column prop="unit" label="单位代码" width="90" />
        <el-table-column prop="unit_conversion_rate" label="换算率" width="90" />
        <el-table-column prop="material_standard_qty" label="标准量" width="90" />
        <el-table-column prop="spec" label="规格" min-width="220" show-overflow-tooltip />
        <el-table-column prop="supplier" label="供应商" width="140" />
        <el-table-column prop="lifecycle" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.lifecycle === '有效' ? 'success' : row.lifecycle === '冻结' ? 'warning' : 'info'" size="small">{{ row.lifecycle }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="!can('material')" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :disabled="!can('material')" @click="remove(row)">删除</el-button>
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
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑物料' : '新增物料'" width="760px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <div class="form-grid">
          <el-form-item label="物料名称" prop="consumable_def_name"><el-input v-model="form.consumable_def_name" /></el-form-item>
          <el-form-item label="Fab 产品"><el-input v-model="form.fab_product_name" /></el-form-item>
          <el-form-item label="物料类型" prop="consumable_type">
            <el-select v-model="form.consumable_type" filterable allow-create>
              <el-option v-for="item in materialTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="主单位名称"><el-input v-model="form.primary_unit_name" /></el-form-item>
          <el-form-item label="主单位代码"><el-input v-model="form.primary_unit_code" /></el-form-item>
          <el-form-item label="单位名称"><el-input v-model="form.unit_name" /></el-form-item>
          <el-form-item label="单位代码"><el-input v-model="form.unit" /></el-form-item>
          <el-form-item label="换算率"><el-input v-model="form.unit_conversion_rate" /></el-form-item>
          <el-form-item label="标准量"><el-input-number v-model="form.material_standard_qty" :min="0" /></el-form-item>
          <el-form-item label="供应商">
            <el-select v-model="supplierSelect" filterable clearable @change="onSupplierChange">
              <el-option v-for="s in suppliers" :key="s.code" :label="s.name" :value="s.code" />
            </el-select>
          </el-form-item>
          <el-form-item label="风险">
            <el-select v-model="form.risk_level">
              <el-option v-for="item in riskLevelOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.lifecycle">
              <el-option v-for="item in lifecycleOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="描述" class="form-wide"><el-input v-model="form.description" /></el-form-item>
          <el-form-item label="规格" class="form-wide"><el-input v-model="form.spec" type="textarea" :rows="3" /></el-form-item>
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
import { createMaterial, deleteMaterial, getMaterials, getSuppliers, updateMaterial } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const materialTypeOptions = useDictionary('MES_CONSUMABLE_TYPE').options
const riskLevelOptions = useDictionary('DICT_RISK_LEVEL').options
const lifecycleOptions = useDictionary('DICT_MATERIAL_LIFECYCLE').options

const { can, refreshSession } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getMaterials)
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const suppliers = ref<any[]>([])
const supplierSelect = ref('')
const filterType = ref('')

const emptyForm = {
  consumable_def_name: '',
  description: '',
  fab_product_name: '',
  consumable_type: '',
  primary_unit_name: '',
  primary_unit_code: '',
  unit_name: '',
  unit: '',
  unit_conversion_rate: '',
  material_standard_qty: null as number | null,
  spec: '',
  supplier: '',
  supplier_id: null as number | null,
  risk_level: '低',
  lifecycle: '有效'
}
const form = ref<any>({ ...emptyForm })

const rules: FormRules = {
  consumable_def_name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
  consumable_type: [{ required: true, message: '请选择物料类型', trigger: 'change' }],
}

const filteredItems = computed(() => {
  if (!filterType.value) return items.value || []
  return (items.value || []).filter((row: any) => row.consumable_type === filterType.value)
})

function onSupplierChange(val: string) {
  const supplier = suppliers.value.find((item: any) => item.code === val)
  form.value.supplier = supplier?.name || ''
  form.value.supplier_id = supplier?.id || null
}

function openCreate() {
  if (!can('material')) return
  editingId.value = null
  form.value = { ...emptyForm }
  supplierSelect.value = ''
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('material')) return
  editingId.value = row.id
  form.value = { ...row }
  const supplier = suppliers.value.find((item: any) => item.id === row.supplier_id || item.name === row.supplier)
  supplierSelect.value = supplier?.code || ''
  dialogVisible.value = true
}

async function save() {
  if (!can('material') || !formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editingId.value) {
        await updateMaterial(editingId.value, form.value)
      } else {
        await createMaterial(form.value)
      }
      ElMessage.success('物料已保存')
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
  if (!can('material')) return
  await ElMessageBox.confirm(`确认删除物料 ${row.consumable_def_name}？已被 BOM 使用的物料会被后端阻止删除。`, '删除确认', { type: 'warning' })
  try {
    await deleteMaterial(row.id)
    ElMessage.success('物料已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(async () => {
  await refreshSession()
  suppliers.value = (await getSuppliers()).items
  await loadData()
})
</script>
