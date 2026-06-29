<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>工艺路线</strong>
          <span class="muted"> · 路线发布后下发 MES 工艺流程和站点控制</span>
        </div>
        <div class="toolbar-actions">
          <el-button :disabled="!can('process')" @click="openRouteCreate">新增路线</el-button>
          <el-button :disabled="!can('process') || !selected || selected.status === '已发布'" @click="submit(selected)">提交</el-button>
          <el-button type="primary" :disabled="!can(['approval', 'process']) || !selected || selected.status === '已发布'" @click="approve(selected)">发布</el-button>
        </div>
      </div>
      <el-table :data="routes" highlight-current-row @current-change="selected = $event" height="680">
        <el-table-column prop="route_no" label="路线编号" width="180" />
        <el-table-column prop="product_model" label="型号" width="130" />
        <el-table-column prop="name" label="路线名称" min-width="210" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="source_route_id" label="来源" width="90">
          <template #default="{ row }">
            <span>{{ row.source_route_id ? `#${row.source_route_id}` : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === '已发布' ? 'success' : row.status === '审批中' ? 'warning' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="release_date" label="发布日期" width="110" />
        <el-table-column label="操作" width="150" fixed="right" class-name="table-actions-cell">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" :disabled="!can('process') || row.status === '已发布'" @click.stop="openRouteEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" :disabled="!can('process') || row.status === '已发布'" @click.stop="removeRoute(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>{{ selected?.name || '工序步骤' }}</strong>
          <span v-if="selected" class="muted"> · {{ selected.product_model }} {{ selected.version }} · {{ selected.status }}</span>
        </div>
        <div class="toolbar-actions">
          <el-button size="small" :disabled="!can('process') || !selected || selected.status === '已发布'" @click="openStepCreate">新增工序</el-button>
        </div>
      </div>
      <div v-if="selected" class="object-strip">
        <div><span>路线编号</span><strong>{{ selected.route_no }}</strong></div>
        <div><span>来源路线</span><strong>{{ selected.source_route_id ? `#${selected.source_route_id}` : '-' }}</strong></div>
        <div><span>发布状态</span><strong>{{ selected.status }} / {{ selected.release_date || '未发布' }}</strong></div>
        <div><span>集成目标</span><strong>MES 工艺流程、工序参数、站点控制</strong></div>
      </div>
      <el-table v-if="selected" :data="selected.steps" size="small" class="section-gap">
        <el-table-column prop="sequence" label="序号" width="70" />
        <el-table-column prop="stage" label="阶段" width="120" />
        <el-table-column prop="operation" label="工序" width="160" />
        <el-table-column prop="key_params" label="关键参数" min-width="220" show-overflow-tooltip />
        <el-table-column prop="owner" label="负责人" width="90" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" class-name="table-actions-cell">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" :disabled="!can('process') || selected.status === '已发布'" @click="openStepEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" :disabled="!can('process') || selected.status === '已发布'" @click="removeStep(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="routeDialogVisible" :title="editingRouteId ? '编辑工艺路线' : '新增工艺路线'" width="720px">
      <el-form :model="routeForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="关联产品">
            <el-select v-model="routeForm.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="路线编号"><el-input v-model="routeForm.route_no" /></el-form-item>
          <el-form-item label="路线名称"><el-input v-model="routeForm.name" /></el-form-item>
          <el-form-item label="版本"><el-input v-model="routeForm.version" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="routeForm.owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="routeForm.status">
              <el-option label="编制中" value="编制中" />
              <el-option label="审批中" value="审批中" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="routeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRoute">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="stepDialogVisible" :title="editingStepId ? '编辑工序' : '新增工序'" width="720px">
      <el-form :model="stepForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="序号"><el-input-number v-model="stepForm.sequence" :min="1" controls-position="right" /></el-form-item>
          <el-form-item label="阶段"><el-input v-model="stepForm.stage" /></el-form-item>
          <el-form-item label="工序"><el-input v-model="stepForm.operation" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="stepForm.owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="stepForm.status">
              <el-option label="有效" value="有效" />
              <el-option label="停用" value="停用" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键参数" class="form-wide"><el-input v-model="stepForm.key_params" type="textarea" :rows="3" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="stepDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStep">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import UserSelect from '../components/UserSelect.vue'
import {
  approveProcessRoute,
  createProcessRoute,
  createProcessStep,
  deleteProcessRoute,
  deleteProcessStep,
  getProducts,
  getRoutes,
  submitProcessRoute,
  updateProcessRoute,
  updateProcessStep,
} from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const routes = ref<any[]>([])
const products = ref<any[]>([])
const selected = ref<any>()
const { can, currentUser, refreshSession } = useAuth()
const routeDialogVisible = ref(false)
const editingRouteId = ref<number | null>(null)
const emptyRoute = { product_id: undefined, route_no: '', name: '', version: 'A0', status: '编制中', owner: '', release_date: '', source_route_id: undefined }
const routeForm = ref<any>({ ...emptyRoute })
const stepDialogVisible = ref(false)
const editingStepId = ref<number | null>(null)
const emptyStep = { sequence: 10, stage: '', operation: '', key_params: '', owner: '', status: '有效' }
const stepForm = ref<any>({ ...emptyStep })

async function loadRoutes(keepId?: number) {
  routes.value = await getRoutes()
  selected.value = routes.value.find((item) => item.id === keepId) || routes.value[0]
}

function openRouteCreate() {
  if (!can('process')) return
  editingRouteId.value = null
  const product = products.value[0]
  routeForm.value = {
    ...emptyRoute,
    product_id: product?.id,
    route_no: product ? `ROUTE-${product.model}-${String(routes.value.length + 1).padStart(2, '0')}` : '',
    name: product ? `${product.model} 工艺路线` : '',
    owner: currentUser.value?.display_name || '',
  }
  routeDialogVisible.value = true
}

function openRouteEdit(row: any) {
  if (!can('process') || row.status === '已发布') return
  editingRouteId.value = row.id
  routeForm.value = { ...row }
  routeDialogVisible.value = true
}

async function saveRoute() {
  if (!can('process')) return
  if (editingRouteId.value) {
    await updateProcessRoute(editingRouteId.value, routeForm.value)
    ElMessage.success('工艺路线已更新')
    await loadRoutes(editingRouteId.value)
  } else {
    const next = await createProcessRoute(routeForm.value)
    ElMessage.success('工艺路线已创建')
    await loadRoutes(next.id)
  }
  routeDialogVisible.value = false
}

async function removeRoute(row: any) {
  if (!can('process') || row.status === '已发布') return
  await ElMessageBox.confirm(`确认删除工艺路线 ${row.route_no}？`, '删除确认', { type: 'warning' })
  await deleteProcessRoute(row.id)
  ElMessage.success('工艺路线已删除')
  await loadRoutes()
}

function openStepCreate() {
  if (!selected.value || !can('process') || selected.value.status === '已发布') return
  editingStepId.value = null
  const nextSequence = selected.value.steps?.length ? Math.max(...selected.value.steps.map((item: any) => item.sequence)) + 10 : 10
  stepForm.value = { ...emptyStep, sequence: nextSequence, owner: currentUser.value?.display_name || '' }
  stepDialogVisible.value = true
}

function openStepEdit(row: any) {
  if (!can('process') || selected.value?.status === '已发布') return
  editingStepId.value = row.id
  stepForm.value = { ...row }
  stepDialogVisible.value = true
}

async function saveStep() {
  if (!selected.value || !can('process')) return
  if (editingStepId.value) {
    await updateProcessStep(editingStepId.value, stepForm.value)
    ElMessage.success('工序已更新')
  } else {
    await createProcessStep(selected.value.id, stepForm.value)
    ElMessage.success('工序已创建')
  }
  stepDialogVisible.value = false
  await loadRoutes(selected.value.id)
}

async function removeStep(row: any) {
  if (!can('process') || selected.value?.status === '已发布') return
  await ElMessageBox.confirm(`确认删除工序 ${row.sequence} ${row.operation}？`, '删除确认', { type: 'warning' })
  await deleteProcessStep(row.id)
  ElMessage.success('工序已删除')
  await loadRoutes(selected.value?.id)
}

async function submit(row: any) {
  if (!row || !can('process')) return
  const next = await submitProcessRoute(row.id, { acted_by: currentUser.value?.display_name || '系统用户', comment: '提交工艺路线发布' })
  ElMessage.success('工艺路线已提交')
  await loadRoutes(next.id)
}

async function approve(row: any) {
  if (!row || !can(['approval', 'process'])) return
  const next = await approveProcessRoute(row.id, { acted_by: currentUser.value?.display_name || '系统用户', comment: '发布工艺路线并下发 MES' })
  ElMessage.success('工艺路线已发布，MES 同步队列已生成')
  await loadRoutes(next.id)
}

onMounted(async () => {
  await refreshSession()
  products.value = await getProducts()
  await loadRoutes()
  loading.value = false
})
</script>
