<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>接口配置</strong>
        <span class="muted"> · ERP / MES / QMS 端点、方向、认证与对象范围</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增端点</el-button>
    </div>
    <el-table :data="endpoints" stripe height="680">
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
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createIntegrationEndpoint, getIntegrationEndpoints, updateIntegrationEndpoint } from '../api'
import UserSelect from '../components/UserSelect.vue'

const loading = ref(true)
const endpoints = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { code: '', name: '', system_type: 'ERP', base_url: '', auth_type: 'Token', direction: '双向', status: '启用', owner: '', object_scope: '' }
const form = ref<any>({ ...emptyForm })

async function loadRows() { endpoints.value = await getIntegrationEndpoints() }
function openCreate() { editingId.value = null; form.value = { ...emptyForm }; dialogVisible.value = true }
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateIntegrationEndpoint(editingId.value, form.value) : await createIntegrationEndpoint(form.value)
  ElMessage.success('接口端点已保存')
  dialogVisible.value = false
  await loadRows()
}
onMounted(async () => { await loadRows(); loading.value = false })
</script>
