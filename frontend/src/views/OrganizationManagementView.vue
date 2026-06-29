<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>组织管理</strong>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索组织编码/名称" :prefix-icon="Search" clearable />
        <el-button v-if="can('admin')" type="primary" :icon="Plus" @click="openCreate">新增组织</el-button>
      </div>
    </div>
    <el-table :data="filteredRows" stripe height="620">
      <el-table-column prop="code" label="编码" width="120" fixed />
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="org_type" label="类型" width="100" />
      <el-table-column prop="parent_code" label="上级编码" width="120" />
      <el-table-column prop="manager" label="负责人" width="120" />
      <el-table-column prop="status" label="状态" width="90" />
      <el-table-column prop="description" label="说明" min-width="220" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="!can('admin')" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :disabled="!can('admin') || ['NZGD', 'PROD'].includes(row.code)" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑组织' : '新增组织'" width="640px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="类型">
            <el-select v-model="form.org_type">
              <el-option label="公司" value="公司" />
              <el-option label="部门" value="部门" />
            </el-select>
          </el-form-item>
          <el-form-item label="上级编码"><el-input v-model="form.parent_code" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.manager" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="启用" value="启用" />
              <el-option label="停用" value="停用" />
            </el-select>
          </el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
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
import { computed, onMounted, ref } from 'vue'
import { createOrganization, deleteOrganization, getOrganizations, updateOrganization } from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'

const loading = ref(true)
const { can } = useAuth()
const keyword = ref('')
const rows = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { code: '', name: '', org_type: '部门', parent_code: 'NZGD', manager: '', status: '启用', description: '' }
const form = ref<any>({ ...emptyForm })

const filteredRows = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return rows.value
  return rows.value.filter((r) => `${r.code} ${r.name}`.toLowerCase().includes(text))
})

async function loadRows() { rows.value = await getOrganizations() }
function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateOrganization(editingId.value, form.value) : await createOrganization(form.value)
  ElMessage.success('组织已保存')
  dialogVisible.value = false
  await loadRows()
}
async function remove(row: any) {
  await ElMessageBox.confirm(`确认删除组织 ${row.name}？`, '删除确认', { type: 'warning' })
  await deleteOrganization(row.id)
  ElMessage.success('组织已删除')
  await loadRows()
}

onMounted(async () => {
  await loadRows()
  loading.value = false
})
</script>
