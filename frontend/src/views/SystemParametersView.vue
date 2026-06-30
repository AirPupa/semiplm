<template>
  <div class="panel system-param-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>系统参数</strong>
        <span class="muted"> · 维护公司、文件存储、编码前缀和日期格式等运行参数</span>
      </div>
      <div class="toolbar-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索键/值/分组/说明"
          :prefix-icon="Search"
          clearable
          style="width: 240px"
          @keyup.enter="onSearch"
          @clear="onSearch"
        />
        <el-button type="primary" :icon="Plus" @click="openCreate">新增参数</el-button>
      </div>
    </div>

    <div class="system-param-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="param_key" label="参数键" width="220" fixed show-overflow-tooltip />
        <el-table-column prop="param_value" label="参数值" min-width="240" show-overflow-tooltip />
        <el-table-column prop="param_group" label="分组" width="130" />
        <el-table-column prop="description" label="说明" min-width="280" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑系统参数' : '新增系统参数'" width="640px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="参数键">
            <el-input v-model="form.param_key" placeholder="例如 company.name" />
          </el-form-item>
          <el-form-item label="分组">
            <el-select v-model="form.param_group" filterable allow-create default-first-option>
              <el-option label="系统" value="系统" />
              <el-option label="公司" value="公司" />
              <el-option label="文件" value="文件" />
              <el-option label="编码" value="编码" />
              <el-option label="日期" value="日期" />
              <el-option label="集成" value="集成" />
            </el-select>
          </el-form-item>
          <el-form-item label="参数值" class="form-wide">
            <el-input v-model="form.param_value" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="说明" class="form-wide">
            <el-input v-model="form.description" />
          </el-form-item>
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
import { createSystemParameter, deleteSystemParameter, getSystemParameters, updateSystemParameter } from '../api'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage<any>(getSystemParameters)
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { param_key: '', param_value: '', param_group: '系统', description: '' }
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
  if (!form.value.param_key?.trim()) {
    ElMessage.warning('请填写参数键')
    return
  }
  editingId.value ? await updateSystemParameter(editingId.value, form.value) : await createSystemParameter(form.value)
  ElMessage.success('系统参数已保存')
  dialogVisible.value = false
  await loadData()
}

async function remove(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除系统参数 ${row.param_key}？`, '删除确认', { type: 'warning' })
    await deleteSystemParameter(row.id)
    ElMessage.success('系统参数已删除')
    await loadData()
  } catch {
    // 用户取消删除时保持静默。
  }
}

onMounted(loadData)
</script>

<style scoped>
.system-param-panel {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 82px);
}

.system-param-table-wrap {
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
