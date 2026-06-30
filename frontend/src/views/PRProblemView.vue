<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>PR 问题报告</strong>
        <span class="muted"> · Problem Report，问题描述、分类、严重度、关联变更</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索 PR 编号/标题" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('change')" type="primary" :icon="Plus" @click="openCreate">新建 PR</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
      <el-table-column prop="pr_no" label="PR 编号" width="140" fixed />
      <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="problem_type" label="问题类型" width="110" />
      <el-table-column prop="severity" label="严重度" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.severity === '严重' ? 'danger' : row.severity === '高' ? 'warning' : 'info'">
            {{ row.severity }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="source" label="来源" width="90" />
      <el-table-column prop="product_model" label="产品型号" width="130" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === '已关闭' ? 'success' : row.status === '评估中' ? 'warning' : 'info'">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reporter" label="报告人" width="100" />
      <el-table-column prop="reported_at" label="报告日期" width="110" />
      <el-table-column prop="related_change_no" label="关联变更" width="120" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="!can('change') || row.status === '已关闭'" @click.stop="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" :disabled="!can('change') || row.status === '已关闭'" @click.stop="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑 PR' : '新建 PR'" width="720px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="问题标题" class="form-wide"><el-input v-model="form.title" /></el-form-item>
          <el-form-item label="PR 编号"><el-input v-model="form.pr_no" placeholder="留空自动生成" /></el-form-item>
          <el-form-item label="问题类型">
            <el-select v-model="form.problem_type">
              <el-option v-for="o in prTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="严重度">
            <el-select v-model="form.severity">
              <el-option v-for="o in severityOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="来源">
            <el-select v-model="form.source">
              <el-option v-for="o in prSourceOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="产品型号">
            <el-select v-model="form.product_model" filterable placeholder="选择产品" @change="onProductChange">
              <el-option v-for="p in products" :key="p.id" :label="p.model" :value="p.model" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option v-for="o in prStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="报告人"><UserSelect v-model="form.reporter" /></el-form-item>
          <el-form-item label="报告日期"><el-input v-model="form.reported_at" /></el-form-item>
          <el-form-item label="关联变更"><el-input v-model="form.related_change_no" placeholder="如 ECR-xxx" /></el-form-item>
          <el-form-item label="问题描述" class="form-wide"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="建议措施" class="form-wide"><el-input v-model="form.suggested_action" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="备注" class="form-wide"><el-input v-model="form.remark" type="textarea" :rows="2" /></el-form-item>
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
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createProblemReport, deleteProblemReport, getProblemReports, updateProblemReport, getProducts } from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const prTypeOptions = useDictionary('DICT_PR_TYPE').options
const severityOptions = useDictionary('DICT_SEVERITY').options
const prSourceOptions = useDictionary('DICT_PR_SOURCE').options
const prStatusOptions = useDictionary('DICT_PR_STATUS').options

const { can, currentUser } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getProblemReports)
const products = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)

const emptyForm = {
  pr_no: '',
  title: '',
  problem_type: '设计问题',
  severity: '中',
  source: '内部',
  product_id: undefined,
  product_model: '',
  description: '',
  suggested_action: '',
  status: '新建',
  reporter: '',
  reported_at: '',
  related_change_no: '',
  remark: '',
}
const form = ref<any>({ ...emptyForm })

function todayText() {
  return new Date().toISOString().slice(0, 10)
}

function onProductChange(model: string) {
  const p = products.value.find((x: any) => x.model === model)
  form.value.product_id = p?.id || undefined
}

function openCreate() {
  editingId.value = null
  form.value = {
    ...emptyForm,
    reporter: currentUser.value?.display_name || '',
    reported_at: todayText(),
  }
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('change') || row.status === '已关闭') return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!can('change')) return
  if (!form.value.title) {
    ElMessage.warning('请输入问题标题')
    return
  }
  if (editingId.value) {
    await updateProblemReport(editingId.value, form.value)
    ElMessage.success('PR 已更新')
  } else {
    await createProblemReport(form.value)
    ElMessage.success('PR 已创建')
  }
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  if (!can('change') || row.status === '已关闭') return
  await ElMessageBox.confirm(`确认删除 PR ${row.pr_no}？已关闭的 PR 不可删除。`, '删除确认', { type: 'warning' })
  await deleteProblemReport(row.id)
  ElMessage.success('PR 已删除')
  await loadData()
}

onMounted(async () => {
  products.value = (await getProducts()).items
  await loadData()
})
</script>
