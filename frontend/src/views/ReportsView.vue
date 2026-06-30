<template>
  <div class="panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>报表与审计</strong>
        <span class="muted"> · 数据完整度、变更周期、项目进度、质量闭环、操作审计</span>
      </div>
      <el-button @click="reloadAll">刷新全部</el-button>
    </div>
    <el-tabs v-model="activeTab" class="compact-tabs" @tab-change="onTabChange">
      <!-- 数据完整度 -->
      <el-tab-pane label="数据完整度" name="completeness">
        <div v-if="completeness" class="report-body">
          <div class="report-tab-toolbar">
            <el-button size="small" @click="() => doExport('completeness')" :loading="exporting === 'completeness'">导出 Excel</el-button>
          </div>
          <el-row :gutter="12" class="metric-row">
            <el-col :span="6" v-for="m in completenessMetrics" :key="m.key">
              <el-card shadow="never" class="metric-card">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value">{{ m.value }}<span class="metric-suffix">{{ m.suffix }}</span></div>
                <el-progress :percentage="m.value" :stroke-width="6" :show-text="false" :color="m.color" />
                <div class="metric-foot">{{ m.foot }}</div>
              </el-card>
            </el-col>
          </el-row>
          <div class="section-title">产品资料齐套明细</div>
          <el-table :data="completeness.products || []" size="small" height="420">
            <el-table-column prop="model" label="型号" width="130" fixed />
            <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="lifecycle" label="生命周期" width="100" />
            <el-table-column prop="owner" label="负责人" width="100" />
            <el-table-column label="需求" width="70" align="center">
              <template #default="{ row }"><el-tag size="small" :type="row.has_req ? 'success' : 'info'">{{ row.has_req ? '有' : '无' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="BOM" width="70" align="center">
              <template #default="{ row }"><el-tag size="small" :type="row.has_bom ? 'success' : 'info'">{{ row.has_bom ? '有' : '无' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="工艺" width="70" align="center">
              <template #default="{ row }"><el-tag size="small" :type="row.has_route ? 'success' : 'info'">{{ row.has_route ? '有' : '无' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="文档" width="70" align="center">
              <template #default="{ row }"><el-tag size="small" :type="row.has_doc ? 'success' : 'info'">{{ row.has_doc ? '有' : '无' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="完整度" width="160">
              <template #default="{ row }"><el-progress :percentage="row.completeness" :stroke-width="8" /></template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 变更周期 -->
      <el-tab-pane label="变更周期" name="change">
        <div v-if="changeCycle" class="report-body">
          <div class="report-tab-toolbar">
            <el-button size="small" @click="() => doExport('change')" :loading="exporting === 'change'">导出 Excel</el-button>
          </div>
          <el-row :gutter="12" class="metric-row">
            <el-col :span="6" v-for="m in changeMetrics" :key="m.key">
              <el-card shadow="never" class="metric-card">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value">{{ m.value }}<span class="metric-suffix">{{ m.suffix }}</span></div>
                <div class="metric-foot">{{ m.foot }}</div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="12" class="section-row">
            <el-col :span="8">
              <div class="section-title">按状态分布</div>
              <div class="dist-list">
                <div v-for="row in changeCycle.by_status || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <el-progress :percentage="distPercent(row.value, changeCycle.summary.change_total)" :stroke-width="10" />
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(changeCycle.by_status || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="section-title">按类型分布</div>
              <div class="dist-list">
                <div v-for="row in changeCycle.by_type || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <el-progress :percentage="distPercent(row.value, changeCycle.summary.change_total)" :stroke-width="10" />
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(changeCycle.by_type || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="section-title">按优先级分布</div>
              <div class="dist-list">
                <div v-for="row in changeCycle.by_priority || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <el-progress :percentage="distPercent(row.value, changeCycle.summary.change_total)" :stroke-width="10" :color="row.name === '高' ? '#f56c6c' : row.name === '中' ? '#e6a23c' : '#409eff'" />
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(changeCycle.by_priority || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
          </el-row>
          <div class="section-title">近期变更 ECA 关闭率</div>
          <el-table :data="changeCycle.recent_changes || []" size="small" height="320">
            <el-table-column prop="change_no" label="变更单" width="160" fixed />
            <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="change_type" label="类型" width="100" />
            <el-table-column prop="priority" label="优先级" width="80">
              <template #default="{ row }"><el-tag size="small" :type="row.priority === '高' ? 'danger' : 'warning'">{{ row.priority }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column label="ECA 进度" width="180">
              <template #default="{ row }">{{ row.eca_closed }}/{{ row.eca_total }} ({{ row.eca_close_rate }}%)</template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 项目进度 -->
      <el-tab-pane label="项目进度" name="project">
        <div v-if="projectProgress" class="report-body">
          <div class="report-tab-toolbar">
            <el-button size="small" @click="() => doExport('project')" :loading="exporting === 'project'">导出 Excel</el-button>
          </div>
          <el-row :gutter="12" class="metric-row">
            <el-col :span="6" v-for="m in projectMetrics" :key="m.key">
              <el-card shadow="never" class="metric-card">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value">{{ m.value }}<span class="metric-suffix">{{ m.suffix }}</span></div>
                <div class="metric-foot">{{ m.foot }}</div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="12" class="section-row">
            <el-col :span="8">
              <div class="section-title">阶段门分布</div>
              <div class="dist-list">
                <div v-for="row in projectProgress.by_phase || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <el-progress :percentage="distPercent(row.value, projectProgress.summary.project_total)" :stroke-width="10" />
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(projectProgress.by_phase || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="section-title">风险等级分布</div>
              <div class="dist-list">
                <div v-for="row in projectProgress.by_risk || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <el-progress :percentage="distPercent(row.value, projectProgress.summary.project_total)" :stroke-width="10" :color="row.name === '高' ? '#f56c6c' : row.name === '中' ? '#e6a23c' : '#67c23a'" />
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(projectProgress.by_risk || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="section-title">风险类型分布</div>
              <div class="dist-list">
                <div v-for="row in projectProgress.by_risk_type || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(projectProgress.by_risk_type || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
          </el-row>
          <div class="section-title">逾期任务 ({{ (projectProgress.overdue_tasks || []).length }})</div>
          <el-table :data="projectProgress.overdue_tasks || []" size="small" height="220">
            <el-table-column prop="project_no" label="项目编号" width="140" />
            <el-table-column prop="project_name" label="项目名称" min-width="160" show-overflow-tooltip />
            <el-table-column prop="name" label="任务" min-width="180" show-overflow-tooltip />
            <el-table-column prop="phase" label="阶段" width="100" />
            <el-table-column prop="owner" label="负责人" width="100" />
            <el-table-column prop="due_date" label="截止日期" width="110">
              <template #default="{ row }"><span class="text-danger">{{ row.due_date }}</span></template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" />
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 质量闭环 -->
      <el-tab-pane label="质量闭环" name="quality">
        <div v-if="qualityClosure" class="report-body">
          <div class="report-tab-toolbar">
            <el-button size="small" @click="() => doExport('quality')" :loading="exporting === 'quality'">导出 Excel</el-button>
          </div>
          <el-row :gutter="12" class="metric-row">
            <el-col :span="6" v-for="m in qualityMetrics" :key="m.key">
              <el-card shadow="never" class="metric-card">
                <div class="metric-label">{{ m.label }}</div>
                <div class="metric-value">{{ m.value }}<span class="metric-suffix">{{ m.suffix }}</span></div>
                <el-progress v-if="m.progress !== undefined" :percentage="m.progress" :stroke-width="6" :show-text="false" :color="m.color" />
                <div class="metric-foot">{{ m.foot }}</div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="12" class="section-row">
            <el-col :span="8">
              <div class="section-title">问题严重度分布</div>
              <div class="dist-list">
                <div v-for="row in qualityClosure.issue_by_severity || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <el-progress :percentage="distPercent(row.value, qualityClosure.summary.issue_total)" :stroke-width="10" :color="row.name === '高' ? '#f56c6c' : row.name === '中' ? '#e6a23c' : '#67c23a'" />
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(qualityClosure.issue_by_severity || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="section-title">问题状态分布</div>
              <div class="dist-list">
                <div v-for="row in qualityClosure.issue_by_status || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <el-progress :percentage="distPercent(row.value, qualityClosure.summary.issue_total)" :stroke-width="10" />
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(qualityClosure.issue_by_status || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="section-title">CAPA 来源分布</div>
              <div class="dist-list">
                <div v-for="row in qualityClosure.capa_by_source || []" :key="row.name" class="dist-item">
                  <span class="dist-name">{{ row.name }}</span>
                  <span class="dist-value">{{ row.value }}</span>
                </div>
                <div v-if="!(qualityClosure.capa_by_source || []).length" class="muted">暂无数据</div>
              </div>
            </el-col>
          </el-row>
          <div v-if="(qualityClosure.quality_trend || []).length" class="section-title">良率趋势（CP / FT）</div>
          <div v-if="(qualityClosure.quality_trend || []).length" class="trend-chart-wrap">
            <svg class="trend-chart" :viewBox="`0 0 ${chartW} ${chartH}`" preserveAspectRatio="xMidYMid meet">
              <line v-for="gy in gridYs" :key="'g'+gy" :x1="padL" :x2="chartW - padR" :y1="gy" :y2="gy" stroke="#eee" stroke-width="1" />
              <text v-for="(gy, i) in gridYs" :key="'t'+gy" :x="padL - 8" :y="gy + 4" text-anchor="end" font-size="11" fill="#999">{{ 100 - i * 20 }}</text>
              <polyline :points="cpLinePoints" fill="none" stroke="#409eff" stroke-width="2" />
              <polyline :points="ftLinePoints" fill="none" stroke="#67c23a" stroke-width="2" />
              <circle v-for="(p, i) in cpPoints" :key="'c'+i" :cx="p.x" :cy="p.y" r="3" fill="#409eff" />
              <circle v-for="(p, i) in ftPoints" :key="'f'+i" :cx="p.x" :cy="p.y" r="3" fill="#67c23a" />
              <text v-for="(p, i) in xLabels" :key="'x'+i" :x="p.x" :y="chartH - padB + 16" text-anchor="middle" font-size="10" fill="#999">{{ p.label }}</text>
              <g transform="translate(80, 12)">
                <rect x="0" y="0" width="12" height="3" fill="#409eff" /><text x="18" y="4" font-size="11" fill="#666">CP 良率</text>
                <rect x="90" y="0" width="12" height="3" fill="#67c23a" /><text x="108" y="4" font-size="11" fill="#666">FT 良率</text>
              </g>
            </svg>
          </div>
          <div class="section-title">质量问题清单（含 CAPA 关闭情况）</div>
          <el-table :data="qualityClosure.issues || []" size="small" height="320">
            <el-table-column prop="issue_no" label="问题编号" width="130" fixed />
            <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="product_model" label="型号" width="120" />
            <el-table-column prop="lot_no" label="Lot" width="110" />
            <el-table-column prop="severity" label="严重度" width="80">
              <template #default="{ row }"><el-tag size="small" :type="row.severity === '高' ? 'danger' : row.severity === '中' ? 'warning' : 'info'">{{ row.severity }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="110" />
            <el-table-column label="CAPA" width="130">
              <template #default="{ row }">{{ row.capa_closed }}/{{ row.capa_count }}</template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  exportReportChangeCycle,
  exportReportCompleteness,
  exportReportProjectProgress,
  exportReportQualityClosure,
  getReportChangeCycle,
  getReportCompleteness,
  getReportProjectProgress,
  getReportQualityClosure,
} from '../api'

const loading = ref(true)
const activeTab = ref('completeness')
const exporting = ref('')
const completeness = ref<any>(null)
const changeCycle = ref<any>(null)
const projectProgress = ref<any>(null)
const qualityClosure = ref<any>(null)

const completenessMetrics = computed(() => {
  const s = completeness.value?.summary || {}
  return [
    { key: 'doc', label: '文档覆盖率', value: s.doc_coverage || 0, suffix: '%', color: '#409eff', foot: '产品有文档比例' },
    { key: 'bom', label: 'BOM 覆盖率', value: s.bom_coverage || 0, suffix: '%', color: '#67c23a', foot: '产品有 BOM 比例' },
    { key: 'route', label: '工艺覆盖率', value: s.route_coverage || 0, suffix: '%', color: '#e6a23c', foot: '产品有工艺路线比例' },
    { key: 'full', label: '资料齐套产品', value: s.full_ready_count || 0, suffix: ` / ${s.product_total || 0}`, color: '#f56c6c', foot: '需求/BOM/工艺/文档 全有' }
  ]
})

const changeMetrics = computed(() => {
  const s = changeCycle.value?.summary || {}
  return [
    { key: 'total', label: '变更单总数', value: s.change_total || 0, suffix: '', foot: '全生命周期' },
    { key: 'eca', label: 'ECA 总数', value: s.eca_total || 0, suffix: '', foot: '执行动作数' },
    { key: 'closed', label: 'ECA 已完成', value: s.eca_closed || 0, suffix: '', foot: '已关闭动作' },
    { key: 'rate', label: 'ECA 关闭率', value: s.eca_close_rate || 0, suffix: '%', foot: '完成动作占比' }
  ]
})

const projectMetrics = computed(() => {
  const s = projectProgress.value?.summary || {}
  return [
    { key: 'proj', label: '项目总数', value: s.project_total || 0, suffix: '', foot: 'NPI 项目' },
    { key: 'overdue', label: '逾期任务数', value: s.overdue_task_count || 0, suffix: '', foot: '截止日已过未完成' },
    { key: 'avg', label: '平均进度', value: s.avg_progress || 0, suffix: '%', foot: '所有项目平均' },
    { key: 'risk', label: '未关闭风险', value: s.open_risk_count || 0, suffix: '', foot: '待处理风险数' }
  ]
})

const qualityMetrics = computed(() => {
  const s = qualityClosure.value?.summary || {}
  return [
    { key: 'issue', label: '质量问题总数', value: s.issue_total || 0, suffix: '', foot: '所有质量问题' },
    { key: 'issue_rate', label: '问题关闭率', value: s.issue_close_rate || 0, suffix: '%', progress: s.issue_close_rate || 0, color: '#67c23a', foot: '已关闭占比' },
    { key: 'capa', label: 'CAPA 总数', value: s.capa_total || 0, suffix: '', foot: '纠正预防措施' },
    { key: 'capa_rate', label: 'CAPA 关闭率', value: s.capa_close_rate || 0, suffix: '%', progress: s.capa_close_rate || 0, color: '#409eff', foot: '已关闭 CAPA 占比' }
  ]
})

function distPercent(value: number, total: number): number {
  if (!total) return 0
  return Math.round((value / total) * 100)
}

async function loadCompleteness() {
  if (!completeness.value) completeness.value = await getReportCompleteness()
}
async function loadChange() {
  if (!changeCycle.value) changeCycle.value = await getReportChangeCycle()
}
async function loadProject() {
  if (!projectProgress.value) projectProgress.value = await getReportProjectProgress()
}
async function loadQuality() {
  if (!qualityClosure.value) qualityClosure.value = await getReportQualityClosure()
}

async function onTabChange(name: string) {
  if (name === 'completeness') await loadCompleteness()
  else if (name === 'change') await loadChange()
  else if (name === 'project') await loadProject()
  else if (name === 'quality') await loadQuality()
}

// ---- 良率趋势 SVG 图表 ----
const chartW = 760
const chartH = 260
const padL = 36
const padR = 16
const padT = 28
const padB = 32
const gridYs = computed(() => {
  const ys: number[] = []
  for (let i = 0; i <= 5; i++) {
    ys.push(padT + (i * (chartH - padT - padB)) / 5)
  }
  return ys
})
const trendData = computed(() => qualityClosure.value?.quality_trend || [])
const cpPoints = computed(() => {
  const data = trendData.value
  if (!data.length) return []
  const n = data.length
  const w = chartW - padL - padR
  const h = chartH - padT - padB
  return data.map((d: any, i: number) => ({
    x: padL + (n === 1 ? w / 2 : (i * w) / (n - 1)),
    y: padT + h - (Math.max(0, Math.min(100, d.cp || 0)) / 100) * h,
  }))
})
const ftPoints = computed(() => {
  const data = trendData.value
  if (!data.length) return []
  const n = data.length
  const w = chartW - padL - padR
  const h = chartH - padT - padB
  return data.map((d: any, i: number) => ({
    x: padL + (n === 1 ? w / 2 : (i * w) / (n - 1)),
    y: padT + h - (Math.max(0, Math.min(100, d.ft || 0)) / 100) * h,
  }))
})
const cpLinePoints = computed(() => cpPoints.value.map((p: any) => `${p.x},${p.y}`).join(' '))
const ftLinePoints = computed(() => ftPoints.value.map((p: any) => `${p.x},${p.y}`).join(' '))
const xLabels = computed(() => {
  const data = trendData.value
  if (!data.length) return []
  const n = data.length
  const w = chartW - padL - padR
  return data.map((d: any, i: number) => ({
    x: padL + (n === 1 ? w / 2 : (i * w) / (n - 1)),
    label: (d.date || '').slice(5),
  }))
})

async function doExport(type: string) {
  exporting.value = type
  try {
    if (type === 'completeness') await exportReportCompleteness()
    else if (type === 'change') await exportReportChangeCycle()
    else if (type === 'project') await exportReportProjectProgress()
    else if (type === 'quality') await exportReportQualityClosure()
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = ''
  }
}

async function reloadAll() {
  loading.value = true
  try {
    completeness.value = await getReportCompleteness()
    changeCycle.value = await getReportChangeCycle()
    projectProgress.value = await getReportProjectProgress()
    qualityClosure.value = await getReportQualityClosure()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadCompleteness()
  loading.value = false
})
</script>

<style scoped>
.report-body {
  padding-top: 8px;
}
.metric-row {
  margin-bottom: 12px;
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
  margin: 16px 0 8px;
  color: var(--el-text-color-primary);
}
.section-row {
  margin-bottom: 12px;
}
.dist-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 4px;
}
.dist-item {
  display: grid;
  grid-template-columns: 80px 1fr 36px;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.dist-name {
  color: var(--el-text-color-regular);
}
.dist-value {
  text-align: right;
  font-weight: 600;
}
.text-danger {
  color: var(--el-color-danger);
}
.report-tab-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.trend-chart-wrap {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 16px;
}
.trend-chart {
  width: 100%;
  height: 260px;
}
</style>
