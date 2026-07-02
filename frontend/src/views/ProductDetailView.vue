<template>
  <div class="product-detail detail-panel" v-loading="loading">
    <!-- 头部：产品定义基础信息 -->
    <div class="detail-header panel">
      <div class="header-main">
        <div class="header-title">
          <span class="eyebrow">ProductDef</span>
          <h2>{{ product.product_def_name || '-' }} <span class="version-tag">v{{ product.product_def_version || '001' }}</span></h2>
          <p>{{ product.description || '无描述' }}</p>
        </div>
        <div class="header-tags">
          <el-tag :type="stateTag(product.product_def_state)">{{ product.product_def_state || '-' }}</el-tag>
          <el-tag type="primary">{{ product.product_type || '-' }}</el-tag>
          <el-tag>{{ product.production_type || '-' }}</el-tag>
        </div>
      </div>
    </div>

    <!-- 引用关系：制造流程 + BOM -->
    <div class="reference-grid">
      <section class="panel reference-card">
        <div class="card-title">
          <span>引用制造流程</span>
          <el-button size="small" link @click="goFlow" :disabled="!product.referenced_flow">查看流程</el-button>
        </div>
        <div class="kv-grid" v-if="product.referenced_flow">
          <div><label>流程名称</label><span>{{ product.referenced_flow.process_flow_name }}</span></div>
          <div><label>版本</label><span>v{{ product.referenced_flow.process_flow_version }}</span></div>
          <div><label>状态</label><el-tag size="small" :type="flowStateTag(product.referenced_flow.process_flow_state)">{{ product.referenced_flow.process_flow_state }}</el-tag></div>
          <div><label>类型</label><span>{{ product.referenced_flow.process_flow_type1 }} / {{ product.referenced_flow.process_flow_type2 }}</span></div>
          <div><label>负责人</label><span>{{ product.referenced_flow.owner || '-' }}</span></div>
          <div><label>描述</label><span>{{ product.referenced_flow.description || '-' }}</span></div>
        </div>
        <div v-else class="empty-ref">
          <span class="muted">未绑定制造流程</span>
          <el-button size="small" v-if="can('product')" @click="goEdit">去绑定</el-button>
        </div>
      </section>

      <section class="panel reference-card">
        <div class="card-title">
          <span>引用 BOM</span>
          <el-button size="small" link @click="goBom" :disabled="!product.referenced_bom">查看 BOM</el-button>
        </div>
        <div class="kv-grid" v-if="product.referenced_bom">
          <div><label>BOM 名称</label><span>{{ product.referenced_bom.bom_name }}</span></div>
          <div><label>版本</label><span>v{{ product.referenced_bom.bom_version }}</span></div>
          <div><label>状态</label><el-tag size="small" :type="bomStateTag(product.referenced_bom.bom_state)">{{ product.referenced_bom.bom_state }}</el-tag></div>
          <div><label>负责人</label><span>{{ product.referenced_bom.owner || '-' }}</span></div>
          <div><label>描述</label><span>{{ product.referenced_bom.description || '-' }}</span></div>
        </div>
        <div v-else class="empty-ref">
          <span class="muted">未绑定 BOM</span>
          <el-button size="small" v-if="can('product')" @click="goEdit">去绑定</el-button>
        </div>
      </section>
    </div>

    <!-- 产品规格 26 字段 -->
    <section class="panel">
      <div class="panel-title">
        <span>产品规格</span>
        <el-tag size="small" type="info">ProductDef 26 字段</el-tag>
        <el-button size="small" v-if="can('product')" @click="goEdit" style="margin-left: auto;">编辑</el-button>
      </div>
      <div class="kv-grid kv-4">
        <div v-for="item in productSpec" :key="item.label">
          <label>{{ item.label }}</label>
          <span>{{ item.value ?? '-' }}</span>
        </div>
      </div>
    </section>

    <!-- 业务关联统计 -->
    <section class="panel">
      <div class="panel-title"><span>业务关联</span></div>
      <div class="stat-grid">
        <div class="stat-tile"><strong>{{ product.documents_count ?? 0 }}</strong><span>文档</span></div>
        <div class="stat-tile"><strong>{{ product.changes_count ?? 0 }}</strong><span>变更单</span></div>
        <div class="stat-tile"><strong>{{ product.quality_lots_count ?? 0 }}</strong><span>质量批次</span></div>
        <div class="stat-tile"><strong>{{ product.requirements_count ?? 0 }}</strong><span>需求</span></div>
        <div class="stat-tile"><strong>{{ (product.projects || []).length }}</strong><span>项目</span></div>
      </div>
    </section>

    <!-- 关联项目（按 product_model 字符串关联）-->
    <section class="panel" v-if="(product.projects || []).length">
      <div class="panel-title"><span>关联项目</span></div>
      <el-table :data="product.projects || []" size="small">
        <el-table-column prop="project_no" label="项目编号" width="160" />
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="phase" label="阶段" width="100" />
        <el-table-column prop="progress" label="进度" width="120">
          <template #default="{ row }"><el-progress :percentage="row.progress || 0" :stroke-width="8" /></template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="100" />
        <el-table-column prop="risk_level" label="风险" width="90" />
      </el-table>
    </section>

    <!-- 版本历史 -->
    <section class="panel">
      <div class="panel-title"><span>版本历史</span></div>
      <el-table :data="versions" size="small">
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="lifecycle" label="生命周期" width="110" />
        <el-table-column prop="readiness" label="完整度" width="90" />
        <el-table-column prop="released_at" label="发布日期" width="120" />
        <el-table-column prop="released_by" label="发布人" width="110" />
        <el-table-column prop="source_change_no" label="来源变更" width="160" />
        <el-table-column prop="summary" label="摘要" min-width="260" show-overflow-tooltip />
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProduct, getProductVersions } from '../api'
import { useAuth } from '../auth'

const route = useRoute()
const router = useRouter()
const { can } = useAuth()
const loading = ref(true)
const product = ref<any>({})
const versions = ref<any[]>([])

const productSpec = computed(() => [
  { label: '产品定义名', value: product.value.product_def_name },
  { label: '版本', value: product.value.product_def_version },
  { label: '产品类型', value: product.value.product_type },
  { label: '生产类型', value: product.value.production_type },
  { label: '产品组', value: product.value.product_group_name },
  { label: '归属组', value: product.value.owner_group_name },
  { label: '负责人', value: product.value.owner },
  { label: '状态', value: product.value.product_def_state },
  { label: '光罩组', value: product.value.reticle_set_name },
  { label: 'Gross Die', value: product.value.gross_die },
  { label: '起始 Bank', value: product.value.start_bank_name },
  { label: '结束 Bank', value: product.value.end_bank_name },
  { label: 'Bin 名称', value: product.value.bin_name },
  { label: '包装数量', value: product.value.package_qty },
  { label: '产品用途', value: product.value.product_usage },
  { label: '最大使用次数', value: product.value.max_use_count },
  { label: '最大回收次数', value: product.value.max_recycle_count },
  { label: 'Dummy最大时长', value: product.value.dummy_max_use_time },
  { label: 'Dummy厚度参数', value: product.value.dummy_thk_param },
  { label: 'Dummy厚度限值', value: product.value.dummy_thk_limit },
  { label: '是否删除', value: product.value.is_deleted ? '是' : '否' },
  { label: '描述', value: product.value.description },
])

function stateTag(s: string) {
  const map: Record<string, string> = { Active: 'success', Frozen: 'warning', Invalid: 'info' }
  return map[s] || 'info'
}
function flowStateTag(s: string) {
  const map: Record<string, string> = { Active: 'success', Frozen: 'warning', Unfrozen: '', Invalid: 'info' }
  return map[s] || 'info'
}
function bomStateTag(s: string) {
  const map: Record<string, string> = { Active: 'success', Frozen: 'warning', Unfrozen: '', Invalid: 'info' }
  return map[s] || 'info'
}

function goFlow() {
  if (product.value.referenced_flow?.id) router.push({ path: '/process', query: { id: product.value.referenced_flow.id } })
}
function goBom() {
  if (product.value.referenced_bom?.id) router.push({ path: '/boms', query: { id: product.value.referenced_bom.id } })
}
function goEdit() {
  router.push({ path: '/products', query: { edit: route.params.id as string } })
}

onMounted(async () => {
  product.value = await getProduct(route.params.id as string)
  versions.value = await getProductVersions(route.params.id as string)
  loading.value = false
})
</script>

<style scoped>
.product-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-header {
  padding: 16px;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.eyebrow {
  color: #86909c;
  font-size: 12px;
}

.header-title h2 {
  margin: 2px 0 4px;
  font-size: 22px;
  line-height: 28px;
}

.version-tag {
  font-size: 14px;
  color: #4e5969;
  font-weight: normal;
}

.header-title p {
  margin: 0;
  color: #4e5969;
}

.header-tags {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.reference-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.reference-card {
  padding: 14px 16px;
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 600;
}

.kv-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.kv-grid label {
  display: block;
  color: #86909c;
  font-size: 12px;
  margin-bottom: 2px;
}

.kv-grid span {
  display: block;
  overflow-wrap: anywhere;
}

.kv-4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.empty-ref {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--semi-line, #e5e6eb);
  font-weight: 600;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  padding: 14px 16px;
}

.stat-tile {
  display: grid;
  place-items: center;
  gap: 4px;
  padding: 14px;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  background: #fafbfc;
}

.stat-tile strong {
  font-size: 24px;
  color: #1d2129;
}

.stat-tile span {
  color: #86909c;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .reference-grid,
  .kv-4,
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
