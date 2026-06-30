<template>
  <div class="panel category-template-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>分类属性</strong>
        <span class="muted"> · 维护业务对象分类和字段属性模板</span>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索分类编码/名称" :prefix-icon="Search" clearable style="width:220px" @keyup.enter="onSearch" @clear="onSearch" />
        <el-button type="primary" :icon="Plus" @click="openCreate">新增分类</el-button>
      </div>
    </div>

    <div class="category-template-table-wrap">
      <el-table :data="items" row-key="id" height="100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="nested-grid">
              <div class="toolbar compact-toolbar">
                <strong>{{ row.name }} 属性模板</strong>
                <el-button size="small" :icon="Plus" @click="openAttributeCreate(row)">新增属性</el-button>
              </div>
              <el-table :data="row.attributes || []" size="small" border>
                <el-table-column prop="sequence" label="序号" width="70" />
                <el-table-column prop="name" label="属性名" width="150" />
                <el-table-column prop="field_key" label="字段键" width="160" />
                <el-table-column prop="data_type" label="类型" width="100" />
                <el-table-column prop="required" label="必填" width="80" />
                <el-table-column prop="dictionary_code" label="字典" min-width="150" />
                <el-table-column prop="default_value" label="默认值" min-width="140" />
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="{ row: attr }">
                    <div class="row-actions">
                      <el-button size="small" @click="openAttributeEdit(row, attr)">编辑</el-button>
                      <el-button size="small" type="danger" @click="removeAttribute(attr)">删除</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="object_type" label="对象" width="120" fixed />
        <el-table-column prop="code" label="分类编码" width="170" />
        <el-table-column prop="name" label="分类名称" width="170" />
        <el-table-column prop="parent_code" label="父分类" width="140" />
        <el-table-column prop="lifecycle_template" label="生命周期" width="150" />
        <el-table-column prop="coding_rule" label="编码规则" width="140" />
        <el-table-column prop="description" label="说明" min-width="240" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分类' : '新增分类'" width="760px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="对象"><el-input v-model="form.object_type" /></el-form-item>
          <el-form-item label="分类编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="分类名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="父分类"><el-input v-model="form.parent_code" /></el-form-item>
          <el-form-item label="生命周期"><el-input v-model="form.lifecycle_template" /></el-form-item>
          <el-form-item label="编码规则"><el-input v-model="form.coding_rule" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="说明"><el-input v-model="form.description" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attributeDialogVisible" :title="attributeEditingId ? '编辑属性' : '新增属性'" width="700px">
      <el-form :model="attributeForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="属性名"><el-input v-model="attributeForm.name" /></el-form-item>
          <el-form-item label="字段键"><el-input v-model="attributeForm.field_key" /></el-form-item>
          <el-form-item label="类型">
            <el-select v-model="attributeForm.data_type">
              <el-option label="文本" value="文本" />
              <el-option label="数字" value="数字" />
              <el-option label="枚举" value="枚举" />
              <el-option label="日期" value="日期" />
            </el-select>
          </el-form-item>
          <el-form-item label="必填"><el-select v-model="attributeForm.required"><el-option label="是" value="是" /><el-option label="否" value="否" /></el-select></el-form-item>
          <el-form-item label="字典编码"><el-input v-model="attributeForm.dictionary_code" /></el-form-item>
          <el-form-item label="默认值"><el-input v-model="attributeForm.default_value" /></el-form-item>
          <el-form-item label="排序"><el-input-number v-model="attributeForm.sequence" :min="1" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="attributeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAttribute">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  createAttributeTemplate,
  createCategoryTemplate,
  deleteAttributeTemplate,
  deleteCategoryTemplate,
  getCategoryTemplates,
  updateAttributeTemplate,
  updateCategoryTemplate,
} from '../api'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage<any>(getCategoryTemplates)
const dialogVisible = ref(false)
const attributeDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const attributeEditingId = ref<number | null>(null)
const parentRow = ref<any | null>(null)
const emptyForm = { object_type: '', code: '', name: '', parent_code: '', lifecycle_template: '', coding_rule: '', status: '启用', description: '' }
const emptyAttributeForm = { name: '', field_key: '', data_type: '文本', required: '否', dictionary_code: '', default_value: '', sequence: 1 }
const form = ref<any>({ ...emptyForm })
const attributeForm = ref<any>({ ...emptyAttributeForm })

function openCreate() {
  editingId.value = null
  form.value = { ...emptyForm }
  dialogVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = { ...row }
  delete form.value.attributes
  dialogVisible.value = true
}

async function save() {
  editingId.value ? await updateCategoryTemplate(editingId.value, form.value) : await createCategoryTemplate(form.value)
  ElMessage.success('分类已保存')
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除分类 ${row.name || row.code}？`, '删除确认', { type: 'warning' })
    await deleteCategoryTemplate(row.id)
    ElMessage.success('分类已删除')
    await loadData()
  } catch {
    // 用户取消删除时保持静默。
  }
}

function openAttributeCreate(row: any) {
  parentRow.value = row
  attributeEditingId.value = null
  attributeForm.value = { ...emptyAttributeForm }
  attributeDialogVisible.value = true
}

function openAttributeEdit(row: any, attr: any) {
  parentRow.value = row
  attributeEditingId.value = attr.id
  attributeForm.value = { ...attr }
  attributeDialogVisible.value = true
}

async function saveAttribute() {
  if (!parentRow.value) return
  attributeEditingId.value ? await updateAttributeTemplate(attributeEditingId.value, attributeForm.value) : await createAttributeTemplate(parentRow.value.id, attributeForm.value)
  ElMessage.success('属性已保存')
  attributeDialogVisible.value = false
  await loadData()
}

async function removeAttribute(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除属性 ${row.name}？`, '删除确认', { type: 'warning' })
    await deleteAttributeTemplate(row.id)
    ElMessage.success('属性已删除')
    await loadData()
  } catch {
    // 用户取消删除时保持静默。
  }
}

onMounted(loadData)
</script>

<style scoped>
.category-template-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 82px);
}

.category-template-table-wrap {
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
