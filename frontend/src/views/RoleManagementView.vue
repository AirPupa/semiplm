<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>角色管理</strong>
        <span class="muted"> · 定义岗位职责、对象权限和流程参与角色</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索角色编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('admin')" type="primary" :icon="Plus" @click="openCreate">新增角色</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="code" label="角色编码" width="150" fixed />
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="description" label="职责说明" min-width="260" />
        <el-table-column label="权限范围" min-width="260">
          <template #default="{ row }">
            <div class="perm-tags">
              <el-tag v-for="perm in (row.permissions || '').split(',').map((s: string) => s.trim()).filter(Boolean)" :key="perm" size="small" effect="plain">{{ permLabel(perm) }}</el-tag>
              <span v-if="!(row.permissions || '').trim()" class="muted">无</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="!can('admin')" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :disabled="!can('admin')" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>
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
          <el-form-item label="权限" class="form-wide">
            <el-checkbox-group v-model="permissionArray">
              <el-checkbox v-for="key in permissionKeys" :key="key.key" :label="key.key">{{ key.label }}</el-checkbox>
            </el-checkbox-group>
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
import { computed, onMounted, ref, watch } from 'vue'
import { createAdminRole, deleteAdminRole, getAdminRoles, updateAdminRole } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'

const { can } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getAdminRoles)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { code: '', name: '', description: '', permissions: '', status: '启用' }
const form = ref<any>({ ...emptyForm })

const permissionKeys = [
  { key: 'all', label: '全部权限' },
  { key: 'system', label: '系统设置' },
  { key: 'organization', label: '组织管理' },
  { key: 'user', label: '用户管理' },
  { key: 'role', label: '角色权限' },
  { key: 'workflow', label: '流程配置' },
  { key: 'integration', label: '集成配置' },
  { key: 'product', label: '产品主数据' },
  { key: 'requirement', label: '需求规格' },
  { key: 'material', label: '研发物料' },
  { key: 'bom', label: '设计 BOM' },
  { key: 'document', label: '文档管理' },
  { key: 'process', label: '工艺路线' },
  { key: 'change', label: '工程变更' },
  { key: 'project', label: '项目管理' },
  { key: 'quality', label: '质量闭环' },
  { key: 'approval', label: '审批处理' },
  { key: 'erp', label: 'ERP 接口' },
  { key: 'mes', label: 'MES 接口' },
]

const permissionArray = computed<string[]>({
  get() {
    const raw = form.value.permissions || ''
    return raw.split(',').map((s: string) => s.trim()).filter(Boolean)
  },
  set(val: string[]) {
    form.value.permissions = val.join(',')
  },
})

function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateAdminRole(editingId.value, form.value) : await createAdminRole(form.value)
  ElMessage.success('角色已保存')
  dialogVisible.value = false
  await loadData()
}
async function remove(row: any) {
  await ElMessageBox.confirm(`确认删除角色 ${row.name}？被用户使用的角色会被后端阻止删除。`, '删除确认', { type: 'warning' })
  await deleteAdminRole(row.id)
  ElMessage.success('角色已删除')
  await loadData()
}

function permLabel(key: string): string {
  const found = permissionKeys.find((p) => p.key === key)
  return found ? found.label : key
}

onMounted(async () => {
  await loadData()
})
</script>

<style scoped>
.perm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
