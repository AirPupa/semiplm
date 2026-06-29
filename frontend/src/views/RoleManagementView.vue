<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>角色管理</strong>
        <span class="muted"> · 定义岗位职责、对象权限和流程参与角色</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索角色编码/名称" :prefix-icon="Search" clearable />
        <el-button v-if="can('admin')" type="primary" :icon="Plus" @click="openCreate">新增角色</el-button>
      </div>
    </div>
    <el-table :data="filteredRoles" stripe height="680">
      <el-table-column prop="code" label="角色编码" width="150" fixed />
      <el-table-column prop="name" label="角色名称" width="150" />
      <el-table-column prop="description" label="职责说明" min-width="260" />
      <el-table-column prop="permissions" label="权限范围" min-width="260" />
      <el-table-column prop="status" label="状态" width="90" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="!can('admin')" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :disabled="!can('admin')" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑角色' : '新增角色'" width="680px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="启用" value="启用" />
              <el-option label="停用" value="停用" />
            </el-select>
          </el-form-item>
          <el-form-item label="权限" class="form-wide"><el-input v-model="form.permissions" /></el-form-item>
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
import { createAdminRole, deleteAdminRole, getAdminRoles, updateAdminRole } from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const { can } = useAuth()
const keyword = ref('')
const roles = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { code: '', name: '', description: '', permissions: '', status: '启用' }
const form = ref<any>({ ...emptyForm })

const filteredRoles = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return roles.value
  return roles.value.filter((r) => `${r.code} ${r.name}`.toLowerCase().includes(text))
})

async function loadRows() { roles.value = await getAdminRoles() }
function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateAdminRole(editingId.value, form.value) : await createAdminRole(form.value)
  ElMessage.success('角色已保存')
  dialogVisible.value = false
  await loadRows()
}
async function remove(row: any) {
  await ElMessageBox.confirm(`确认删除角色 ${row.name}？被用户使用的角色会被后端阻止删除。`, '删除确认', { type: 'warning' })
  await deleteAdminRole(row.id)
  ElMessage.success('角色已删除')
  await loadRows()
}

onMounted(async () => {
  await loadRows()
  loading.value = false
})
</script>
