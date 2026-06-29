<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>物料主数据</strong>
        <span class="muted"> · 衬底、外延、Mask、工艺材料与测试治具统一编码</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索物料编码/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('material')" type="primary" :icon="Plus" @click="openCreate">新增物料</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="code" label="物料编码" width="150" fixed />
        <el-table-column prop="name" label="物料名称" min-width="180" />
        <el-table-column prop="category" label="类别" width="130" />
        <el-table-column prop="specification" label="规格/参数" min-width="220" />
        <el-table-column prop="supplier" label="供应商" width="140" />
        <el-table-column prop="risk_level" label="风险" width="90">
          <template #default="{ row }">
            <el-tag :type="row.risk_level === '高' ? 'danger' : row.risk_level === '中' ? 'warning' : 'success'" size="small">
              {{ row.risk_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lifecycle" label="状态" width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :disabled="!can('material')" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" :disabled="!can('material')" @click="remove(row)">删除</el-button>
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
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑物料' : '新增物料'" width="640px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="物料编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="物料名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="类别"><el-input v-model="form.category" /></el-form-item>
          <el-form-item label="供应商"><el-input v-model="form.supplier" /></el-form-item>
          <el-form-item label="风险">
            <el-select v-model="form.risk_level">
              <el-option label="低" value="低" />
              <el-option label="中" value="中" />
              <el-option label="高" value="高" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.lifecycle">
              <el-option label="有效" value="有效" />
              <el-option label="替代" value="替代" />
              <el-option label="冻结" value="冻结" />
              <el-option label="停用" value="停用" />
            </el-select>
          </el-form-item>
          <el-form-item label="规格参数" class="form-wide"><el-input v-model="form.specification" type="textarea" :rows="3" /></el-form-item>
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
import { createMaterial, deleteMaterial, getMaterials, updateMaterial } from '../api'
import { useAuth } from '../auth'
import { useListPage } from '../composables/useListPage'

const { can, refreshSession } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getMaterials)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { code: '', name: '', category: '', specification: '', supplier: '', risk_level: '低', lifecycle: '有效' }
const form = ref<any>({ ...emptyForm })

function openCreate() {
  if (!can('material')) return
  editingId.value = null
  form.value = { ...emptyForm }
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('material')) return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!can('material')) return
  if (editingId.value) {
    await updateMaterial(editingId.value, form.value)
  } else {
    await createMaterial(form.value)
  }
  ElMessage.success('物料已保存')
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  if (!can('material')) return
  await ElMessageBox.confirm(`确认删除物料 ${row.code}？已被 BOM 使用的物料会被后端阻止删除。`, '删除确认', { type: 'warning' })
  await deleteMaterial(row.id)
  ElMessage.success('物料已删除')
  await loadData()
}

onMounted(async () => {
  await refreshSession()
  await loadData()
})
</script>
