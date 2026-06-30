<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>工程变更</strong>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索变更单号/标题" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button :icon="Operation" @click="openBatchControl">批次控制</el-button>
        <el-button v-if="can('change')" type="primary" :icon="Plus" @click="openCreate">新建变更</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" row-key="id" :expand-row-keys="expandedRowKeys" @expand-change="onExpandChange" height="100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="bom-detail-expand">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="产品">{{ row.product_model }}</el-descriptions-item>
                <el-descriptions-item label="负责人">{{ row.owner }}</el-descriptions-item>
                <el-descriptions-item label="提交日期">{{ row.submitted_at || '-' }}</el-descriptions-item>
                <el-descriptions-item label="状态">{{ row.status }}</el-descriptions-item>
                <el-descriptions-item label="变更原因" :span="2">{{ row.reason }}</el-descriptions-item>
                <el-descriptions-item label="变更前" :span="2">{{ row.before_desc }}</el-descriptions-item>
                <el-descriptions-item label="变更后" :span="2">{{ row.after_desc }}</el-descriptions-item>
              </el-descriptions>
              <div class="section-gap">
                <div class="toolbar compact-toolbar">
                  <div class="panel-title">影响分析</div>
                  <div class="toolbar-actions">
                    <el-button size="small" :disabled="!can('change') || row.status === '已关闭'" @click="runAnalyze">重新分析</el-button>
                    <el-button size="small" :disabled="!can('change') || row.status === '已关闭'" @click="openImpactCreate">新增影响</el-button>
                  </div>
                </div>
                <el-table :data="row.impacts" size="small">
                  <el-table-column prop="type" label="对象" width="100" />
                  <el-table-column prop="target" label="范围" />
                  <el-table-column prop="risk" label="风险" width="80" />
                  <el-table-column prop="action" label="动作" />
                  <el-table-column label="操作" width="130">
                    <template #default="{ row: itemRow }">
                      <el-button size="small" :disabled="!can('change') || row.status === '已关闭'" @click="openImpactEdit(itemRow)">编辑</el-button>
                      <el-button size="small" type="danger" :disabled="!can('change') || row.status === '已关闭'" @click="removeImpact(itemRow)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="section-gap">
                <div class="panel-title">审批流程</div>
                <el-steps direction="vertical" :active="2" finish-status="success">
                  <el-step v-for="item in row.approvals" :key="item.step" :title="item.step" :description="`${item.approver} · ${item.status} ${item.comment}`" />
                </el-steps>
              </div>
              <div class="section-gap">
                <div class="toolbar compact-toolbar">
                  <div class="panel-title">ECN / ECA 执行动作</div>
                  <div class="toolbar-actions">
                    <el-button size="small" :disabled="!can('change') || row.status === '已关闭'" @click="openActionCreate">新增动作</el-button>
                  </div>
                </div>
                <el-table :data="row.actions" size="small">
                  <el-table-column prop="action_no" label="动作编号" width="190" />
                  <el-table-column prop="action_type" label="动作" width="100" />
                  <el-table-column prop="target_type" label="对象类型" width="90" />
                  <el-table-column prop="target_object" label="对象" min-width="180" />
                  <el-table-column prop="target_version" label="当前版本" width="90" />
                  <el-table-column prop="effectivity_type" label="生效方式" width="100" />
                  <el-table-column prop="effectivity_scope" label="生效范围" width="110" />
                  <el-table-column prop="effective_date" label="生效日期" width="110" />
                  <el-table-column prop="effective_batch" label="生效批次" width="140" />
                  <el-table-column prop="generated_object_no" label="生成对象" min-width="160" show-overflow-tooltip />
                  <el-table-column prop="department" label="部门" width="110" />
                  <el-table-column prop="owner" label="负责人" width="90" />
                  <el-table-column prop="status" label="状态" width="90">
                    <template #default="{ row: itemRow }">
                      <el-tag size="small" :type="itemRow.status === '进行中' ? 'warning' : itemRow.status === '待处理' ? 'info' : 'success'">
                        {{ itemRow.status }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="due_date" label="截止" width="110" />
                  <el-table-column label="操作" width="160">
                    <template #default="{ row: itemRow }">
                      <el-button size="small" :disabled="!can('change') || itemRow.status === '已完成'" @click="openActionEdit(itemRow)">编辑</el-button>
                      <el-button size="small" type="primary" :disabled="!can('change') || itemRow.status === '已完成'" @click="closeAction(itemRow)">关闭</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="section-gap">
                <div class="panel-title">版本归档</div>
                <el-table :data="revisionArchive" size="small" empty-text="暂无升版记录">
                  <el-table-column prop="target_type" label="对象类型" width="90" />
                  <el-table-column prop="source_object" label="来源对象" min-width="180" show-overflow-tooltip />
                  <el-table-column prop="source_version" label="来源版本" width="90" />
                  <el-table-column label="生成对象" min-width="170">
                    <template #default="{ row: itemRow }">
                      <a v-if="itemRow.generated_url" href="javascript:void(0)" class="archive-link" @click="navigateTo(itemRow.generated_url)">{{ itemRow.generated_object_no }}</a>
                      <span v-else>{{ itemRow.generated_object_no }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="effectivity_type" label="生效方式" width="100" />
                  <el-table-column prop="effectivity_scope" label="生效范围" width="110" />
                  <el-table-column prop="effective_date" label="生效日期" width="110" />
                  <el-table-column prop="effective_batch" label="生效批次" width="140" />
                  <el-table-column prop="release_gate_status" label="发布门" width="110">
                    <template #default="{ row: itemRow }">
                      <el-tag size="small" :type="itemRow.release_gate_status === '可提交' ? 'success' : 'warning'">{{ itemRow.release_gate_status }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="owner" label="负责人" width="90" />
                  <el-table-column label="操作" width="80" fixed="right">
                    <template #default="{ row: itemRow }">
                      <el-button size="small" @click="showArchiveDetail(itemRow)">详情</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <AttachmentPanel object-type="Change" :object-id="row.id" :can-edit="can('change')" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="change_no" label="变更单号" width="180" fixed />
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="product_model" label="型号" width="130" />
        <el-table-column prop="change_type" label="类型" width="110" />
        <el-table-column prop="priority" label="优先级" width="90" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" :disabled="!can('change') || !['草稿', '已驳回'].includes(row.status)" @click.stop="openEdit(row)">编辑</el-button>
              <el-button size="small" type="primary" :disabled="!can('change') || !['草稿', '已驳回'].includes(row.status)" @click.stop="submit(row)">提交</el-button>
              <el-button size="small" type="danger" :disabled="!can('change') || row.status !== '草稿'" @click.stop="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <el-dialog v-model="archiveDialogVisible" title="版本归档详情" width="760px">
      <template v-if="archiveDetail.action_no">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="动作编号">{{ archiveDetail.action_no }}</el-descriptions-item>
          <el-descriptions-item label="动作类型">{{ archiveDetail.action_type }}</el-descriptions-item>
          <el-descriptions-item label="来源对象">{{ archiveDetail.source_object }}</el-descriptions-item>
          <el-descriptions-item label="来源版本">{{ archiveDetail.source_version }}</el-descriptions-item>
          <el-descriptions-item label="生成对象">{{ archiveDetail.generated_object_no }}</el-descriptions-item>
          <el-descriptions-item label="对象类型">{{ archiveDetail.target_type }}</el-descriptions-item>
          <el-descriptions-item label="生效方式">{{ archiveDetail.effectivity_type }}</el-descriptions-item>
          <el-descriptions-item label="生效范围">{{ archiveDetail.effectivity_scope }}</el-descriptions-item>
          <el-descriptions-item label="生效日期">{{ archiveDetail.effective_date }}</el-descriptions-item>
          <el-descriptions-item label="生效批次">{{ archiveDetail.effective_batch }}</el-descriptions-item>
          <el-descriptions-item label="变更状态">{{ archiveDetail.change_status || '-' }}</el-descriptions-item>
          <el-descriptions-item label="发布门">
            <el-tag size="small" :type="archiveDetail.release_gate_status === '可提交' ? 'success' : 'warning'">{{ archiveDetail.release_gate_status || '-' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责人">{{ archiveDetail.owner }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ archiveDetail.status }}</el-descriptions-item>
          <el-descriptions-item label="发布校验" :span="2">{{ archiveDetail.release_gate_message || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="archiveDetail.target_id" style="margin-top:16px">
          <div class="panel-title" style="margin-bottom:8px">版本链路追溯</div>
          <el-table :data="versionHistory" size="small" empty-text="暂无版本历史" v-loading="versionLoading">
            <el-table-column prop="version" label="版本" width="80" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.is_current ? 'primary' : row.status === '已发布' ? 'success' : 'info'">
                  {{ row.status }}{{ row.is_current ? ' · 当前' : '' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="change_no" label="生成变更单" width="150" show-overflow-tooltip />
            <el-table-column prop="eca_action_no" label="ECA 动作" width="130" show-overflow-tooltip />
            <el-table-column prop="eca_effectivity_type" label="生效方式" width="90" />
            <el-table-column prop="eca_effective_batch" label="生效批次" width="120" show-overflow-tooltip />
            <el-table-column prop="release_gate_status" label="发布门" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.release_gate_status" size="small" :type="row.release_gate_status === '可提交' ? 'success' : 'warning'">{{ row.release_gate_status }}</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="effective_date" label="生效日期" width="100" />
            <el-table-column prop="release_date" label="发布日期" width="100" />
          </el-table>
        </div>
        <div style="margin-top:16px;text-align:center">
          <el-button v-if="archiveDetail.generated_url" type="primary" @click="navigateTo(archiveDetail.generated_url)">查看生成对象</el-button>
          <el-button v-if="archiveDetail.target_url" @click="navigateTo(archiveDetail.target_url)">查看来源对象</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="batchDialogVisible" title="生效批次控制" width="900px" top="5vh">
      <div style="margin-bottom:12px;display:flex;gap:12px;align-items:center">
        <span style="font-weight:600">选择产品</span>
        <el-select v-model="batchProductId" filterable placeholder="选择产品查看批次总览" style="width:280px" @change="loadBatchData">
          <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
        </el-select>
      </div>
      <div v-loading="batchLoading">
        <template v-if="batchData.batches && batchData.batches.length">
          <div class="panel-title" style="margin-bottom:8px">批次总览（{{ batchData.product_model }}）</div>
          <el-table :data="batchData.batches" size="small" border>
            <el-table-column prop="effective_batch" label="生效批次" width="150" fixed />
            <el-table-column prop="effectivity_type" label="生效方式" width="100" />
            <el-table-column prop="effective_date" label="生效日期" width="110" />
            <el-table-column label="关联变更" min-width="160">
              <template #default="{ row }">
                <span v-for="(no, idx) in row.change_nos" :key="no">
                  <a v-if="idx < 3" href="javascript:void(0)" class="archive-link" @click="jumpToChange(no)">{{ no }}</a><span v-if="idx < Math.min(row.change_nos.length, 3) - 1">, </span>
                  <span v-if="row.change_nos.length > 3" class="muted"> 等{{ row.change_nos.length }}张</span>
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="action_count" label="动作数" width="80" />
            <el-table-column prop="done_count" label="已完成" width="80" />
            <el-table-column prop="pending_count" label="待执行" width="80" />
            <el-table-column label="批次状态" width="100" fixed="right">
              <template #default="{ row }">
                <el-tag size="small" :type="row.batch_status === '已生效' ? 'success' : row.batch_status === '执行中' ? 'warning' : 'info'">{{ row.batch_status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="expandBatch(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-collapse v-model="expandedBatches" style="margin-top:12px">
            <el-collapse-item v-for="batch in batchData.batches" :key="batch.effective_batch" :name="batch.effective_batch">
              <template #title>
                <span style="font-weight:600">{{ batch.effective_batch }}</span>
                <span class="muted" style="margin-left:8px">{{ batch.action_count }} 个动作 · {{ batch.batch_status }}</span>
              </template>
              <el-table :data="batch.actions" size="small">
                <el-table-column prop="action_no" label="动作编号" width="170" />
                <el-table-column prop="action_type" label="动作" width="90" />
                <el-table-column prop="target_type" label="对象类型" width="80" />
                <el-table-column prop="target_object" label="对象" min-width="160" show-overflow-tooltip />
                <el-table-column prop="generated_object_no" label="生成对象" min-width="140" show-overflow-tooltip />
                <el-table-column prop="change_no" label="变更单" width="140" />
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag size="small" :type="row.status === '已完成' ? 'success' : 'warning'">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="发布门" width="90">
                  <template #default="{ row }">
                    <el-tag v-if="row.generated_object_no" size="small" :type="row.release_gate_status ? 'success' : 'warning'">{{ row.release_gate_status ? '可提交' : '待闭环' }}</el-tag>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </template>
        <template v-else-if="batchData.no_batch_actions && batchData.no_batch_actions.length">
          <div class="panel-title" style="margin-bottom:8px">日期生效动作（无批次）</div>
          <el-table :data="batchData.no_batch_actions" size="small">
            <el-table-column prop="action_no" label="动作编号" width="170" />
            <el-table-column prop="change_no" label="变更单" width="140" />
            <el-table-column prop="target_type" label="对象类型" width="80" />
            <el-table-column prop="target_object" label="对象" min-width="160" show-overflow-tooltip />
            <el-table-column prop="effective_date" label="生效日期" width="100" />
            <el-table-column prop="status" label="状态" width="80" />
          </el-table>
        </template>
        <el-empty v-else-if="batchProductId" description="该产品暂无生效批次数据" />
        <el-empty v-else description="请选择产品查看批次总览" />
      </div>
    </el-dialog>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑变更' : '新建变更'" width="760px">
      <el-form :model="form" label-width="90px">
        <div class="form-grid">
          <el-form-item label="变更单号"><el-input v-model="form.change_no" /></el-form-item>
          <el-form-item label="关联产品">
            <el-select v-model="form.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="变更类型">
            <el-select v-model="form.change_type">
              <el-option label="PR 问题报告" value="PR" />
              <el-option label="ECR 变更申请" value="ECR" />
              <el-option label="ECO 变更指令" value="ECO" />
              <el-option label="ECN 变更通知" value="ECN" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="form.priority">
              <el-option label="高" value="高" />
              <el-option label="中" value="中" />
              <el-option label="低" value="低" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="form.status">
              <el-option label="草稿" value="草稿" />
              <el-option label="审批中" value="审批中" />
              <el-option label="执行中" value="执行中" />
              <el-option label="已关闭" value="已关闭" />
            </el-select>
          </el-form-item>
          <el-form-item label="标题" class="form-wide"><el-input v-model="form.title" /></el-form-item>
          <el-form-item label="变更原因" class="form-wide"><el-input v-model="form.reason" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="变更前" class="form-wide"><el-input v-model="form.before_desc" type="textarea" :rows="3" /></el-form-item>
          <el-form-item label="变更后" class="form-wide"><el-input v-model="form.after_desc" type="textarea" :rows="3" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="impactDialogVisible" :title="editingImpactId ? '编辑影响项' : '新增影响项'" width="620px">
      <el-form :model="impactForm" label-width="86px">
        <el-form-item label="对象类型"><el-input v-model="impactForm.impact_type" /></el-form-item>
        <el-form-item label="影响范围"><el-input v-model="impactForm.target" /></el-form-item>
        <el-form-item label="风险">
          <el-select v-model="impactForm.risk">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理动作"><el-input v-model="impactForm.action" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="impactDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveImpact">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="actionDialogVisible" :title="editingActionId ? '编辑 ECA 动作' : '新增 ECA 动作'" width="760px">
      <el-form :model="actionForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="动作编号"><el-input v-model="actionForm.action_no" placeholder="留空自动生成" /></el-form-item>
          <el-form-item label="动作类型"><el-input v-model="actionForm.action_type" /></el-form-item>
          <el-form-item label="对象类型">
            <el-select v-model="actionForm.target_type" clearable>
              <el-option label="BOM" value="BOM" />
              <el-option label="文档" value="文档" />
              <el-option label="工艺路线" value="工艺路线" />
              <el-option label="通知" value="通知" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="对象ID"><el-input-number v-model="actionForm.target_id" :min="1" controls-position="right" /></el-form-item>
          <el-form-item label="当前版本"><el-input v-model="actionForm.target_version" /></el-form-item>
          <el-form-item label="生效方式">
            <el-select v-model="actionForm.effectivity_type">
              <el-option label="日期" value="日期" />
              <el-option label="批次" value="批次" />
              <el-option label="日期+批次" value="日期+批次" />
            </el-select>
          </el-form-item>
          <el-form-item label="生效范围"><el-input v-model="actionForm.effectivity_scope" /></el-form-item>
          <el-form-item label="生效日期"><el-input v-model="actionForm.effective_date" /></el-form-item>
          <el-form-item label="生效批次"><el-input v-model="actionForm.effective_batch" placeholder="LOT / Wafer / 试产批次" /></el-form-item>
          <el-form-item label="生成对象"><el-input v-model="actionForm.generated_object_no" disabled /></el-form-item>
          <el-form-item label="对象" class="form-wide"><el-input v-model="actionForm.target_object" /></el-form-item>
          <el-form-item label="部门"><el-input v-model="actionForm.department" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="actionForm.owner" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="actionForm.status">
              <el-option label="待处理" value="待处理" />
              <el-option label="进行中" value="进行中" />
              <el-option label="已完成" value="已完成" />
            </el-select>
          </el-form-item>
          <el-form-item label="截止日期"><el-input v-model="actionForm.due_date" /></el-form-item>
          <el-form-item label="结果" class="form-wide"><el-input v-model="actionForm.result" type="textarea" :rows="3" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAction">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Operation, Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  analyzeChange,
  closeChangeAction,
  createChange,
  createChangeAction,
  createChangeImpact,
  deleteChange,
  deleteChangeImpact,
  getBomVersionHistory,
  getChangeRevisionArchive,
  getChanges,
  getDocumentVersionHistory,
  getProductEffectivityBatches,
  getProcessRouteVersionHistory,
  getProducts,
  submitChange,
  updateChange,
  updateChangeAction,
  updateChangeImpact,
} from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import AttachmentPanel from '../components/AttachmentPanel.vue'
import { useListPage } from '../composables/useListPage'

const router = useRouter()
const { can, currentUser, refreshSession } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getChanges)
const products = ref<any[]>([])
const selected = ref<any>()
const expandedRowKeys = ref<number[]>([])
const revisionArchive = ref<any[]>([])
const archiveDialogVisible = ref(false)
const archiveDetail = ref<any>({})
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const emptyForm = { product_id: undefined, change_no: '', title: '', change_type: 'ECR', reason: '', status: '草稿', priority: '中', owner: '', before_desc: '', after_desc: '' }
const form = ref<any>({ ...emptyForm })
const impactDialogVisible = ref(false)
const editingImpactId = ref<number | null>(null)
const emptyImpact = { impact_type: '', target: '', risk: '中', action: '' }
const impactForm = ref<any>({ ...emptyImpact })
const actionDialogVisible = ref(false)
const editingActionId = ref<number | null>(null)
const emptyAction = {
  action_no: '',
  action_type: '资料更新',
  target_type: '',
  target_id: undefined,
  target_version: '',
  target_object: '',
  effectivity_type: '日期',
  effectivity_scope: '',
  effective_date: '',
  effective_batch: '',
  generated_object_no: '',
  department: '',
  owner: '',
  status: '待处理',
  due_date: '',
  result: '',
}
const actionForm = ref<any>({ ...emptyAction })

const batchDialogVisible = ref(false)
const batchProductId = ref<number | undefined>(undefined)
const batchData = ref<any>({})
const batchLoading = ref(false)
const expandedBatches = ref<string[]>([])

const versionHistory = ref<any[]>([])
const versionLoading = ref(false)

function todayText() {
  return new Date().toISOString().slice(0, 10)
}

function navigateTo(url: string) {
  router.push(url)
}

async function showArchiveDetail(row: any) {
  archiveDetail.value = row
  archiveDialogVisible.value = true
  versionHistory.value = []
  versionLoading.value = true
  try {
    if (row.target_type === 'BOM' && row.target_id) {
      versionHistory.value = await getBomVersionHistory(row.target_id)
    } else if (row.target_type === '文档' && row.target_id) {
      versionHistory.value = await getDocumentVersionHistory(row.target_id)
    } else if (row.target_type === '工艺路线' && row.target_id) {
      versionHistory.value = await getProcessRouteVersionHistory(row.target_id)
    }
  } catch {
    versionHistory.value = []
  } finally {
    versionLoading.value = false
  }
}

function openBatchControl() {
  batchDialogVisible.value = true
  if (!batchProductId.value && products.value.length) {
    batchProductId.value = products.value[0].id
    loadBatchData()
  }
}

async function loadBatchData() {
  if (!batchProductId.value) {
    batchData.value = {}
    return
  }
  batchLoading.value = true
  expandedBatches.value = []
  try {
    batchData.value = await getProductEffectivityBatches(batchProductId.value)
  } catch {
    batchData.value = {}
  } finally {
    batchLoading.value = false
  }
}

function expandBatch(row: any) {
  const idx = expandedBatches.value.indexOf(row.effective_batch)
  if (idx >= 0) {
    expandedBatches.value.splice(idx, 1)
  } else {
    expandedBatches.value.push(row.effective_batch)
  }
}

async function jumpToChange(changeNo: string) {
  batchDialogVisible.value = false
  const list = items.value || []
  const target = list.find((item) => item.change_no === changeNo)
  if (target) {
    selected.value = target
    expandedRowKeys.value = [target.id]
    revisionArchive.value = await getChangeRevisionArchive(target.id)
  }
}

async function loadChanges(selectedId?: number) {
  await loadData()
  const list = items.value || []
  const target = selectedId ? list.find((item) => item.id === selectedId) : list[0]
  selected.value = target || null
  expandedRowKeys.value = target ? [target.id] : []
  revisionArchive.value = target ? await getChangeRevisionArchive(target.id) : []
}

async function onExpandChange(row: any, expandedRows: any[]) {
  const isExpanded = expandedRows.some((r: any) => r.id === row.id)
  if (isExpanded) {
    expandedRowKeys.value = [row.id]
    selected.value = row
    revisionArchive.value = await getChangeRevisionArchive(row.id)
  } else {
    expandedRowKeys.value = []
    selected.value = null
    revisionArchive.value = []
  }
}

function openCreate() {
  if (!can('change')) return
  editingId.value = null
  const product = products.value[0]
  form.value = {
    ...emptyForm,
    product_id: product?.id,
    change_no: product ? `ECR-${product.model}-${String((items.value || []).length + 1).padStart(3, '0')}` : '',
    owner: currentUser.value?.display_name || '',
  }
  dialogVisible.value = true
}

function openEdit(row: any) {
  if (!can('change') || !['草稿', '已驳回'].includes(row.status)) return
  editingId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function save() {
  if (!can('change')) return
  if (editingId.value) {
    await updateChange(editingId.value, form.value)
    ElMessage.success('变更已更新')
    await loadChanges(editingId.value)
  } else {
    const next = await createChange(form.value)
    ElMessage.success('变更已创建')
    await loadChanges(next.id)
  }
  dialogVisible.value = false
}

async function submit(row: any) {
  if (!can('change') || !['草稿', '已驳回'].includes(row.status)) return
  await submitChange(row.id)
  ElMessage.success('变更已提交审批')
  await loadChanges(row.id)
}

async function remove(row: any) {
  if (!can('change') || row.status !== '草稿') return
  await ElMessageBox.confirm(`确认删除变更 ${row.change_no}？只有草稿允许删除。`, '删除确认', { type: 'warning' })
  await deleteChange(row.id)
  ElMessage.success('变更已删除')
  await loadChanges()
}

async function runAnalyze() {
  if (!selected.value || !can('change')) return
  const next = await analyzeChange(selected.value.id)
  ElMessage.success('影响分析已生成')
  await loadChanges(next.id)
}

function openImpactCreate() {
  if (!selected.value || !can('change')) return
  editingImpactId.value = null
  impactForm.value = { ...emptyImpact }
  impactDialogVisible.value = true
}

function openImpactEdit(row: any) {
  if (!can('change')) return
  editingImpactId.value = row.id
  impactForm.value = { impact_type: row.impact_type || row.type, target: row.target, risk: row.risk, action: row.action }
  impactDialogVisible.value = true
}

async function saveImpact() {
  if (!selected.value || !can('change')) return
  if (editingImpactId.value) {
    await updateChangeImpact(editingImpactId.value, impactForm.value)
  } else {
    await createChangeImpact(selected.value.id, impactForm.value)
  }
  ElMessage.success('影响项已保存')
  impactDialogVisible.value = false
  await loadChanges(selected.value.id)
}

async function removeImpact(row: any) {
  if (!can('change')) return
  await deleteChangeImpact(row.id)
  ElMessage.success('影响项已删除')
  await loadChanges(selected.value?.id)
}

function openActionCreate() {
  if (!selected.value || !can('change')) return
  editingActionId.value = null
  actionForm.value = { ...emptyAction, effective_date: todayText(), owner: currentUser.value?.display_name || '' }
  actionDialogVisible.value = true
}

function openActionEdit(row: any) {
  if (!can('change')) return
  editingActionId.value = row.id
  actionForm.value = { ...row }
  actionDialogVisible.value = true
}

async function saveAction() {
  if (!selected.value || !can('change')) return
  const effectivityType = actionForm.value.effectivity_type || '日期'
  if (effectivityType.includes('日期') && !actionForm.value.effective_date) {
    ElMessage.warning('请填写生效日期')
    return
  }
  if (effectivityType.includes('批次') && !actionForm.value.effective_batch) {
    ElMessage.warning('请填写生效批次')
    return
  }
  if (editingActionId.value) {
    await updateChangeAction(editingActionId.value, actionForm.value)
  } else {
    await createChangeAction(selected.value.id, actionForm.value)
  }
  ElMessage.success('ECA 动作已保存')
  actionDialogVisible.value = false
  await loadChanges(selected.value.id)
}

async function closeAction(row: any) {
  if (!can('change')) return
  const { value } = await ElMessageBox.prompt('请输入执行结果', '关闭 ECA 动作', {
    inputValue: row.result || '已完成并归档',
    confirmButtonText: '确认',
    cancelButtonText: '取消',
  })
  const next = await closeChangeAction(row.id, { acted_by: currentUser.value?.display_name || '系统用户', result: value })
  ElMessage.success(next.closed_change ? 'ECA 已全部关闭，变更已关闭' : 'ECA 动作已关闭')
  await loadChanges(selected.value?.id)
}

onMounted(async () => {
  await refreshSession()
  products.value = (await getProducts()).items
  await loadChanges()
})
</script>

<style scoped>
.archive-link {
  color: var(--color-primary, rgb(22, 93, 255));
  text-decoration: none;
  font-weight: 500;
}
.archive-link:hover {
  text-decoration: underline;
}
</style>
