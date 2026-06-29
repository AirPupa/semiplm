<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel list-panel">
      <div class="toolbar">
        <div>
          <strong>产品版本基线</strong>
          <span class="muted"> · 将型号、EBOM、工艺、规格文件和变更冻结为可发布数据包</span>
        </div>
        <div class="toolbar-actions">
          <el-input v-model="keyword" placeholder="搜索基线编号/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
          <el-button type="primary" :icon="CollectionTag">创建基线</el-button>
        </div>
      </div>
      <div class="list-table-wrap">
        <el-table :data="items" highlight-current-row @current-change="selected = $event" height="100%">
          <el-table-column prop="baseline_no" label="基线编号" width="190" fixed />
          <el-table-column prop="name" label="基线名称" min-width="220" />
          <el-table-column prop="product_model" label="型号" width="130" />
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="status" label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === '已发布' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="released_at" label="发布日期" width="120" />
        </el-table>
      </div>
      <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
      </div>
    </div>
    <div class="panel detail-panel">
      <div class="panel-title">{{ selected?.name || '基线明细' }}</div>
      <el-table :data="selected?.items || []" size="small">
        <el-table-column prop="item_type" label="对象类型" width="100" />
        <el-table-column prop="item_no" label="对象编号" width="170" />
        <el-table-column prop="title" label="名称" min-width="220" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="status" label="状态" width="100" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CollectionTag, Search } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { getBaselines } from '../api'
import { useListPage } from '../composables/useListPage'

const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getBaselines)
const selected = ref<any>()

onMounted(async () => {
  await loadData()
  selected.value = (items.value || [])[0]
})
</script>
