<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>工程变更</strong>
          <span class="muted"> · ECR / ECN / ECA 变更闭环</span>
        </div>
        <el-button v-if="can('change')" type="primary" :icon="Plus" @click="openCreate">新建变更</el-button>
      </div>
      <el-table :data="changes" highlight-current-row @current-change="selectChange" height="680">
        <el-table-column prop="change_no" label="变更单号" width="180" fixed />
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="product_model" label="型号" width="130" />
        <el-table-column prop="change_type" label="类型" width="110" />
        <el-table-column prop="priority" label="优先级" width="90" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="!can('change') || !['草稿', '已驳回'].includes(row.status)" @click.stop="openEdit(row)">编辑</el-button>
            <el-button size="small" type="primary" :disabled="!can('change') || !['草稿', '已驳回'].includes(row.status)" @click.stop="submit(row)">提交</el-button>
            <el-button size="small" type="danger" :disabled="!can('change') || row.status !== '草稿'" @click.stop="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="panel">
      <div class="panel-title">{{ selected?.change_no || '变更详情' }}</div>
      <template v-if="selected">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="产品">{{ selected.product_model }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ selected.owner }}</el-descriptions-item>
          <el-descriptions-item label="提交日期">{{ selected.submitted_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ selected.status }}</el-descriptions-item>
          <el-descriptions-item label="变更原因" :span="2">{{ selected.reason }}</el-descriptions-item>
          <el-descriptions-item label="变更前" :span="2">{{ selected.before_desc }}</el-descriptions-item>
          <el-descriptions-item label="变更后" :span="2">{{ selected.after_desc }}</el-descriptions-item>
        </el-descriptions>
        <div class="section-gap">
          <div class="toolbar compact-toolbar">
            <div class="panel-title">影响分析</div>
            <div class="toolbar-actions">
              <el-button size="small" :disabled="!can('change') || selected.status === '已关闭'" @click="runAnalyze">重新分析</el-button>
              <el-button size="small" :disabled="!can('change') || selected.status === '已关闭'" @click="openImpactCreate">新增影响</el-button>
            </div>
          </div>
          <el-table :data="selected.impacts" size="small">
            <el-table-column prop="type" label="对象" width="100" />
            <el-table-column prop="target" label="范围" />
            <el-table-column prop="risk" label="风险" width="80" />
            <el-table-column prop="action" label="动作" />
            <el-table-column label="操作" width="130">
              <template #default="{ row }">
                <el-button size="small" :disabled="!can('change') || selected.status === '已关闭'" @click="openImpactEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" :disabled="!can('change') || selected.status === '已关闭'" @click="removeImpact(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="section-gap">
          <div class="panel-title">审批流程</div>
          <el-steps direction="vertical" :active="2" finish-status="success">
            <el-step v-for="item in selected.approvals" :key="item.step" :title="item.step" :description="`${item.approver} · ${item.status} ${item.comment}`" />
          </el-steps>
        </div>
        <div class="section-gap">
          <div class="toolbar compact-toolbar">
            <div class="panel-title">ECN / ECA 执行动作</div>
            <div class="toolbar-actions">
              <el-button size="small" :disabled="!can('change') || selected.status === '已关闭'" @click="openActionCreate">新增动作</el-button>
            </div>
          </div>
          <el-table :data="selected.actions" size="small">
            <el-table-column prop="action_no" label="动作编号" width="190" />
            <el-table-column prop="action_type" label="动作" width="100" />
            <el-table-column prop="target_type" label="对象类型" width="90" />
            <el-table-column prop="target_object" label="对象" min-width="180" />
            <el-table-column prop="target_version" label="当前版本" width="90" />
            <el-table-column prop="effectivity_type" label="生效方式" width="100" />
            <el-table-column prop="effectivity_scope" label="生效范围" width="110" />
            <el-table-column prop="effective_date" label="生效日期" width="110" />
            <el-table-column prop="effective_batch" label="生效批次" width="140" />
            <el-table-column prop="generated_object_no" label="生成对象" min-width="160" show-overflow-tooltip />
            <el-table-column prop="department" label="部门" width="110" />
            <el-table-column prop="owner" label="负责人" width="90" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === '进行中' ? 'warning' : row.status === '待处理' ? 'info' : 'success'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="due_date" label="截止" width="110" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button size="small" :disabled="!can('change') || row.status === '已完成'" @click="openActionEdit(row)">编辑</el-button>
                <el-button size="small" type="primary" :disabled="!can('change') || row.status === '已完成'" @click="closeAction(row)">关闭</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="section-gap">
          <div class="panel-title">版本归档</div>
          <el-table :data="revisionArchive" size="small" empty-text="暂无升版记录">
            <el-table-column prop="target_type" label="对象类型" width="90" />
            <el-table-column prop="source_object" label="来源对象" min-width="180" show-overflow-tooltip />
            <el-table-column prop="source_version" label="来源版本" width="90" />
            <el-table-column label="生成对象" min-width="170">
              <template #default="{ row }">
                <a v-if="row.generated_url" href="javascript:void(0)" class="archive-link" @click="navigateTo(row.generated_url)">{{ row.generated_object_no }}</a>
                <span v-else>{{ row.generated_object_no }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="effectivity_type" label="生效方式" width="100" />
            <el-table-column prop="effectivity_scope" label="生效范围" width="110" />
            <el-table-column prop="effective_date" label="生效日期" width="110" />
            <el-table-column prop="effective_batch" label="生效批次" width="140" />
            <el-table-column prop="owner" label="负责人" width="90" />
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="showArchiveDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>
    </div>

    <el-dialog v-model="archiveDialogVisible" title="版本归档详情" width="640px">
      <template v-if="archiveDetail.action_no">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="动作编号">{{ archiveDetail.action_no }}</el-descriptions-item>
          <el-descriptions-item label="动作类型">{{ archiveDetail.action_type }}</el-descriptions-item>
          <el-descriptions-item label="来源对象">{{ archiveDetail.source_object }}</el-descriptions-item>
          <el-descriptions-item label="来源版本">{{ archiveDetail.source_version }}</el-descriptions-item>
          <el-descriptions-item label="生成对象">{{ archiveDetail.generated_object_no }}</el-descriptions-item>
          <el-descriptions-item label="对象类型">{{ archiveDetail.target_type }}</el-descriptions-item>
          <el-descriptions-item label="生效方式">{{ archiveDetail.effectivity_type }}</el-descriptions-item>
          <el-descriptions-item label="生效范围">{{ archiveDetail.effectivity_scope }}</el-descriptions-item>
          <el-descriptions-item label="生效日期">{{ archiveDetail.effective_date }}</el-descriptions-item>
          <el-descriptions-item label="生效批次">{{ archiveDetail.effective_batch }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ archiveDetail.owner }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ archiveDetail.status }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="archiveDetail.generated_url" style="margin-top:16px;text-align:center">
          <el-button type="primary" @click="navigateTo(archiveDetail.generated_url)">查看生成对象</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑变更' : '新建变更'" width="760px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="变更单号"><el-input v-model="form.change_no" /></el-form-item>
          <el-form-item label="关联产品">
            <el-select v-model="form.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="变更类型">
            <el-select v-model="form.change_type">
              <el-option label="PR 问题报告" value="PR" />
              <el-option label="ECR 变更申请" value="ECR" />
              <el-option label="ECO 变更指令" value="ECO" />
              <el-option label="ECN 变更通知" value="ECN" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="form.priority">
              <el-option label="高" value="高" />
              <el-option label="中" value="中" />
              <el-option label="低" value="低" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="草稿" value="草稿" />
              <el-option label="审批中" value="审批中" />
              <el-option label="执行中" value="执行中" />
              <el-option label="已关闭" value="已关闭" />
            </el-select>
          </el-form-item>
          <el-form-item label="标题" class="form-wide"><el-input v-model="form.title" /></el-form-item>
          <el-form-item label="变更原因" class="form-wide"><el-input v-model="form.reason" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="变更前" class="form-wide"><el-input v-model="form.before_desc" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="变更后" class="form-wide"><el-input v-model="form.after_desc" type="textarea" :rows="3" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="impactDialogVisible" :title="editingImpactId ? '编辑影响项' : '新增影响项'" width="620px">
      <el-form :model="impactForm" label-width="86px">
        <el-form-item label="对象类型"><el-input v-model="impactForm.impact_type" /></el-form-item>
        <el-form-item label="影响范围"><el-input v-model="impactForm.target" /></el-form-item>
        <el-form-item label="风险">
          <el-select v-model="impactForm.risk">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理动作"><el-input v-model="impactForm.action" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="impactDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveImpact">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="actionDialogVisible" :title="editingActionId ? '编辑 ECA 动作' : '新增 ECA 动作'" width="760px">
      <el-form :model="actionForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="动作编号"><el-input v-model="actionForm.action_no" placeholder="留空自动生成" /></el-form-item>
          <el-form-item label="动作类型"><el-input v-model="actionForm.action_type" /></el-form-item>
          <el-form-item label="对象类型">
            <el-select v-model="actionForm.target_type" clearable>
              <el-option label="BOM" value="BOM" />
              <el-option label="文档" value="文档" />
              <el-option label="工艺路线" value="工艺路线" />
              <el-option label="通知" value="通知" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="对象ID"><el-input-number v-model="actionForm.target_id" :min="1" controls-position="right" /></el-form-item>
          <el-form-item label="当前版本"><el-input v-model="actionForm.target_version" /></el-form-item>
          <el-form-item label="生效方式">
            <el-select v-model="actionForm.effectivity_type">
              <el-option label="日期" value="日期" />
              <el-option label="批次" value="批次" />
              <el-option label="日期+批次" value="日期+批次" />
            </el-select>
          </el-form-item>
          <el-form-item label="生效范围"><el-input v-model="actionForm.effectivity_scope" /></el-form-item>
          <el-form-item label="生效日期"><el-input v-model="actionForm.effective_date" /></el-form-item>
          <el-form-item label="生效批次"><el-input v-model="actionForm.effective_batch" placeholder="LOT / Wafer / 试产批次" /></el-form-item>
          <el-form-item label="生成对象"><el-input v-model="actionForm.generated_object_no" disabled /></el-form-item>
          <el-form-item label="对象" class="form-wide"><el-input v-model="actionForm.target_object" /></el-form-item>
          <el-form-item label="部门"><el-input v-model="actionForm.department" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="actionForm.owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="actionForm.status">
              <el-option label="待处理" value="待处理" />
              <el-option label="进行中" value="进行中" />
              <el-option label="已完成" value="已完成" />
            </el-select>
          </el-form-item>
          <el-form-item label="截止日期"><el-input v-model="actionForm.due_date" /></el-form-item>
          <el-form-item label="结果" class="form-wide"><el-input v-model="actionForm.result" type="textarea" :rows="3" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAction">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  analyzeChange,
  closeChangeAction,
  createChange,
  createChangeAction,
  createChangeImpact,
  deleteChange,
  deleteChangeImpact,
  getChangeRevisionArchive,
  getChanges,
  getProducts,
  submitChange,
  updateChange,
  updateChangeAction,
  updateChangeImpact,
} from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'

const loading = ref(true)
const router = useRouter()
const { can, currentUser, refreshSession } = useAuth()
const changes = ref<any[]>([])
const products = ref<any[]>([])
const selected = ref<any>()
const revisionArchive = ref<any[]>([])
const archiveDialogVisible = ref(false)
const archiveDetail = ref<any>({})
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { product_id: undefined, change_no: '', title: '', change_type: 'ECR', reason: '', status: '草稿', priority: '中', owner: '', before_desc: '', after_desc: '' }
const form = ref<any>({ ...emptyForm })
const impactDialogVisible = ref(false)
const editingImpactId = ref<number | null>(null)
const emptyImpact = { impact_type: '', target: '', risk: '中', action: '' }
const impactForm = ref<any>({ ...emptyImpact })
const actionDialogVisible = ref(false)
const editingActionId = ref<number | null>(null)
const emptyAction = {
  action_no: '',
  action_type: '资料更新',
  target_type: '',
  target_id: undefined,
  target_version: '',
  target_object: '',
  effectivity_type: '日期',
  effectivity_scope: '',
  effective_date: '',
  effective_batch: '',
  generated_object_no: '',
  department: '',
  owner: '',
  status: '待处理',
  due_date: '',
  result: '',
}
const actionForm = ref<any>({ ...emptyAction })

function todayText() {
  return new Date().toISOString().slice(0, 10)
}

function navigateTo(url: string) {
  router.push(url)
}

function showArchiveDetail(row: any) {
  archiveDetail.value = row
  archiveDialogVisible.value = true
}

async function loadChanges(selectedId?: number) {
  changes.value = await getChanges()
  selected.value = changes.value.find((item) => item.id === selectedId) || changes.value[0]
  revisionArchive.value = selected.value ? await getChangeRevisionArchive(selected.value.id) : []
}

async function selectChange(row: any) {
  selected.value = row
  revisionArchive.value = row ? await getChangeRevisionArchive(row.id) : []
}

function openCreate() {
  if (!can('change')) return
  editingId.value = null
  const product = products.value[0]
  form.value = {
    ...emptyForm,
    product_id: product?.id,
    change_no: product ? `ECR-${product.model}-${String(changes.value.length + 1).padStart(3, '0')}` : '',
    owner: currentUser.value?.display_name || '',
  }
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('change') || !['草稿', '已驳回'].includes(row.status)) return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!can('change')) return
  if (editingId.value) {
    await updateChange(editingId.value, form.value)
    ElMessage.success('变更已更新')
    await loadChanges(editingId.value)
  } else {
    const next = await createChange(form.value)
    ElMessage.success('变更已创建')
    await loadChanges(next.id)
  }
  dialogVisible.value = false
}

async function submit(row: any) {
  if (!can('change') || !['草稿', '已驳回'].includes(row.status)) return
  await submitChange(row.id)
  ElMessage.success('变更已提交审批')
  await loadChanges(row.id)
}

async function remove(row: any) {
  if (!can('change') || row.status !== '草稿') return
  await ElMessageBox.confirm(`确认删除变更 ${row.change_no}？只有草稿允许删除。`, '删除确认', { type: 'warning' })
  await deleteChange(row.id)
  ElMessage.success('变更已删除')
  await loadChanges()
}

async function runAnalyze() {
  if (!selected.value || !can('change')) return
  const next = await analyzeChange(selected.value.id)
  ElMessage.success('影响分析已生成')
  await loadChanges(next.id)
}

function openImpactCreate() {
  if (!selected.value || !can('change')) return
  editingImpactId.value = null
  impactForm.value = { ...emptyImpact }
  impactDialogVisible.value = true
}

function openImpactEdit(row: any) {
  if (!can('change')) return
  editingImpactId.value = row.id
  impactForm.value = { impact_type: row.impact_type || row.type, target: row.target, risk: row.risk, action: row.action }
  impactDialogVisible.value = true
}

async function saveImpact() {
  if (!selected.value || !can('change')) return
  if (editingImpactId.value) {
    await updateChangeImpact(editingImpactId.value, impactForm.value)
  } else {
    await createChangeImpact(selected.value.id, impactForm.value)
  }
  ElMessage.success('影响项已保存')
  impactDialogVisible.value = false
  await loadChanges(selected.value.id)
}

async function removeImpact(row: any) {
  if (!can('change')) return
  await deleteChangeImpact(row.id)
  ElMessage.success('影响项已删除')
  await loadChanges(selected.value?.id)
}

function openActionCreate() {
  if (!selected.value || !can('change')) return
  editingActionId.value = null
  actionForm.value = { ...emptyAction, effective_date: todayText(), owner: currentUser.value?.display_name || '' }
  actionDialogVisible.value = true
}

function openActionEdit(row: any) {
  if (!can('change')) return
  editingActionId.value = row.id
  actionForm.value = { ...row }
  actionDialogVisible.value = true
}

async function saveAction() {
  if (!selected.value || !can('change')) return
  const effectivityType = actionForm.value.effectivity_type || '日期'
  if (effectivityType.includes('日期') && !actionForm.value.effective_date) {
    ElMessage.warning('请填写生效日期')
    return
  }
  if (effectivityType.includes('批次') && !actionForm.value.effective_batch) {
    ElMessage.warning('请填写生效批次')
    return
  }
  if (editingActionId.value) {
    await updateChangeAction(editingActionId.value, actionForm.value)
  } else {
    await createChangeAction(selected.value.id, actionForm.value)
  }
  ElMessage.success('ECA 动作已保存')
  actionDialogVisible.value = false
  await loadChanges(selected.value.id)
}

async function closeAction(row: any) {
  if (!can('change')) return
  const { value } = await ElMessageBox.prompt('请输入执行结果', '关闭 ECA 动作', {
    inputValue: row.result || '已完成并归档',
    confirmButtonText: '确认',
    cancelButtonText: '取消',
  })
  const next = await closeChangeAction(row.id, { acted_by: currentUser.value?.display_name || '系统用户', result: value })
  ElMessage.success(next.closed_change ? 'ECA 已全部关闭，变更已关闭' : 'ECA 动作已关闭')
  await loadChanges(selected.value?.id)
}

onMounted(async () => {
  await refreshSession()
  products.value = await getProducts()
  await loadChanges()
  loading.value = false
})
</script>

<style scoped>
.archive-link {
  color: var(--color-primary, rgb(22, 93, 255));
  text-decoration: none;
  font-weight: 500;
}
.archive-link:hover {
  text-decoration: underline;
}
</style>
