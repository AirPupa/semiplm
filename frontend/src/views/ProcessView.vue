<template>
  <div class="process-page">
    <!-- 制造流程列表 -->
    <div class="panel list-panel" v-loading="loading">
      <div class="toolbar">
        <div><strong>工艺流程</strong><span class="muted"> · PLM 主控源头，被产品引用，对齐 MES ProcessFlow</span></div>
        <div class="toolbar-actions">
          <el-select v-model="filterState" placeholder="流程状态" clearable style="width: 120px" @change="onSearch">
            <el-option label="Active" value="Active" />
            <el-option label="Frozen" value="Frozen" />
            <el-option label="Unfrozen" value="Unfrozen" />
            <el-option label="Invalid" value="Invalid" />
          </el-select>
          <el-input v-model="keyword" placeholder="搜索流程名称/描述" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
          <el-button v-if="can('process')" type="primary" :icon="Plus" @click="openCreateFlow">新增流程</el-button>
        </div>
      </div>
      <div class="list-table-wrap">
        <el-table :data="items" height="100%" highlight-current-row @current-change="onSelectFlow">
          <el-table-column prop="process_flow_name" label="流程名称" min-width="150" />
          <el-table-column prop="process_flow_version" label="版本" width="80" />
          <el-table-column prop="process_flow_type1" label="类型1" width="90">
            <template #default="{ row }">{{ row.process_flow_type1 === 'Main' ? '主流程' : '子流程' }}</template>
          </el-table-column>
          <el-table-column prop="process_flow_type2" label="类型2" width="100" />
          <el-table-column prop="process_flow_state" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="stateTag(row.process_flow_state)" size="small">{{ row.process_flow_state }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="owner_group_name" label="归属组" width="120" />
          <el-table-column prop="owner" label="负责人" width="100" />
          <el-table-column prop="process_group_name" label="流程组" width="120" />
          <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="onSelectFlow(row)">详情</el-button>
              <el-button size="small" @click="openEditFlow(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeFlow(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
      </div>
    </div>

    <!-- 流程详情 4 tab -->
    <div class="panel detail-panel" v-if="currentFlow">
      <div class="toolbar">
        <div>
          <strong>{{ currentFlow.process_flow_name }} / v{{ currentFlow.process_flow_version }}</strong>
          <span class="muted"> · {{ currentFlow.description || '无描述' }}</span>
        </div>
        <div class="toolbar-actions">
          <el-button size="small" @click="currentFlow = null">关闭详情</el-button>
        </div>
      </div>
      <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- 工序 tab -->
        <el-tab-pane label="工序" name="seq">
          <div class="sub-toolbar">
            <span class="muted">流程工序序列（ProcessFlowSeq）</span>
            <el-button v-if="can('process')" size="small" type="primary" :icon="Plus" @click="openCreateSeq">新增工序</el-button>
          </div>
          <el-table :data="currentFlow.seqs || []" size="small">
            <el-table-column prop="idx" label="序号" width="70" />
            <el-table-column prop="process_flow_seq_name" label="工序序列名" min-width="150" />
            <el-table-column prop="process_name" label="引用工序" min-width="140" />
            <el-table-column prop="process_version" label="工序版本" width="90" />
            <el-table-column prop="step_source" label="来源" width="100" />
            <el-table-column prop="process_flow_seq_type" label="序列类型" width="110" />
            <el-table-column prop="process_stage_name" label="阶段" width="110" />
            <el-table-column prop="work_layer" label="工作层" width="100" />
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button size="small" link @click="openEditSeq(row)">编辑</el-button>
                <el-button size="small" link type="danger" @click="removeSeq(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 制程内容 tab -->
        <el-tab-pane label="制程内容" name="content">
          <div class="sub-toolbar">
            <span class="muted">制程内容（含分支/返工字段，ProcessFlowContent）</span>
            <el-button v-if="can('process')" size="small" type="primary" :icon="Plus" @click="openCreateContent">新增内容</el-button>
          </div>
          <el-table :data="currentFlow.contents || []" size="small">
            <el-table-column prop="process_flow_seq_name" label="工序序列" min-width="130" />
            <el-table-column prop="process_capability_name" label="制程能力" width="130" />
            <el-table-column prop="recipe_name" label="配方" min-width="150" show-overflow-tooltip />
            <el-table-column prop="lot_sampling_rule" label="抽检规则" width="110" />
            <el-table-column label="跳过/必经" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.is_mandatory_step" type="danger" size="small">必经</el-tag>
                <el-tag v-else-if="row.is_skip_allowed" type="warning" size="small">可跳过</el-tag>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="branch_flow_name" label="分支流程" width="120" />
            <el-table-column prop="rework_flow_name" label="返工流程" width="120" />
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button size="small" link @click="openEditContent(row)">编辑</el-button>
                <el-button size="small" link type="danger" @click="removeContent(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 量测 tab -->
        <el-tab-pane label="量测" name="measure">
          <div class="sub-toolbar">
            <span class="muted">量测项（ProcessFlowMeasure）</span>
            <el-button v-if="can('process')" size="small" type="primary" :icon="Plus" @click="openCreateMeasure">新增量测</el-button>
          </div>
          <el-table :data="currentFlow.measures || []" size="small">
            <el-table-column prop="process_flow_seq_name" label="工序序列" min-width="130" />
            <el-table-column prop="measure_item" label="量测项" width="100" />
            <el-table-column prop="target" label="目标值" width="90" />
            <el-table-column prop="lower_spec_limit" label="下限" width="90" />
            <el-table-column prop="upper_spec_limit" label="上限" width="90" />
            <el-table-column prop="sample_count" label="抽样数" width="90" />
            <el-table-column prop="sample_count_type" label="抽样方式" width="110" />
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button size="small" link @click="openEditMeasure(row)">编辑</el-button>
                <el-button size="small" link type="danger" @click="removeMeasure(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 防污染 tab -->
        <el-tab-pane label="防污染" name="contamination">
          <div class="sub-toolbar">
            <span class="muted">防污染要求（ProcessFlowContamination）</span>
            <el-button v-if="can('process')" size="small" type="primary" :icon="Plus" @click="openCreateContamination">新增</el-button>
          </div>
          <el-table :data="currentFlow.contaminations || []" size="small">
            <el-table-column prop="process_flow_seq_name" label="工序序列" min-width="140" />
            <el-table-column prop="require_contamination_levels" label="要求污染等级" min-width="200" show-overflow-tooltip />
            <el-table-column prop="affect_contamination_level" label="影响污染等级" width="140" />
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button size="small" link @click="openEditContamination(row)">编辑</el-button>
                <el-button size="small" link type="danger" @click="removeContamination(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 流程表单 -->
    <el-dialog v-model="flowDialog" :title="editingFlowId ? '编辑制造流程' : '新增制造流程'" width="640px">
      <el-form ref="flowFormRef" :model="flowForm" :rules="flowRules" label-width="100px">
        <div class="form-grid">
          <el-form-item label="流程名称" prop="process_flow_name"><el-input v-model="flowForm.process_flow_name" :disabled="!!editingFlowId" /></el-form-item>
          <el-form-item label="版本" prop="process_flow_version"><el-input v-model="flowForm.process_flow_version" :disabled="!!editingFlowId" /></el-form-item>
          <el-form-item label="类型1">
            <el-select v-model="flowForm.process_flow_type1">
              <el-option label="主流程" value="Main" />
              <el-option label="子流程" value="Sub" />
            </el-select>
          </el-form-item>
          <el-form-item label="类型2">
            <el-select v-model="flowForm.process_flow_type2">
              <el-option label="生产" value="Production" />
              <el-option label="工程" value="Engineering" />
              <el-option label="监控" value="Monitor" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="flowForm.process_flow_state">
              <el-option label="Active" value="Active" />
              <el-option label="Frozen" value="Frozen" />
              <el-option label="Unfrozen" value="Unfrozen" />
              <el-option label="Invalid" value="Invalid" />
            </el-select>
          </el-form-item>
          <el-form-item label="归属组"><el-input v-model="flowForm.owner_group_name" /></el-form-item>
          <el-form-item label="负责人"><el-input v-model="flowForm.owner" /></el-form-item>
          <el-form-item label="流程组"><el-input v-model="flowForm.process_group_name" /></el-form-item>
          <el-form-item label="描述" class="form-wide"><el-input v-model="flowForm.description" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="flowDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveFlow">保存</el-button>
      </template>
    </el-dialog>

    <!-- 工序 Seq 表单 -->
    <el-dialog v-model="seqDialog" :title="editingSeqId ? '编辑工序' : '新增工序'" width="680px">
      <el-form ref="seqFormRef" :model="seqForm" :rules="seqRules" label-width="110px">
        <div class="form-grid">
          <el-form-item label="序号" prop="idx"><el-input-number v-model="seqForm.idx" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="序列名称" prop="process_flow_seq_name"><el-input v-model="seqForm.process_flow_seq_name" /></el-form-item>
          <el-form-item label="引用工序">
            <el-select v-model="seqForm.process_name" filterable clearable @change="onSeqStepChange">
              <el-option v-for="s in stepOptions" :key="s.process_step_name + '|' + s.process_step_version" :label="`${s.process_step_name} v${s.process_step_version}`" :value="s.process_step_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="工序版本"><el-input v-model="seqForm.process_version" /></el-form-item>
          <el-form-item label="来源">
            <el-select v-model="seqForm.step_source">
              <el-option label="主流程" value="MainFlow" />
              <el-option label="子流程" value="SubFlow" />
            </el-select>
          </el-form-item>
          <el-form-item label="序列类型">
            <el-select v-model="seqForm.process_flow_seq_type">
              <el-option label="工序" value="ProcessStep" />
              <el-option label="子流程" value="SubProcessFlow" />
            </el-select>
          </el-form-item>
          <el-form-item label="分段"><el-input v-model="seqForm.process_group1" /></el-form-item>
          <el-form-item label="工艺层"><el-input v-model="seqForm.process_group2" /></el-form-item>
          <el-form-item label="阶段"><el-input v-model="seqForm.process_stage_name" /></el-form-item>
          <el-form-item label="工作层"><el-input v-model="seqForm.work_layer" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="seqDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveSeq">保存</el-button>
      </template>
    </el-dialog>

    <!-- 制程内容表单 -->
    <el-dialog v-model="contentDialog" :title="editingContentId ? '编辑制程内容' : '新增制程内容'" width="860px">
      <el-form ref="contentFormRef" :model="contentForm" :rules="contentRules" label-width="110px">
        <div class="form-grid">
          <el-form-item label="工序序列" prop="process_flow_seq_name">
            <el-select v-model="contentForm.process_flow_seq_name" filterable>
              <el-option v-for="s in (currentFlow?.seqs || [])" :key="s.process_flow_seq_name" :label="s.process_flow_seq_name" :value="s.process_flow_seq_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="制程能力">
            <el-select v-model="contentForm.process_capability_name" filterable clearable>
              <el-option v-for="c in capOptions" :key="c.process_capability_name" :label="c.process_capability_name" :value="c.process_capability_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="配方名称"><el-input v-model="contentForm.recipe_name" /></el-form-item>
          <el-form-item label="配方描述"><el-input v-model="contentForm.recipe_name_description" /></el-form-item>
          <el-form-item label="DC规格"><el-input v-model="contentForm.dc_spec_name" /></el-form-item>
          <el-form-item label="良率限值"><el-input v-model="contentForm.yield_limit" /></el-form-item>
          <el-form-item label="光罩组"><el-input v-model="contentForm.reticle_group_name" /></el-form-item>
          <el-form-item label="光罩名称"><el-input v-model="contentForm.reticle_name" /></el-form-item>
          <el-form-item label="探针卡"><el-input v-model="contentForm.probe_card_name" /></el-form-item>
          <el-form-item label="抽检规则"><el-input v-model="contentForm.lot_sampling_rule" /></el-form-item>
          <el-form-item label="抽样用户组"><el-input v-model="contentForm.sampling_user_group" /></el-form-item>
          <el-form-item label="分支流程组"><el-input v-model="contentForm.branch_flow_group" /></el-form-item>
          <el-form-item label="分支流程名"><el-input v-model="contentForm.branch_flow_name" /></el-form-item>
          <el-form-item label="返工流程组"><el-input v-model="contentForm.rework_flow_group" /></el-form-item>
          <el-form-item label="返工流程名"><el-input v-model="contentForm.rework_flow_name" /></el-form-item>
          <el-form-item label="晶圆选择规则"><el-input v-model="contentForm.wafer_selection_rule" /></el-form-item>
          <el-form-item label="墨点能力"><el-input v-model="contentForm.ink_able" /></el-form-item>
          <el-form-item label="允许跳过"><el-switch v-model="contentForm.is_skip_allowed" /></el-form-item>
          <el-form-item label="必经工序"><el-switch v-model="contentForm.is_mandatory_step" /></el-form-item>
          <el-form-item label="翻转"><el-switch v-model="contentForm.is_flip" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="contentDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveContent">保存</el-button>
      </template>
    </el-dialog>

    <!-- 量测表单 -->
    <el-dialog v-model="measureDialog" :title="editingMeasureId ? '编辑量测项' : '新增量测项'" width="680px">
      <el-form ref="measureFormRef" :model="measureForm" :rules="measureRules" label-width="110px">
        <div class="form-grid">
          <el-form-item label="工序序列" prop="process_flow_seq_name">
            <el-select v-model="measureForm.process_flow_seq_name" filterable>
              <el-option v-for="s in (currentFlow?.seqs || [])" :key="s.process_flow_seq_name" :label="s.process_flow_seq_name" :value="s.process_flow_seq_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键工序序列"><el-input v-model="measureForm.key_process_flow_seq_name" /></el-form-item>
          <el-form-item label="量测项">
            <el-select v-model="measureForm.measure_item">
              <el-option label="PARTICLE" value="PARTICLE" />
              <el-option label="TH" value="TH" />
              <el-option label="RS" value="RS" />
              <el-option label="CD" value="CD" />
              <el-option label="OL" value="OL" />
              <el-option label="DEFECT" value="DEFECT" />
              <el-option label="T" value="T" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标值"><el-input-number v-model="measureForm.target" controls-position="right" /></el-form-item>
          <el-form-item label="下限"><el-input-number v-model="measureForm.lower_spec_limit" controls-position="right" /></el-form-item>
          <el-form-item label="上限"><el-input-number v-model="measureForm.upper_spec_limit" controls-position="right" /></el-form-item>
          <el-form-item label="抽样数"><el-input-number v-model="measureForm.sample_count" :min="0" controls-position="right" /></el-form-item>
          <el-form-item label="抽样槽位"><el-input v-model="measureForm.sample_slots" /></el-form-item>
          <el-form-item label="抽样方式"><el-input v-model="measureForm.sample_count_type" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="measureDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveMeasure">保存</el-button>
      </template>
    </el-dialog>

    <!-- 防污染表单 -->
    <el-dialog v-model="contaminationDialog" :title="editingContaminationId ? '编辑防污染' : '新增防污染'" width="580px">
      <el-form ref="contaminationFormRef" :model="contaminationForm" :rules="contaminationRules" label-width="120px">
        <div class="form-grid">
          <el-form-item label="工序序列" prop="process_flow_seq_name">
            <el-select v-model="contaminationForm.process_flow_seq_name" filterable>
              <el-option v-for="s in (currentFlow?.seqs || [])" :key="s.process_flow_seq_name" :label="s.process_flow_seq_name" :value="s.process_flow_seq_name" />
            </el-select>
          </el-form-item>
          <el-form-item label="要求污染等级"><el-input v-model="contaminationForm.require_contamination_levels" placeholder="如 1,2,3" /></el-form-item>
          <el-form-item label="影响污染等级"><el-input v-model="contaminationForm.affect_contamination_level" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="contaminationDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveContamination">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  createFlowContent, createFlowContamination, createFlowMeasure, createFlowSeq,
  createProcessFlow, deleteFlowContent, deleteFlowContamination, deleteFlowMeasure,
  deleteFlowSeq, deleteProcessFlow, getProcessCapabilities, getProcessFlow, getProcessFlows,
  getProcessSteps, updateFlowContent, updateFlowContamination, updateFlowMeasure,
  updateFlowSeq, updateProcessFlow,
} from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'

const { can } = useAuth()
const filterState = ref('')
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(
  (params) => getProcessFlows({ ...params, state: filterState.value }),
)

const currentFlow = ref<any>(null)
const activeTab = ref('seq')
const capOptions = ref<any[]>([])
const stepOptions = ref<any[]>([])
const saving = ref(false)

function stateTag(state: string) {
  const map: Record<string, string> = { Active: 'success', Frozen: 'warning', Unfrozen: '', Invalid: 'info' }
  return map[state] || 'info'
}

async function reloadDetail() {
  if (!currentFlow.value) return
  const detail = await getProcessFlow(currentFlow.value.id)
  currentFlow.value = detail
}

function onSelectFlow(row: any) {
  if (!row) return
  currentFlow.value = row
  activeTab.value = 'seq'
  loadDetail()
}

async function loadDetail() {
  if (!currentFlow.value) return
  try {
    const detail = await getProcessFlow(currentFlow.value.id)
    currentFlow.value = detail
  } catch (e: any) {
    ElMessage.error('加载详情失败')
  }
}

// ===== 流程 CRUD =====
const flowFormRef = ref<FormInstance>()
const flowDialog = ref(false)
const editingFlowId = ref<number | null>(null)
const emptyFlow = {
  process_flow_name: '', process_flow_version: '001', description: '', process_flow_type1: 'Main',
  process_flow_type2: 'Production', process_flow_state: 'Active', owner_group_name: '',
  owner: '', process_group_name: '',
}
const flowForm = ref<any>({ ...emptyFlow })
const flowRules: FormRules = {
  process_flow_name: [{ required: true, message: '请输入流程名称', trigger: 'blur' }],
  process_flow_version: [{ required: true, message: '请输入版本', trigger: 'blur' }],
}
function openCreateFlow() {
  editingFlowId.value = null
  flowForm.value = { ...emptyFlow }
  flowDialog.value = true
}
function openEditFlow(row: any) {
  editingFlowId.value = row.id
  flowForm.value = { ...row }
  flowDialog.value = true
}
async function saveFlow() {
  if (!flowFormRef.value) return
  await flowFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      editingFlowId.value ? await updateProcessFlow(editingFlowId.value, flowForm.value) : await createProcessFlow(flowForm.value)
      ElMessage.success('已保存')
      flowDialog.value = false
      await loadData()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}
async function removeFlow(row: any) {
  await ElMessageBox.confirm('确认删除此制造流程？', '删除确认', { type: 'warning' })
  try {
    await deleteProcessFlow(row.id)
    ElMessage.success('已删除')
    if (currentFlow.value?.id === row.id) currentFlow.value = null
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

// ===== 工序 Seq CRUD =====
const seqFormRef = ref<FormInstance>()
const seqDialog = ref(false)
const editingSeqId = ref<number | null>(null)
const emptySeq = {
  idx: 0, step_source: 'MainFlow', process_flow_seq_name: '', process_name: '', process_version: '',
  process_flow_seq_type: 'ProcessStep', process_group1: '', process_group2: '', process_stage_name: '', work_layer: '',
}
const seqForm = ref<any>({ ...emptySeq })
const seqRules: FormRules = {
  process_flow_seq_name: [{ required: true, message: '请输入序列名称', trigger: 'blur' }],
}
function openCreateSeq() {
  editingSeqId.value = null
  seqForm.value = { ...emptySeq }
  seqDialog.value = true
}
function openEditSeq(row: any) {
  editingSeqId.value = row.id
  seqForm.value = { ...row }
  seqDialog.value = true
}
function onSeqStepChange(name: string) {
  const step = stepOptions.value.find((s) => s.process_step_name === name)
  if (step) {
    seqForm.value.process_version = step.process_step_version
    if (step.process_stage_name) seqForm.value.process_stage_name = step.process_stage_name
  }
}
async function saveSeq() {
  if (!seqFormRef.value || !currentFlow.value) return
  await seqFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      editingSeqId.value ? await updateFlowSeq(editingSeqId.value, seqForm.value) : await createFlowSeq(currentFlow.value.id, seqForm.value)
      ElMessage.success('已保存')
      seqDialog.value = false
      await reloadDetail()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}
async function removeSeq(row: any) {
  await ElMessageBox.confirm('确认删除此工序？', '删除确认', { type: 'warning' })
  try {
    await deleteFlowSeq(row.id)
    ElMessage.success('已删除')
    await reloadDetail()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

// ===== 制程内容 CRUD =====
const contentFormRef = ref<FormInstance>()
const contentDialog = ref(false)
const editingContentId = ref<number | null>(null)
const emptyContent = {
  process_flow_seq_name: '', process_capability_name: '', recipe_name: '', recipe_name_description: '',
  dc_spec_name: '', yield_limit: '', reticle_group_name: '', reticle_name: '', probe_card_name: '',
  lot_sampling_rule: '', is_skip_allowed: false, is_mandatory_step: false, sampling_user_group: '',
  is_flip: false, branch_flow_group: '', branch_flow_name: '', rework_flow_group: '', rework_flow_name: '',
  wafer_selection_rule: '', ink_able: '',
}
const contentForm = ref<any>({ ...emptyContent })
const contentRules: FormRules = {
  process_flow_seq_name: [{ required: true, message: '请选择工序序列', trigger: 'change' }],
}
function openCreateContent() {
  editingContentId.value = null
  contentForm.value = { ...emptyContent }
  contentDialog.value = true
}
function openEditContent(row: any) {
  editingContentId.value = row.id
  contentForm.value = { ...row }
  contentDialog.value = true
}
async function saveContent() {
  if (!contentFormRef.value || !currentFlow.value) return
  await contentFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      editingContentId.value ? await updateFlowContent(editingContentId.value, contentForm.value) : await createFlowContent(currentFlow.value.id, contentForm.value)
      ElMessage.success('已保存')
      contentDialog.value = false
      await reloadDetail()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}
async function removeContent(row: any) {
  await ElMessageBox.confirm('确认删除此制程内容？', '删除确认', { type: 'warning' })
  try {
    await deleteFlowContent(row.id)
    ElMessage.success('已删除')
    await reloadDetail()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

// ===== 量测 CRUD =====
const measureFormRef = ref<FormInstance>()
const measureDialog = ref(false)
const editingMeasureId = ref<number | null>(null)
const emptyMeasure = {
  process_flow_seq_name: '', key_process_flow_seq_name: '', measure_item: '', target: null,
  lower_spec_limit: null, upper_spec_limit: null, sample_count: null, sample_slots: '', sample_count_type: '',
}
const measureForm = ref<any>({ ...emptyMeasure })
const measureRules: FormRules = {
  process_flow_seq_name: [{ required: true, message: '请选择工序序列', trigger: 'change' }],
}
function openCreateMeasure() {
  editingMeasureId.value = null
  measureForm.value = { ...emptyMeasure }
  measureDialog.value = true
}
function openEditMeasure(row: any) {
  editingMeasureId.value = row.id
  measureForm.value = { ...row }
  measureDialog.value = true
}
async function saveMeasure() {
  if (!measureFormRef.value || !currentFlow.value) return
  await measureFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      editingMeasureId.value ? await updateFlowMeasure(editingMeasureId.value, measureForm.value) : await createFlowMeasure(currentFlow.value.id, measureForm.value)
      ElMessage.success('已保存')
      measureDialog.value = false
      await reloadDetail()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}
async function removeMeasure(row: any) {
  await ElMessageBox.confirm('确认删除此量测项？', '删除确认', { type: 'warning' })
  try {
    await deleteFlowMeasure(row.id)
    ElMessage.success('已删除')
    await reloadDetail()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

// ===== 防污染 CRUD =====
const contaminationFormRef = ref<FormInstance>()
const contaminationDialog = ref(false)
const editingContaminationId = ref<number | null>(null)
const emptyContamination = { process_flow_seq_name: '', require_contamination_levels: '', affect_contamination_level: '' }
const contaminationForm = ref<any>({ ...emptyContamination })
const contaminationRules: FormRules = {
  process_flow_seq_name: [{ required: true, message: '请选择工序序列', trigger: 'change' }],
}
function openCreateContamination() {
  editingContaminationId.value = null
  contaminationForm.value = { ...emptyContamination }
  contaminationDialog.value = true
}
function openEditContamination(row: any) {
  editingContaminationId.value = row.id
  contaminationForm.value = { ...row }
  contaminationDialog.value = true
}
async function saveContamination() {
  if (!contaminationFormRef.value || !currentFlow.value) return
  await contaminationFormRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      editingContaminationId.value ? await updateFlowContamination(editingContaminationId.value, contaminationForm.value) : await createFlowContamination(currentFlow.value.id, contaminationForm.value)
      ElMessage.success('已保存')
      contaminationDialog.value = false
      await reloadDetail()
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}
async function removeContamination(row: any) {
  await ElMessageBox.confirm('确认删除此防污染记录？', '删除确认', { type: 'warning' })
  try {
    await deleteFlowContamination(row.id)
    ElMessage.success('已删除')
    await reloadDetail()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(async () => {
  await loadData()
  const [capRes, stepRes] = await Promise.all([getProcessCapabilities(), getProcessSteps({ page: 1, page_size: 500 })])
  capOptions.value = capRes.items ?? []
  stepOptions.value = stepRes.items ?? []
})
</script>

<style scoped>
.process-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.detail-panel {
  min-height: 360px;
}
.detail-tabs {
  padding: 0 16px 12px;
}
.sub-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
</style>
