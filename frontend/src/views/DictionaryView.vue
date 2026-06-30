<template>
  <div class="panel dictionary-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>数据字典</strong>
        <span class="muted"> · 维护系统枚举值和下拉选项</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索字典编码/名称/值" :prefix-icon="Search" clearable style="width:220px" @keyup.enter="onSearch" @clear="onSearch" />
        <el-button type="primary" :icon="Plus" @click="openCreate">新增字典项</el-button>
      </div>
    </div>

    <div class="dictionary-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="dict_code" label="字典编码" width="170" />
        <el-table-column prop="dict_name" label="字典名称" width="130" />
        <el-table-column prop="item_value" label="值" min-width="140" />
        <el-table-column prop="item_label" label="显示名" min-width="140" />
        <el-table-column prop="object_scope" label="适用对象" width="150" />
        <el-table-column prop="sequence" label="排序" width="80" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }"><el-tag size="small" :type="row.status === '启用' ? 'success' : 'info'">{{ row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
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
        background
        @size-change="onSizeChange"
        @current-change="onPageChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑字典项' : '新增字典项'" width="760px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="字典编码"><el-input v-model="form.dict_code" /></el-form-item>
          <el-form-item label="字典名称"><el-input v-model="form.dict_name" /></el-form-item>
          <el-form-item label="值"><el-input v-model="form.item_value" /></el-form-item>
          <el-form-item label="显示名"><el-input v-model="form.item_label" /></el-form-item>
          <el-form-item label="适用对象"><el-input v-model="form.object_scope" /></el-form-item>
          <el-form-item label="排序"><el-input-number v-model="form.sequence" :min="1" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
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
import {
  createDictionaryItem,
  deleteDictionaryItem,
  getDictionaryItems,
  updateDictionaryItem,
} from '../api'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage<any>(getDictionaryItems)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { dict_code: '', dict_name: '', item_value: '', item_label: '', object_scope: '', sequence: 1, status: '启用' }
const form = ref<any>({ ...emptyForm })

function openCreate() {
  editingId.value = null
  form.value = { ...emptyForm }
  dialogVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  editingId.value ? await updateDictionaryItem(editingId.value, form.value) : await createDictionaryItem(form.value)
  ElMessage.success('字典项已保存')
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除字典项 ${row.dict_name || row.dict_code}？`, '删除确认', { type: 'warning' })
    await deleteDictionaryItem(row.id)
    ElMessage.success('字典项已删除')
    await loadData()
  } catch {
    // 用户取消
  }
}

onMounted(loadData)
</script>

<style scoped>
.dictionary-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 82px);
}

.dictionary-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0;
}
</style>
