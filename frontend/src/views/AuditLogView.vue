<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>操作日志</strong><span class="muted"> · 关键对象操作审计追溯</span></div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索对象编号/摘要/操作人" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" style="width:220px" />
        <el-select v-model="filterObjectType" clearable placeholder="对象类型" style="width:130px" @change="onSearch">
          <el-option label="产品" value="产品" />
          <el-option label="BOM" value="BOM" />
          <el-option label="文档" value="文档" />
          <el-option label="变更" value="变更" />
          <el-option label="工艺路线" value="工艺路线" />
          <el-option label="项目" value="项目" />
          <el-option label="质量" value="质量" />
          <el-option label="物料" value="物料" />
          <el-option label="系统配置" value="系统配置" />
        </el-select>
        <el-select v-model="filterAction" clearable placeholder="动作" style="width:110px" @change="onSearch">
          <el-option v-for="o in actionTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button @click="onSearch">刷新</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" height="100%">
        <el-table-column prop="operated_at" label="时间" width="170" />
        <el-table-column prop="action" label="动作" width="90" />
        <el-table-column prop="object_type" label="对象类型" width="100" />
        <el-table-column prop="object_no" label="对象编号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="summary" label="摘要" min-width="320" show-overflow-tooltip />
        <el-table-column prop="operated_by" label="操作人" width="110" />
      </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { getAuditLogs } from '../api'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const filterObjectType = ref('')
const filterAction = ref('')
const actionTypeOptions = useDictionary('DICT_ACTION_TYPE').options
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(
  (params) => getAuditLogs({ ...params, object_type: filterObjectType.value, action: filterAction.value })
)

onMounted(async () => {
  await loadData()
})
</script>
