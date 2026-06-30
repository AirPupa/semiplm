<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>基础配置</strong>
        <span class="muted"> · 编码、分类属性、生命周期、枚举字典统一维护</span>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增配置</el-button>
    </div>

    <el-tabs v-model="activeTab" class="admin-tabs">
      <el-tab-pane label="编码规则" name="coding">
        <el-table :data="codingRules" height="620">
          <el-table-column prop="object_type" label="对象" width="110" />
          <el-table-column prop="code" label="规则编码" width="150" />
          <el-table-column prop="name" label="规则名称" min-width="160" />
          <el-table-column prop="pattern" label="编码模式" min-width="230" />
          <el-table-column prop="current_no" label="当前流水" width="100" />
          <el-table-column prop="sample" label="样例" min-width="170" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeMain(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="分类属性" name="category">
        <el-table :data="categories" row-key="id" height="620">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="nested-grid">
                <div class="toolbar compact-toolbar">
                  <strong>{{ row.name }} 属性模板</strong>
                  <el-button size="small" :icon="Plus" @click="openChildCreate(row)">新增属性</el-button>
                </div>
                <el-table :data="row.attributes" size="small" border>
                  <el-table-column prop="sequence" label="序号" width="70" />
                  <el-table-column prop="name" label="属性名" width="140" />
                  <el-table-column prop="field_key" label="字段键" width="150" />
                  <el-table-column prop="data_type" label="类型" width="100" />
                  <el-table-column prop="required" label="必填" width="80" />
                  <el-table-column prop="dictionary_code" label="字典" min-width="150" />
                  <el-table-column prop="default_value" label="默认值" min-width="140" />
                  <el-table-column label="操作" width="150">
                    <template #default="{ row: attr }">
                      <el-button size="small" @click="openChildEdit(row, attr)">编辑</el-button>
                      <el-button size="small" type="danger" @click="removeChild(attr)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="object_type" label="对象" width="110" />
          <el-table-column prop="code" label="分类编码" width="160" />
          <el-table-column prop="name" label="分类名称" width="160" />
          <el-table-column prop="lifecycle_template" label="生命周期" width="150" />
          <el-table-column prop="coding_rule" label="编码规则" width="140" />
          <el-table-column prop="description" label="说明" min-width="240" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeMain(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="生命周期" name="lifecycle">
        <el-table :data="lifecycles" row-key="id" height="620">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="nested-grid">
                <div class="toolbar compact-toolbar">
                  <strong>{{ row.name }} 状态流转</strong>
                  <el-button size="small" :icon="Plus" @click="openChildCreate(row)">新增状态</el-button>
                </div>
                <el-table :data="row.states" size="small" border>
                  <el-table-column prop="sequence" label="序号" width="70" />
                  <el-table-column prop="name" label="状态" width="120" />
                  <el-table-column prop="state_type" label="类型" width="110" />
                  <el-table-column prop="allow_edit" label="允许编辑" width="100" />
                  <el-table-column prop="require_workflow" label="需流程" width="90" />
                  <el-table-column prop="next_states" label="可流转到" min-width="180" />
                  <el-table-column label="操作" width="150">
                    <template #default="{ row: state }">
                      <el-button size="small" @click="openChildEdit(row, state)">编辑</el-button>
                      <el-button size="small" type="danger" @click="removeChild(state)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="object_type" label="对象" width="120" />
          <el-table-column prop="code" label="模板编码" width="150" />
          <el-table-column prop="name" label="模板名称" width="170" />
          <el-table-column prop="description" label="说明" min-width="260" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeMain(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="数据字典" name="dictionary">
        <el-table :data="dictionaryItems" height="620">
          <el-table-column prop="dict_code" label="字典编码" width="170" />
          <el-table-column prop="dict_name" label="字典名称" width="130" />
          <el-table-column prop="item_value" label="值" min-width="140" />
          <el-table-column prop="item_label" label="显示名" min-width="140" />
          <el-table-column prop="object_scope" label="适用对象" width="150" />
          <el-table-column prop="sequence" label="排序" width="80" />
          <el-table-column prop="status" label="状态" width="90" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeMain(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="760px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <template v-if="activeTab === 'coding'">
            <el-form-item label="对象"><el-input v-model="form.object_type" /></el-form-item>
            <el-form-item label="规则编码"><el-input v-model="form.code" /></el-form-item>
            <el-form-item label="规则名称"><el-input v-model="form.name" /></el-form-item>
            <el-form-item label="前缀"><el-input v-model="form.prefix" /></el-form-item>
            <el-form-item label="编码模式"><el-input v-model="form.pattern" /></el-form-item>
            <el-form-item label="当前流水"><el-input-number v-model="form.current_no" :min="0" /></el-form-item>
            <el-form-item label="样例"><el-input v-model="form.sample" /></el-form-item>
            <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          </template>
          <template v-else-if="activeTab === 'category'">
            <el-form-item label="对象"><el-input v-model="form.object_type" /></el-form-item>
            <el-form-item label="分类编码"><el-input v-model="form.code" /></el-form-item>
            <el-form-item label="分类名称"><el-input v-model="form.name" /></el-form-item>
            <el-form-item label="父分类"><el-input v-model="form.parent_code" /></el-form-item>
            <el-form-item label="生命周期"><el-input v-model="form.lifecycle_template" /></el-form-item>
            <el-form-item label="编码规则"><el-input v-model="form.coding_rule" /></el-form-item>
            <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
            <el-form-item label="说明"><el-input v-model="form.description" /></el-form-item>
          </template>
          <template v-else-if="activeTab === 'lifecycle'">
            <el-form-item label="模板编码"><el-input v-model="form.code" /></el-form-item>
            <el-form-item label="模板名称"><el-input v-model="form.name" /></el-form-item>
            <el-form-item label="对象"><el-input v-model="form.object_type" /></el-form-item>
            <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
            <el-form-item label="说明"><el-input v-model="form.description" /></el-form-item>
          </template>
          <template v-else>
            <el-form-item label="字典编码"><el-input v-model="form.dict_code" /></el-form-item>
            <el-form-item label="字典名称"><el-input v-model="form.dict_name" /></el-form-item>
            <el-form-item label="值"><el-input v-model="form.item_value" /></el-form-item>
            <el-form-item label="显示名"><el-input v-model="form.item_label" /></el-form-item>
            <el-form-item label="适用对象"><el-input v-model="form.object_scope" /></el-form-item>
            <el-form-item label="排序"><el-input-number v-model="form.sequence" :min="1" /></el-form-item>
            <el-form-item label="状态"><el-select v-model="form.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          </template>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMain">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="childDialogVisible" :title="childDialogTitle" width="680px">
      <el-form :model="childForm" label-width="100px">
        <div class="form-grid">
          <template v-if="activeTab === 'category'">
            <el-form-item label="属性名"><el-input v-model="childForm.name" /></el-form-item>
            <el-form-item label="字段键"><el-input v-model="childForm.field_key" /></el-form-item>
            <el-form-item label="类型"><el-select v-model="childForm.data_type"><el-option label="文本" value="文本" /><el-option label="数字" value="数字" /><el-option label="枚举" value="枚举" /><el-option label="日期" value="日期" /></el-select></el-form-item>
            <el-form-item label="必填"><el-select v-model="childForm.required"><el-option label="是" value="是" /><el-option label="否" value="否" /></el-select></el-form-item>
            <el-form-item label="字典编码"><el-input v-model="childForm.dictionary_code" /></el-form-item>
            <el-form-item label="默认值"><el-input v-model="childForm.default_value" /></el-form-item>
            <el-form-item label="排序"><el-input-number v-model="childForm.sequence" :min="1" /></el-form-item>
          </template>
          <template v-else>
            <el-form-item label="排序"><el-input-number v-model="childForm.sequence" :min="1" /></el-form-item>
            <el-form-item label="状态名"><el-input v-model="childForm.name" /></el-form-item>
            <el-form-item label="状态类型"><el-input v-model="childForm.state_type" /></el-form-item>
            <el-form-item label="允许编辑"><el-select v-model="childForm.allow_edit"><el-option label="是" value="是" /><el-option label="否" value="否" /></el-select></el-form-item>
            <el-form-item label="需流程"><el-select v-model="childForm.require_workflow"><el-option label="是" value="是" /><el-option label="否" value="否" /></el-select></el-form-item>
            <el-form-item label="可流转到"><el-input v-model="childForm.next_states" /></el-form-item>
          </template>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="childDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveChild">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import {
  createAttributeTemplate,
  createCategoryTemplate,
  createCodingRule,
  createDictionaryItem,
  createLifecycleState,
  createLifecycleTemplate,
  deleteAttributeTemplate,
  deleteCategoryTemplate,
  deleteCodingRule,
  deleteDictionaryItem,
  deleteLifecycleState,
  deleteLifecycleTemplate,
  getCategoryTemplates,
  getCodingRules,
  getDictionaryItems,
  getLifecycleTemplates,
  updateAttributeTemplate,
  updateCategoryTemplate,
  updateCodingRule,
  updateDictionaryItem,
  updateLifecycleState,
  updateLifecycleTemplate,
} from '../api'

const loading = ref(true)
const activeTab = ref('coding')
const codingRules = ref<any[]>([])
const categories = ref<any[]>([])
const lifecycles = ref<any[]>([])
const dictionaryItems = ref<any[]>([])
const dialogVisible = ref(false)
const childDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const childEditingId = ref<number | null>(null)
const parentRow = ref<any | null>(null)
const form = ref<any>({})
const childForm = ref<any>({})

const dialogTitle = computed(() => `${editingId.value ? '编辑' : '新增'}${tabName.value}`)
const childDialogTitle = computed(() => `${childEditingId.value ? '编辑' : '新增'}${activeTab.value === 'category' ? '属性' : '状态'}`)
const tabName = computed(() => ({ coding: '编码规则', category: '分类模板', lifecycle: '生命周期', dictionary: '字典项' }[activeTab.value] || '配置'))

async function loadRows() {
  const [rules, categoryRows, lifecycleRows, dictionaries] = await Promise.all([
    getCodingRules({ page: 1, page_size: 1000 }),
    getCategoryTemplates({ page: 1, page_size: 1000 }),
    getLifecycleTemplates({ page: 1, page_size: 1000 }),
    getDictionaryItems({ page: 1, page_size: 1000 }),
  ])
  codingRules.value = rules.items ?? rules
  categories.value = categoryRows.items ?? categoryRows
  lifecycles.value = lifecycleRows.items ?? lifecycleRows
  dictionaryItems.value = dictionaries.items ?? dictionaries
}

function emptyMainForm() {
  if (activeTab.value === 'coding') return { object_type: '', code: '', name: '', prefix: '', pattern: '', current_no: 0, sample: '', status: '启用', owner: '' }
  if (activeTab.value === 'category') return { object_type: '', code: '', name: '', parent_code: '', lifecycle_template: '', coding_rule: '', status: '启用', description: '' }
  if (activeTab.value === 'lifecycle') return { code: '', name: '', object_type: '', status: '启用', description: '' }
  return { dict_code: '', dict_name: '', item_value: '', item_label: '', object_scope: '', sequence: 1, status: '启用' }
}

function emptyChildForm() {
  if (activeTab.value === 'category') return { name: '', field_key: '', data_type: '文本', required: '否', dictionary_code: '', default_value: '', sequence: 1 }
  return { sequence: 1, name: '', state_type: '中间态', allow_edit: '是', require_workflow: '否', next_states: '' }
}

function openCreate() {
  editingId.value = null
  form.value = emptyMainForm()
  dialogVisible.value = true
}

function openEdit(row: any) {
  editingId.value = row.id
  form.value = { ...row }
  delete form.value.attributes
  delete form.value.states
  dialogVisible.value = true
}

async function saveMain() {
  if (activeTab.value === 'coding') editingId.value ? await updateCodingRule(editingId.value, form.value) : await createCodingRule(form.value)
  if (activeTab.value === 'category') editingId.value ? await updateCategoryTemplate(editingId.value, form.value) : await createCategoryTemplate(form.value)
  if (activeTab.value === 'lifecycle') editingId.value ? await updateLifecycleTemplate(editingId.value, form.value) : await createLifecycleTemplate(form.value)
  if (activeTab.value === 'dictionary') editingId.value ? await updateDictionaryItem(editingId.value, form.value) : await createDictionaryItem(form.value)
  ElMessage.success('配置已保存')
  dialogVisible.value = false
  await loadRows()
}

async function removeMain(row: any) {
  await ElMessageBox.confirm(`确认删除 ${row.name || row.code || row.dict_name || row.param_key}？`, '删除确认', { type: 'warning' })
  if (activeTab.value === 'coding') await deleteCodingRule(row.id)
  if (activeTab.value === 'category') await deleteCategoryTemplate(row.id)
  if (activeTab.value === 'lifecycle') await deleteLifecycleTemplate(row.id)
  if (activeTab.value === 'dictionary') await deleteDictionaryItem(row.id)
  ElMessage.success('配置已删除')
  await loadRows()
}

function openChildCreate(row: any) {
  parentRow.value = row
  childEditingId.value = null
  childForm.value = emptyChildForm()
  childDialogVisible.value = true
}

function openChildEdit(row: any, child: any) {
  parentRow.value = row
  childEditingId.value = child.id
  childForm.value = { ...child }
  childDialogVisible.value = true
}

async function saveChild() {
  if (!parentRow.value) return
  if (activeTab.value === 'category') {
    childEditingId.value ? await updateAttributeTemplate(childEditingId.value, childForm.value) : await createAttributeTemplate(parentRow.value.id, childForm.value)
  } else {
    childEditingId.value ? await updateLifecycleState(childEditingId.value, childForm.value) : await createLifecycleState(parentRow.value.id, childForm.value)
  }
  ElMessage.success('子项已保存')
  childDialogVisible.value = false
  await loadRows()
}

async function removeChild(row: any) {
  await ElMessageBox.confirm(`确认删除 ${row.name}？`, '删除确认', { type: 'warning' })
  activeTab.value === 'category' ? await deleteAttributeTemplate(row.id) : await deleteLifecycleState(row.id)
  ElMessage.success('子项已删除')
  await loadRows()
}

watch(activeTab, () => {
  dialogVisible.value = false
  childDialogVisible.value = false
})

onMounted(async () => {
  await loadRows()
  loading.value = false
})
</script>
