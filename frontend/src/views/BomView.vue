<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>BOM 对象管理</strong>
          <span class="muted"> · 表头、结构明细、审核发布与 ERP 下发联动</span>
        </div>
        <div class="toolbar-actions">
          <el-button v-if="can('bom')" :disabled="!selected" @click="openTransform">转 PBOM/MBOM</el-button>
          <el-button :disabled="!selected" @click="openCompare">BOM 比较</el-button>
          <el-button v-if="can('bom')" type="primary" :icon="Plus" @click="openBomCreate">新建 BOM</el-button>
        </div>
      </div>
      <el-table :data="boms" highlight-current-row @current-change="selectBom" height="680">
        <el-table-column prop="product_model" label="产品型号" width="130" fixed />
        <el-table-column prop="product_name" label="产品名称" min-width="180" />
        <el-table-column prop="type" label="类型" width="90" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="当前" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_current" size="small" type="success">当前</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="effective_date" label="生效日" width="110" />
        <el-table-column prop="expiry_date" label="失效日" width="110" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === '已发布' ? 'success' : row.status === '审批中' ? 'warning' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="90" />
        <el-table-column prop="release_date" label="发布日期" width="120" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="!can('bom') || row.status === '已发布'" @click.stop="openBomEdit(row)">编辑</el-button>
            <el-button size="small" :disabled="!can('bom') || row.status === '已发布'" @click.stop="submit(row)">提交</el-button>
            <el-button size="small" type="primary" :disabled="!can(['approval', 'bom']) || row.status === '已发布'" @click.stop="approve(row)">发布</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>{{ selected?.product_model || '选择 BOM' }} 结构明细</strong>
          <span v-if="selected" class="muted"> · {{ selected.type }} {{ selected.version }} · {{ selected.status }}</span>
        </div>
        <div class="toolbar-actions">
          <el-button :icon="Plus" @click="openItemCreate" :disabled="!can('bom') || !selected || selected.status === '已发布'">新增行</el-button>
          <el-button type="danger" @click="removeBom" :disabled="!can('bom') || !selected || selected.status === '已发布'">删除 BOM</el-button>
        </div>
      </div>
      <div v-if="selected" class="object-strip">
        <div><span>产品</span><strong>{{ selected.product_model }}</strong></div>
        <div><span>有效性</span><strong>{{ selected.effectivity_type }} · {{ selected.effective_date || '未设置' }} - {{ selected.expiry_date || '长期' }}</strong></div>
        <div><span>下游</span><strong>{{ selected.source_bom_id ? `来源 BOM#${selected.source_bom_id}` : '发布后进入 ERP 队列' }}</strong></div>
      </div>
      <el-table :data="selected?.items || []" size="small" height="610">
        <el-table-column prop="material_code" label="物料编码" width="130" fixed />
        <el-table-column prop="material_name" label="物料名称" min-width="150" />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="specification" label="规格" min-width="150" />
        <el-table-column prop="quantity" label="用量" width="80" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="process_step" label="工序" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.process_step_id" size="small" type="success">{{ row.process_step }}</el-tag>
            <span v-else>{{ row.process_step || '未绑定' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="substitute" label="替代料" width="110" />
        <el-table-column prop="effective_date" label="生效日" width="110" />
        <el-table-column prop="expiry_date" label="失效日" width="110" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openWhereUsed(row)">反查</el-button>
            <el-button size="small" @click="openItemEdit(row)" :disabled="!can('bom') || selected?.status === '已发布'">编辑</el-button>
            <el-button size="small" type="danger" @click="removeItem(row)" :disabled="!can('bom') || selected?.status === '已发布'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="bomDialogVisible" :title="bomEditingId ? '编辑 BOM' : '新建 BOM'" width="620px">
      <el-form :model="bomForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="关联产品">
            <el-select v-model="bomForm.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="BOM 类型">
            <el-select v-model="bomForm.bom_type">
              <el-option label="EBOM" value="EBOM" />
              <el-option label="MBOM" value="MBOM" />
              <el-option label="PBOM" value="PBOM" />
            </el-select>
          </el-form-item>
          <el-form-item label="版本"><el-input v-model="bomForm.version" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="bomForm.status">
              <el-option label="编制中" value="编制中" />
              <el-option label="审批中" value="审批中" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="bomForm.owner" /></el-form-item>
          <el-form-item label="发布日期"><el-input v-model="bomForm.release_date" placeholder="发布时自动写入" /></el-form-item>
          <el-form-item label="有效类型">
            <el-select v-model="bomForm.effectivity_type">
              <el-option label="日期" value="日期" />
              <el-option label="批次" value="批次" />
              <el-option label="项目" value="项目" />
            </el-select>
          </el-form-item>
          <el-form-item label="生效日期"><el-input v-model="bomForm.effective_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="失效日期"><el-input v-model="bomForm.expiry_date" placeholder="空表示长期有效" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="bomDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBom">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="itemDialogVisible" :title="itemEditingId ? '编辑 BOM 行' : '新增 BOM 行'" width="720px">
      <el-form :model="itemForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="物料编码"><el-input v-model="itemForm.material_code" /></el-form-item>
          <el-form-item label="物料名称"><el-input v-model="itemForm.material_name" /></el-form-item>
          <el-form-item label="类别"><el-input v-model="itemForm.category" /></el-form-item>
          <el-form-item label="规格"><el-input v-model="itemForm.specification" /></el-form-item>
          <el-form-item label="用量"><el-input-number v-model="itemForm.quantity" :min="0" :precision="3" /></el-form-item>
          <el-form-item label="单位"><el-input v-model="itemForm.unit" /></el-form-item>
          <el-form-item label="位置"><el-input v-model="itemForm.position" /></el-form-item>
          <el-form-item label="关联工序">
            <el-select v-model="itemForm.process_step_id" filterable clearable placeholder="选择真实工艺路线工序">
              <el-option
                v-for="step in processSteps"
                :key="step.id"
                :label="step.label"
                :value="step.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="替代料"><el-input v-model="itemForm.substitute" /></el-form-item>
          <el-form-item label="状态"><el-input v-model="itemForm.status" /></el-form-item>
          <el-form-item label="生效日期"><el-input v-model="itemForm.effective_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="失效日期"><el-input v-model="itemForm.expiry_date" placeholder="空表示长期有效" /></el-form-item>
          <el-form-item label="有效说明" class="form-wide"><el-input v-model="itemForm.effectivity_note" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="transformDialogVisible" title="EBOM/PBOM/MBOM 转换" width="560px">
      <el-form :model="transformForm" label-width="100px">
        <el-form-item label="来源 BOM"><span>{{ selected?.product_model }} {{ selected?.type }} {{ selected?.version }}</span></el-form-item>
        <el-form-item label="目标类型">
          <el-select v-model="transformForm.target_type">
            <el-option label="PBOM" value="PBOM" />
            <el-option label="MBOM" value="MBOM" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标版本"><el-input v-model="transformForm.version" /></el-form-item>
        <el-form-item label="负责人"><UserSelect v-model="transformForm.owner" /></el-form-item>
        <el-form-item label="生效日期"><el-input v-model="transformForm.effective_date" placeholder="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="有效类型">
          <el-select v-model="transformForm.effectivity_type">
            <el-option label="日期" value="日期" />
            <el-option label="批次" value="批次" />
            <el-option label="项目" value="项目" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transformDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTransform">生成下游 BOM</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="compareDialogVisible" title="BOM 比较" width="860px">
      <div class="toolbar compact-toolbar">
        <span class="muted">基准：{{ selected?.product_model }} {{ selected?.type }} {{ selected?.version }}</span>
        <div class="toolbar-actions">
          <el-select v-model="compareTargetId" placeholder="选择对比 BOM" style="width: 260px">
            <el-option
              v-for="bom in compareOptions"
              :key="bom.id"
              :label="`${bom.product_model} ${bom.type} ${bom.version}`"
              :value="bom.id"
            />
          </el-select>
          <el-button type="primary" @click="loadCompare">比较</el-button>
        </div>
      </div>
      <div v-if="compareResult" class="object-strip">
        <div><span>新增</span><strong>{{ compareResult.summary.added }}</strong></div>
        <div><span>删除</span><strong>{{ compareResult.summary.removed }}</strong></div>
        <div><span>变更</span><strong>{{ compareResult.summary.changed }}</strong></div>
      </div>
      <el-table :data="compareResult?.changes || []" height="420" size="small">
        <el-table-column prop="change_type" label="类型" width="80" fixed />
        <el-table-column prop="material_code" label="物料编码" width="140" />
        <el-table-column prop="material_name" label="物料名称" min-width="180" />
        <el-table-column prop="process_step" label="工序" width="120" />
        <el-table-column prop="from_quantity" label="原用量" width="90" />
        <el-table-column prop="to_quantity" label="新用量" width="90" />
        <el-table-column prop="from_status" label="原状态" width="90" />
        <el-table-column prop="to_status" label="新状态" width="90" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="whereUsedDialogVisible" :title="`${whereUsedMaterial} 反查`" width="820px">
      <el-table :data="whereUsedRows" height="420" size="small">
        <el-table-column prop="product_model" label="产品型号" width="140" fixed />
        <el-table-column prop="bom_type" label="BOM 类型" width="100" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="bom_status" label="BOM 状态" width="100" />
        <el-table-column prop="quantity" label="用量" width="80" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="process_step" label="工序" width="130" />
        <el-table-column prop="effective_date" label="生效日" width="110" />
        <el-table-column prop="expiry_date" label="失效日" width="110" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import {
  approveBom,
  compareBoms,
  createBom,
  createBomItem,
  deleteBom,
  deleteBomItem,
  getBomWhereUsed,
  getBoms,
  getProductProcessSteps,
  getProducts,
  submitBom,
  transformBom,
  updateBom,
  updateBomItem
} from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'

const loading = ref(true)
const { can, currentUser, refreshSession } = useAuth()
const boms = ref<any[]>([])
const products = ref<any[]>([])
const processSteps = ref<any[]>([])
const selected = ref<any>()
const bomDialogVisible = ref(false)
const itemDialogVisible = ref(false)
const transformDialogVisible = ref(false)
const compareDialogVisible = ref(false)
const whereUsedDialogVisible = ref(false)
const bomEditingId = ref<number | null>(null)
const itemEditingId = ref<number | null>(null)
const emptyBom = { product_id: undefined, bom_type: 'EBOM', version: 'A0', status: '编制中', owner: '', release_date: '', effective_date: '', expiry_date: '', effectivity_type: '日期' }
const emptyItem = { material_code: '', material_name: '', category: '', specification: '', quantity: 1, unit: '件', position: '', process_step_id: undefined, process_step: '', substitute: '', status: '有效', effective_date: '', expiry_date: '', effectivity_note: '' }
const bomForm = ref<any>({ ...emptyBom })
const itemForm = ref<any>({ ...emptyItem })
const transformForm = ref<any>({ target_type: 'PBOM', version: 'A0', owner: '', effective_date: '', effectivity_type: '日期' })
const compareTargetId = ref<number | undefined>()
const compareResult = ref<any>()
const whereUsedRows = ref<any[]>([])
const whereUsedMaterial = ref('')

async function loadBoms(keepId?: number) {
  boms.value = await getBoms()
  selected.value = boms.value.find((item) => item.id === keepId) || boms.value[0]
  await loadProcessSteps()
}

async function selectBom(row: any) {
  selected.value = row
  await loadProcessSteps()
}

async function loadProcessSteps() {
  processSteps.value = selected.value?.product_id ? await getProductProcessSteps(selected.value.product_id) : []
}

function openBomCreate() {
  if (!can('bom')) return
  bomEditingId.value = null
  bomForm.value = { ...emptyBom, product_id: products.value[0]?.id, owner: currentUser.value?.display_name || '' }
  bomDialogVisible.value = true
}

function openBomEdit(row: any) {
  if (!can('bom') || row.status === '已发布') return
  bomEditingId.value = row.id
  bomForm.value = {
    product_id: row.product_id,
    bom_type: row.type,
    version: row.version,
    status: row.status,
    owner: row.owner,
    release_date: row.release_date,
    effective_date: row.effective_date,
    expiry_date: row.expiry_date,
    effectivity_type: row.effectivity_type || '日期'
  }
  bomDialogVisible.value = true
}

async function saveBom() {
  if (!can('bom')) return
  const row = bomEditingId.value ? await updateBom(bomEditingId.value, bomForm.value) : await createBom(bomForm.value)
  ElMessage.success('BOM 已保存')
  bomDialogVisible.value = false
  await loadBoms(row.id)
}

function openItemCreate() {
  if (!can('bom') || !selected.value || selected.value.status === '已发布') return
  itemEditingId.value = null
  itemForm.value = { ...emptyItem }
  itemDialogVisible.value = true
}

function openItemEdit(row: any) {
  if (!can('bom') || selected.value?.status === '已发布') return
  itemEditingId.value = row.id
  itemForm.value = { ...row }
  itemDialogVisible.value = true
}

async function saveItem() {
  if (!can('bom')) return
  if (!selected.value) return
  if (itemEditingId.value) {
    await updateBomItem(itemEditingId.value, itemForm.value)
  } else {
    await createBomItem(selected.value.id, itemForm.value)
  }
  ElMessage.success('BOM 明细已保存')
  itemDialogVisible.value = false
  await loadBoms(selected.value.id)
}

async function removeItem(row: any) {
  if (!can('bom')) return
  await ElMessageBox.confirm(`确认删除 BOM 行 ${row.material_code}？`, '删除确认', { type: 'warning' })
  await deleteBomItem(row.id)
  ElMessage.success('BOM 行已删除')
  await loadBoms(selected.value?.id)
}

async function removeBom() {
  if (!can('bom')) return
  if (!selected.value) return
  await ElMessageBox.confirm(`确认删除 ${selected.value.product_model} ${selected.value.type}？`, '删除确认', { type: 'warning' })
  await deleteBom(selected.value.id)
  ElMessage.success('BOM 已删除')
  await loadBoms()
}

async function submit(row: any) {
  if (!can('bom')) return
  await submitBom(row.id)
  ElMessage.success('BOM 已提交审核')
  await loadBoms(row.id)
}

async function approve(row: any) {
  if (!can(['approval', 'bom'])) return
  const result = await approveBom(row.id)
  const closedCount = result.closed_versions?.length || 0
  ElMessage.success(closedCount ? `BOM 已发布，并自动失效 ${closedCount} 个旧版本` : 'BOM 已发布，ERP 同步队列已生成')
  await loadBoms(row.id)
}

const compareOptions = computed(() => {
  if (!selected.value) return []
  return boms.value.filter((item) => item.id !== selected.value.id && item.product_id === selected.value.product_id)
})

function openTransform() {
  if (!can('bom') || !selected.value) return
  transformForm.value = {
    target_type: selected.value.type === 'EBOM' ? 'PBOM' : 'MBOM',
    version: selected.value.version,
    owner: selected.value.owner,
    effective_date: selected.value.effective_date || '',
    effectivity_type: selected.value.effectivity_type || '日期'
  }
  transformDialogVisible.value = true
}

async function saveTransform() {
  if (!can('bom') || !selected.value) return
  const row = await transformBom(selected.value.id, transformForm.value)
  ElMessage.success(`${row.type} 已生成，可继续维护工序和有效期`)
  transformDialogVisible.value = false
  await loadBoms(row.id)
}

function openCompare() {
  if (!selected.value) return
  compareTargetId.value = compareOptions.value[0]?.id
  compareResult.value = undefined
  compareDialogVisible.value = true
}

async function loadCompare() {
  if (!selected.value || !compareTargetId.value) return
  compareResult.value = await compareBoms(selected.value.id, compareTargetId.value)
}

async function openWhereUsed(row: any) {
  whereUsedMaterial.value = row.material_code
  whereUsedRows.value = await getBomWhereUsed(row.material_code)
  whereUsedDialogVisible.value = true
}

onMounted(async () => {
  await refreshSession()
  products.value = await getProducts()
  await loadBoms()
  loading.value = false
})
</script>
