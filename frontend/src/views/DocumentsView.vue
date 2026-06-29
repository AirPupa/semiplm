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
      <el-table :data="items" height="100%">
        <el-table-column prop="doc_no" label="文档编号" width="190" fixed />
        <el-table-column prop="title" label="文档名称" min-width="220" />
        <el-table-column prop="product_model" label="产品型号" width="130" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="status" label="文件状态" width="110" />
        <el-table-column prop="approval_status" label="签核状态" width="110" />
        <el-table-column prop="owner" label="负责人" width="90" />
        <el-table-column prop="updated_at" label="更新时间" width="120" />
        <el-table-column label="操作" width="230" fixed="right" class-name="table-actions-cell">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" :disabled="!can('document') || row.status === '已发布'" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" :disabled="!can('document') || row.status === '已发布'" @click="submit(row)">提交</el-button>
              <el-button size="small" type="primary" :disabled="!can(['approval', 'document']) || row.status === '已发布'" @click="approve(row)">发布</el-button>
              <el-button size="small" type="danger" :disabled="!can('document') || row.status === '已发布'" @click="remove(row)">删除</el-button>
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
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑文档' : '登记文档'" width="720px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="文档编号"><el-input v-model="form.doc_no" /></el-form-item>
          <el-form-item label="关联产品">
            <el-select v-model="form.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类"><el-input v-model="form.category" /></el-form-item>
          <el-form-item label="版本"><el-input v-model="form.version" /></el-form-item>
          <el-form-item label="文件状态">
            <el-select v-model="form.status">
              <el-option label="编制中" value="编制中" />
              <el-option label="审批中" value="审批中" />
              <el-option label="已发布" value="已发布" />
              <el-option label="已废止" value="已废止" />
            </el-select>
          </el-form-item>
          <el-form-item label="签核状态">
            <el-select v-model="form.approval_status">
              <el-option label="未提交" value="未提交" />
              <el-option label="流转中" value="流转中" />
              <el-option label="已签核" value="已签核" />
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
  </div>
</template>

<script setup lang="ts">
import { Search, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { approveDocument, createDocument, deleteDocument, getDocuments, getProducts, submitDocument, updateDocument } from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import { useListPage } from '../composables/useListPage'

const { can, refreshSession } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getDocuments)
const products = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { product_id: undefined, doc_no: '', title: '', category: '', version: 'A0', status: '编制中', owner: '', approval_status: '未提交', updated_at: '' }
const form = ref<any>({ ...emptyForm })

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
  await approveDocument(row.id)
  ElMessage.success('文档已签核发布，QMS 同步队列已生成')
  await loadData()
}

onMounted(async () => {
  await refreshSession()
  products.value = (await getProducts()).items
  await loadData()
})
</script>
