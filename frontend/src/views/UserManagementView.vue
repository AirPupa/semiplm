<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>用户管理</strong>
        <span class="muted"> · 维护组织用户、岗位角色和部门归属</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索账号/姓名" :prefix-icon="Search" clearable />
        <el-button v-if="can('admin')" type="primary" :icon="Plus" @click="openCreate">新增用户</el-button>
      </div>
    </div>
    <el-table :data="filteredUsers" stripe height="680">
      <el-table-column prop="username" label="账号" width="140" fixed />
      <el-table-column prop="display_name" label="姓名" width="120" />
      <el-table-column prop="role" label="角色" width="160" />
      <el-table-column prop="department" label="部门" min-width="150" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="!can('admin')" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :disabled="!can('admin')" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新增用户'" width="560px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="账号"><el-input v-model="form.username" /></el-form-item>
          <el-form-item label="姓名"><el-input v-model="form.display_name" /></el-form-item>
          <el-form-item label="角色">
            <el-select v-model="form.role">
              <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="部门">
            <el-select v-model="form.department">
              <el-option label="生产部" value="生产部" />
            </el-select>
          </el-form-item>
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
import { createAdminUser, deleteAdminUser, getAdminRoles, getAdminUsers, updateAdminUser } from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const { can } = useAuth()
const keyword = ref('')
const users = ref<any[]>([])
const roles = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { username: '', display_name: '', role: '', department: '生产部' }
const form = ref<any>({ ...emptyForm })

const filteredUsers = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) return users.value
  return users.value.filter((u) => `${u.username} ${u.display_name} ${u.role}`.toLowerCase().includes(text))
})

async function loadRows() {
  const [userRows, roleRows] = await Promise.all([getAdminUsers(), getAdminRoles()])
  users.value = userRows
  roles.value = roleRows
}
function openCreate() { editingId.value = null; form.value = { ...emptyForm, role: roles.value[0]?.name, department: '生产部' }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateAdminUser(editingId.value, form.value) : await createAdminUser(form.value)
  ElMessage.success('用户已保存')
  dialogVisible.value = false
  await loadRows()
}
async function remove(row: any) {
  await ElMessageBox.confirm(`确认删除用户 ${row.display_name}？`, '删除确认', { type: 'warning' })
  await deleteAdminUser(row.id)
  ElMessage.success('用户已删除')
  await loadRows()
}

onMounted(async () => {
  await loadRows()
  loading.value = false
})
</script>
