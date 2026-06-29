<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>需求规格池</strong>
          <span class="muted"> · 客户输入、NPI 阶段门、质量体系要求可追溯到型号</span>
        </div>
        <el-button v-if="can('requirement')" type="primary" :icon="Plus" @click="openCreate">新建需求</el-button>
      </div>
      <el-table :data="requirements" highlight-current-row @current-change="selected = $event" height="680">
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
            <el-button size="small" :disabled="!can('requirement')" @click.stop="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :disabled="!can('requirement') || ['已确认', '已发布'].includes(row.status)" @click.stop="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="panel">
      <div class="panel-title">{{ selected?.req_no || '需求详情' }}</div>
      <template v-if="selected">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="来源">{{ selected.source }}</el-descriptions-item>
          <el-descriptions-item label="产品">{{ selected.product_model }}</el-descriptions-item>
          <el-descriptions-item label="负责人">{{ selected.owner }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ selected.status }}</el-descriptions-item>
          <el-descriptions-item label="验收准则">{{ selected.acceptance_criteria }}</el-descriptions-item>
        </el-descriptions>
        <div class="trace-box section-gap">
          <div>
            <span>输入</span>
            <strong>{{ selected.source }}</strong>
          </div>
          <el-icon><Right /></el-icon>
          <div>
            <span>规格</span>
            <strong>{{ selected.category }}</strong>
          </div>
          <el-icon><Right /></el-icon>
          <div>
            <span>输出</span>
            <strong>BOM / 工艺 / 文档 / 测试规范</strong>
          </div>
        </div>
      </template>
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
          <el-form-item label="来源"><el-input v-model="form.source" /></el-form-item>
          <el-form-item label="分类"><el-input v-model="form.category" /></el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="form.priority">
              <el-option label="高" value="高" />
              <el-option label="中" value="中" />
              <el-option label="低" value="低" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="草稿" value="草稿" />
              <el-option label="验证中" value="验证中" />
              <el-option label="进行中" value="进行中" />
              <el-option label="已确认" value="已确认" />
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
import { Plus, Right } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createRequirement, deleteRequirement, getProducts, getRequirements, updateRequirement } from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'

const loading = ref(true)
const { can, currentUser, refreshSession } = useAuth()
const requirements = ref<any[]>([])
const selected = ref<any>()
const products = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { product_id: undefined, req_no: '', source: '', category: '', title: '', priority: '中', status: '草稿', owner: '', acceptance_criteria: '' }
const form = ref<any>({ ...emptyForm })

async function loadRequirements() {
  requirements.value = await getRequirements()
  selected.value = requirements.value[0]
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
  products.value = await getProducts()
  await loadRequirements()
  loading.value = false
})
</script>
