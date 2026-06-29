<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>操作日志</strong><span class="muted"> · 关键对象操作审计追溯</span></div>
      <div class="toolbar-actions">
        <el-select v-model="filterObjectType" clearable placeholder="对象类型" style="width:140px" @change="load">
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
        <el-select v-model="filterAction" clearable placeholder="动作" style="width:120px" @change="load">
          <el-option label="新增" value="新增" />
          <el-option label="编辑" value="编辑" />
          <el-option label="删除" value="删除" />
          <el-option label="提交" value="提交" />
          <el-option label="发布" value="发布" />
          <el-option label="关闭" value="关闭" />
        </el-select>
        <el-button @click="load">刷新</el-button>
      </div>
    </div>
    <el-table :data="logs" stripe height="680">
      <el-table-column prop="operated_at" label="时间" width="170" />
      <el-table-column prop="action" label="动作" width="90" />
      <el-table-column prop="object_type" label="对象类型" width="100" />
      <el-table-column prop="object_no" label="对象编号" min-width="180" show-overflow-tooltip />
      <el-table-column prop="summary" label="摘要" min-width="320" show-overflow-tooltip />
      <el-table-column prop="operated_by" label="操作人" width="110" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getAuditLogs } from '../api'

const loading = ref(true)
const logs = ref<any[]>([])
const filterObjectType = ref('')
const filterAction = ref('')

async function load() {
  const params: any = { limit: 300 }
  if (filterObjectType.value) params.object_type = filterObjectType.value
  if (filterAction.value) params.action = filterAction.value
  logs.value = await getAuditLogs(params)
}

onMounted(async () => {
  await load()
  loading.value = false
})
</script>
