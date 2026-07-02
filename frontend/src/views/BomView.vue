<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>设计 BOM</strong>
        <span class="muted"> · Bom + BomItem 三段式用料，按工步绑定</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索 BOM 名称/版本/负责人" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button :disabled="!selected" @click="openCompare">BOM 比较</el-button>
        <el-button :disabled="!selected" @click="openProcessCoverage">工序校验</el-button>
        <el-button :disabled="!selected" @click="openLineage">版本链</el-button>
        <el-button v-if="can('bom')" type="primary" :icon="Plus" @click="openBomCreate">新建 BOM</el-button>
      </div>
    </div>

    <div class="list-table-wrap">
      <el-table :data="items" row-key="id" :expand-row-keys="expandedRowKeys" @expand-change="onExpandChange" height="100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="bom-detail-expand">
              <div class="expand-toolbar">
                <div>
                  <strong>{{ row.bom_name }} 明细</strong>
                  <span class="muted"> · {{ row.bom_version }} · {{ row.bom_state }}</span>
                </div>
                <div class="toolbar-actions">
                  <el-button size="small" :icon="Plus" @click="openItemCreate" :disabled="!can('bom') || isLocked(row)">新增行</el-button>
                  <el-button size="small" @click="triggerImport" :disabled="!can('bom') || isLocked(row)">导入</el-button>
                  <el-button size="small" @click="handleDownloadTemplate">下载模板</el-button>
                  <el-button size="small" @click="openBatchEdit" :disabled="!can('bom') || isLocked(row) || !row.items?.length">批量编辑</el-button>
                  <el-button size="small" type="danger" @click="removeBom" :disabled="!can('bom') || isLocked(row)">删除 BOM</el-button>
                </div>
              </div>
              <input ref="fileInputRef" type="file" style="display:none" @change="handleImport" />
              <div class="object-strip">
                <div><span>BOM</span><strong>{{ row.bom_name }}</strong></div>
                <div><span>版本</span><strong>{{ row.bom_version }}</strong></div>
                <div><span>明细</span><strong>{{ row.items?.length || 0 }}</strong></div>
                <div><span>负责人</span><strong>{{ row.owner || '-' }}</strong></div>
              </div>
              <el-table :data="row.items || []" size="small" max-height="420">
                <el-table-column prop="idx" label="序号" width="70" fixed />
                <el-table-column prop="material_type" label="物料类型" width="120" />
                <el-table-column prop="material_def_name" label="物料名称" min-width="180" />
                <el-table-column prop="material_def_version" label="物料版本" width="100" />
                <el-table-column prop="require_quantity" label="需求量" width="90" />
                <el-table-column prop="unit" label="单位" width="80" />
                <el-table-column prop="process_step_name" label="工序" width="150">
                  <template #default="{ row: itemRow }">
                    <el-tag v-if="itemRow.process_step_name" size="small" type="success">{{ itemRow.process_step_name }}</el-tag>
                    <span v-else class="muted">未绑定</span>
                  </template>
                </el-table-column>
                <el-table-column prop="process_step_version" label="工序版本" width="100" />
                <el-table-column label="操作" width="190" fixed="right">
                  <template #default="{ row: itemRow }">
                    <div class="row-actions">
                      <el-button size="small" @click="openWhereUsed(itemRow)">反查</el-button>
                      <el-button size="small" @click="openItemEdit(itemRow)" :disabled="!can('bom') || isLocked(row)">编辑</el-button>
                      <el-button size="small" type="danger" @click="removeItem(itemRow)" :disabled="!can('bom') || isLocked(row)">删除</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <AttachmentPanel :object-type="'BOM'" :object-id="row.id" :can-edit="can('bom')" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="bom_name" label="BOM 名称" width="170" fixed />
        <el-table-column prop="bom_version" label="版本" width="90" />
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.bom_state === 'Active' ? 'success' : row.bom_state === 'Frozen' ? 'warning' : row.bom_state === 'Invalid' ? 'danger' : 'info'">{{ row.bom_state }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="100" />
        <el-table-column label="明细数" width="90">
          <template #default="{ row }">{{ row.items?.length || 0 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" :disabled="!can('bom') || isLocked(row)" @click.stop="openBomEdit(row)">编辑</el-button>
              <el-button size="small" :disabled="!can('bom') || row.bom_state !== 'Unfrozen'" @click.stop="submit(row)">冻结</el-button>
              <el-button size="small" type="primary" :disabled="!can(['approval', 'bom']) || row.bom_state !== 'Frozen'" @click.stop="approve(row)">发布</el-button>
              <el-button size="small" @click.stop="handleExport(row)">导出</el-button>
              <el-button size="small" @click.stop="openVersionHistory(row)">版本</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <el-dialog v-model="bomDialogVisible" :title="bomEditingId ? '编辑 BOM' : '新建 BOM'" width="680px">
      <el-form :model="bomForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="BOM 名称"><el-input v-model="bomForm.bom_name" /></el-form-item>
          <el-form-item label="BOM 版本"><el-input v-model="bomForm.bom_version" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="bomForm.bom_state">
              <el-option v-for="item in bomStateOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="bomForm.owner" /></el-form-item>
          <el-form-item label="描述" class="form-wide"><el-input v-model="bomForm.description" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="bomDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBom">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="itemDialogVisible" :title="itemEditingId ? '编辑 BOM 行' : '新增 BOM 行'" width="760px">
      <el-form :model="itemForm" label-width="110px">
        <div class="form-grid">
          <el-form-item label="序号"><el-input-number v-model="itemForm.idx" :min="1" /></el-form-item>
          <el-form-item label="物料类型">
            <el-select v-model="itemForm.material_type">
              <el-option v-for="item in materialTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="物料名称">
            <el-select v-model="itemForm.material_def_name" filterable allow-create>
              <el-option v-for="material in materials" :key="material.consumable_def_name" :label="material.consumable_def_name" :value="material.consumable_def_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="物料版本"><el-input v-model="itemForm.material_def_version" /></el-form-item>
          <el-form-item label="需求量"><el-input-number v-model="itemForm.require_quantity" :min="0" :precision="4" /></el-form-item>
          <el-form-item label="单位"><el-input v-model="itemForm.unit" /></el-form-item>
          <el-form-item label="工序">
            <el-select v-model="itemForm.process_step_name" filterable clearable>
              <el-option v-for="step in processSteps" :key="`${step.process_step_name}-${step.process_step_version}`" :label="`${step.process_step_name}@${step.process_step_version}`" :value="step.process_step_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="工序版本"><el-input v-model="itemForm.process_step_version" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="compareDialogVisible" title="BOM 比较" width="860px">
      <div class="toolbar compact-toolbar">
        <span class="muted">基准：{{ selected?.bom_name }} {{ selected?.bom_version }}</span>
        <div class="toolbar-actions">
          <el-select v-model="compareTargetId" placeholder="选择对比 BOM" style="width: 260px">
            <el-option v-for="bom in compareOptions" :key="bom.id" :label="`${bom.bom_name}@${bom.bom_version}`" :value="bom.id" />
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
        <el-table-column prop="material_def_name" label="物料名称" min-width="180" />
        <el-table-column prop="material_type" label="物料类型" width="120" />
        <el-table-column prop="process_step_name" label="工序" width="140" />
        <el-table-column prop="from_quantity" label="原需求量" width="100" />
        <el-table-column prop="to_quantity" label="新需求量" width="100" />
        <el-table-column prop="from_unit" label="原单位" width="90" />
        <el-table-column prop="to_unit" label="新单位" width="90" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="whereUsedDialogVisible" :title="`${whereUsedMaterial} 反查`" width="820px">
      <el-table :data="whereUsedRows" height="420" size="small">
        <el-table-column prop="bom_name" label="BOM 名称" width="170" fixed />
        <el-table-column prop="bom_version" label="版本" width="90" />
        <el-table-column prop="bom_state" label="状态" width="100" />
        <el-table-column prop="material_type" label="物料类型" width="120" />
        <el-table-column prop="require_quantity" label="需求量" width="90" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="process_step_name" label="工序" width="130" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="processCoverageDialogVisible" title="工序物料分配校验" width="780px">
      <div v-if="processCoverage" class="object-strip">
        <div><span>明细总数</span><strong>{{ processCoverage.total_items }}</strong></div>
        <div><span>已分配工序</span><strong>{{ processCoverage.assigned }}</strong></div>
        <div><span>未分配</span><strong :style="{ color: processCoverage.unassigned > 0 ? 'var(--el-color-danger)' : '' }">{{ processCoverage.unassigned }}</strong></div>
        <div><span>覆盖率</span><strong>{{ (processCoverage.coverage_rate * 100).toFixed(1) }}%</strong></div>
      </div>
      <el-table :data="processCoverage?.unassigned_items || []" height="380" size="small">
        <el-table-column prop="material_def_name" label="物料名称" min-width="180" fixed />
        <el-table-column prop="material_type" label="物料类型" width="120" />
        <el-table-column prop="require_quantity" label="需求量" width="90" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="process_step_name" label="工序" width="140" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="lineageDialogVisible" title="BOM 版本链" width="820px">
      <div v-if="lineageData">
        <div class="muted" style="margin-bottom: 8px">当前：{{ lineageData.current.bom_name }} {{ lineageData.current.bom_version }}</div>
        <div v-if="!lineageData.has_lineage" class="muted">该 BOM 暂无同名版本</div>
        <el-table v-else :data="lineageData.descendants" size="small">
          <el-table-column prop="bom_name" label="BOM 名称" min-width="170" />
          <el-table-column prop="bom_version" label="版本" width="90" />
          <el-table-column prop="bom_state" label="状态" width="100" />
        </el-table>
      </div>
    </el-dialog>

    <el-dialog v-model="versionHistoryVisible" title="BOM 版本历史" width="760px">
      <el-table :data="versionHistory" height="420" size="small">
        <el-table-column prop="bom_version" label="版本" width="90" fixed />
        <el-table-column label="当前" width="70">
          <template #default="{ row }"><el-tag v-if="row.is_current" size="small" type="success">当前</el-tag></template>
        </el-table-column>
        <el-table-column prop="bom_state" label="状态" width="100" />
        <el-table-column prop="bom_name" label="BOM 名称" min-width="170" />
        <el-table-column prop="owner" label="负责人" width="100" />
        <el-table-column prop="description" label="描述" min-width="220" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="batchEditVisible" title="BOM 批量编辑" width="900px">
      <el-tabs v-model="batchTab">
        <el-tab-pane label="批量替换物料" name="replace">
          <el-form label-width="110px" style="margin-top: 10px">
            <el-form-item label="原物料名称"><el-input v-model="batchReplaceForm.from_code" /></el-form-item>
            <el-form-item label="新物料名称"><el-input v-model="batchReplaceForm.to_code" /></el-form-item>
            <el-form-item label="新物料版本"><el-input v-model="batchReplaceForm.to_name" /></el-form-item>
            <el-button type="primary" @click="executeBatchReplace" :disabled="!batchReplaceForm.from_code || !batchReplaceForm.to_code">执行替换</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="批量修改需求量" name="quantity">
          <el-table :data="selected?.items || []" height="300" size="small" @selection-change="(val: any[]) => batchSelection = val">
            <el-table-column type="selection" width="45" />
            <el-table-column prop="material_def_name" label="物料名称" min-width="160" />
            <el-table-column prop="require_quantity" label="当前需求量" width="110" />
            <el-table-column prop="unit" label="单位" width="70" />
          </el-table>
          <div style="margin-top: 10px; display: flex; align-items: center; gap: 10px">
            <span>统一改为</span>
            <el-input-number v-model="batchQuantity" :min="0" :precision="4" :step="0.1" style="width: 140px" />
            <el-button type="primary" @click="executeBatchQuantity" :disabled="!batchSelection.length">执行修改</el-button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="批量删除明细" name="delete">
          <el-table :data="selected?.items || []" height="300" size="small" @selection-change="(val: any[]) => batchSelection = val">
            <el-table-column type="selection" width="45" />
            <el-table-column prop="material_def_name" label="物料名称" min-width="160" />
            <el-table-column prop="process_step_name" label="工序" width="140" />
          </el-table>
          <div style="margin-top: 10px">
            <el-button type="danger" @click="executeBatchDelete" :disabled="!batchSelection.length">删除选中项 ({{ batchSelection.length }})</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import {
  approveBom,
  batchDeleteBomItems,
  batchReplaceBomMaterial,
  batchUpdateBomQuantity,
  compareBoms,
  createBom,
  createBomItem,
  deleteBom,
  deleteBomItem,
  downloadBomTemplate,
  exportBomExcel,
  getBomLineage,
  getBomProcessCoverage,
  getBomVersionHistory,
  getBomWhereUsed,
  getBoms,
  getMaterials,
  getProcessSteps,
  importBomExcel,
  submitBom,
  updateBom,
  updateBomItem
} from '../api'
import { useAuth } from '../auth'
import AttachmentPanel from '../components/AttachmentPanel.vue'
import UserSelect from '../components/UserSelect.vue'
import { useDictionary } from '../composables/useDictionary'
import { useListPage } from '../composables/useListPage'

const { can, currentUser, refreshSession } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getBoms)
const materialTypeOptions = computed(() => [
  { label: 'Consumable', value: 'Consumable' },
  { label: 'Durable', value: 'Durable' },
  { label: 'Product', value: 'Product' },
])
const bomStateOptions = computed(() => [
  { label: 'Unfrozen', value: 'Unfrozen' },
  { label: 'Frozen', value: 'Frozen' },
  { label: 'Active', value: 'Active' },
  { label: 'Invalid', value: 'Invalid' },
])

const selected = ref<any>()
const expandedRowKeys = ref<number[]>([])
const materials = ref<any[]>([])
const processSteps = ref<any[]>([])
const bomDialogVisible = ref(false)
const itemDialogVisible = ref(false)
const compareDialogVisible = ref(false)
const whereUsedDialogVisible = ref(false)
const processCoverageDialogVisible = ref(false)
const lineageDialogVisible = ref(false)
const versionHistoryVisible = ref(false)
const batchEditVisible = ref(false)
const bomEditingId = ref<number | null>(null)
const itemEditingId = ref<number | null>(null)
const compareTargetId = ref<number | undefined>()
const compareResult = ref<any>()
const processCoverage = ref<any>()
const lineageData = ref<any>()
const whereUsedRows = ref<any[]>([])
const whereUsedMaterial = ref('')
const versionHistory = ref<any[]>([])
const fileInputRef = ref<HTMLInputElement>()
const batchTab = ref('replace')
const batchSelection = ref<any[]>([])
const batchReplaceForm = ref<any>({ from_code: '', to_code: '', to_name: '' })
const batchQuantity = ref(1)

const emptyBom = { bom_state: 'Unfrozen', bom_name: '', bom_version: '001', description: '', owner: '' }
const emptyItem = { idx: null, material_type: 'Consumable', material_def_name: '', material_def_version: '001', require_quantity: 1, unit: 'EA', process_step_name: '', process_step_version: '001' }
const bomForm = ref<any>({ ...emptyBom })
const itemForm = ref<any>({ ...emptyItem })

const compareOptions = computed(() => (items.value || []).filter((item: any) => item.id !== selected.value?.id))

function isLocked(row: any) {
  return ['Frozen', 'Active', 'Invalid'].includes(row?.bom_state)
}

async function loadBoms(keepId?: number) {
  await loadData()
  const target = keepId ? (items.value || []).find((item: any) => item.id === keepId) : (items.value || [])[0]
  selected.value = target || null
  expandedRowKeys.value = target ? [target.id] : []
}

async function loadLookups() {
  const [materialRes, stepRes] = await Promise.all([
    getMaterials({ page: 1, page_size: 500 }),
    getProcessSteps({ page: 1, page_size: 500 }),
  ])
  materials.value = materialRes.items || []
  processSteps.value = stepRes.items || []
}

async function onExpandChange(row: any, expandedRows: any[]) {
  const isExpanded = expandedRows.some((item: any) => item.id === row.id)
  expandedRowKeys.value = isExpanded ? [row.id] : []
  selected.value = isExpanded ? row : null
}

function openBomCreate() {
  if (!can('bom')) return
  bomEditingId.value = null
  bomForm.value = { ...emptyBom, owner: currentUser.value?.display_name || '' }
  bomDialogVisible.value = true
}

function openBomEdit(row: any) {
  if (!can('bom') || isLocked(row)) return
  bomEditingId.value = row.id
  bomForm.value = { bom_state: row.bom_state, bom_name: row.bom_name, bom_version: row.bom_version, description: row.description, owner: row.owner }
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
  if (!can('bom') || !selected.value || isLocked(selected.value)) return
  itemEditingId.value = null
  itemForm.value = { ...emptyItem, idx: (selected.value.items?.length || 0) + 1 }
  itemDialogVisible.value = true
}

function openItemEdit(row: any) {
  if (!can('bom') || isLocked(selected.value)) return
  itemEditingId.value = row.id
  itemForm.value = { ...row }
  itemDialogVisible.value = true
}

async function saveItem() {
  if (!can('bom') || !selected.value) return
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
  if (!can('bom') || !selected.value) return
  await ElMessageBox.confirm(`确认删除 BOM 行 ${row.material_def_name}？`, '删除确认', { type: 'warning' })
  await deleteBomItem(row.id)
  ElMessage.success('BOM 行已删除')
  await loadBoms(selected.value.id)
}

async function removeBom() {
  if (!can('bom') || !selected.value) return
  await ElMessageBox.confirm(`确认删除 ${selected.value.bom_name}@${selected.value.bom_version}？`, '删除确认', { type: 'warning' })
  await deleteBom(selected.value.id)
  ElMessage.success('BOM 已删除')
  await loadBoms()
}

async function submit(row: any) {
  await submitBom(row.id)
  ElMessage.success('BOM 已冻结')
  await loadBoms(row.id)
}

async function approve(row: any) {
  await approveBom(row.id)
  ElMessage.success('BOM 已发布')
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

async function openProcessCoverage() {
  if (!selected.value) return
  processCoverage.value = await getBomProcessCoverage(selected.value.id)
  processCoverageDialogVisible.value = true
}

async function openLineage() {
  if (!selected.value) return
  lineageData.value = await getBomLineage(selected.value.id)
  lineageDialogVisible.value = true
}

async function openWhereUsed(row: any) {
  whereUsedMaterial.value = row.material_def_name
  whereUsedRows.value = await getBomWhereUsed(row.material_def_name)
  whereUsedDialogVisible.value = true
}

async function handleExport(row: any) {
  try {
    const response = await exportBomExcel(row.id)
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${row.bom_name}-${row.bom_version}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}

function triggerImport() {
  fileInputRef.value?.click()
}

async function handleImport(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !selected.value) return
  try {
    const result = await importBomExcel(selected.value.id, file)
    ElMessage.success(`成功导入 ${result.imported} 条明细`)
    await loadBoms(selected.value.id)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '导入失败')
  }
  target.value = ''
}

async function handleDownloadTemplate() {
  const response = await downloadBomTemplate()
  const blob = new Blob([response.data])
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'BOM_template.xlsx'
  link.click()
  window.URL.revokeObjectURL(url)
}

function openBatchEdit() {
  if (!can('bom') || !selected.value || isLocked(selected.value)) return
  batchTab.value = 'replace'
  batchSelection.value = []
  batchReplaceForm.value = { from_code: '', to_code: '', to_name: '' }
  batchQuantity.value = 1
  batchEditVisible.value = true
}

async function executeBatchReplace() {
  if (!selected.value) return
  const result = await batchReplaceBomMaterial(selected.value.id, batchReplaceForm.value)
  ElMessage.success(`已替换 ${result.updated} 条记录`)
  batchEditVisible.value = false
  await loadBoms(selected.value.id)
}

async function executeBatchQuantity() {
  if (!selected.value || !batchSelection.value.length) return
  const ids = batchSelection.value.map((item: any) => item.id)
  const result = await batchUpdateBomQuantity(selected.value.id, { item_ids: ids, quantity: batchQuantity.value })
  ElMessage.success(`已修改 ${result.updated} 条需求量`)
  batchEditVisible.value = false
  await loadBoms(selected.value.id)
}

async function executeBatchDelete() {
  if (!selected.value || !batchSelection.value.length) return
  await ElMessageBox.confirm(`确认删除选中的 ${batchSelection.value.length} 条 BOM 行？`, '批量删除确认', { type: 'warning' })
  const ids = batchSelection.value.map((item: any) => item.id)
  const result = await batchDeleteBomItems(selected.value.id, { item_ids: ids })
  ElMessage.success(`已删除 ${result.deleted} 条 BOM 行`)
  batchEditVisible.value = false
  await loadBoms(selected.value.id)
}

async function openVersionHistory(row: any) {
  versionHistory.value = await getBomVersionHistory(row.id)
  versionHistoryVisible.value = true
}

onMounted(async () => {
  await refreshSession()
  await loadLookups()
  await loadBoms()
})
</script>
