<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>文档中心</strong><span class="muted"> · 规格书、工艺文件、测试报告、可靠性资料</span></div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索文档编号/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('document')" type="primary" :icon="Upload" @click="openCreate">登记文档</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" @sort-change="onSortChange" @expand-change="onExpandChange">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="document-files-panel">
              <div class="document-files-header">
                <strong>文档文件与附件</strong>
              </div>
              <el-table :data="fileRowsCache[row.id] || []" size="small" max-height="300" v-loading="!!fileRowsLoading[row.id]">
                <el-table-column label="文件名" min-width="180">
                  <template #default="{ row: fileRow }">
                    <el-tag v-if="fileRow.is_main" size="small" type="primary">主文件</el-tag>
                    <el-tag v-else size="small" type="info">附件</el-tag>
                    <span class="file-name">{{ fileRow.file_name }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="大小" width="90">
                  <template #default="{ row: fileRow }">{{ formatFileSize(fileRow.file_size) }}</template>
                </el-table-column>
                <el-table-column prop="uploaded_by" label="上传人" width="100" />
                <el-table-column prop="uploaded_at" label="上传时间" width="140" />
                <el-table-column label="操作" width="130" fixed="right">
                  <template #default="{ row: fileRow }">
                    <div class="row-actions">
                      <el-button size="small" @click="fileRow.is_main ? download(row) : downloadAttachmentFile(fileRow)">下载</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <div class="attachment-upload-bar" v-if="can('document') && row.status === '编制中'">
                <el-upload :show-file-list="false" :before-upload="(file: File) => handleAttachmentUpload(file, row.id)">
                  <el-button size="small">上传附件</el-button>
                </el-upload>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="doc_no" label="文档编号" width="170" fixed />
        <el-table-column prop="title" label="文档名称" min-width="200" />
        <el-table-column prop="product_model" label="产品型号" width="120" />
        <el-table-column prop="category" label="分类" width="110" />
        <el-table-column prop="version" label="版本" width="100" sortable="custom" />
        <el-table-column prop="status" label="文件状态" width="120" sortable="custom">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="approval_status" label="签核状态" width="120" sortable="custom">
          <template #default="{ row }">
            <el-tag size="small" :type="approvalTagType(row.approval_status)">{{ row.approval_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="80" />
        <el-table-column label="附件" width="140">
          <template #default="{ row }">
            <span v-if="row.file_name" class="file-badge">{{ row.file_name }}</span>
            <span v-else class="muted">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="110" sortable="custom" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" :disabled="!can('document') || row.status === '已发布'" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="primary" :disabled="!can(['approval', 'document']) || row.status === '已发布'" @click="approve(row)">发布</el-button>
              <el-button size="small" :disabled="!row.file_name" @click="download(row)">下载</el-button>
              <el-dropdown trigger="click" @command="(cmd: string) => handleDocAction(cmd, row)">
                <el-button size="small" class="more-btn">更多</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="submit" :disabled="!can('document') || row.status === '已发布'">提交</el-dropdown-item>
                    <el-dropdown-item command="upload" :disabled="!can('document') || row.status === '已发布' || row.status === '审批中'">上传文件</el-dropdown-item>
                    <el-dropdown-item command="preview" :disabled="!row.file_name" divided>预览</el-dropdown-item>
                    <el-dropdown-item command="distribute" :disabled="row.status !== '已发布'">发放</el-dropdown-item>
                    <el-dropdown-item command="version">版本历史</el-dropdown-item>
                    <el-dropdown-item command="relations">关联对象</el-dropdown-item>
                    <el-dropdown-item command="delete" :disabled="!can('document') || row.status === '已发布'" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
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
        @current-change="onPageChange"
        @size-change="onSizeChange"
      />
    </div>
    <input ref="fileInput" type="file" style="display:none" @change="handleFileUpload" />
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑文档' : '登记文档'" width="720px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="文档编号"><el-input v-model="form.doc_no" /></el-form-item>
          <el-form-item label="关联产品">
            <el-select v-model="form.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="form.category" filterable>
              <el-option v-for="o in docCategoryOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="版本"><el-input v-model="form.version" /></el-form-item>
          <el-form-item label="文件状态">
            <el-select v-model="form.status">
              <el-option v-for="o in docStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="签核状态">
            <el-select v-model="form.approval_status">
              <el-option v-for="o in approvalStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="更新时间"><el-input v-model="form.updated_at" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="文档名称" class="form-wide"><el-input v-model="form.title" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="versionHistoryVisible" title="文档版本历史" width="900px">
      <el-table :data="versionHistory" height="420" size="small">
        <el-table-column prop="version" label="版本" width="70" fixed />
        <el-table-column label="当前" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.is_current" size="small" type="success">当前</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="owner" label="负责人" width="80" />
        <el-table-column prop="updated_at" label="更新时间" width="110" />
        <el-table-column prop="source_version" label="来源版本" width="90" />
        <el-table-column prop="change_no" label="变更单" width="150" show-overflow-tooltip />
        <el-table-column prop="change_status" label="变更状态" width="90" />
        <el-table-column prop="eca_action_no" label="ECA动作" width="150" show-overflow-tooltip />
        <el-table-column label="发布门" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.release_gate_status" size="small" :type="row.release_gate_status === '可提交' ? 'success' : 'warning'">{{ row.release_gate_status }}</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="previewVisible" :title="`预览 - ${previewTitle}`" width="80%" top="5vh" destroy-on-close>
      <div v-loading="previewLoading" class="preview-container">
        <iframe v-if="previewUrl && previewType === 'pdf'" :src="previewUrl" class="preview-iframe" />
        <img v-else-if="previewUrl && previewType === 'image'" :src="previewUrl" class="preview-image" />
        <div v-else class="preview-error">
          <span>该文件类型不支持在线预览，仅支持 PDF 和图片格式。</span>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="relationsVisible" title="文档关联对象" width="940px">
      <div v-if="!relationsData" class="gantt-empty">加载中…</div>
      <template v-else>
        <div class="object-strip" style="margin-bottom:8px">
          <div><span>文档</span><strong>{{ relationsData.doc_no }} · {{ relationsData.title }}</strong></div>
          <div><span>产品</span><strong>{{ relationsData.product_model || '未关联' }}</strong></div>
          <div><span>生命周期</span><strong>{{ relationsData.product_lifecycle || '-' }}</strong></div>
          <div><span>BOM</span><strong>{{ relationsData.counts.boms }}</strong></div>
          <div><span>工艺</span><strong>{{ relationsData.counts.process_routes }}</strong></div>
          <div><span>项目</span><strong>{{ relationsData.counts.projects }}</strong></div>
          <div><span>变更</span><strong>{{ relationsData.counts.changes }}</strong></div>
          <div><span>同源文档</span><strong>{{ relationsData.counts.related_documents }}</strong></div>
        </div>
        <div v-if="!relationsData.product_id" class="gantt-empty">该文档未关联有效产品，无法聚合关联对象</div>
        <el-tabs v-else class="compact-tabs" type="card">
          <el-tab-pane :label="`BOM (${relationsData.counts.boms})`">
            <el-table :data="relationsData.boms" size="small" max-height="320">
              <el-table-column prop="bom_type" label="类型" width="80" />
              <el-table-column prop="version" label="版本" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="owner" label="负责人" width="100" />
              <el-table-column prop="release_date" label="发布日" width="110" />
              <el-table-column prop="effective_date" label="生效日" width="110" />
              <el-table-column label="当前" width="70">
                <template #default="{ row }">
                  <el-tag v-if="row.is_current" size="small" type="success">当前</el-tag>
                  <span v-else class="muted">-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`工艺路线 (${relationsData.counts.process_routes})`">
            <el-table :data="relationsData.process_routes" size="small" max-height="320">
              <el-table-column prop="route_no" label="编号" width="140" />
              <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="version" label="版本" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="owner" label="负责人" width="100" />
              <el-table-column prop="release_date" label="发布日" width="110" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`项目 (${relationsData.counts.projects})`">
            <el-table :data="relationsData.projects" size="small" max-height="320">
              <el-table-column prop="project_no" label="项目编号" width="150" />
              <el-table-column prop="name" label="项目名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="phase" label="阶段" width="90" />
              <el-table-column prop="progress" label="进度" width="80" />
              <el-table-column prop="owner" label="负责人" width="100" />
              <el-table-column label="归档" width="80">
                <template #default="{ row }">
                  <el-tag v-if="row.is_archived" size="small" type="info">已归档</el-tag>
                  <span v-else class="muted">-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`工程变更 (${relationsData.counts.changes})`">
            <el-table :data="relationsData.changes" size="small" max-height="320">
              <el-table-column prop="change_no" label="编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="change_type" label="类型" width="80" />
              <el-table-column prop="priority" label="优先级" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="owner" label="负责人" width="100" />
              <el-table-column prop="submitted_at" label="提交日" width="110" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`同源文档 (${relationsData.counts.related_documents})`">
            <el-table :data="relationsData.related_documents" size="small" max-height="320">
              <el-table-column prop="doc_no" label="编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="category" label="类别" width="100" />
              <el-table-column prop="version" label="版本" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="owner" label="负责人" width="100" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>

    <el-dialog v-model="distributeVisible" title="文档发放/回收" width="800px">
      <div class="toolbar compact-toolbar" style="margin-bottom: 12px">
        <span class="muted">{{ distributeDoc?.doc_no }} · {{ distributeDoc?.title }} · v{{ distributeDoc?.version }}</span>
      </div>
      <el-form :model="distributeForm" label-width="80px" style="margin-bottom: 16px">
        <div class="form-grid">
          <el-form-item label="接收类型">
            <el-select v-model="distributeForm.recipient_type">
              <el-option v-for="o in recipientTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="接收方">
            <el-input v-model="distributeForm.recipient" placeholder="多个接收方用逗号分隔" />
          </el-form-item>
        </div>
        <el-button type="primary" size="small" @click="executeDistribute" :disabled="!distributeForm.recipient">发放</el-button>
      </el-form>
      <el-table :data="distributions" height="300" size="small">
        <el-table-column prop="recipient_type" label="类型" width="70" />
        <el-table-column prop="recipient" label="接收方" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === '已发放' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="distributed_by" label="发放人" width="80" />
        <el-table-column prop="distributed_at" label="发放时间" width="110" />
        <el-table-column prop="recalled_by" label="回收人" width="80" />
        <el-table-column prop="recalled_at" label="回收时间" width="110" />
        <el-table-column prop="recall_reason" label="回收原因" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '已发放'" size="small" type="warning" @click="recallDistributionRow(row)">回收</el-button>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Search, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { approveDocument, createDocument, deleteDocument, distributeDocument, downloadAttachment, downloadDocumentFile, getAttachments, getDocumentDistributions, getDocumentRelations, getDocumentVersionHistory, getDocuments, getProducts, previewDocumentFile, recallDistribution, submitDocument, updateDocument, uploadAttachment, uploadDocumentFile } from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const { can, refreshSession } = useAuth()
const docCategoryOptions = useDictionary('DICT_DOC_CATEGORY').options
const docStatusOptions = useDictionary('DICT_DOC_STATUS').options
const approvalStatusOptions = useDictionary('DICT_APPROVAL_STATUS').options
const recipientTypeOptions = useDictionary('DICT_RECIPIENT_TYPE').options
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange, onSortChange } = useListPage(getDocuments)
const products = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const uploadTargetId = ref<number | null>(null)
const versionHistoryVisible = ref(false)
const versionHistory = ref<any[]>([])
const previewVisible = ref(false)
const previewUrl = ref('')
const previewType = ref<'pdf' | 'image' | ''>('')
const previewTitle = ref('')
const previewLoading = ref(false)
const distributeVisible = ref(false)
const distributeDoc = ref<any>(null)
const distributeForm = ref<any>({ recipient_type: '角色', recipient: '', distributed_by: '' })
const distributions = ref<any[]>([])
const relationsVisible = ref(false)
const relationsData = ref<any>(null)
const emptyForm = { product_id: undefined, doc_no: '', title: '', category: '', version: 'A0', status: '编制中', owner: '', approval_status: '未提交', updated_at: '' }
const form = ref<any>({ ...emptyForm })
const attachmentCache = ref<Map<number, any[]>>(new Map())
const fileRowsCache = ref<Record<number, any[]>>({})
const fileRowsLoading = ref<Record<number, boolean>>({})

function statusTagType(status: string): string {
  switch (status) {
    case '已发布': return 'success'
    case '审批中': return 'warning'
    case '编制中': return 'info'
    case '已废止': return 'danger'
    default: return ''
  }
}

function approvalTagType(status: string): string {
  switch (status) {
    case '已签核': return 'success'
    case '流转中': return 'warning'
    case '未提交': return 'info'
    default: return ''
  }
}

function formatFileSize(bytes?: number | null): string {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function loadDocumentFileRows(row: any) {
  const rowId = row.id
  if (fileRowsCache.value[rowId]) return
  fileRowsLoading.value[rowId] = true
  try {
    const attachments = (await getAttachments('Document', rowId)) || []
    const rows = []
    if (row.file_name) {
      rows.push({
        id: `main-${row.id}`,
        file_name: row.file_name,
        file_size: row.file_size,
        uploaded_by: row.owner,
        uploaded_at: row.updated_at,
        is_main: true,
        attachment_id: null,
      })
    }
    for (const att of attachments) {
      rows.push({
        id: `att-${att.id}`,
        file_name: att.file_name,
        file_size: att.file_size,
        uploaded_by: att.uploaded_by,
        uploaded_at: att.uploaded_at,
        is_main: false,
        attachment_id: att.id,
      })
    }
    fileRowsCache.value[rowId] = rows
  } finally {
    fileRowsLoading.value[rowId] = false
  }
}

async function onExpandChange(row: any, expandedRows: any[]) {
  const isExpanded = expandedRows.some((r: any) => r.id === row.id)
  if (isExpanded) {
    await loadDocumentFileRows(row)
  }
}

async function handleAttachmentUpload(file: File, documentId: number) {
  try {
    await uploadAttachment('Document', documentId, file)
    ElMessage.success('附件上传成功')
    delete fileRowsCache.value[documentId]
    // 找到当前行重新加载附件
    const row = (items.value || []).find((r: any) => r.id === documentId)
    if (row) await loadDocumentFileRows(row)
  } catch {
    ElMessage.error('附件上传失败')
  }
  return false
}

async function downloadAttachmentFile(row: any) {
  if (!row.attachment_id) return
  try {
    await downloadAttachment(row.attachment_id)
  } catch {
    ElMessage.error('附件下载失败')
  }
}

async function openRelations(row: any) {
  relationsData.value = null
  relationsVisible.value = true
  try {
    relationsData.value = await getDocumentRelations(row.id)
  } catch (e: any) {
    ElMessage.error('加载关联对象失败')
    relationsVisible.value = false
  }
}

function handleDocAction(cmd: string, row: any) {
  switch (cmd) {
    case 'edit': openEdit(row); break
    case 'submit': submit(row); break
    case 'approve': approve(row); break
    case 'upload': triggerUpload(row); break
    case 'preview': preview(row); break
    case 'download': download(row); break
    case 'distribute': openDistribute(row); break
    case 'version': openVersionHistory(row); break
    case 'relations': openRelations(row); break
    case 'delete': remove(row); break
  }
}

function openCreate() {
  if (!can('document')) return
  editingId.value = null
  form.value = { ...emptyForm, product_id: products.value[0]?.id }
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('document') || row.status === '已发布') return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!can('document')) return
  if (editingId.value) {
    await updateDocument(editingId.value, form.value)
  } else {
    await createDocument(form.value)
  }
  ElMessage.success('文档已保存')
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  if (!can('document') || row.status === '已发布') return
  await ElMessageBox.confirm(`确认删除文档 ${row.doc_no}？已发布文档会被后端阻止删除。`, '删除确认', { type: 'warning' })
  await deleteDocument(row.id)
  ElMessage.success('文档已删除')
  await loadData()
}

async function submit(row: any) {
  if (!can('document') || row.status === '已发布') return
  await submitDocument(row.id)
  ElMessage.success('文档已提交审核')
  await loadData()
}

async function approve(row: any) {
  if (!can(['approval', 'document']) || row.status === '已发布') return
  const res = await approveDocument(row.id)
  if (res?.auto_distributed_to?.length) {
    ElMessage.success(`文档已签核发布，已按变更通知单自动发放给 ${res.auto_distributed_to.length} 位接收人`)
  } else {
    ElMessage.success('文档已签核发布，QMS 同步队列已生成')
  }
  await loadData()
}

function triggerUpload(row: any) {
  if (!can('document') || row.status === '已发布' || row.status === '审批中') return
  uploadTargetId.value = row.id
  fileInput.value?.click()
}

async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !uploadTargetId.value) return
  try {
    await uploadDocumentFile(uploadTargetId.value, file)
    ElMessage.success('文件上传成功')
    await loadData()
  } catch (err: any) {
    const detail = err?.response?.data?.detail || err?.message || ''
    ElMessage.error(detail ? `文件上传失败：${detail}` : '文件上传失败')
  }
  target.value = ''
  uploadTargetId.value = null
}

async function download(row: any) {
  if (!row.file_name) return
  try {
    const response = await downloadDocumentFile(row.id)
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = row.file_name
    link.click()
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('文件下载失败')
  }
}

async function openVersionHistory(row: any) {
  versionHistory.value = await getDocumentVersionHistory(row.id)
  versionHistoryVisible.value = true
}

const PREVIEWABLE_EXTS = ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']

async function preview(row: any) {
  if (!row.file_name) return
  const ext = row.file_name.substring(row.file_name.lastIndexOf('.')).toLowerCase()
  if (!PREVIEWABLE_EXTS.includes(ext)) {
    ElMessage.warning('该文件类型不支持在线预览，仅支持 PDF 和图片')
    return
  }
  previewLoading.value = true
  previewVisible.value = true
  previewTitle.value = row.file_name
  previewType.value = ext === '.pdf' ? 'pdf' : 'image'
  previewUrl.value = ''
  try {
    const response = await previewDocumentFile(row.id)
    const blob = new Blob([response.data], { type: String(response.headers['content-type'] || 'application/octet-stream') })
    previewUrl.value = window.URL.createObjectURL(blob)
  } catch {
    ElMessage.error('预览加载失败')
    previewVisible.value = false
  } finally {
    previewLoading.value = false
  }
}

async function openDistribute(row: any) {
  if (row.status !== '已发布') return
  distributeDoc.value = row
  distributeForm.value = { recipient_type: '角色', recipient: '', distributed_by: '' }
  distributeVisible.value = true
  await loadDistributions(row.id)
}

async function loadDistributions(docId: number) {
  try {
    const result = await getDocumentDistributions(docId)
    distributions.value = result.items || []
  } catch {
    distributions.value = []
  }
}

async function executeDistribute() {
  if (!distributeDoc.value || !distributeForm.value.recipient) return
  try {
    const result = await distributeDocument(distributeDoc.value.id, {
      ...distributeForm.value,
      document_id: distributeDoc.value.id,
    })
    ElMessage.success(`已发放到 ${result.count} 个接收方`)
    distributeForm.value.recipient = ''
    await loadDistributions(distributeDoc.value.id)
  } catch {
    ElMessage.error('发放失败')
  }
}

async function recallDistributionRow(row: any) {
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入回收原因', '文档回收', {
      type: 'warning',
      inputPlaceholder: '回收原因（可选）',
      inputValidator: () => true,
    })
    await recallDistribution(row.id, { recall_reason: reason || '' })
    ElMessage.success('文档已回收')
    if (distributeDoc.value) {
      await loadDistributions(distributeDoc.value.id)
    }
  } catch {
    // user cancelled
  }
}

onMounted(async () => {
  await refreshSession()
  products.value = (await getProducts()).items
  await loadData()
})
</script>

<style scoped>
.file-badge {
  font-size: 12px;
  color: #409eff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
  max-width: 120px;
}
.preview-container {
  height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.preview-error {
  color: #999;
  font-size: 14px;
}

.document-files-panel {
  margin: 8px 24px 12px 24px;
  padding: 12px 16px;
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.document-files-header {
  margin-bottom: 8px;
  font-size: 14px;
}
.document-files-panel .file-name {
  margin-left: 8px;
  font-size: 13px;
}
.attachment-upload-bar {
  margin-top: 8px;
}
</style>
