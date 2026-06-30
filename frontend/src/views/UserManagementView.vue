<template>
  <div class="panel um-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>用户管理</strong>
        <span class="muted"> · 维护组织用户、岗位角色和部门归属</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索账号/姓名" :prefix-icon="Search" clearable @keyup.enter="handleSearch" @clear="handleSearch" style="width: 200px" />
        <el-button v-if="can('admin')" type="primary" :icon="Plus" @click="openCreate">新增用户</el-button>
      </div>
    </div>
    <div class="um-table-wrap">
      <el-table :data="users" height="100%">
        <el-table-column label="头像" width="70" fixed>
          <template #default="{ row }">
            <span class="user-avatar">
              <img v-if="row.avatar_url" :src="row.avatar_url" alt="" />
              <span v-else>{{ (row.display_name || row.username || 'U').slice(0, 1) }}</span>
            </span>
          </template>
        </el-table-column>
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
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="handleSizeChange"
        @current-change="loadRows"
      />
    </div>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新增用户'" width="560px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="账号"><el-input v-model="form.username" /></el-form-item>
          <el-form-item label="姓名"><el-input v-model="form.display_name" /></el-form-item>
          <el-form-item label="头像URL"><el-input v-model="form.avatar_url" /></el-form-item>
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
import { onMounted, reactive, ref } from 'vue'
import { createAdminUser, deleteAdminUser, getAdminRoles, getAdminUsers, updateAdminUser } from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const { can } = useAuth()
const keyword = ref('')
const users = ref<any[]>([])
const roles = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { username: '', display_name: '', role: '', department: '生产部', avatar_url: '' }
const form = ref<any>({ ...emptyForm })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

async function loadRows() {
  loading.value = true
  try {
    const [res, roleRows] = await Promise.all([
      getAdminUsers({ page: pagination.page, page_size: pagination.pageSize, keyword: keyword.value.trim() }),
      getAdminRoles(),
    ])
    users.value = res.items
    pagination.total = res.total
    roles.value = roleRows
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  loadRows()
}

function handleSizeChange() {
  pagination.page = 1
  loadRows()
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
})
</script>

<style scoped>
.um-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 82px);
}

.um-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0;
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  overflow: hidden;
  background: #e8f4f8;
  color: #1f6f8b;
  font-weight: 600;
}
.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
