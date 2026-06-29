<template>
  <div v-loading="loading">
    <div class="toolbar">
      <div><strong>质量闭环管理</strong><span class="muted"> · Lot 追溯、缺陷问题、CAPA 纠正预防</span></div>
    </div>
    <el-tabs class="panel">
      <el-tab-pane label="Lot / Wafer 追溯">
        <el-table :data="quality.lots || []" stripe height="600">
          <el-table-column prop="product_model" label="型号" width="130" />
          <el-table-column prop="lot_no" label="Lot" width="190" />
          <el-table-column prop="wafer_id" label="Wafer ID" width="110" />
          <el-table-column prop="stage" label="阶段" width="90" />
          <el-table-column prop="cp_yield" label="CP 良率" width="100" />
          <el-table-column prop="ft_yield" label="FT 良率" width="100" />
          <el-table-column prop="status" label="状态" width="110" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="质量问题">
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(480px,1fr));gap:12px">
          <el-card v-for="issue in quality.issues || []" :key="issue.id" shadow="never">
            <template #header>
              <div class="toolbar">
                <strong>{{ issue.issue_no }}</strong>
                <div>
                  <el-tag :type="issue.status === '已关闭' ? 'success' : issue.status === 'CAPA 执行中' ? 'warning' : 'danger'" size="small">{{ issue.status }}</el-tag>
                  <el-button v-if="can('quality') && issue.status !== 'CAPA 执行中' && issue.status !== '已关闭'" size="small" type="primary" style="margin-left:8px" @click="createCAPA(issue)">发起 CAPA</el-button>
                </div>
              </div>
            </template>
            <p><strong>{{ issue.title }}</strong></p>
            <p class="muted">产品 {{ issue.product_model }} · Lot {{ issue.lot_no }} · {{ issue.owner }}</p>
            <el-divider />
            <p><strong>原因：</strong>{{ issue.root_cause }}</p>
            <p><strong>措施：</strong>{{ issue.corrective_action }}</p>
          </el-card>
        </div>
      </el-tab-pane>
      <el-tab-pane label="CAPA 管理">
        <div class="toolbar">
          <el-button v-if="can('quality')" type="primary" :icon="Plus" @click="openCreateCAPA">新增 CAPA</el-button>
        </div>
        <el-table :data="capas" stripe height="580">
          <el-table-column prop="capa_no" label="CAPA 编号" width="130" />
          <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="100" />
          <el-table-column prop="owner" label="负责人" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><el-tag :type="row.status === '已关闭' ? 'success' : row.status === '执行中' ? 'warning' : 'info'" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="due_date" label="截止日期" width="110" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEditCAPA(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="removeCAPA(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="capaDialog" :title="capaEditingId ? '编辑 CAPA' : '新增 CAPA'" width="680px">
      <el-form :model="capaForm" label-width="110px">
        <el-form-item label="CAPA 编号"><el-input v-model="capaForm.capa_no" :disabled="!!capaEditingId" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="capaForm.title" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="capaForm.source" /></el-form-item>
        <el-form-item label="负责人"><el-input v-model="capaForm.owner" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="capaForm.status"><el-option label="待处理" value="待处理" /><el-option label="执行中" value="执行中" /><el-option label="已关闭" value="已关闭" /></el-select></el-form-item>
        <el-form-item label="截止日期"><el-input v-model="capaForm.due_date" placeholder="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="根因分析"><el-input v-model="capaForm.root_cause" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="纠正措施"><el-input v-model="capaForm.corrective_action" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="预防措施"><el-input v-model="capaForm.preventive_action" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="关闭结论"><el-input v-model="capaForm.result" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="capaDialog = false">取消</el-button>
        <el-button type="primary" @click="saveCAPA">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { createCAPAFromIssue, createQualityCAPA, deleteQualityCAPA, getQuality, getQualityCAPAs, updateQualityCAPA } from '../api'
import { useAuth } from '../auth'

const loading = ref(true)
const { can } = useAuth()
const quality = ref<any>({})
const capas = ref<any[]>([])
const capaDialog = ref(false)
const capaEditingId = ref<number | null>(null)
const capaForm = ref<any>({ capa_no: '', title: '', source: '质量问题', owner: '', status: '待处理', due_date: '', root_cause: '', corrective_action: '', preventive_action: '', result: '' })

async function load() {
  quality.value = await getQuality()
  capas.value = await getQualityCAPAs()
}

async function createCAPA(issue: any) {
  await ElMessageBox.confirm(`为 ${issue.issue_no} 创建 CAPA？`, '发起 CAPA', { type: 'info' })
  await createCAPAFromIssue(issue.id)
  ElMessage.success('CAPA 已创建')
  await load()
}

function openCreateCAPA() {
  capaEditingId.value = null
  capaForm.value = { capa_no: '', title: '', source: '质量问题', owner: '', status: '待处理', due_date: '', root_cause: '', corrective_action: '', preventive_action: '', result: '' }
  capaDialog.value = true
}
function openEditCAPA(row: any) {
  capaEditingId.value = row.id
  capaForm.value = { ...row }
  capaDialog.value = true
}
async function saveCAPA() {
  capaEditingId.value ? await updateQualityCAPA(capaEditingId.value, capaForm.value) : await createQualityCAPA(capaForm.value)
  ElMessage.success('CAPA 已保存')
  capaDialog.value = false
  await load()
}
async function removeCAPA(row: any) {
  await ElMessageBox.confirm('确认删除此 CAPA？', '删除确认', { type: 'warning' })
  await deleteQualityCAPA(row.id)
  ElMessage.success('CAPA 已删除')
  await load()
}

onMounted(async () => { await load(); loading.value = false })
</script>
