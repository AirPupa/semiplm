<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>替代料管理</strong><span class="muted"> · 替代策略、风险等级、有效期</span></div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索物料编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('material')" type="primary" :icon="Plus" @click="openCreate">新增替代料</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
      <el-table-column prop="material_code" label="主物料编码" width="140" />
      <el-table-column prop="material_name" label="主物料名称" min-width="160" />
      <el-table-column prop="substitute_code" label="替代物料编码" width="140" />
      <el-table-column prop="substitute_name" label="替代物料名称" min-width="160" />
      <el-table-column prop="substitute_type" label="替代类型" width="100" />
      <el-table-column prop="strategy" label="策略" width="100" />
      <el-table-column prop="risk_level" label="风险" width="80" />
      <el-table-column prop="status" label="状态" width="90" />
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
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="主物料编码"><el-input v-model="form.material_code" /></el-form-item>
          <el-form-item label="主物料名称"><el-input v-model="form.material_name" /></el-form-item>
          <el-form-item label="替代物料编码"><el-input v-model="form.substitute_code" /></el-form-item>
          <el-form-item label="替代物料名称"><el-input v-model="form.substitute_name" /></el-form-item>
          <el-form-item label="替代类型"><el-input v-model="form.substitute_type" /></el-form-item>
          <el-form-item label="策略"><el-input v-model="form.strategy" /></el-form-item>
          <el-form-item label="风险等级"><el-select v-model="form.risk_level"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="生效日期"><el-input v-model="form.effective_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="失效日期"><el-input v-model="form.expiry_date" placeholder="YYYY-MM-DD" /></el-form-item>
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
import { createSubstituteMaterial, deleteSubstituteMaterial, getSubstituteMaterials, updateSubstituteMaterial } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'

const { can } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getSubstituteMaterials)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { material_code: '', material_name: '', substitute_code: '', substitute_name: '', substitute_type: '功能替代', strategy: '一对一', risk_level: '中', status: '启用', effective_date: '', expiry_date: '', description: '' }
const form = ref<any>({ ...emptyForm })

function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateSubstituteMaterial(editingId.value, form.value) : await createSubstituteMaterial(form.value)
  ElMessage.success('替代料已保存')
  dialogVisible.value = false
  await loadData()
}
async function remove(row: any) {
  await ElMessageBox.confirm('确认删除此替代料关系？', '删除确认', { type: 'warning' })
  await deleteSubstituteMaterial(row.id)
  ElMessage.success('替代料已删除')
  await loadData()
}
onMounted(async () => { await loadData() })
</script>
