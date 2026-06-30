<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div>
        <strong>BOM 对象管理</strong>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索产品型号/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('bom')" :disabled="!selected" @click="openTransform">转 PBOM/MBOM</el-button>
        <el-button :disabled="!selected" @click="openCompare">BOM 比较</el-button>
        <el-button :disabled="!selected" @click="openProcessCoverage">工序校验</el-button>
        <el-button :disabled="!selected" @click="openLineage">转换血缘</el-button>
        <el-button v-if="can('bom')" type="primary" :icon="Plus" @click="openBomCreate">新建 BOM</el-button>
      </div>
    </div>
    <div class="list-table-wrap">
      <el-table :data="items" row-key="id" :expand-row-keys="expandedRowKeys" @expand-change="onExpandChange" height="100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="bom-detail-expand">
              <div class="expand-toolbar">
                <div>
                  <strong>{{ row.product_model }} 结构明细</strong>
                  <span class="muted"> · {{ row.type }} {{ row.version }} · {{ row.status }}</span>
                </div>
                <div class="toolbar-actions">
                  <el-button size="small" :icon="Plus" @click="openItemCreate" :disabled="!can('bom') || row.status === '已发布'">新增行</el-button>
                  <el-button size="small" @click="triggerImport" :disabled="!can('bom') || row.status === '已发布'">导入</el-button>
                  <el-button size="small" @click="handleDownloadTemplate" :disabled="!can('bom')">下载模板</el-button>
                  <el-button size="small" @click="openBatchEdit" :disabled="!can('bom') || row.status === '已发布' || !row.items?.length">批量编辑</el-button>
                  <el-button size="small" type="danger" @click="removeBom" :disabled="!can('bom') || row.status === '已发布'">删除 BOM</el-button>
                </div>
              </div>
              <input ref="fileInputRef" type="file" style="display:none" @change="handleImport" />
              <div class="object-strip">
                <div><span>产品</span><strong>{{ row.product_model }}</strong></div>
                <div><span>有效性</span><strong>{{ row.effectivity_type }} · {{ row.effective_date || '未设置' }} - {{ row.expiry_date || '长期' }}</strong></div>
                <div><span>下游</span><strong>{{ row.source_bom_id ? `来源 BOM#${row.source_bom_id}` : '发布后进入 ERP 队列' }}</strong></div>
              </div>
              <el-table :data="row.items || []" size="small" max-height="400">
                <el-table-column prop="material_code" label="物料编码" width="130" fixed />
                <el-table-column prop="material_name" label="物料名称" min-width="150" />
                <el-table-column prop="category" label="类别" width="100" />
                <el-table-column prop="specification" label="规格" min-width="150" />
                <el-table-column prop="quantity" label="用量" width="80" />
                <el-table-column prop="unit" label="单位" width="70" />
                <el-table-column prop="process_step" label="工序" width="140">
                  <template #default="{ row: itemRow }">
                    <el-tag v-if="itemRow.process_step_id" size="small" type="success">{{ itemRow.process_step }}</el-tag>
                    <span v-else>{{ itemRow.process_step || '未绑定' }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="substitute" label="替代料" width="110" />
                <el-table-column prop="effective_date" label="生效日" width="110" />
                <el-table-column prop="expiry_date" label="失效日" width="110" />
                <el-table-column prop="status" label="状态" width="90" />
                <el-table-column label="操作" width="190" fixed="right">
                  <template #default="{ row: itemRow }">
                    <div class="row-actions">
                      <el-button size="small" @click="openWhereUsed(itemRow)">反查</el-button>
                      <el-button size="small" @click="openItemEdit(itemRow)" :disabled="!can('bom') || row.status === '已发布'">编辑</el-button>
                      <el-button size="small" type="danger" @click="removeItem(itemRow)" :disabled="!can('bom') || row.status === '已发布'">删除</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <AttachmentPanel :object-type="'BOM'" :object-id="row.id" :can-edit="can('bom')" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="product_model" label="产品型号" width="120" fixed />
        <el-table-column prop="product_name" label="产品名称" min-width="180" />
        <el-table-column prop="type" label="类型" width="80" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="effective_date" label="生效日" width="110" />
        <el-table-column prop="expiry_date" label="失效日" width="110" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_current" size="small" type="success" style="margin-right: 4px">当前</el-tag>
            <el-tag size="small" :type="row.status === '已发布' ? 'success' : row.status === '审批中' ? 'warning' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="负责人" width="90" />
        <el-table-column prop="release_date" label="发布日期" width="120" />
        <el-table-column label="操作" width="290" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" :disabled="!can('bom') || row.status === '已发布'" @click.stop="openBomEdit(row)">编辑</el-button>
              <el-button size="small" :disabled="!can('bom') || row.status === '已发布'" @click.stop="submit(row)">提交</el-button>
              <el-button size="small" type="primary" :disabled="!can(['approval', 'bom']) || row.status === '已发布'" @click.stop="approve(row)">发布</el-button>
              <el-button size="small" @click.stop="handleExport(row)">导出</el-button>
              <el-button size="small" @click.stop="openVersionHistory(row)">版本</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <el-dialog v-model="bomDialogVisible" :title="bomEditingId ? '编辑 BOM' : '新建 BOM'" width="620px">
      <el-form :model="bomForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="关联产品">
            <el-select v-model="bomForm.product_id" filterable>
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="BOM 类型">
            <el-select v-model="bomForm.bom_type">
              <el-option v-for="o in bomTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="版本"><el-input v-model="bomForm.version" /></el-form-item>
          <el-form-item label="状态">
            <el-select v-model="bomForm.status">
              <el-option v-for="o in bomStatusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="bomForm.owner" /></el-form-item>
          <el-form-item label="发布日期"><el-input v-model="bomForm.release_date" placeholder="发布时自动写入" /></el-form-item>
          <el-form-item label="有效类型">
            <el-select v-model="bomForm.effectivity_type">
              <el-option v-for="o in bomEffectivityOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="生效日期"><el-input v-model="bomForm.effective_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="失效日期"><el-input v-model="bomForm.expiry_date" placeholder="空表示长期有效" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="bomDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBom">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="itemDialogVisible" :title="itemEditingId ? '编辑 BOM 行' : '新增 BOM 行'" width="720px">
      <el-form :model="itemForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="物料编码"><el-input v-model="itemForm.material_code" /></el-form-item>
          <el-form-item label="物料名称"><el-input v-model="itemForm.material_name" /></el-form-item>
          <el-form-item label="类别"><el-input v-model="itemForm.category" /></el-form-item>
          <el-form-item label="规格"><el-input v-model="itemForm.specification" /></el-form-item>
          <el-form-item label="用量"><el-input-number v-model="itemForm.quantity" :min="0" :precision="3" /></el-form-item>
          <el-form-item label="单位"><el-input v-model="itemForm.unit" /></el-form-item>
          <el-form-item label="位置"><el-input v-model="itemForm.position" /></el-form-item>
          <el-form-item label="关联工序">
            <el-select v-model="itemForm.process_step_id" filterable clearable placeholder="选择真实工艺路线工序">
              <el-option
                v-for="step in processSteps"
                :key="step.id"
                :label="step.label"
                :value="step.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="替代料"><el-input v-model="itemForm.substitute" /></el-form-item>
          <el-form-item label="状态"><el-input v-model="itemForm.status" /></el-form-item>
          <el-form-item label="生效日期"><el-input v-model="itemForm.effective_date" placeholder="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="失效日期"><el-input v-model="itemForm.expiry_date" placeholder="空表示长期有效" /></el-form-item>
          <el-form-item label="有效说明" class="form-wide"><el-input v-model="itemForm.effectivity_note" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="transformDialogVisible" title="EBOM/PBOM/MBOM 转换" width="560px">
      <el-form :model="transformForm" label-width="100px">
        <el-form-item label="来源 BOM"><span>{{ selected?.product_model }} {{ selected?.type }} {{ selected?.version }}</span></el-form-item>
        <el-form-item label="目标类型">
          <el-select v-model="transformForm.target_type">
            <el-option v-for="o in downstreamBomTypeOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标版本"><el-input v-model="transformForm.version" /></el-form-item>
        <el-form-item label="负责人"><UserSelect v-model="transformForm.owner" /></el-form-item>
        <el-form-item label="生效日期"><el-input v-model="transformForm.effective_date" placeholder="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="有效类型">
          <el-select v-model="transformForm.effectivity_type">
            <el-option v-for="o in bomEffectivityOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="transformDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTransform">生成下游 BOM</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="compareDialogVisible" title="BOM 比较" width="860px">
      <div class="toolbar compact-toolbar">
        <span class="muted">基准：{{ selected?.product_model }} {{ selected?.type }} {{ selected?.version }}</span>
        <div class="toolbar-actions">
          <el-select v-model="compareTargetId" placeholder="选择对比 BOM" style="width: 260px">
            <el-option
              v-for="bom in compareOptions"
              :key="bom.id"
              :label="`${bom.product_model} ${bom.type} ${bom.version}`"
              :value="bom.id"
            />
          </el-select>
          <el-button type="primary" @click="loadCompare">比较</el-button>
        </div>
      </div>
      <div v-if="compareResult" class="object-strip">
        <div><span>新增</span><strong>{{ compareResult.summary.added }}</strong></div>
        <div><span>删除</span><strong>{{ compareResult.summary.removed }}</strong></div>
        <div><span>变更</span><strong>{{ compareResult.summary.changed }}</strong></div>
      </div>
      <el-table :data="compareResult?.changes || []" height="420" size="small">
        <el-table-column prop="change_type" label="类型" width="80" fixed />
        <el-table-column prop="material_code" label="物料编码" width="140" />
        <el-table-column prop="material_name" label="物料名称" min-width="180" />
        <el-table-column prop="process_step" label="工序" width="120" />
        <el-table-column prop="from_quantity" label="原用量" width="90" />
        <el-table-column prop="to_quantity" label="新用量" width="90" />
        <el-table-column prop="from_status" label="原状态" width="90" />
        <el-table-column prop="to_status" label="新状态" width="90" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="whereUsedDialogVisible" :title="`${whereUsedMaterial} 反查`" width="820px">
      <el-table :data="whereUsedRows" height="420" size="small">
        <el-table-column prop="product_model" label="产品型号" width="140" fixed />
        <el-table-column prop="bom_type" label="BOM 类型" width="100" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="bom_status" label="BOM 状态" width="100" />
        <el-table-column prop="quantity" label="用量" width="80" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="process_step" label="工序" width="130" />
        <el-table-column prop="effective_date" label="生效日" width="110" />
        <el-table-column prop="expiry_date" label="失效日" width="110" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="processCoverageDialogVisible" title="工序物料分配校验" width="780px">
      <div v-if="processCoverage" class="object-strip">
        <div><span>明细总数</span><strong>{{ processCoverage.total_items }}</strong></div>
        <div><span>已分配工序</span><strong>{{ processCoverage.assigned }}</strong></div>
        <div><span>未分配</span><strong :style="{ color: processCoverage.unassigned > 0 ? 'var(--el-color-danger)' : '' }">{{ processCoverage.unassigned }}</strong></div>
        <div><span>覆盖率</span><strong>{{ (processCoverage.coverage_rate * 100).toFixed(1) }}%</strong></div>
        <div>
          <el-tag v-if="processCoverage.is_complete" size="small" type="success">分配完整</el-tag>
          <el-tag v-else size="small" type="warning">存在未分配工序</el-tag>
        </div>
      </div>
      <div v-if="processCoverage && !processCoverage.is_complete" class="muted" style="margin: 4px 0 8px">以下明细未关联工艺工序，发布前请补齐分配。</div>
      <el-table :data="processCoverage?.unassigned_items || []" height="380" size="small">
        <el-table-column prop="material_code" label="物料编码" width="140" fixed />
        <el-table-column prop="material_name" label="物料名称" min-width="180" />
        <el-table-column prop="position" label="位置" width="90" />
        <el-table-column prop="quantity" label="用量" width="80" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="process_step" label="工序" width="140" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="lineageDialogVisible" title="BOM 转换血缘" width="820px">
      <div v-if="lineageData">
        <div class="muted" style="margin-bottom: 8px">当前：{{ lineageData.current.product_model }} {{ lineageData.current.bom_type }} {{ lineageData.current.version }}</div>
        <div v-if="!lineageData.has_lineage" class="muted">该 BOM 暂无转换血缘记录</div>
        <template v-else>
          <div v-if="lineageData.ancestors.length" style="margin-bottom: 16px">
            <div style="font-weight: 600; margin-bottom: 6px">来源链路（向上溯源）</div>
            <el-table :data="lineageData.ancestors" size="small">
              <el-table-column prop="bom_type" label="类型" width="90" />
              <el-table-column prop="version" label="版本" width="90" />
              <el-table-column prop="product_model" label="产品型号" width="140" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="effective_date" label="生效日" width="120" />
              <el-table-column label="操作" width="90">
                <template #default="{ row }">
                  <el-button size="small" @click="loadBoms(row.id)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-if="lineageData.descendants.length">
            <div style="font-weight: 600; margin-bottom: 6px">派生 BOM（向下追溯）</div>
            <el-table :data="lineageData.descendants" size="small">
              <el-table-column prop="bom_type" label="类型" width="90" />
              <el-table-column prop="version" label="版本" width="90" />
              <el-table-column prop="product_model" label="产品型号" width="140" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="effective_date" label="生效日" width="120" />
              <el-table-column label="操作" width="90">
                <template #default="{ row }">
                  <el-button size="small" @click="loadBoms(row.id)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </div>
    </el-dialog>

    <el-dialog v-model="versionHistoryVisible" title="BOM 版本历史" width="960px">
      <el-table :data="versionHistory" height="420" size="small">
        <el-table-column prop="version" label="版本" width="80" fixed />
        <el-table-column label="当前" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.is_current" size="small" type="success">当前</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="bom_type" label="类型" width="80" />
        <el-table-column prop="owner" label="负责人" width="90" />
        <el-table-column prop="effective_date" label="生效日" width="110" />
        <el-table-column prop="expiry_date" label="失效日" width="110" />
        <el-table-column prop="source_bom_id" label="来源BOM" width="90" />
        <el-table-column prop="change_no" label="变更单" width="130" />
        <el-table-column prop="change_status" label="变更状态" width="90" />
        <el-table-column prop="eca_action_no" label="ECA动作" width="110" />
        <el-table-column label="发布门" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.release_gate_status" size="small" :type="row.release_gate_status === '可提交' ? 'success' : 'warning'">{{ row.release_gate_status }}</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="batchEditVisible" title="BOM 批量编辑" width="900px">
      <el-tabs v-model="batchTab">
        <el-tab-pane label="批量替换物料" name="replace">
          <el-form label-width="100px" style="margin-top: 10px">
            <el-form-item label="原物料编码">
              <el-input v-model="batchReplaceForm.from_code" placeholder="输入要被替换的物料编码" />
            </el-form-item>
            <el-form-item label="新物料编码">
              <el-input v-model="batchReplaceForm.to_code" placeholder="输入新物料编码" />
            </el-form-item>
            <el-form-item label="物料名称">
              <el-input v-model="batchReplaceForm.to_name" placeholder="留空则从物料库自动填充" />
            </el-form-item>
            <el-button type="primary" @click="executeBatchReplace" :disabled="!batchReplaceForm.from_code || !batchReplaceForm.to_code">执行替换</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="批量修改用量" name="quantity">
          <div style="margin-bottom: 10px">
            <el-button size="small" @click="batchSelection = []">清空选择</el-button>
            <span class="muted" style="margin-left: 12px">已选 {{ batchSelection.length }} 项</span>
          </div>
          <el-table :data="selected?.items || []" height="300" size="small" @selection-change="(val: any[]) => batchSelection = val">
            <el-table-column type="selection" width="45" />
            <el-table-column prop="material_code" label="物料编码" width="130" />
            <el-table-column prop="material_name" label="物料名称" min-width="150" />
            <el-table-column prop="quantity" label="当前用量" width="100" />
            <el-table-column prop="unit" label="单位" width="70" />
          </el-table>
          <div style="margin-top: 10px; display: flex; align-items: center; gap: 10px">
            <span>统一改为</span>
            <el-input-number v-model="batchQuantity" :min="0" :precision="3" :step="0.1" style="width: 140px" />
            <el-button type="primary" @click="executeBatchQuantity" :disabled="!batchSelection.length">执行修改</el-button>
          </div>
        </el-tab-pane>
        <el-tab-pane label="批量删除子件" name="delete">
          <div style="margin-bottom: 10px">
            <el-button size="small" @click="batchSelection = []">清空选择</el-button>
            <span class="muted" style="margin-left: 12px">已选 {{ batchSelection.length }} 项</span>
          </div>
          <el-table :data="selected?.items || []" height="300" size="small" @selection-change="(val: any[]) => batchSelection = val">
            <el-table-column type="selection" width="45" />
            <el-table-column prop="material_code" label="物料编码" width="130" />
            <el-table-column prop="material_name" label="物料名称" min-width="150" />
            <el-table-column prop="quantity" label="用量" width="100" />
            <el-table-column prop="process_step" label="工序" width="140" />
          </el-table>
          <div style="margin-top: 10px">
            <el-button type="danger" @click="executeBatchDelete" :disabled="!batchSelection.length">删除选中项 ({{ batchSelection.length }})</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import {
  approveBom,
  batchDeleteBomItems,
  batchReplaceBomMaterial,
  batchUpdateBomQuantity,
  compareBoms,
  createBom,
  createBomItem,
  deleteBom,
  deleteBomItem,
  downloadBomTemplate,
  exportBomExcel,
  getBomLineage,
  getBomProcessCoverage,
  getBomVersionHistory,
  getBomWhereUsed,
  getBoms,
  getProductProcessSteps,
  getProducts,
  importBomExcel,
  submitBom,
  transformBom,
  updateBom,
  updateBomItem
} from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import AttachmentPanel from '../components/AttachmentPanel.vue'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const { can, currentUser, refreshSession } = useAuth()
const bomTypeOptions = useDictionary('DICT_BOM_TYPE').options
const bomStatusOptions = useDictionary('DICT_BOM_STATUS').options
const effectivityOptions = useDictionary('DICT_EFFECTIVITY_TYPE').options
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getBoms)
const products = ref<any[]>([])
const processSteps = ref<any[]>([])
const selected = ref<any>()
const expandedRowKeys = ref<number[]>([])
const bomDialogVisible = ref(false)
const itemDialogVisible = ref(false)
const transformDialogVisible = ref(false)
const compareDialogVisible = ref(false)
const whereUsedDialogVisible = ref(false)
const bomEditingId = ref<number | null>(null)
const itemEditingId = ref<number | null>(null)
const emptyBom = { product_id: undefined, bom_type: 'EBOM', version: 'A0', status: '编制中', owner: '', release_date: '', effective_date: '', expiry_date: '', effectivity_type: '日期' }
const emptyItem = { material_code: '', material_name: '', category: '', specification: '', quantity: 1, unit: '件', position: '', process_step_id: undefined, process_step: '', substitute: '', status: '有效', effective_date: '', expiry_date: '', effectivity_note: '' }
const bomForm = ref<any>({ ...emptyBom })
const itemForm = ref<any>({ ...emptyItem })
const transformForm = ref<any>({ target_type: 'PBOM', version: 'A0', owner: '', effective_date: '', effectivity_type: '日期' })
const compareTargetId = ref<number | undefined>()
const compareResult = ref<any>()
const processCoverageDialogVisible = ref(false)
const processCoverage = ref<any>()
const lineageDialogVisible = ref(false)
const lineageData = ref<any>()
const whereUsedRows = ref<any[]>([])
const whereUsedMaterial = ref('')
const versionHistoryVisible = ref(false)
const versionHistory = ref<any[]>([])
const fileInputRef = ref<HTMLInputElement>()
const batchEditVisible = ref(false)
const batchTab = ref('replace')
const batchSelection = ref<any[]>([])
const batchReplaceForm = ref<any>({ from_code: '', to_code: '', to_name: '' })
const batchQuantity = ref(1)

const bomEffectivityOptions = computed(() => effectivityOptions.value.filter((o) => ['日期', '批次', '项目'].includes(o.value)))
const downstreamBomTypeOptions = computed(() => bomTypeOptions.value.filter((o) => ['PBOM', 'MBOM'].includes(o.value)))

async function loadBoms(keepId?: number) {
  await loadData()
  const target = keepId
    ? (items.value || []).find((item) => item.id === keepId)
    : (items.value || [])[0]
  selected.value = target || null
  expandedRowKeys.value = target ? [target.id] : []
  await loadProcessSteps()
}

async function onExpandChange(row: any, expandedRows: any[]) {
  const isExpanded = expandedRows.some((r: any) => r.id === row.id)
  if (isExpanded) {
    expandedRowKeys.value = [row.id]
    selected.value = row
    await loadProcessSteps()
  } else {
    expandedRowKeys.value = []
    selected.value = null
  }
}

async function loadProcessSteps() {
  processSteps.value = selected.value?.product_id ? await getProductProcessSteps(selected.value.product_id) : []
}

function openBomCreate() {
  if (!can('bom')) return
  bomEditingId.value = null
  bomForm.value = { ...emptyBom, product_id: products.value[0]?.id, owner: currentUser.value?.display_name || '' }
  bomDialogVisible.value = true
}

function openBomEdit(row: any) {
  if (!can('bom') || row.status === '已发布') return
  bomEditingId.value = row.id
  bomForm.value = {
    product_id: row.product_id,
    bom_type: row.type,
    version: row.version,
    status: row.status,
    owner: row.owner,
    release_date: row.release_date,
    effective_date: row.effective_date,
    expiry_date: row.expiry_date,
    effectivity_type: row.effectivity_type || '日期'
  }
  bomDialogVisible.value = true
}

async function saveBom() {
  if (!can('bom')) return
  const row = bomEditingId.value ? await updateBom(bomEditingId.value, bomForm.value) : await createBom(bomForm.value)
  ElMessage.success('BOM 已保存')
  bomDialogVisible.value = false
  await loadBoms(row.id)
}

function openItemCreate() {
  if (!can('bom') || !selected.value || selected.value.status === '已发布') return
  itemEditingId.value = null
  itemForm.value = { ...emptyItem }
  itemDialogVisible.value = true
}

function openItemEdit(row: any) {
  if (!can('bom') || selected.value?.status === '已发布') return
  itemEditingId.value = row.id
  itemForm.value = { ...row }
  itemDialogVisible.value = true
}

async function saveItem() {
  if (!can('bom')) return
  if (!selected.value) return
  if (itemEditingId.value) {
    await updateBomItem(itemEditingId.value, itemForm.value)
  } else {
    await createBomItem(selected.value.id, itemForm.value)
  }
  ElMessage.success('BOM 明细已保存')
  itemDialogVisible.value = false
  await loadBoms(selected.value.id)
}

async function removeItem(row: any) {
  if (!can('bom')) return
  await ElMessageBox.confirm(`确认删除 BOM 行 ${row.material_code}？`, '删除确认', { type: 'warning' })
  await deleteBomItem(row.id)
  ElMessage.success('BOM 行已删除')
  await loadBoms(selected.value?.id)
}

async function removeBom() {
  if (!can('bom')) return
  if (!selected.value) return
  await ElMessageBox.confirm(`确认删除 ${selected.value.product_model} ${selected.value.type}？`, '删除确认', { type: 'warning' })
  await deleteBom(selected.value.id)
  ElMessage.success('BOM 已删除')
  await loadBoms()
}

async function submit(row: any) {
  if (!can('bom')) return
  await submitBom(row.id)
  ElMessage.success('BOM 已提交审核')
  await loadBoms(row.id)
}

async function approve(row: any) {
  if (!can(['approval', 'bom'])) return
  const result = await approveBom(row.id)
  const closedCount = result.closed_versions?.length || 0
  ElMessage.success(closedCount ? `BOM 已发布，并自动失效 ${closedCount} 个旧版本` : 'BOM 已发布，ERP 同步队列已生成')
  await loadBoms(row.id)
}

const compareOptions = computed(() => {
  if (!selected.value) return []
  return (items.value || []).filter((item) => item.id !== selected.value.id && item.product_id === selected.value.product_id)
})

function openTransform() {
  if (!can('bom') || !selected.value) return
  transformForm.value = {
    target_type: selected.value.type === 'EBOM' ? 'PBOM' : 'MBOM',
    version: selected.value.version,
    owner: selected.value.owner,
    effective_date: selected.value.effective_date || '',
    effectivity_type: selected.value.effectivity_type || '日期'
  }
  transformDialogVisible.value = true
}

async function saveTransform() {
  if (!can('bom') || !selected.value) return
  const row = await transformBom(selected.value.id, transformForm.value)
  const diff = row.transform_diff
  transformDialogVisible.value = false
  await loadBoms(row.id)
  if (diff) {
    const completeness = diff.process_is_complete ? '工序分配完整' : `仍有 ${diff.process_unassigned} 条未分配工序`
    ElMessageBox.alert(
      `已生成 ${row.type} ${row.version}，共 ${diff.items_total} 条明细。\n` +
      `与来源差异：新增 ${diff.items_added} · 删除 ${diff.items_removed} · 变更 ${diff.items_changed}\n` +
      `${completeness}，可前往「工序校验」核对，前往「转换血缘」查看链路。`,
      '转换完成',
      { confirmButtonText: '知道了' }
    )
  } else {
    ElMessage.success(`${row.type} 已生成`)
  }
}

function openCompare() {
  if (!selected.value) return
  compareTargetId.value = compareOptions.value[0]?.id
  compareResult.value = undefined
  compareDialogVisible.value = true
}

async function loadCompare() {
  if (!selected.value || !compareTargetId.value) return
  compareResult.value = await compareBoms(selected.value.id, compareTargetId.value)
}

async function openProcessCoverage() {
  if (!selected.value) return
  processCoverage.value = await getBomProcessCoverage(selected.value.id)
  processCoverageDialogVisible.value = true
}

async function openLineage() {
  if (!selected.value) return
  lineageData.value = await getBomLineage(selected.value.id)
  lineageDialogVisible.value = true
}

async function openWhereUsed(row: any) {
  whereUsedMaterial.value = row.material_code
  whereUsedRows.value = await getBomWhereUsed(row.material_code)
  whereUsedDialogVisible.value = true
}

async function handleExport(row: any) {
  try {
    const response = await exportBomExcel(row.id)
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${row.bom_type || 'BOM'}-${row.product_model || ''}-${row.version || ''}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('导出失败')
  }
}

function triggerImport() {
  fileInputRef.value?.click()
}

async function handleImport(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !selected.value) return
  try {
    const result = await importBomExcel(selected.value.id, file)
    const parts: string[] = [`成功导入 ${result.imported} 条物料`]
    if (result.warnings?.length) {
      parts.push(`警告 ${result.warnings.length} 条`)
    }
    if (result.errors?.length) {
      parts.push(`错误/跳过 ${result.errors.length} 条`)
    }
    ElMessage.success(parts.join('，'))
    // Show detailed warnings/errors if any
    if (result.warnings?.length || result.errors?.length) {
      const details = [
        ...(result.warnings || []).map((w: any) => `⚠️ 行${w.row}: ${w.message}`),
        ...(result.errors || []).map((e: any) => `❌ 行${e.row}: ${e.message}`),
      ].join('\n')
      await ElMessageBox.alert(details, '导入结果详情', { type: 'warning', customClass: 'import-detail-msg' })
    }
    await loadBoms(selected.value?.id)
  } catch {
    ElMessage.error('导入失败')
  }
  target.value = ''
}

async function handleDownloadTemplate() {
  try {
    const response = await downloadBomTemplate()
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'BOM_template.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('模板下载失败')
  }
}

function openBatchEdit() {
  if (!can('bom') || !selected.value || selected.value.status === '已发布') return
  batchTab.value = 'replace'
  batchSelection.value = []
  batchReplaceForm.value = { from_code: '', to_code: '', to_name: '' }
  batchQuantity.value = 1
  batchEditVisible.value = true
}

async function executeBatchReplace() {
  if (!selected.value) return
  try {
    const result = await batchReplaceBomMaterial(selected.value.id, batchReplaceForm.value)
    ElMessage.success(`已替换 ${result.updated} 条物料记录`)
    batchEditVisible.value = false
    await loadBoms(selected.value.id)
  } catch {
    ElMessage.error('批量替换失败')
  }
}

async function executeBatchQuantity() {
  if (!selected.value || !batchSelection.value.length) return
  try {
    const ids = batchSelection.value.map((item: any) => item.id)
    const result = await batchUpdateBomQuantity(selected.value.id, { item_ids: ids, quantity: batchQuantity.value })
    ElMessage.success(`已修改 ${result.updated} 条物料用量`)
    batchEditVisible.value = false
    await loadBoms(selected.value.id)
  } catch {
    ElMessage.error('批量修改用量失败')
  }
}

async function executeBatchDelete() {
  if (!selected.value || !batchSelection.value.length) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${batchSelection.value.length} 条BOM行？`, '批量删除确认', { type: 'warning' })
    const ids = batchSelection.value.map((item: any) => item.id)
    const result = await batchDeleteBomItems(selected.value.id, { item_ids: ids })
    ElMessage.success(`已删除 ${result.deleted} 条BOM行`)
    batchEditVisible.value = false
    await loadBoms(selected.value.id)
  } catch {
    // user cancelled or error
  }
}

async function openVersionHistory(row: any) {
  versionHistory.value = await getBomVersionHistory(row.id)
  versionHistoryVisible.value = true
}

onMounted(async () => {
  await refreshSession()
  products.value = (await getProducts()).items
  await loadBoms()
})
</script>
