<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>芯片型号台账</strong>
        <span class="muted"> · 产品生命周期、工艺平台、封装与客户料号统一管理</span>
      </div>
      <el-button v-if="can('product')" type="primary" :icon="Plus" @click="openCreate">新建型号</el-button>
    </div>
    <el-table :data="products" stripe height="680" @row-click="openDetail">
      <el-table-column prop="model" label="产品型号" width="130" fixed />
      <el-table-column prop="name" label="产品名称" min-width="190" />
      <el-table-column prop="product_type" label="类型" width="90" />
      <el-table-column prop="process_platform" label="工艺平台" width="120" />
      <el-table-column prop="package_type" label="封装" width="100" />
      <el-table-column prop="lifecycle" label="生命周期" width="100">
        <template #default="{ row }"><el-tag size="small">{{ row.lifecycle }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="owner" label="负责人" width="90" />
      <el-table-column prop="readiness" label="资料完整度" width="140">
        <template #default="{ row }"><el-progress :percentage="row.readiness" :stroke-width="8" /></template>
      </el-table-column>
      <el-table-column prop="customer_part_no" label="客户料号" width="150" />
      <el-table-column prop="latest_release" label="最近发布" width="120" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="!can('product')" @click.stop="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :disabled="!can('product')" @click.stop="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑型号' : '新建型号'" width="720px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="产品编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="产品型号"><el-input v-model="form.model" /></el-form-item>
          <el-form-item label="产品名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="产品类型"><el-input v-model="form.product_type" /></el-form-item>
          <el-form-item label="工艺平台"><el-input v-model="form.process_platform" /></el-form-item>
          <el-form-item label="晶圆尺寸"><el-input v-model="form.wafer_size" /></el-form-item>
          <el-form-item label="封装形式"><el-input v-model="form.package_type" /></el-form-item>
          <el-form-item label="生命周期">
            <el-select v-model="form.lifecycle">
              <el-option v-for="item in lifecycles" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="版本"><el-input v-model="form.version" /></el-form-item>
          <el-form-item label="内部料号"><el-input v-model="form.internal_part_no" /></el-form-item>
          <el-form-item label="客户料号"><el-input v-model="form.customer_part_no" /></el-form-item>
          <el-form-item label="质量等级"><el-input v-model="form.quality_grade" /></el-form-item>
          <el-form-item label="应用领域"><el-input v-model="form.application" /></el-form-item>
          <el-form-item label="完整度"><el-input-number v-model="form.readiness" :min="0" :max="100" /></el-form-item>
          <el-form-item label="最近发布"><el-input v-model="form.latest_release" placeholder="YYYY-MM-DD" /></el-form-item>
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
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createProduct, deleteProduct, getProducts, updateProduct } from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'

const router = useRouter()
const { can, currentUser, refreshSession } = useAuth()
const loading = ref(true)
const products = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const lifecycles = ['设计中', '流片', '验证', '试产', '量产', '冻结', '废止']
const emptyForm = {
  code: '',
  model: '',
  name: '',
  product_type: '光电芯片',
  process_platform: '',
  wafer_size: '',
  package_type: '',
  temperature_grade: '',
  quality_grade: '',
  application: '',
  lifecycle: '设计中',
  owner: '',
  customer_part_no: '',
  internal_part_no: '',
  version: 'A0',
  readiness: 0,
  latest_release: ''
}
const form = ref<any>({ ...emptyForm })

function openDetail(row: any) {
  router.push(`/products/${row.id}`)
}

async function loadProducts() {
  products.value = await getProducts()
}

function openCreate() {
  if (!can('product')) return
  editingId.value = null
  form.value = { ...emptyForm, owner: currentUser.value?.display_name || '' }
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('product')) return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!can('product')) return
  if (editingId.value) {
    await updateProduct(editingId.value, form.value)
  } else {
    await createProduct(form.value)
  }
  ElMessage.success('产品型号已保存')
  dialogVisible.value = false
  await loadProducts()
}

async function remove(row: any) {
  if (!can('product')) return
  await ElMessageBox.confirm(`确认删除产品 ${row.model}？已有业务关联的产品会被后端阻止删除。`, '删除确认', { type: 'warning' })
  await deleteProduct(row.id)
  ElMessage.success('产品型号已删除')
  await loadProducts()
}

onMounted(async () => {
  await refreshSession()
  await loadProducts()
  loading.value = false
})
</script>
