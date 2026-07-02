<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>产品库</strong>
        <span class="muted"> · PLM 主控源头，对齐 MES ProductDef 26 字段</span>
      </div>
      <div class="toolbar-actions">
        <el-select v-model="filterState" placeholder="产品状态" clearable style="width: 130px" @change="onSearch">
          <el-option label="Active" value="Active" />
          <el-option label="Frozen" value="Frozen" />
          <el-option label="Invalid" value="Invalid" />
        </el-select>
        <el-select v-model="filterType" placeholder="产品类型" clearable style="width: 130px" @change="onSearch">
          <el-option label="SBD" value="SBD" />
          <el-option label="MOS" value="MOS" />
          <el-option label="NPW" value="NPW" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索产品名称/描述/类型/负责人" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" style="width: 260px" />
        <el-button v-if="can('product')" type="primary" :icon="Plus" @click="openCreate">新增产品</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%" @row-click="openDetail">
        <el-table-column prop="product_def_name" label="产品定义名" min-width="150" fixed />
        <el-table-column prop="product_def_version" label="版本" width="80" />
        <el-table-column prop="product_type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTag(row.product_type)">{{ row.product_type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="production_type" label="生产类型" width="100" />
        <el-table-column prop="product_group_name" label="产品组" width="110" />
        <el-table-column prop="process_flow_name" label="引用制造流程" min-width="150">
          <template #default="{ row }">
            <span v-if="row.process_flow_name">{{ row.process_flow_name }} v{{ row.process_flow_version || '001' }}</span>
            <span v-else class="muted">未绑定</span>
          </template>
        </el-table-column>
        <el-table-column prop="bom_name" label="引用 BOM" min-width="130">
          <template #default="{ row }">
            <span v-if="row.bom_name">{{ row.bom_name }} v{{ row.bom_version || '001' }}</span>
            <span v-else class="muted">未绑定</span>
          </template>
        </el-table-column>
        <el-table-column prop="reticle_set_name" label="光罩组" width="110" />
        <el-table-column prop="gross_die" label="Gross Die" width="100" />
        <el-table-column prop="product_def_state" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="stateTag(row.product_def_state)">{{ row.product_def_state }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="100" />
        <el-table-column prop="owner_group_name" label="归属组" width="110" />
        <el-table-column prop="bin_name" label="Bin" width="100" />
        <el-table-column prop="package_qty" label="包装数" width="90" />
        <el-table-column prop="product_usage" label="用途" width="110" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="!can('product')" @click.stop="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :disabled="!can('product')" @click.stop="remove(row)">删除</el-button>
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
        @size-change="onSizeChange"
        @current-change="loadData"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑产品' : '新增产品'" width="900px" top="5vh">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <div class="form-grid">
          <!-- 基础定义 -->
          <el-form-item label="产品定义名" prop="product_def_name"><el-input v-model="form.product_def_name" :disabled="!!editingId" /></el-form-item>
          <el-form-item label="版本" prop="product_def_version"><el-input v-model="form.product_def_version" :disabled="!!editingId" /></el-form-item>
          <el-form-item label="产品类型">
            <el-select v-model="form.product_type">
              <el-option label="SBD" value="SBD" />
              <el-option label="MOS" value="MOS" />
              <el-option label="NPW" value="NPW" />
            </el-select>
          </el-form-item>
          <el-form-item label="生产类型">
            <el-select v-model="form.production_type">
              <el-option label="Mass Production" value="Mass Production" />
              <el-option label="Engineering" value="Engineering" />
              <el-option label="Monitor" value="Monitor" />
            </el-select>
          </el-form-item>
          <el-form-item label="产品状态">
            <el-select v-model="form.product_def_state">
              <el-option label="Active" value="Active" />
              <el-option label="Frozen" value="Frozen" />
              <el-option label="Invalid" value="Invalid" />
            </el-select>
          </el-form-item>
          <el-form-item label="产品组"><el-input v-model="form.product_group_name" /></el-form-item>
          <el-form-item label="归属组"><el-input v-model="form.owner_group_name" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>

          <!-- 工艺/BOM 引用 -->
          <el-form-item label="制造流程名">
            <el-select v-model="form.process_flow_name" filterable clearable @change="onFlowChange">
              <el-option v-for="f in flowOptions" :key="f.process_flow_name + '|' + f.process_flow_version" :label="`${f.process_flow_name} v${f.process_flow_version}`" :value="f.process_flow_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="制造流程版本">
            <el-select v-model="form.process_flow_version" filterable clearable>
              <el-option v-for="v in flowVersionOptions" :key="v" :label="v" :value="v" />
            </el-select>
          </el-form-item>
          <el-form-item label="BOM 名称">
            <el-select v-model="form.bom_name" filterable clearable @change="onBomChange">
              <el-option v-for="b in bomOptions" :key="b.bom_name + '|' + b.bom_version" :label="`${b.bom_name} v${b.bom_version}`" :value="b.bom_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="BOM 版本">
            <el-select v-model="form.bom_version" filterable clearable>
              <el-option v-for="v in bomVersionOptions" :key="v" :label="v" :value="v" />
            </el-select>
          </el-form-item>

          <!-- 光罩/Bank/产量 -->
          <el-form-item label="光罩组"><el-input v-model="form.reticle_set_name" /></el-form-item>
          <el-form-item label="Gross Die"><el-input-number v-model="form.gross_die" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="起始 Bank"><el-input v-model="form.start_bank_name" /></el-form-item>
          <el-form-item label="结束 Bank"><el-input v-model="form.end_bank_name" /></el-form-item>
          <el-form-item label="Bin 名称"><el-input v-model="form.bin_name" /></el-form-item>
          <el-form-item label="包装数量"><el-input-number v-model="form.package_qty" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="产品用途"><el-input v-model="form.product_usage" /></el-form-item>
          <el-form-item label="最大使用次数"><el-input-number v-model="form.max_use_count" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="最大回收次数"><el-input-number v-model="form.max_recycle_count" :min="0" controls-position="right" /></el-form-item>

          <!-- Dummy 参数 -->
          <el-form-item label="Dummy最大时长"><el-input-number v-model="form.dummy_max_use_time" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="Dummy厚度参数"><el-input v-model="form.dummy_thk_param" /></el-form-item>
          <el-form-item label="Dummy厚度限值"><el-input-number v-model="form.dummy_thk_limit" :precision="3" controls-position="right" /></el-form-item>
          <el-form-item label="是否删除"><el-switch v-model="form.is_deleted" /></el-form-item>

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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createProduct, deleteProduct, getProducts, updateProduct } from '../api'
import { getProcessFlows, getBoms } from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import { useListPage } from '../composables/useListPage'

const router = useRouter()
const { can, currentUser } = useAuth()
const filterState = ref('')
const filterType = ref('')
const { pagination, keyword, items, loading, loadData, onSearch, onSizeChange } = useListPage(
  (params) => getProducts({ ...params, state: filterState.value, product_type: filterType.value }),
)

// 引用对象下拉
const flowOptions = ref<any[]>([])
const bomOptions = ref<any[]>([])

const flowVersionOptions = computed(() => {
  if (!form.value.process_flow_name) return []
  return flowOptions.value
    .filter((f) => f.process_flow_name === form.value.process_flow_name)
    .map((f) => f.process_flow_version)
})
const bomVersionOptions = computed(() => {
  if (!form.value.bom_name) return []
  return bomOptions.value
    .filter((b) => b.bom_name === form.value.bom_name)
    .map((b) => b.bom_version)
})

// 表单
const formRef = ref<FormInstance>()
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const emptyForm = {
  product_def_name: '',
  product_def_version: '001',
  description: '',
  product_def_state: 'Active',
  product_type: 'SBD',
  production_type: 'Mass Production',
  product_group_name: '',
  process_flow_name: '',
  process_flow_version: '',
  bom_name: '',
  bom_version: '',
  reticle_set_name: '',
  gross_die: null as number | null,
  start_bank_name: '',
  end_bank_name: '',
  owner: '',
  max_use_count: null as number | null,
  max_recycle_count: null as number | null,
  owner_group_name: '',
  dummy_max_use_time: null as number | null,
  dummy_thk_param: '',
  dummy_thk_limit: null as number | null,
  is_deleted: false,
  bin_name: '',
  package_qty: null as number | null,
  product_usage: '',
}
const form = ref<any>({ ...emptyForm })
const rules: FormRules = {
  product_def_name: [{ required: true, message: '请输入产品定义名', trigger: 'blur' }],
  product_def_version: [{ required: true, message: '请输入版本', trigger: 'blur' }],
}

function typeTag(t: string) {
  const map: Record<string, string> = { SBD: 'success', MOS: 'primary', NPW: 'warning' }
  return map[t] || 'info'
}
function stateTag(s: string) {
  const map: Record<string, string> = { Active: 'success', Frozen: 'warning', Invalid: 'info' }
  return map[s] || 'info'
}

function onFlowChange(name: string) {
  const versions = flowOptions.value.filter((f) => f.process_flow_name === name).map((f) => f.process_flow_version)
  form.value.process_flow_version = versions.length === 1 ? versions[0] : ''
}
function onBomChange(name: string) {
  const versions = bomOptions.value.filter((b) => b.bom_name === name).map((b) => b.bom_version)
  form.value.bom_version = versions.length === 1 ? versions[0] : ''
}

function openDetail(row: any) {
  router.push(`/products/${row.id}`)
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
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (editingId.value) {
        await updateProduct(editingId.value, form.value)
      } else {
        await createProduct(form.value)
      }
      ElMessage.success('产品已保存')
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
  if (!can('product')) return
  await ElMessageBox.confirm(`确认删除产品 ${row.product_def_name}？已有业务关联的产品会被后端阻止删除。`, '删除确认', { type: 'warning' })
  try {
    await deleteProduct(row.id)
    ElMessage.success('产品已删除')
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

async function loadReferenceOptions() {
  const [flowRes, bomRes] = await Promise.all([
    getProcessFlows({ page: 1, page_size: 500 }),
    getBoms({ page: 1, page_size: 500 }),
  ])
  flowOptions.value = flowRes.items ?? []
  bomOptions.value = bomRes.items ?? []
}

onMounted(async () => {
  await Promise.all([loadData(), loadReferenceOptions()])
})
</script>

<style scoped>
.list-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 82px);
}

.list-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0;
}
</style>
