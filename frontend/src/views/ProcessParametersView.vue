<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>工艺参数库</strong>
        <span class="muted"> · CD、Overlay、刻蚀深度、膜厚、片阻、LIV/IV、Wafer Map 等工艺参数定义</span>
      </div>
      <el-button v-if="can('process')" type="primary" :icon="Plus" @click="openCreate">新建参数</el-button>
    </div>

    <el-table :data="filtered" stripe height="680">
      <el-table-column prop="param_code" label="参数编号" width="140" fixed />
      <el-table-column prop="param_name" label="参数名称" width="180" />
      <el-table-column prop="param_type" label="类型" width="130">
        <template #default="{ row }">
          <el-tag size="small">{{ row.param_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="unit" label="单位" width="90" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="default_value" label="默认值" width="120" />
      <el-table-column prop="min_value" label="最小值" width="120" />
      <el-table-column prop="max_value" label="最大值" width="120" />
      <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === '启用' ? 'success' : 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="!can('process')" @click.stop="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :disabled="!can('process')" @click.stop="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑参数' : '新建参数'" width="680px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="参数编号"><el-input v-model="form.param_code" placeholder="留空自动生成" /></el-form-item>
          <el-form-item label="参数名称" class="required"><el-input v-model="form.param_name" /></el-form-item>
          <el-form-item label="参数类型">
            <el-select v-model="form.param_type">
              <el-option label="CD" value="CD" />
              <el-option label="Overlay" value="Overlay" />
              <el-option label="刻蚀深度" value="刻蚀深度" />
              <el-option label="膜厚" value="膜厚" />
              <el-option label="片阻" value="片阻" />
              <el-option label="LIV/IV" value="LIV/IV" />
              <el-option label="Wafer Map" value="Wafer Map" />
              <el-option label="折射率" value="折射率" />
              <el-option label="应力" value="应力" />
              <el-option label="粗糙度" value="粗糙度" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="单位"><el-input v-model="form.unit" placeholder="nm / μm / Ω/sq" /></el-form-item>
          <el-form-item label="分类"><el-input v-model="form.category" placeholder="如 光刻/刻蚀/薄膜" /></el-form-item>
          <el-form-item label="默认值"><el-input v-model="form.default_value" /></el-form-item>
          <el-form-item label="最小值"><el-input v-model="form.min_value" /></el-form-item>
          <el-form-item label="最大值"><el-input v-model="form.max_value" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="启用" value="启用" />
              <el-option label="停用" value="停用" />
            </el-select>
          </el-form-item>
          <el-form-item label="说明" class="form-wide">
            <el-input v-model="form.description" type="textarea" :rows="3" />
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
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { createProcessParameter, deleteProcessParameter, getProcessParameters, updateProcessParameter } from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const { can } = useAuth()
const params = ref<any[]>([])
const search = ref('')
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = () => ({
  param_code: '',
  param_name: '',
  param_type: 'CD',
  unit: '',
  category: '',
  default_value: '',
  min_value: '',
  max_value: '',
  description: '',
  status: '启用',
})
const form = ref<any>(emptyForm())

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return params.value
  return params.value.filter((r: any) =>
    r.param_code?.toLowerCase().includes(q) ||
    r.param_name?.toLowerCase().includes(q) ||
    r.param_type?.toLowerCase().includes(q) ||
    r.category?.toLowerCase().includes(q)
  )
})

async function load() {
  params.value = await getProcessParameters()
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('process')) return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!can('process')) return
  if (!form.value.param_name) {
    ElMessage.warning('请输入参数名称')
    return
  }
  if (editingId.value) {
    await updateProcessParameter(editingId.value, form.value)
    ElMessage.success('参数已更新')
  } else {
    await createProcessParameter(form.value)
    ElMessage.success('参数已创建')
  }
  dialogVisible.value = false
  await load()
}

async function remove(row: any) {
  if (!can('process')) return
  await ElMessageBox.confirm(`确认删除参数 ${row.param_code}？`, '删除确认', { type: 'warning' })
  await deleteProcessParameter(row.id)
  ElMessage.success('参数已删除')
  await load()
}

onMounted(async () => {
  await load()
  loading.value = false
})
</script>
