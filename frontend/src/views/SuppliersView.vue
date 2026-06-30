<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>供应商/制造商</strong><span class="muted"> · 资质、风险、状态管理</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 100px" @change="onFilterChange">
          <el-option label="启用" value="启用" />
          <el-option label="停用" value="停用" />
        </el-select>
        <el-select v-model="filterRisk" placeholder="风险" clearable style="width: 100px" @change="onFilterChange">
          <el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('material')" type="primary" :icon="Plus" @click="openCreate">新增供应商</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="filteredItems" height="100%">
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="supplier_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTagColor(row.supplier_type)">{{ row.supplier_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="contact" label="联系人" width="100" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip />
        <el-table-column prop="certification" label="资质" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.certification" size="small" type="success">{{ row.certification }}</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
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
        <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑供应商' : '新增供应商'" width="640px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <div class="form-grid">
          <el-form-item label="编码" prop="code"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="类型" prop="supplier_type">
            <el-select v-model="form.supplier_type">
              <el-option v-for="o in supplierTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
          <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
          <el-form-item label="邮箱" prop="email"><el-input v-model="form.email" /></el-form-item>
          <el-form-item label="资质"><el-input v-model="form.certification" /></el-form-item>
          <el-form-item label="风险等级"><el-select v-model="form.risk_level"><el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option v-for="o in commonStatusOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="地址" class="form-wide"><el-input v-model="form.address" type="textarea" :rows="2" /></el-form-item>
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
import { createSupplier, deleteSupplier, getSuppliers, updateSupplier } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const riskLevelOptions = useDictionary('DICT_RISK_LEVEL').options
const supplierTypeOptions = useDictionary('DICT_SUPPLIER_TYPE').options
const commonStatusOptions = useDictionary('DICT_COMMON_STATUS').options

const { can } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getSuppliers)
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const filterStatus = ref('')
const filterRisk = ref('')
const emptyForm = { code: '', name: '', supplier_type: '材料', contact: '', phone: '', email: '', address: '', certification: '', risk_level: '中', status: '启用', description: '' }
const form = ref<any>({ ...emptyForm })

const rules: FormRules = {
  code: [{ required: true, message: '请输入供应商编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }],
}

const filteredItems = computed(() => {
  let result = items.value || []
  if (filterStatus.value) result = result.filter((r: any) => r.status === filterStatus.value)
  if (filterRisk.value) result = result.filter((r: any) => r.risk_level === filterRisk.value)
  return result
})

function onFilterChange() {
  // 前端筛选
}

function typeTagColor(type: string) {
  const map: Record<string, string> = { '材料': 'primary', '加工': 'warning', '物流': 'success', '设备': 'danger', '服务': 'info' }
  return map[type] || 'info'
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
      editingId.value ? await updateSupplier(editingId.value, form.value) : await createSupplier(form.value)
      ElMessage.success('供应商已保存')
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
  await ElMessageBox.confirm('确认删除此供应商？', '删除确认', { type: 'warning' })
  try {
    await deleteSupplier(row.id)
    ElMessage.success('供应商已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
onMounted(async () => { await loadData() })
</script>
