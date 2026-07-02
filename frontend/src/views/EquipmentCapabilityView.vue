<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>设备能力</strong><span class="muted"> · 按设备类型建立能力映射（PLM 改造：设备类型+能力）</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterEqType" placeholder="设备类型" clearable filterable style="width: 180px" @change="loadData">
          <el-option v-for="e in eqTypeOptions" :key="e.equipment_type_name" :label="e.equipment_type_name" :value="e.equipment_type_name" />
        </el-select>
        <el-select v-model="filterCap" placeholder="制程能力" clearable filterable style="width: 180px" @change="loadData">
          <el-option v-for="c in capOptions" :key="c.process_capability_name" :label="c.process_capability_name" :value="c.process_capability_name" />
        </el-select>
        <el-button v-if="can('process')" type="primary" :icon="Plus" @click="openCreate">新增能力映射</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="equipment_type_name" label="设备类型" min-width="160" />
        <el-table-column prop="process_capability_name" label="制程能力" min-width="160" />
        <el-table-column prop="assign_flag" label="分配标志" width="100">
          <template #default="{ row }">
            <el-tag :type="row.assign_flag ? 'success' : 'info'" size="small">{{ row.assign_flag ? '已分配' : '未分配' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="equipment_capability_state" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.equipment_capability_state === 'Valid' ? 'success' : 'info'" size="small">{{ row.equipment_capability_state === 'Valid' ? '有效' : '失效' }}</el-tag>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑设备能力' : '新增设备能力'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <div class="form-grid">
          <el-form-item label="设备类型" prop="equipment_type_name">
            <el-select v-model="form.equipment_type_name" filterable :disabled="!!editingId">
              <el-option v-for="e in eqTypeOptions" :key="e.equipment_type_name" :label="e.equipment_type_name" :value="e.equipment_type_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="制程能力" prop="process_capability_name">
            <el-select v-model="form.process_capability_name" filterable :disabled="!!editingId">
              <el-option v-for="c in capOptions" :key="c.process_capability_name" :label="c.process_capability_name" :value="c.process_capability_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="分配标志"><el-switch v-model="form.assign_flag" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.equipment_capability_state">
              <el-option label="有效" value="Valid" />
              <el-option label="失效" value="Invalid" />
            </el-select>
          </el-form-item>
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
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  createEquipmentCapability,
  deleteEquipmentCapability,
  getEquipmentCapabilities,
  getEquipmentTypes,
  getProcessCapabilities,
  updateEquipmentCapability,
} from '../api'
import { useAuth } from '../auth'

const { can } = useAuth()
const items = ref<any[]>([])
const loading = ref(true)
const filterEqType = ref('')
const filterCap = ref('')
const eqTypeOptions = ref<any[]>([])
const capOptions = ref<any[]>([])
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const emptyForm = { equipment_type_name: '', process_capability_name: '', assign_flag: true, equipment_capability_state: 'Valid' }
const form = ref<any>({ ...emptyForm })
const rules: FormRules = {
  equipment_type_name: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  process_capability_name: [{ required: true, message: '请选择制程能力', trigger: 'change' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await getEquipmentCapabilities({ eqtype: filterEqType.value, capability: filterCap.value })
    items.value = res.items ?? []
  } finally {
    loading.value = false
  }
}
async function loadOptions() {
  const [eqRes, capRes] = await Promise.all([getEquipmentTypes(), getProcessCapabilities()])
  eqTypeOptions.value = eqRes.items ?? []
  capOptions.value = capRes.items ?? []
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
      editingId.value ? await updateEquipmentCapability(editingId.value, form.value) : await createEquipmentCapability(form.value)
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
  await ElMessageBox.confirm('确认删除此设备能力映射？', '删除确认', { type: 'warning' })
  try {
    await deleteEquipmentCapability(row.id)
    ElMessage.success('已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}
onMounted(async () => {
  await Promise.all([loadData(), loadOptions()])
})
</script>
