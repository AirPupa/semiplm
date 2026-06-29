<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>供应商/制造商</strong><span class="muted"> · 资质、风险、状态管理</span></div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('material')" type="primary" :icon="Plus" @click="openCreate">新增供应商</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="supplier_type" label="类型" width="100" />
      <el-table-column prop="contact" label="联系人" width="100" />
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column prop="email" label="邮箱" min-width="150" />
      <el-table-column prop="certification" label="资质" width="100" />
      <el-table-column prop="risk_level" label="风险" width="80" />
      <el-table-column prop="status" label="状态" width="90" />
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
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="类型"><el-input v-model="form.supplier_type" /></el-form-item>
          <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
          <el-form-item label="电话"><el-input v-model="form.phone" /></el-form-item>
          <el-form-item label="邮箱"><el-input v-model="form.email" /></el-form-item>
          <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
          <el-form-item label="资质"><el-input v-model="form.certification" /></el-form-item>
          <el-form-item label="风险等级"><el-select v-model="form.risk_level"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createSupplier, deleteSupplier, getSuppliers, updateSupplier } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'

const { can } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getSuppliers)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { code: '', name: '', supplier_type: '材料', contact: '', phone: '', email: '', address: '', certification: '', risk_level: '中', status: '启用', description: '' }
const form = ref<any>({ ...emptyForm })

function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateSupplier(editingId.value, form.value) : await createSupplier(form.value)
  ElMessage.success('供应商已保存')
  dialogVisible.value = false
  await loadData()
}
async function remove(row: any) {
  await ElMessageBox.confirm('确认删除此供应商？', '删除确认', { type: 'warning' })
  await deleteSupplier(row.id)
  ElMessage.success('供应商已删除')
  await loadData()
}
onMounted(async () => { await loadData() })
</script>
