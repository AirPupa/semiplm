<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>物料主数据</strong>
        <span class="muted"> · 衬底、外延、Mask、工艺材料与测试治具统一编码</span>
      </div>
      <div class="toolbar-actions">
        <el-select v-model="filterCategory" placeholder="类别" clearable style="width: 120px" @change="onFilterChange">
          <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索物料编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('material')" type="primary" :icon="Plus" @click="openCreate">新增物料</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="filteredItems" height="100%">
        <el-table-column prop="code" label="物料编码" width="150" fixed />
        <el-table-column prop="name" label="物料名称" min-width="180" />
        <el-table-column prop="category" label="类别" width="130">
          <template #default="{ row }">
            <el-tag size="small" :type="categoryColor(row.category)">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="specification" label="规格/参数" min-width="220" show-overflow-tooltip />
        <el-table-column prop="supplier" label="供应商" width="140" />
        <el-table-column prop="risk_level" label="风险" width="90">
          <template #default="{ row }">
            <el-tag :type="row.risk_level === '高' ? 'danger' : row.risk_level === '中' ? 'warning' : 'success'" size="small">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lifecycle" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.lifecycle === '有效' ? 'success' : row.lifecycle === '冻结' ? 'warning' : row.lifecycle === '停用' ? 'info' : 'primary'" size="small">{{ row.lifecycle }}</el-tag>
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
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑物料' : '新增物料'" width="640px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <div class="form-grid">
          <el-form-item label="物料编码" prop="code"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="物料名称" prop="name"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="类别" prop="category">
            <el-select v-model="form.category" filterable allow-create>
              <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
          <el-form-item label="供应商">
            <el-select v-model="supplierSelect" filterable clearable placeholder="请选择供应商" @change="onSupplierChange">
              <el-option v-for="s in suppliers" :key="s.code" :label="s.name" :value="s.code" />
            </el-select>
          </el-form-item>
          <el-form-item label="风险">
            <el-select v-model="form.risk_level">
              <el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.lifecycle">
              <el-option v-for="o in materialLifecycleOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="规格参数" class="form-wide"><el-input v-model="form.specification" type="textarea" :rows="3" /></el-form-item>
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

const categories = useDictionary('DICT_MATERIAL_CATEGORY').labels
const riskLevelOptions = useDictionary('DICT_RISK_LEVEL').options
const materialLifecycleOptions = useDictionary('DICT_MATERIAL_LIFECYCLE').options

const { can, refreshSession } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getMaterials)
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const suppliers = ref<any[]>([])
const supplierSelect = ref('')
const filterCategory = ref('')
const emptyForm = { code: '', name: '', category: '', specification: '', supplier: '', supplier_id: null as number | null, risk_level: '低', lifecycle: '有效' }
const form = ref<any>({ ...emptyForm })

const rules: FormRules = {
  code: [{ required: true, message: '请输入物料编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择类别', trigger: 'change' }],
}

const filteredItems = computed(() => {
  if (!filterCategory.value) return items.value || []
  return (items.value || []).filter((r: any) => r.category === filterCategory.value)
})

function onFilterChange() {
  // 前端筛选
}

function categoryColor(cat: string) {
  const map: Record<string, string> = { '衬底': 'primary', '外延': 'success', 'Mask': 'warning', '工艺材料': 'danger', '测试治具': 'info', '辅料': '', '包材': '' }
  return map[cat] || ''
}

function onSupplierChange(val: string) {
  const s = suppliers.value.find((x: any) => x.code === val)
  if (s) {
    form.value.supplier = s.name
    form.value.supplier_id = s.id
  } else {
    form.value.supplier = ''
    form.value.supplier_id = null
  }
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
  if (row.supplier_id) {
    const s = suppliers.value.find((x: any) => x.id === row.supplier_id)
    supplierSelect.value = s ? s.code : ''
  } else if (row.supplier) {
    const s = suppliers.value.find((x: any) => x.name === row.supplier)
    supplierSelect.value = s ? s.code : ''
  } else {
    supplierSelect.value = ''
  }
  dialogVisible.value = true
}

async function save() {
  if (!can('material')) return
  if (!formRef.value) return
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
  await ElMessageBox.confirm(`确认删除物料 ${row.code}？已被 BOM 使用的物料会被后端阻止删除。`, '删除确认', { type: 'warning' })
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
