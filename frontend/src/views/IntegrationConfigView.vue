<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>接口配置</strong>
        <span class="muted"> · ERP / MES / QMS 端点、方向、认证与对象范围</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button type="primary" :icon="Plus" @click="openCreate">新增端点</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="code" label="编码" width="130" fixed />
        <el-table-column prop="name" label="名称" width="190" />
        <el-table-column prop="system_type" label="系统" width="90" />
        <el-table-column prop="base_url" label="接口地址" min-width="240" />
        <el-table-column prop="auth_type" label="认证" width="90" />
        <el-table-column prop="direction" label="方向" width="90" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="object_scope" label="对象范围" min-width="240" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }"><el-button size="small" @click="openEdit(row)">编辑</el-button></template>
        </el-table-column>
      </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑接口端点' : '新增接口端点'" width="720px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="系统"><el-select v-model="form.system_type"><el-option label="ERP" value="ERP" /><el-option label="MES" value="MES" /><el-option label="QMS" value="QMS" /></el-select></el-form-item>
          <el-form-item label="方向"><el-select v-model="form.direction"><el-option label="下发" value="下发" /><el-option label="接收" value="接收" /><el-option label="双向" value="双向" /></el-select></el-form-item>
          <el-form-item label="认证"><el-input v-model="form.auth_type" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="接口地址" class="form-wide"><el-input v-model="form.base_url" /></el-form-item>
          <el-form-item label="对象范围" class="form-wide"><el-input v-model="form.object_scope" type="textarea" :rows="3" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createIntegrationEndpoint, getIntegrationEndpoints, updateIntegrationEndpoint } from '../api'
import UserSelect from '../components/UserSelect.vue'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getIntegrationEndpoints)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { code: '', name: '', system_type: 'ERP', base_url: '', auth_type: 'Token', direction: '双向', status: '启用', owner: '', object_scope: '' }
const form = ref<any>({ ...emptyForm })

function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateIntegrationEndpoint(editingId.value, form.value) : await createIntegrationEndpoint(form.value)
  ElMessage.success('接口端点已保存')
  dialogVisible.value = false
  await loadData()
}
onMounted(async () => {
  await loadData()
})
</script>
