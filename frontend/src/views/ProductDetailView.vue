<template>
  <div v-loading="loading">
    <div class="detail-header">
      <div class="panel">
        <div class="panel-title">
          <span>{{ product.model }} · {{ product.name }}</span>
          <el-tag>{{ product.lifecycle }}</el-tag>
        </div>
        <div class="kv">
          <div><label>产品类型</label><span>{{ product.product_type }}</span></div>
          <div><label>工艺平台</label><span>{{ product.process_platform }}</span></div>
          <div><label>晶圆尺寸</label><span>{{ product.wafer_size }}</span></div>
          <div><label>封装形式</label><span>{{ product.package_type }}</span></div>
          <div><label>质量等级</label><span>{{ product.quality_grade }}</span></div>
          <div><label>应用领域</label><span>{{ product.application }}</span></div>
          <div><label>内部料号</label><span>{{ product.internal_part_no }}</span></div>
          <div><label>客户料号</label><span>{{ product.customer_part_no }}</span></div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-title">数据包完整度</div>
        <el-progress type="dashboard" :percentage="product.readiness || 0" />
        <div class="muted">当前版本 {{ product.version }} · {{ product.owner }} 负责</div>
      </div>
    </div>
    <el-tabs class="panel">
      <el-tab-pane label="关联 BOM">
        <el-table :data="product.boms || []" size="small">
          <el-table-column prop="type" label="类型" width="100" />
          <el-table-column prop="version" label="版本" width="100" />
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column prop="owner" label="负责人" width="120" />
          <el-table-column prop="release_date" label="发布日期" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="文档资料">
        <el-table :data="product.documents || []" size="small">
          <el-table-column prop="doc_no" label="文档编号" width="180" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column prop="version" label="版本" width="90" />
          <el-table-column prop="approval_status" label="签核" width="120" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="工程变更">
        <el-table :data="product.changes || []" size="small">
          <el-table-column prop="change_no" label="变更单" width="180" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="priority" label="优先级" width="100" />
          <el-table-column prop="status" label="状态" width="120" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="工艺路线">
        <el-table :data="product.routes || []" size="small">
          <el-table-column prop="route_no" label="路线编号" width="160" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="version" label="版本" width="90" />
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column prop="steps" label="工序数" width="90" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="需求规格">
        <el-table :data="product.requirements || []" size="small">
          <el-table-column prop="req_no" label="需求编号" width="160" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="source" label="来源" width="120" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column prop="priority" label="优先级" width="100" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="owner" label="负责人" width="120" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="关联项目">
        <el-table :data="product.projects || []" size="small">
          <el-table-column prop="project_no" label="项目编号" width="160" />
          <el-table-column prop="name" label="项目名称" />
          <el-table-column prop="phase" label="阶段" width="120" />
          <el-table-column prop="progress" label="进度" width="90" />
          <el-table-column prop="owner" label="负责人" width="120" />
          <el-table-column prop="risk_level" label="风险" width="100" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="质量摘要">
        <el-table :data="product.quality || []" size="small">
          <el-table-column prop="lot_no" label="Lot" />
          <el-table-column prop="stage" label="阶段" width="100" />
          <el-table-column prop="cp_yield" label="CP 良率" width="120" />
          <el-table-column prop="ft_yield" label="FT 良率" width="120" />
          <el-table-column prop="status" label="状态" width="120" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="版本历史">
        <el-table :data="versions" size="small">
          <el-table-column prop="version" label="版本" width="80" />
          <el-table-column prop="lifecycle" label="生命周期" width="100" />
          <el-table-column prop="readiness" label="完整度" width="80" />
          <el-table-column prop="released_at" label="发布日期" width="120" />
          <el-table-column prop="released_by" label="发布人" width="100" />
          <el-table-column prop="source_change_no" label="来源变更" width="160" />
          <el-table-column prop="summary" label="摘要" min-width="260" show-overflow-tooltip />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getProduct, getProductVersions } from '../api'

const route = useRoute()
const loading = ref(true)
const product = ref<any>({})
const versions = ref<any[]>([])

onMounted(async () => {
  product.value = await getProduct(route.params.id as string)
  versions.value = await getProductVersions(route.params.id as string)
  loading.value = false
})
</script>
