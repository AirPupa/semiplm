<template>
  <div class="grid-main" v-loading="loading">
    <div class="panel">
      <div class="toolbar">
        <div>
          <strong>产品版本基线</strong>
          <span class="muted"> · 将型号、EBOM、工艺、规格文件和变更冻结为可发布数据包</span>
        </div>
        <el-button type="primary" :icon="CollectionTag">创建基线</el-button>
      </div>
      <el-table :data="baselines" highlight-current-row @current-change="selected = $event" height="680">
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
    <div class="panel">
      <div class="panel-title">{{ selected?.name || '基线明细' }}</div>
      <el-table :data="selected?.items || []" size="small" height="680">
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
import { CollectionTag } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { getBaselines } from '../api'

const loading = ref(true)
const baselines = ref<any[]>([])
const selected = ref<any>()

onMounted(async () => {
  baselines.value = await getBaselines()
  selected.value = baselines.value[0]
  loading.value = false
})
</script>
