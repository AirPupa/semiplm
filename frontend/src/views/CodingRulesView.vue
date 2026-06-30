<template>
  <div class="panel coding-rule-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>编码规则</strong>
        <span class="muted"> · 维护产品、物料、BOM、文档、变更、项目等对象编号规则</span>
      </div>
      <div class="toolbar-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索规则编码/名称"
          :prefix-icon="Search"
          clearable
          style="width: 220px"
          @keyup.enter="onSearch"
          @clear="onSearch"
        />
        <el-button type="primary" :icon="Plus" @click="openCreate">新增规则</el-button>
      </div>
    </div>

    <div class="coding-rule-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="object_type" label="对象" width="120" fixed />
        <el-table-column prop="code" label="规则编码" width="160" />
        <el-table-column prop="name" label="规则名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="prefix" label="前缀" width="100" />
        <el-table-column prop="pattern" label="编码模式" min-width="240" show-overflow-tooltip />
        <el-table-column prop="current_no" label="当前流水" width="100" />
        <el-table-column prop="sample" label="样例" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === '启用' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑编码规则' : '新增编码规则'" width="760px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="对象">
            <el-select v-model="form.object_type" filterable allow-create default-first-option>
              <el-option label="产品" value="产品" />
              <el-option label="物料" value="物料" />
              <el-option label="BOM" value="BOM" />
              <el-option label="文档" value="文档" />
              <el-option label="需求" value="需求" />
              <el-option label="变更" value="变更" />
              <el-option label="项目" value="项目" />
              <el-option label="质量" value="质量" />
            </el-select>
          </el-form-item>
          <el-form-item label="规则编码"><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="规则名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="前缀"><el-input v-model="form.prefix" /></el-form-item>
          <el-form-item label="编码模式" class="form-wide">
            <el-input v-model="form.pattern" placeholder="{PREFIX}-{YYYYMM}-{SEQ4}" />
          </el-form-item>
          <el-form-item label="当前流水"><el-input-number v-model="form.current_no" :min="0" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="启用" value="启用" />
              <el-option label="停用" value="停用" />
            </el-select>
          </el-form-item>
          <el-form-item label="样例" class="form-wide"><el-input v-model="form.sample" /></el-form-item>
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
import { createCodingRule, deleteCodingRule, getCodingRules, updateCodingRule } from '../api'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage<any>(getCodingRules)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { object_type: '', code: '', name: '', prefix: '', pattern: '', current_no: 0, sample: '', status: '启用', owner: '' }
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
  if (!form.value.code?.trim() || !form.value.name?.trim()) {
    ElMessage.warning('请填写规则编码和规则名称')
    return
  }
  editingId.value ? await updateCodingRule(editingId.value, form.value) : await createCodingRule(form.value)
  ElMessage.success('编码规则已保存')
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除编码规则 ${row.code}？`, '删除确认', { type: 'warning' })
    await deleteCodingRule(row.id)
    ElMessage.success('编码规则已删除')
    await loadData()
  } catch {
    // 用户取消删除时保持静默。
  }
}

onMounted(loadData)
</script>

<style scoped>
.coding-rule-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 82px);
}

.coding-rule-table-wrap {
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
