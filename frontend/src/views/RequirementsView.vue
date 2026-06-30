<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>需求规格池</strong>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索需求编号/标题" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('requirement')" type="primary" :icon="Plus" @click="openCreate">新建需求</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" row-key="id" :expand-row-keys="expandedRowKeys" @expand-change="onExpandChange" height="100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="bom-detail-expand">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="来源">{{ row.source }}</el-descriptions-item>
                <el-descriptions-item label="产品">{{ row.product_model }}</el-descriptions-item>
                <el-descriptions-item label="负责人">{{ row.owner }}</el-descriptions-item>
                <el-descriptions-item label="状态">{{ row.status }}</el-descriptions-item>
                <el-descriptions-item label="验收准则">{{ row.acceptance_criteria }}</el-descriptions-item>
              </el-descriptions>
              <div class="trace-box section-gap">
                <div>
                  <span>输入</span>
                  <strong>{{ row.source }}</strong>
                </div>
                <el-icon><Right /></el-icon>
                <div>
                  <span>规格</span>
                  <strong>{{ row.category }}</strong>
                </div>
                <el-icon><Right /></el-icon>
                <div>
                  <span>输出</span>
                  <strong>BOM / 工艺 / 文档 / 项目</strong>
                </div>
              </div>
              <div v-loading="traceLoading" class="section-gap">
                <div v-if="!trace" class="muted small-gap">点击下方按钮加载完整追溯链路</div>
                <template v-else>
                  <el-tabs class="trace-tabs">
                    <el-tab-pane :label="`产品 (${trace.product ? 1 : 0})`">
                      <el-table v-if="trace.product" :data="[trace.product]" size="small">
                        <el-table-column prop="model" label="型号" width="140" />
                        <el-table-column prop="name" label="名称" />
                        <el-table-column prop="lifecycle" label="生命周期" width="120" />
                        <el-table-column prop="version" label="版本" width="80" />
                        <el-table-column prop="readiness" label="完整度" width="90" />
                      </el-table>
                      <div v-else class="muted">未关联产品</div>
                    </el-tab-pane>
                    <el-tab-pane :label="`BOM (${(trace.boms || []).length})`">
                      <el-table :data="trace.boms || []" size="small">
                        <el-table-column prop="type" label="类型" width="100" />
                        <el-table-column prop="version" label="版本" width="100" />
                        <el-table-column prop="status" label="状态" width="120" />
                        <el-table-column prop="owner" label="负责人" width="120" />
                        <el-table-column prop="release_date" label="发布日期" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`工程变更 (${(trace.changes || []).length})`">
                      <el-table :data="trace.changes || []" size="small">
                        <el-table-column prop="change_no" label="变更单" width="180" />
                        <el-table-column prop="title" label="标题" />
                        <el-table-column prop="priority" label="优先级" width="100" />
                        <el-table-column prop="status" label="状态" width="120" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`文档 (${(trace.documents || []).length})`">
                      <el-table :data="trace.documents || []" size="small">
                        <el-table-column prop="doc_no" label="文档编号" width="180" />
                        <el-table-column prop="title" label="标题" />
                        <el-table-column prop="category" label="分类" width="120" />
                        <el-table-column prop="version" label="版本" width="90" />
                        <el-table-column prop="status" label="状态" width="100" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`工艺路线 (${(trace.routes || []).length})`">
                      <el-table :data="trace.routes || []" size="small">
                        <el-table-column prop="route_no" label="路线编号" width="160" />
                        <el-table-column prop="name" label="名称" />
                        <el-table-column prop="version" label="版本" width="90" />
                        <el-table-column prop="status" label="状态" width="120" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`项目 (${(trace.projects || []).length})`">
                      <el-table :data="trace.projects || []" size="small">
                        <el-table-column prop="project_no" label="项目编号" width="160" />
                        <el-table-column prop="name" label="项目名称" />
                        <el-table-column prop="phase" label="阶段" width="120" />
                        <el-table-column prop="progress" label="进度" width="90" />
                        <el-table-column prop="owner" label="负责人" width="120" />
                        <el-table-column prop="risk_level" label="风险" width="100" />
                      </el-table>
                    </el-tab-pane>
                  </el-tabs>
                </template>
              </div>
              <AttachmentPanel object-type="Requirement" :object-id="row.id" :can-edit="can('requirement')" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="req_no" label="需求编号" width="190" fixed />
        <el-table-column prop="title" label="需求标题" min-width="260" />
        <el-table-column prop="product_model" label="产品型号" width="130" />
        <el-table-column prop="category" label="分类" width="110" />
        <el-table-column prop="priority" label="优先级" width="90">
          <template #default="{ row }"><el-tag size="small" :type="row.priority === '高' ? 'danger' : 'warning'">{{ row.priority }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" :disabled="!can('requirement')" @click.stop="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" :disabled="!can('requirement') || ['已确认', '已发布'].includes(row.status)" @click.stop="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑需求' : '新建需求'" width="720px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="需求编号"><el-input v-model="form.req_no" /></el-form-item>
          <el-form-item label="关联产品">
            <el-select v-model="form.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="来源">
            <el-select v-model="form.source" filterable>
              <el-option v-for="o in requirementSourceOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="form.category" filterable>
              <el-option v-for="o in requirementCategoryOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="form.priority">
              <el-option v-for="o in priorityOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option v-for="o in requirementStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="标题" class="form-wide"><el-input v-model="form.title" /></el-form-item>
          <el-form-item label="验收准则" class="form-wide"><el-input v-model="form.acceptance_criteria" type="textarea" :rows="3" /></el-form-item>
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
import { Plus, Right, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createRequirement, deleteRequirement, getProducts, getRequirementTrace, getRequirements, updateRequirement } from '../api'
import { useAuth } from '../auth'
import AttachmentPanel from '../components/AttachmentPanel.vue'
import UserSelect from '../components/UserSelect.vue'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const { can, currentUser, refreshSession } = useAuth()
const requirementSourceOptions = useDictionary('DICT_REQUIREMENT_SOURCE').options
const requirementCategoryOptions = useDictionary('DICT_REQUIREMENT_CATEGORY').options
const priorityOptions = useDictionary('DICT_PRIORITY').options
const requirementStatusOptions = useDictionary('DICT_REQUIREMENT_STATUS').options
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getRequirements)
const selected = ref<any>()
const expandedRowKeys = ref<number[]>([])
const products = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const trace = ref<any>(null)
const traceLoading = ref(false)
const emptyForm = { product_id: undefined, req_no: '', source: '', category: '', title: '', priority: '中', status: '草稿', owner: '', acceptance_criteria: '' }
const form = ref<any>({ ...emptyForm })

async function loadTrace(id: number) {
  traceLoading.value = true
  try {
    trace.value = await getRequirementTrace(id)
  } catch (e) {
    trace.value = null
  } finally {
    traceLoading.value = false
  }
}

async function loadRequirements() {
  await loadData()
  selected.value = (items.value || [])[0]
  expandedRowKeys.value = selected.value ? [selected.value.id] : []
  if (selected.value?.id) {
    await loadTrace(selected.value.id)
  }
}

function openCreate() {
  if (!can('requirement')) return
  editingId.value = null
  form.value = { ...emptyForm, product_id: products.value[0]?.id, owner: currentUser.value?.display_name || '' }
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('requirement')) return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function onExpandChange(row: any, expandedRows: any[]) {
  const isExpanded = expandedRows.some((r: any) => r.id === row.id)
  if (isExpanded) {
    expandedRowKeys.value = [row.id]
    selected.value = row
    if (row?.id) await loadTrace(row.id)
  } else {
    expandedRowKeys.value = []
    selected.value = null
    trace.value = null
  }
}

async function save() {
  if (!can('requirement')) return
  if (editingId.value) {
    await updateRequirement(editingId.value, form.value)
  } else {
    await createRequirement(form.value)
  }
  ElMessage.success('需求已保存')
  dialogVisible.value = false
  await loadRequirements()
}

async function remove(row: any) {
  if (!can('requirement')) return
  await ElMessageBox.confirm(`确认删除需求 ${row.req_no}？已确认需求会被后端阻止删除。`, '删除确认', { type: 'warning' })
  await deleteRequirement(row.id)
  ElMessage.success('需求已删除')
  await loadRequirements()
}

onMounted(async () => {
  await refreshSession()
  products.value = (await getProducts()).items
  await loadRequirements()
})
</script>
