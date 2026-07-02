<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>设备类型</strong><span class="muted"> · 设备族/型号分类，工艺设计资源</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterState" placeholder="状态" clearable style="width: 110px" @change="loadData">
          <el-option label="有效" value="Valid" />
          <el-option label="失效" value="Invalid" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索类型名称/描述" :prefix-icon="Search" clearable @keyup.enter="loadData" @clear="loadData" />
        <el-button v-if="can('process')" type="primary" :icon="Plus" @click="openCreate">新增类型</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="equipment_type_name" label="设备类型名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="process_type1" label="生产类型" width="100" />
        <el-table-column prop="process_type2" label="工序类型" width="100" />
        <el-table-column prop="construct_type1" label="构造1" width="90" />
        <el-table-column prop="construct_type2" label="构造2" width="100" />
        <el-table-column prop="process_capacity" label="加工容量" width="90" />
        <el-table-column prop="batch_capacity" label="批量容量" width="90" />
        <el-table-column prop="equipment_type_state" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.equipment_type_state === 'Valid' ? 'success' : 'info'" size="small">{{ row.equipment_type_state === 'Valid' ? '有效' : '失效' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑设备类型' : '新增设备类型'" width="720px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <div class="form-grid">
          <el-form-item label="类型名称" prop="equipment_type_name"><el-input v-model="form.equipment_type_name" :disabled="!!editingId" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.equipment_type_state">
              <el-option label="有效" value="Valid" />
              <el-option label="失效" value="Invalid" />
            </el-select>
          </el-form-item>
          <el-form-item label="生产类型">
            <el-select v-model="form.process_type1">
              <el-option label="生产" value="Production" />
              <el-option label="库存" value="Inventory" />
            </el-select>
          </el-form-item>
          <el-form-item label="工序类型">
            <el-select v-model="form.process_type2">
              <el-option label="工艺" value="Process" />
              <el-option label="量测" value="Metrology" />
              <el-option label="分选" value="Sort" />
              <el-option label="存储" value="Storage" />
              <el-option label="搬运" value="Transport" />
            </el-select>
          </el-form-item>
          <el-form-item label="构造类型1">
            <el-select v-model="form.construct_type1">
              <el-option label="主" value="Main" />
              <el-option label="子" value="Sub" />
              <el-option label="内部" value="Internal" />
            </el-select>
          </el-form-item>
          <el-form-item label="构造类型2">
            <el-select v-model="form.construct_type2">
              <el-option label="普通" value="Normal" />
              <el-option label="内部" value="Internal" />
              <el-option label="Cluster" value="Cluster" />
              <el-option label="Inline" value="Inline" />
            </el-select>
          </el-form-item>
          <el-form-item label="加工容量"><el-input-number v-model="form.process_capacity" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="批量容量"><el-input-number v-model="form.batch_capacity" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="Job数下限"><el-input-number v-model="form.process_job_count_min" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="Job数上限"><el-input-number v-model="form.process_job_count_max" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="Dummy卸载">
            <el-switch v-model="form.dummy_unmount_flag" />
          </el-form-item>
          <el-form-item label="描述" class="form-wide"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createEquipmentType, deleteEquipmentType, getEquipmentTypes, updateEquipmentType } from '../api'
import { useAuth } from '../auth'

const { can } = useAuth()
const items = ref<any[]>([])
const loading = ref(true)
const keyword = ref('')
const filterState = ref('')
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const emptyForm = {
  equipment_type_name: '', description: '', process_type1: 'Production', process_type2: 'Process',
  construct_type1: 'Main', construct_type2: 'Normal', process_capacity: null, process_job_count_min: null,
  process_job_count_max: null, batch_capacity: null, dummy_unmount_flag: false, equipment_type_state: 'Valid',
}
const form = ref<any>({ ...emptyForm })
const rules: FormRules = {
  equipment_type_name: [{ required: true, message: '请输入设备类型名称', trigger: 'blur' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await getEquipmentTypes({ keyword: keyword.value.trim(), state: filterState.value })
    items.value = res.items ?? []
  } finally {
    loading.value = false
  }
}
function openCreate() {
  editingId.value = null
  form.value = { ...emptyForm }
  dialogVisible.value = true
}
function openEdit(row: any) {
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}
async function save() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      editingId.value ? await updateEquipmentType(editingId.value, form.value) : await createEquipmentType(form.value)
      ElMessage.success('已保存')
      dialogVisible.value = false
      await loadData()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}
async function remove(row: any) {
  await ElMessageBox.confirm('确认删除此设备类型？', '删除确认', { type: 'warning' })
  try {
    await deleteEquipmentType(row.id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
onMounted(loadData)
</script>
