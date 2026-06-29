<template>
  <a-spin :loading="loading" dot>
    <div class="arco-dashboard">
      <section class="dashboard-head">
        <div>
          <span class="dashboard-kicker">R&D COMMAND CENTER</span>
          <h2>研发驾驶舱</h2>
          <p>围绕产品、项目、BOM、文档和质量趋势查看研发制造数据状态。</p>
        </div>
        <div class="dashboard-status">
          <a-button type="primary" status="normal" @click="reload">刷新数据</a-button>
        </div>
      </section>

      <a-row :gutter="[14, 14]" class="stat-row">
        <a-col v-for="item in metricCards" :key="item.key" :xs="24" :sm="12" :lg="item.span">
          <a-card :bordered="false" class="metric-card">
            <div class="metric-topline">
              <span>{{ item.label }}</span>
              <a-tag :color="item.color">{{ item.tag }}</a-tag>
            </div>
            <a-statistic :value="item.value" :suffix="item.suffix" :precision="0" />
            <a-progress
              v-if="item.progress !== undefined"
              :percent="item.progress"
              :show-text="false"
              size="small"
              :color="item.progressColor"
            />
            <div class="metric-foot">{{ item.hint }}</div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="[14, 14]" class="section-row">
        <a-col :xs="24" :xl="15">
          <a-card :bordered="false" class="dashboard-card">
            <template #title>良率趋势</template>
            <template #extra><span class="card-extra">CP / FT 最近批次</span></template>
            <div ref="yieldChart" class="arco-chart chart-main"></div>
          </a-card>
        </a-col>
        <a-col :xs="24" :xl="9">
          <a-card :bordered="false" class="dashboard-card">
            <template #title>生命周期分布</template>
            <template #extra><span class="card-extra">产品状态</span></template>
            <div ref="lifeChart" class="arco-chart chart-main"></div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="[14, 14]" class="section-row">
        <a-col :xs="24" :xl="10">
          <a-card :bordered="false" class="dashboard-card">
            <template #title>工程变更类型</template>
            <template #extra><span class="card-extra">ECR/ECO 统计</span></template>
            <div ref="changeChart" class="arco-chart chart-secondary"></div>
          </a-card>
        </a-col>
        <a-col :xs="24" :xl="14">
          <a-card :bordered="false" class="dashboard-card">
            <template #title>近期研发任务</template>
            <template #extra><span class="card-extra">阶段门交付物</span></template>
            <a-table
              row-key="name"
              :columns="taskColumns"
              :data="data.recent_tasks || []"
              :pagination="false"
              :bordered="false"
              :scroll="{ y: 278 }"
              size="small"
              class="task-table"
            />
          </a-card>
        </a-col>
      </a-row>
    </div>
  </a-spin>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { getDashboard } from '../api'

const loading = ref(true)
const data = ref<any>({})
const yieldChart = ref<HTMLElement>()
const lifeChart = ref<HTMLElement>()
const changeChart = ref<HTMLElement>()
const charts: echarts.ECharts[] = []

const metricCards = computed(() => [
  {
    key: 'products',
    label: '芯片型号',
    value: data.value.metrics?.products || 0,
    suffix: '',
    tag: '主数据',
    color: 'arcoblue',
    span: 5,
    hint: '产品、版本、资料包聚合'
  },
  {
    key: 'projects',
    label: '进行中项目',
    value: data.value.metrics?.active_projects || 0,
    suffix: '',
    tag: 'NPI',
    color: 'purple',
    span: 5,
    hint: 'APQP 阶段门推进'
  },
  {
    key: 'changes',
    label: '待处理变更',
    value: data.value.metrics?.pending_changes || 0,
    suffix: '',
    tag: 'ECR',
    color: 'orange',
    span: 5,
    hint: '影响分析与会签闭环'
  },
  {
    key: 'documents',
    label: '文档齐套率',
    value: data.value.metrics?.document_readiness || 0,
    suffix: '%',
    tag: 'DCC',
    color: 'green',
    span: 5,
    progress: (data.value.metrics?.document_readiness || 0) / 100,
    progressColor: '#00b42a',
    hint: '规格、工艺、测试、可靠性'
  },
  {
    key: 'bom',
    label: 'BOM 完整率',
    value: data.value.metrics?.bom_readiness || 0,
    suffix: '%',
    tag: 'EBOM',
    color: 'red',
    span: 4,
    progress: (data.value.metrics?.bom_readiness || 0) / 100,
    progressColor: '#f53f3f',
    hint: '结构、用量、替代料校验'
  }
])

const taskColumns = [
  { title: '任务', dataIndex: 'name', ellipsis: true, tooltip: true },
  { title: '阶段', dataIndex: 'phase', width: 96 },
  { title: '负责人', dataIndex: 'owner', width: 96 },
  { title: '状态', dataIndex: 'status', width: 104 },
  { title: '截止日期', dataIndex: 'due_date', width: 126 }
]

function chartTheme() {
  return {
    textStyle: { color: '#4e5969', fontFamily: 'Inter, Microsoft YaHei, PingFang SC, Arial' },
    color: ['#165dff', '#00b42a', '#ff7d00', '#722ed1', '#14c9c9']
  }
}

function resetCharts() {
  while (charts.length) charts.pop()?.dispose()
}

function renderCharts() {
  resetCharts()
  const quality = data.value.quality_trend || []
  const lifecycle = data.value.lifecycle || []
  const changes = data.value.changes || []

  const y = echarts.init(yieldChart.value!, undefined, { renderer: 'canvas' })
  y.setOption({
    ...chartTheme(),
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e5e6eb', textStyle: { color: '#1d2129' } },
    legend: { top: 0, right: 8, data: ['CP 良率', 'FT 良率'] },
    grid: { left: 42, right: 18, top: 46, bottom: 32 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: quality.map((item: any) => item.date),
      axisLine: { lineStyle: { color: '#e5e6eb' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      min: 88,
      max: 98,
      axisLabel: { formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#edf1f7' } }
    },
    series: [
      {
        name: 'CP 良率',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        areaStyle: { opacity: 0.12 },
        data: quality.map((item: any) => item.cp)
      },
      {
        name: 'FT 良率',
        type: 'line',
        smooth: true,
        symbolSize: 7,
        areaStyle: { opacity: 0.1 },
        data: quality.map((item: any) => item.ft)
      }
    ]
  })

  const l = echarts.init(lifeChart.value!, undefined, { renderer: 'canvas' })
  l.setOption({
    ...chartTheme(),
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    series: [
      {
        type: 'pie',
        radius: ['48%', '70%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        label: { formatter: '{b}: {c}' },
        data: lifecycle
      }
    ]
  })

  const c = echarts.init(changeChart.value!, undefined, { renderer: 'canvas' })
  c.setOption({
    ...chartTheme(),
    tooltip: { trigger: 'axis' },
    grid: { left: 38, right: 18, top: 24, bottom: 58 },
    xAxis: {
      type: 'category',
      data: changes.map((item: any) => item.name),
      axisLabel: { interval: 0, width: 92, overflow: 'break' },
      axisLine: { lineStyle: { color: '#e5e6eb' } },
      axisTick: { show: false }
    },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf1f7' } } },
    series: [{ type: 'bar', data: changes.map((item: any) => item.value), barWidth: 28, itemStyle: { borderRadius: [5, 5, 0, 0] } }]
  })

  charts.push(y, l, c)
}

async function reload() {
  loading.value = true
  data.value = await getDashboard()
  loading.value = false
  await nextTick()
  renderCharts()
}

onMounted(reload)
onBeforeUnmount(resetCharts)
</script>

<style scoped>
.arco-dashboard {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.dashboard-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 20px;
  border: 1px solid #e5e6eb;
  border-radius: 10px;
  background:
    linear-gradient(135deg, rgba(22, 93, 255, 0.08), rgba(20, 201, 201, 0.05)),
    #fff;
}

.dashboard-kicker {
  color: #165dff;
  font-size: 12px;
  font-weight: 700;
}

.dashboard-head h2 {
  margin: 6px 0 4px;
  color: #1d2129;
  font-size: 24px;
}

.dashboard-head p {
  margin: 0;
  color: #4e5969;
}

.dashboard-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.stat-row,
.section-row {
  min-width: 0;
}

.metric-card,
.dashboard-card {
  height: 100%;
  border: 1px solid #e5e6eb;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(29, 33, 41, 0.04);
}

.metric-card :deep(.arco-card-body) {
  padding: 15px 16px;
}

.metric-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  color: #4e5969;
  font-size: 13px;
}

.metric-foot {
  margin-top: 10px;
  color: #86909c;
  font-size: 12px;
}

.dashboard-card :deep(.arco-card-header) {
  height: 48px;
  border-bottom: 1px solid #f2f3f5;
}

.dashboard-card :deep(.arco-card-header-title) {
  color: #1d2129;
  font-weight: 700;
}

.card-extra {
  color: #86909c;
  font-size: 12px;
}

.arco-chart {
  width: 100%;
}

.chart-main {
  height: 318px;
}

.chart-secondary {
  height: 298px;
}

.task-table :deep(.arco-table-th) {
  background: #f7f8fa;
  color: #4e5969;
  font-weight: 600;
}

.task-table :deep(.arco-table-td) {
  color: #1d2129;
}

@media (max-width: 1080px) {
  .dashboard-head {
    flex-direction: column;
  }

  .dashboard-status {
    justify-content: flex-start;
  }
}
</style>
