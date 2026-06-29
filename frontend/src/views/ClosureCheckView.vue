<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>业务闭环验证</strong>
        <span class="muted"> · 端到端检查产品在 9 个业务环节的数据完整性，定位断点</span>
      </div>
      <el-button @click="loadData">刷新</el-button>
    </div>

    <template v-if="data">
      <!-- 顶部指标卡 -->
      <el-row :gutter="12" class="metric-row">
        <el-col :span="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">产品总数</div>
            <div class="metric-value">{{ data.summary.product_total }}</div>
            <div class="metric-foot">参与闭环验证</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">完整闭环产品</div>
            <div class="metric-value text-success">{{ data.summary.full_closed }}</div>
            <div class="metric-foot">9 环节全有数据</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">整体闭环率</div>
            <div class="metric-value">{{ data.summary.closure_rate }}<span class="metric-suffix">%</span></div>
            <el-progress :percentage="data.summary.closure_rate" :stroke-width="6" :show-text="false" color="#67c23a" />
            <div class="metric-foot">完整闭环产品占比</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="never" class="metric-card">
            <div class="metric-label">断点总数</div>
            <div class="metric-value" :class="{ 'text-danger': data.summary.total_breakpoints > 0 }">{{ data.summary.total_breakpoints }}</div>
            <div class="metric-foot">缺失环节累计</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 环节覆盖率横向条 -->
      <div class="section-title">环节覆盖率</div>
      <div class="stage-coverage">
        <div v-for="s in data.stage_coverage" :key="s.key" class="coverage-item">
          <div class="coverage-head">
            <span class="coverage-label">{{ s.label }}</span>
            <span class="coverage-rate" :class="rateClass(s.rate)">{{ s.rate }}%</span>
          </div>
          <el-progress :percentage="s.rate" :stroke-width="10" :show-text="false" :color="rateColor(s.rate)" />
          <div class="coverage-foot">{{ s.ok_count }} / {{ s.total }} 产品覆盖</div>
        </div>
      </div>

      <!-- 产品 × 环节矩阵 -->
      <div class="section-title">产品闭环矩阵</div>
      <el-table :data="data.products || []" size="small" height="480" :row-class-name="rowClass">
        <el-table-column prop="model" label="型号" width="130" fixed />
        <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="lifecycle" label="生命周期" width="100" />
        <el-table-column v-for="s in data.stages" :key="s.key" :label="s.label" width="92" align="center">
          <template #default="{ row }">
            <el-tooltip :content="stageTooltip(row, s.key)" placement="top">
              <span class="stage-dot" :class="row.stage_status[s.key]">
                {{ row.counts[s.key] }}
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="断点" width="70" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.breakpoints > 0 }">{{ row.breakpoints }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.closed ? 'success' : 'warning'">{{ row.closed ? '完整' : '有断点' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <!-- 图例 -->
      <div class="legend">
        <span class="legend-item"><span class="stage-dot ok">N</span> 有数据</span>
        <span class="legend-item"><span class="stage-dot gap">0</span> 缺失（断点）</span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getClosureCheck } from '../api'

const loading = ref(true)
const data = ref<any>(null)

async function loadData() {
  loading.value = true
  try {
    data.value = await getClosureCheck()
  } finally {
    loading.value = false
  }
}

function rateClass(rate: number): string {
  if (rate >= 80) return 'text-success'
  if (rate >= 50) return 'text-warning'
  return 'text-danger'
}

function rateColor(rate: number): string {
  if (rate >= 80) return '#67c23a'
  if (rate >= 50) return '#e6a23c'
  return '#f56c6c'
}

function stageTooltip(row: any, key: string): string {
  const status = row.stage_status[key]
  const cnt = row.counts[key]
  if (status === 'ok') return `有 ${cnt} 条数据`
  return '无数据（断点）'
}

function rowClass({ row }: { row: any }): string {
  return row.closed ? 'row-closed' : 'row-broken'
}

onMounted(loadData)
</script>

<style scoped>
.metric-row {
  margin-bottom: 16px;
}
.metric-card {
  text-align: center;
}
.metric-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}
.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}
.metric-suffix {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-left: 2px;
}
.metric-foot {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 6px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  margin: 18px 0 10px;
  color: var(--el-text-color-primary);
}
.stage-coverage {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 8px;
}
.coverage-item {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  padding: 10px;
  background: var(--el-bg-color);
}
.coverage-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.coverage-label {
  font-size: 13px;
  font-weight: 600;
}
.coverage-rate {
  font-size: 14px;
  font-weight: 600;
}
.coverage-foot {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}
.stage-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 22px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
}
.stage-dot.ok {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border: 1px solid var(--el-color-success-light-5);
}
.stage-dot.gap {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
  border: 1px solid var(--el-color-danger-light-5);
}
.legend {
  margin-top: 12px;
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.text-success {
  color: var(--el-color-success);
}
.text-warning {
  color: var(--el-color-warning);
}
.text-danger {
  color: var(--el-color-danger);
}
:deep(.row-broken) {
  background-color: var(--el-color-warning-light-9);
}
:deep(.row-closed) {
  background-color: var(--el-color-success-light-9);
}
</style>
