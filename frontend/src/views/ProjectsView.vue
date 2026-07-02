<template>
  <div class="panel list-panel" v-loading="loading">
    <div class="toolbar">
      <div><strong>项目管理</strong><span class="muted"> · 项目计划、阶段门、交付物、风险登记</span></div>
      <div class="toolbar-actions">
        <el-input v-model="keyword" placeholder="搜索项目编号/名称" :prefix-icon="Search" clearable @keyup.enter="onSearch" @clear="onSearch" />
        <el-button v-if="can('project')" type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
        <el-button v-if="can('project')" type="default" @click="openFromTemplate">从模板创建</el-button>
        <el-button v-if="can('project')" type="default" @click="showTemplateDialog = true">项目模板</el-button>
      </div>
    </div>

    <div class="list-table-wrap">
    <el-table :data="items" row-key="id" height="100%">
      <el-table-column type="expand">
        <template #default="{ row }">
          <el-tabs class="compact-tabs" @tab-change="(name: any) => onTabChange(row, String(name))">
            <el-tab-pane label="阶段任务" name="tasks">
              <div v-if="can('project')" class="phase-gate-criteria" v-loading="false">
                <div class="gate-header">
                  <span class="gate-title">阶段门准入（{{ row.phase }}）</span>
                  <el-tag size="small" :type="phaseGateReady(row) ? 'success' : 'warning'">{{ phaseGateReady(row) ? '可推进' : '未满足' }}</el-tag>
                </div>
                <div class="gate-body">
                  <span class="gate-item">交付物 <b>{{ phaseDeliverableDone(row) }}/{{ phaseDeliverableTotal(row) }}</b> 已完成</span>
                  <span class="gate-sep">·</span>
                  <span class="gate-item">任务 <b>{{ phaseTaskDone(row) }}/{{ phaseTaskTotal(row) }}</b> 已完成</span>
                  <span class="gate-sep">·</span>
                  <span v-if="phaseGateReady(row)" class="gate-ok">准入条件已满足，可推进阶段门</span>
                  <span v-else class="gate-pending">存在未完成交付物，无法推进</span>
                </div>
              </div>
              <div style="margin-bottom:8px" v-if="can('project')">
                <el-button size="small" type="primary" @click="openCreateTask(row)">新增任务</el-button>
                <el-button size="small" type="success" @click="advancePhase(row)" :disabled="row.phase === '量产导入' || !phaseGateReady(row)">推进阶段门</el-button>
              </div>
              <el-table :data="row.tasks" size="small">
                <el-table-column prop="name" label="任务" min-width="180" />
                <el-table-column prop="phase" label="阶段" width="100" />
                <el-table-column prop="owner" label="负责人" width="110" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row: t }">
                    <el-tag size="small" :type="t.status === '已完成' ? 'success' : t.status === '进行中' ? 'warning' : 'info'">{{ t.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="due_date" label="截止日期" width="120" />
                <el-table-column label="操作" width="130" v-if="can('project')">
                  <template #default="{ row: t }">
                    <el-button size="small" @click="openEditTask(row, t)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeTask(t)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="交付物" name="deliverables">
              <el-table :data="row.deliverables" size="small">
                <el-table-column prop="name" label="交付物" min-width="140" />
                <el-table-column prop="deliverable_type" label="类型" width="90" />
                <el-table-column prop="phase" label="阶段" width="80" />
                <el-table-column prop="owner" label="负责人" width="90" />
                <el-table-column prop="status" label="状态" width="90">
                  <template #default="{ row: d }">
                    <el-tag size="small" :type="d.status === '已完成' ? 'success' : d.status === '已关闭' ? 'info' : d.status === '进行中' ? 'warning' : 'info'">{{ d.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="关联对象" min-width="180">
                  <template #default="{ row: d }">
                    <span v-if="!d.object_type" class="muted">-</span>
                    <template v-else>
                      <span>{{ d.object_type }} · </span>
                      <span :title="d.object_label">{{ d.object_label || `#${d.object_id}` }}</span>
                      <el-tag v-if="d.object_status" size="small" :type="d.object_released ? 'success' : 'warning'" style="margin-left:4px">{{ d.object_status }}</el-tag>
                    </template>
                  </template>
                </el-table-column>
                <el-table-column prop="due_date" label="截止日" width="100" />
                <el-table-column label="操作" width="100" v-if="can('project')">
                  <template #default="{ row: d }">
                    <el-button size="small" @click="openEditDeliverable(row, d)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeDeliverable(d)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div style="margin-top:8px; display:flex; gap:8px">
                <el-button v-if="can('project')" size="small" type="primary" @click="openCreateDeliverable(row)">新增交付物</el-button>
                <el-button size="small" @click="openClosureCheck(row)">结项校验</el-button>
              </div>
            </el-tab-pane>
            <el-tab-pane label="风险登记" name="risks">
              <el-table :data="row.risks" size="small">
                <el-table-column prop="risk_type" label="类型" width="100" />
                <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
                <el-table-column prop="impact" label="影响" width="80" />
                <el-table-column prop="probability" label="概率" width="80" />
                <el-table-column prop="severity" label="严重度" width="80" />
                <el-table-column prop="owner" label="负责人" width="100" />
                <el-table-column prop="status" label="状态" width="100" />
                <el-table-column prop="mitigation" label="缓解措施" min-width="200" show-overflow-tooltip />
                <el-table-column label="操作" width="100" v-if="can('project')">
                  <template #default="{ row: r }">
                    <el-button size="small" @click="openEditRisk(row, r)">编辑</el-button>
                    <el-button size="small" type="danger" @click="removeRisk(r)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-button v-if="can('project')" size="small" type="primary" @click="openCreateRisk(row)" style="margin-top:8px">新增风险</el-button>
            </el-tab-pane>
            <el-tab-pane label="计划甘特图" name="gantt" lazy>
              <div :ref="(el: any) => setGanttRef(el, row.id)" class="gantt-chart-container"></div>
              <div v-if="!hasDatedTasks(row)" class="gantt-empty">暂无带日期的任务，请在任务编辑中填写开始日期和截止日期</div>
            </el-tab-pane>
            <el-tab-pane label="关联对象" name="cross-modules" lazy>
              <div v-if="!crossModulesData[row.id]" class="gantt-empty">加载中…</div>
              <template v-else>
                <div class="object-strip" style="margin-bottom:8px">
                  <div><span>产品</span><strong>{{ crossModulesData[row.id].product_model || '未关联' }}</strong></div>
                  <div><span>生命周期</span><strong>{{ crossModulesData[row.id].product_lifecycle || '-' }}</strong></div>
                  <div><span>BOM</span><strong>{{ crossModulesData[row.id].counts.boms }}</strong></div>
                  <div><span>文档</span><strong>{{ crossModulesData[row.id].counts.documents }}</strong></div>
                  <div><span>工艺</span><strong>{{ crossModulesData[row.id].counts.process_routes }}</strong></div>
                  <div><span>变更</span><strong>{{ crossModulesData[row.id].counts.changes }}</strong></div>
                  <div><span>质量</span><strong>{{ crossModulesData[row.id].counts.quality_issues }}</strong></div>
                  <div><span>需求</span><strong>{{ crossModulesData[row.id].counts.requirements }}</strong></div>
                </div>
                <div v-if="!crossModulesData[row.id].product_id" class="gantt-empty">该项目未关联有效产品型号，无法聚合关联对象</div>
                <template v-else>
                  <el-tabs class="compact-tabs" type="card">
                    <el-tab-pane :label="`BOM (${crossModulesData[row.id].counts.boms})`">
                      <el-table :data="crossModulesData[row.id].boms" size="small" max-height="280">
                        <el-table-column prop="bom_type" label="类型" width="80" />
                        <el-table-column prop="version" label="版本" width="80" />
                        <el-table-column prop="status" label="状态" width="90" />
                        <el-table-column prop="owner" label="负责人" width="100" />
                        <el-table-column prop="release_date" label="发布日" width="110" />
                        <el-table-column prop="effective_date" label="生效日" width="110" />
                        <el-table-column label="当前" width="70">
                          <template #default="{ row: b }">
                            <el-tag v-if="b.is_current" size="small" type="success">当前</el-tag>
                            <span v-else class="muted">-</span>
                          </template>
                        </el-table-column>
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`文档 (${crossModulesData[row.id].counts.documents})`">
                      <el-table :data="crossModulesData[row.id].documents" size="small" max-height="280">
                        <el-table-column prop="doc_no" label="编号" width="140" />
                        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
                        <el-table-column prop="category" label="类别" width="100" />
                        <el-table-column prop="version" label="版本" width="80" />
                        <el-table-column prop="status" label="状态" width="90" />
                        <el-table-column prop="owner" label="负责人" width="100" />
                        <el-table-column prop="updated_at" label="更新" width="110" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`工艺路线 (${crossModulesData[row.id].counts.process_routes})`">
                      <el-table :data="crossModulesData[row.id].process_routes" size="small" max-height="280">
                        <el-table-column prop="route_no" label="编号" width="140" />
                        <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
                        <el-table-column prop="version" label="版本" width="80" />
                        <el-table-column prop="status" label="状态" width="90" />
                        <el-table-column prop="owner" label="负责人" width="100" />
                        <el-table-column prop="release_date" label="发布日" width="110" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`工程变更 (${crossModulesData[row.id].counts.changes})`">
                      <el-table :data="crossModulesData[row.id].changes" size="small" max-height="280">
                        <el-table-column prop="change_no" label="编号" width="140" />
                        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
                        <el-table-column prop="change_type" label="类型" width="80" />
                        <el-table-column prop="priority" label="优先级" width="80" />
                        <el-table-column prop="status" label="状态" width="90" />
                        <el-table-column prop="owner" label="负责人" width="100" />
                        <el-table-column prop="submitted_at" label="提交日" width="110" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`质量问题 (${crossModulesData[row.id].counts.quality_issues})`">
                      <el-table :data="crossModulesData[row.id].quality_issues" size="small" max-height="280">
                        <el-table-column prop="issue_no" label="编号" width="140" />
                        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
                        <el-table-column prop="severity" label="严重度" width="80" />
                        <el-table-column prop="lot_no" label="批次" width="120" />
                        <el-table-column prop="status" label="状态" width="90" />
                        <el-table-column prop="owner" label="负责人" width="100" />
                      </el-table>
                    </el-tab-pane>
                    <el-tab-pane :label="`需求规格 (${crossModulesData[row.id].counts.requirements})`">
                      <el-table :data="crossModulesData[row.id].requirements" size="small" max-height="280">
                        <el-table-column prop="req_no" label="编号" width="140" />
                        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
                        <el-table-column prop="category" label="类别" width="100" />
                        <el-table-column prop="priority" label="优先级" width="80" />
                        <el-table-column prop="status" label="状态" width="90" />
                        <el-table-column prop="owner" label="负责人" width="100" />
                      </el-table>
                    </el-tab-pane>
                  </el-tabs>
                </template>
              </template>
            </el-tab-pane>
          </el-tabs>
          <AttachmentPanel object-type="Project" :object-id="row.id" :can-edit="can('project')" />
        </template>
      </el-table-column>
      <el-table-column prop="project_no" label="项目编号" width="150" />
      <el-table-column prop="name" label="项目名称" min-width="200" />
      <el-table-column prop="product_model" label="产品型号" width="130" />
      <el-table-column prop="phase" label="阶段" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.phase === '量产导入' ? 'success' : 'primary'">{{ row.phase }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="progress" label="进度" width="160">
        <template #default="{ row }"><el-progress :percentage="row.progress" :status="row.progress >= 100 ? 'success' : undefined" /></template>
      </el-table-column>
      <el-table-column prop="owner" label="负责人" width="100" />
      <el-table-column prop="risk_level" label="风险" width="80" />
      <el-table-column prop="end_date" label="计划完成" width="110" />
      <el-table-column label="归档" width="90">
        <template #default="{ row }">
          <el-tag v-if="row.is_archived" size="small" type="info">已归档</el-tag>
          <span v-else class="muted">-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <el-button size="small" @click="openEdit(row)" :disabled="row.is_archived">编辑</el-button>
            <el-button v-if="!row.is_archived && can('project')" size="small" type="warning" @click="openArchive(row)">归档</el-button>
            <el-button v-if="row.is_archived" size="small" @click="openArchivePackage(row)">数据包</el-button>
            <el-button v-if="row.is_archived && can('project')" size="small" @click="handleUnarchive(row)">撤销</el-button>
            <el-button v-if="!row.is_archived && can('project')" size="small" type="danger" @click="remove(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    </div>
    <div class="pagination-bar" v-if="pagination.total > pagination.pageSize">
      <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[20, 50, 100, 200]" layout="total, sizes, prev, pager, next, jumper" @current-change="onPageChange" @size-change="onSizeChange" />
    </div>

    <!-- Project Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑项目' : '新建项目'" width="640px">
      <el-form :model="form" label-width="100px">
        <div class="form-grid">
          <el-form-item label="项目编号"><el-input v-model="form.project_no" /></el-form-item>
          <el-form-item label="项目名称"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="产品型号">
            <el-select v-model="form.product_model" filterable clearable placeholder="选择产品">
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.model" />
            </el-select>
          </el-form-item>
          <el-form-item label="阶段"><el-select v-model="form.phase"><el-option v-for="o in phaseOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="进度"><el-input-number v-model="form.progress" :min="0" :max="100" /></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="form.owner" /></el-form-item>
          <el-form-item label="开始日期"><el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item>
          <el-form-item label="计划完成"><el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item>
          <el-form-item label="风险等级"><el-select v-model="form.risk_level"><el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>

    <!-- Task Dialog -->
    <el-dialog v-model="taskDialog" :title="taskEditingId ? '编辑任务' : '新增任务'" width="540px">
      <el-form :model="taskForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="任务名称" class="form-wide"><el-input v-model="taskForm.name" /></el-form-item>
          <el-form-item label="阶段"><el-select v-model="taskForm.phase"><el-option v-for="o in phaseOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="taskForm.owner" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="taskForm.status"><el-option v-for="o in taskStatusOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="截止日期"><el-date-picker v-model="taskForm.due_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item>
          <el-form-item label="开始日期"><el-date-picker v-model="taskForm.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item>
          <el-form-item label="依赖任务" class="form-wide">
            <el-select v-model="taskDependsIds" multiple filterable clearable placeholder="选择前置任务" @change="onDependsChange">
              <el-option v-for="t in taskDependencyOptions" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="taskDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>

    <!-- Deliverable Dialog -->
    <el-dialog v-model="deliverableDialog" title="交付物" width="640px">
      <el-form :model="deliverableForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="名称"><el-input v-model="deliverableForm.name" /></el-form-item>
          <el-form-item label="类型"><el-select v-model="deliverableForm.deliverable_type"><el-option v-for="o in deliverableTypeOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="阶段"><el-select v-model="deliverableForm.phase"><el-option v-for="o in phaseOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="deliverableForm.owner" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="deliverableForm.status"><el-option v-for="o in deliverableStatusOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="截止日期"><el-date-picker v-model="deliverableForm.due_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item>
          <el-form-item label="关联对象类型">
            <el-select v-model="deliverableForm.object_type" clearable placeholder="可选" @change="onObjectTypeChange">
              <el-option label="BOM" value="BOM" />
              <el-option label="文档" value="文档" />
              <el-option label="工艺路线" value="工艺路线" />
            </el-select>
          </el-form-item>
          <el-form-item label="关联对象">
            <el-select v-model="deliverableForm.object_id" filterable clearable placeholder="选择关联对象" :disabled="!deliverableForm.object_type">
              <el-option v-for="obj in linkableObjects" :key="obj.id" :label="obj.label" :value="obj.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="deliverableForm.description" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="deliverableDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDeliverable">保存</el-button>
      </template>
    </el-dialog>

    <!-- Risk Dialog -->
    <el-dialog v-model="riskDialog" title="风险登记" width="600px">
      <el-form :model="riskForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="风险类型"><el-select v-model="riskForm.risk_type"><el-option v-for="o in riskTypeOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="描述"><el-input v-model="riskForm.description" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="影响"><el-select v-model="riskForm.impact"><el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="概率"><el-select v-model="riskForm.probability"><el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="严重度"><el-select v-model="riskForm.severity"><el-option v-for="o in riskLevelOptions" :key="o.value" :label="o.label" :value="o.value" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="riskForm.owner" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="riskForm.status"><el-option label="待处理" value="待处理" /><el-option label="已识别" value="已识别" /><el-option label="已关闭" value="已关闭" /></el-select></el-form-item>
          <el-form-item label="缓解措施" class="form-wide"><el-input v-model="riskForm.mitigation" type="textarea" :rows="2" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="riskDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRisk">保存</el-button>
      </template>
    </el-dialog>

    <!-- Template Dialog -->
    <el-dialog v-model="showTemplateDialog" title="项目模板管理" width="760px">
      <div class="toolbar">
        <el-button v-if="can('project')" size="small" type="primary" @click="openCreateTemplate">新增模板</el-button>
      </div>
      <el-table :data="templates">
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" width="140" />
        <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
        <el-table-column label="阶段定义" min-width="220">
          <template #default="{ row }">{{ stagesToText(row.stages) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" />
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button size="small" @click="openEditTemplate(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeTemplate(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Template Form Sub-Dialog -->
    <el-dialog v-model="templateDialogVisible" :title="templateEditingId ? '编辑模板' : '新增模板'" width="720px" append-to-body>
      <el-form :model="templateForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="templateForm.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="templateForm.name" /></el-form-item>
          <el-form-item label="描述" class="form-wide"><el-input v-model="templateForm.description" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="阶段" class="form-wide"><el-input v-model="templateForm.stages" placeholder="概念,设计,流片,验证,试产" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="templateForm.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>

    <!-- Create From Template Dialog -->
    <el-dialog v-model="fromTemplateDialog" title="从模板创建项目" width="640px">
      <el-form :model="fromTemplateForm" label-width="100px">
        <div class="form-grid">
          <el-form-item label="模板" class="form-wide">
            <el-select v-model="fromTemplateForm.template_id" filterable placeholder="选择模板">
              <el-option v-for="tpl in templates" :key="tpl.id" :label="`${tpl.code} · ${tpl.name}`" :value="tpl.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="项目编号"><el-input v-model="fromTemplateForm.project_no" /></el-form-item>
          <el-form-item label="项目名称"><el-input v-model="fromTemplateForm.name" /></el-form-item>
          <el-form-item label="产品型号">
            <el-select v-model="fromTemplateForm.product_model" filterable clearable placeholder="选择产品">
              <el-option v-for="product in products" :key="product.id" :label="product.model" :value="product.model" />
            </el-select>
          </el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="fromTemplateForm.owner" /></el-form-item>
          <el-form-item label="开始日期"><el-date-picker v-model="fromTemplateForm.start_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item>
          <el-form-item label="结束日期"><el-date-picker v-model="fromTemplateForm.end_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="fromTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFromTemplate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="closureDialogVisible" title="交付物齐套校验" width="900px">
      <div v-if="closureData" class="object-strip" style="margin-bottom:8px">
        <div><span>项目</span><strong>{{ closureData.project_no }}</strong></div>
        <div><span>当前阶段</span><strong>{{ closureData.phase }}</strong></div>
        <div><span>进度</span><strong>{{ closureData.progress }}%</strong></div>
        <div><span>交付物</span><strong>{{ closureData.total }}</strong></div>
        <div><span>已齐套</span><strong :style="{ color: closureData.ready === closureData.total ? '' : 'var(--el-color-danger)' }">{{ closureData.ready }}/{{ closureData.total }}</strong></div>
        <div>
          <el-tag v-if="closureData.is_complete" size="small" type="success">全部齐套</el-tag>
          <el-tag v-else size="small" type="warning">{{ closureData.pending }} 项未齐套</el-tag>
        </div>
      </div>
      <div v-if="closureData && !closureData.is_complete" class="muted" style="margin: 4px 0 8px">未齐套项：交付物状态须为「已完成/已关闭」，且绑定对象（BOM/文档/工艺路线）须「已发布」。</div>
      <el-table :data="closureData?.items || []" height="420" size="small">
        <el-table-column prop="phase" label="阶段" width="80" fixed />
        <el-table-column prop="name" label="交付物" min-width="150" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status_ok ? 'success' : 'warning'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联对象" min-width="180">
          <template #default="{ row }">
            <span v-if="!row.object_type" class="muted">无</span>
            <template v-else>
              <span>{{ row.object_type }} · {{ row.object_label || `#${row.object_id}` }}</span>
              <el-tag v-if="row.object_status" size="small" :type="row.object_ok ? 'success' : 'warning'" style="margin-left:4px">{{ row.object_status }}</el-tag>
            </template>
          </template>
        </el-table-column>
        <el-table-column label="齐套" width="80" fixed="right">
          <template #default="{ row }">
            <el-tag v-if="row.ready" size="small" type="success">齐套</el-tag>
            <el-tag v-else size="small" type="danger">未齐</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="问题" min-width="160">
          <template #default="{ row }">
            <span v-if="row.issue" style="color: var(--el-color-danger)">{{ row.issue }}</span>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="archiveDialogVisible" title="项目归档" width="680px">
      <el-form :model="archiveForm" label-width="100px">
        <el-form-item label="项目"><span>{{ archiveTarget?.project_no }} {{ archiveTarget?.name }}</span></el-form-item>
        <el-form-item label="当前阶段"><span>{{ archiveTarget?.phase }}</span></el-form-item>
        <el-form-item label="归档说明">
          <el-input v-model="archiveForm.summary" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="归档说明（可选，记录结案要点）" style="max-width:480px" />
        </el-form-item>
        <div class="muted" style="margin-left:100px; max-width:480px">归档条件：阶段须为「量产导入」且交付物全部齐套。归档后项目及关联对象进入只读。</div>
      </el-form>
      <template #footer>
        <el-button @click="archiveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveArchive">确认归档</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="archivePackageDialogVisible" title="项目归档数据包" width="960px">
      <div v-if="!archivePackageData" class="gantt-empty">加载中…</div>
      <template v-else>
        <div class="object-strip" style="margin-bottom:8px">
          <div><span>项目</span><strong>{{ archivePackageData.project.project_no }}</strong></div>
          <div><span>产品</span><strong>{{ archivePackageData.project.product_model }}</strong></div>
          <div><span>归档日</span><strong>{{ archivePackageData.project.archived_at }}</strong></div>
          <div><span>归档人</span><strong>{{ archivePackageData.project.archived_by }}</strong></div>
        </div>
        <div v-if="archivePackageData.project.archive_summary" style="margin:4px 0 12px">
          <strong>归档说明：</strong>{{ archivePackageData.project.archive_summary }}
        </div>
        <el-tabs class="compact-tabs" type="card">
          <el-tab-pane :label="`交付物 (${archivePackageData.counts.deliverables})`">
            <el-table :data="archivePackageData.deliverables" size="small" max-height="320">
              <el-table-column prop="phase" label="阶段" width="80" />
              <el-table-column prop="name" label="交付物" min-width="140" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column label="关联对象" min-width="180">
                <template #default="{ row }">
                  <span v-if="!row.object_type" class="muted">-</span>
                  <span v-else>{{ row.object_type }} · {{ row.object_label }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="owner" label="负责人" width="90" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`BOM (${archivePackageData.counts.boms})`">
            <el-table :data="archivePackageData.boms" size="small" max-height="320">
              <el-table-column prop="bom_type" label="类型" width="80" />
              <el-table-column prop="version" label="版本" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="items_count" label="明细数" width="80" />
              <el-table-column prop="owner" label="负责人" width="90" />
              <el-table-column prop="release_date" label="发布日" width="110" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`文档 (${archivePackageData.counts.documents})`">
            <el-table :data="archivePackageData.documents" size="small" max-height="320">
              <el-table-column prop="doc_no" label="编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="category" label="类别" width="100" />
              <el-table-column prop="version" label="版本" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`工艺路线 (${archivePackageData.counts.process_routes})`">
            <el-table :data="archivePackageData.process_routes" size="small" max-height="320">
              <el-table-column prop="route_no" label="编号" width="140" />
              <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="version" label="版本" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`工程变更 (${archivePackageData.counts.changes})`">
            <el-table :data="archivePackageData.changes" size="small" max-height="320">
              <el-table-column prop="change_no" label="编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="change_type" label="类型" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`质量问题 (${archivePackageData.counts.quality_issues})`">
            <el-table :data="archivePackageData.quality_issues" size="small" max-height="320">
              <el-table-column prop="issue_no" label="编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="severity" label="严重度" width="80" />
              <el-table-column prop="status" label="状态" width="90" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`质量报告 (${archivePackageData.counts.quality_reports})`">
            <el-table :data="archivePackageData.quality_reports" size="small" max-height="320">
              <el-table-column prop="report_no" label="编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="report_type" label="类型" width="100" />
              <el-table-column prop="status" label="状态" width="90" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane :label="`流程记录 (${archivePackageData.counts.workflow_instances})`">
            <el-table :data="archivePackageData.workflow_instances" size="small" max-height="320">
              <el-table-column prop="object_type" label="对象类型" width="100" />
              <el-table-column prop="object_no" label="对象编号" width="140" />
              <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
              <el-table-column prop="status" label="状态" width="90" />
              <el-table-column prop="started_by" label="发起人" width="90" />
              <el-table-column prop="started_at" label="发起日" width="110" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  advanceProjectPhase, archiveProject, createProject, createProjectDeliverable, createProjectFromTemplate, createProjectRisk, createProjectTask, createProjectTemplate, deleteProject, deleteProjectDeliverable,
  deleteProjectRisk, deleteProjectTask, deleteProjectTemplate, getBoms, getDocuments, getProducts, getProjects, getProjectTemplates, getProjectArchivePackage, getProjectCrossModules, getProjectClosureCheck, getProcessFlows, unarchiveProject, updateProject, updateProjectDeliverable,
  updateProjectRisk, updateProjectTask, updateProjectTemplate,
} from '../api'
import { useAuth } from '../auth'
import UserSelect from '../components/UserSelect.vue'
import AttachmentPanel from '../components/AttachmentPanel.vue'
import { useListPage } from '../composables/useListPage'
import { useDictionary } from '../composables/useDictionary'

const phaseOptions = useDictionary('DICT_PROJECT_PHASE').options
const riskLevelOptions = useDictionary('DICT_RISK_LEVEL').options
const taskStatusOptions = useDictionary('DICT_TASK_STATUS').options
const deliverableStatusOptions = useDictionary('DICT_DELIVERABLE_STATUS').options
const deliverableTypeOptions = useDictionary('DICT_DELIVERABLE_TYPE').options
const riskTypeOptions = useDictionary('DICT_RISK_TYPE').options

const { can, currentUser } = useAuth()
const { pagination, keyword, items, loading, loadData, onSearch, onPageChange, onSizeChange } = useListPage(getProjects)
const products = ref<any[]>([])
const templates = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const form = ref<any>({ project_no: '', name: '', product_model: '', phase: '概念', progress: 0, owner: '', start_date: '', end_date: '', risk_level: '低' })

const taskDialog = ref(false)
const taskProjectId = ref<number>(0)
const taskEditingId = ref<number | null>(null)
const taskForm = ref<any>({ name: '', phase: '概念', owner: '', status: '待处理', due_date: '', start_date: '', depends_on: '' })

const deliverableDialog = ref(false)
const deliverableProjectId = ref<number>(0)
const deliverableEditingId = ref<number | null>(null)
const deliverableForm = ref<any>({ name: '', deliverable_type: '', phase: '', owner: '', status: '待处理', due_date: '', description: '', object_type: '', object_id: undefined })
const linkableObjects = ref<any[]>([])
const bomList = ref<any[]>([])
const documentList = ref<any[]>([])
const routeList = ref<any[]>([])

const riskDialog = ref(false)
const riskProjectId = ref<number>(0)
const riskEditingId = ref<number | null>(null)
const riskForm = ref<any>({ risk_type: '技术', description: '', impact: '中', probability: '中', severity: '中', owner: '', status: '待处理', mitigation: '' })

const showTemplateDialog = ref(false)
const templateDialogVisible = ref(false)
const templateEditingId = ref<number | null>(null)
const templateForm = ref<any>({ code: '', name: '', description: '', stages: '概念,设计,流片,验证,试产', status: '启用' })

const fromTemplateDialog = ref(false)
const fromTemplateForm = ref<any>({ template_id: undefined, project_no: '', name: '', product_model: '', owner: '', start_date: '', end_date: '' })

const closureDialogVisible = ref(false)
const closureData = ref<any>(null)

async function openClosureCheck(row: any) {
  try {
    closureData.value = await getProjectClosureCheck(row.id)
    closureDialogVisible.value = true
  } catch (e: any) {
    ElMessage.error('加载齐套校验失败')
  }
}

const archiveDialogVisible = ref(false)
const archiveTarget = ref<any>(null)
const archiveForm = ref<any>({ summary: '' })
const archivePackageDialogVisible = ref(false)
const archivePackageData = ref<any>(null)

function openArchive(row: any) {
  archiveTarget.value = row
  archiveForm.value = { summary: '' }
  archiveDialogVisible.value = true
}

async function saveArchive() {
  if (!archiveTarget.value) return
  try {
    await archiveProject(archiveTarget.value.id, { summary: archiveForm.value.summary })
    ElMessage.success('项目已归档')
    archiveDialogVisible.value = false
    await loadData()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '归档失败'
    ElMessage.error(msg)
  }
}

async function openArchivePackage(row: any) {
  try {
    archivePackageData.value = await getProjectArchivePackage(row.id)
    archivePackageDialogVisible.value = true
  } catch (e: any) {
    ElMessage.error('加载数据包失败')
  }
}

async function handleUnarchive(row: any) {
  try {
    await ElMessageBox.confirm(`确认撤销归档项目「${row.project_no}」？撤销后项目恢复可编辑。`, '撤销归档', { type: 'warning' })
  } catch {
    return
  }
  try {
    await unarchiveProject(row.id)
    ElMessage.success('已撤销归档')
    await loadData()
  } catch (e: any) {
    ElMessage.error('撤销归档失败')
  }
}

const PHASE_COLORS: Record<string, string> = {
  '概念': '#5b8ff9', '设计': '#5ad8a6', '流片': '#5d7092',
  '验证': '#f6bd16', '试产': '#e8684a', '量产导入': '#6dc8ec',
}

const ganttRefs = ref<Record<number, HTMLElement | null>>({})
const ganttInstances: echarts.ECharts[] = []
const crossModulesData = ref<Record<number, any>>({})

function setGanttRef(el: any, id: number) {
  ganttRefs.value[id] = el
}

function hasDatedTasks(row: any): boolean {
  return (row.tasks || []).some((t: any) => t.start_date && t.due_date)
}

function onTabChange(row: any, tabName: string) {
  if (tabName === 'gantt') {
    nextTick(() => {
      const el = ganttRefs.value[row.id]
      if (el) renderGantt(el, row.tasks)
    })
  } else if (tabName === 'cross-modules' && !crossModulesData.value[row.id]) {
    loadCrossModules(row.id)
  }
}

async function loadCrossModules(projectId: number) {
  try {
    const data = await getProjectCrossModules(projectId)
    crossModulesData.value[projectId] = data
  } catch (e: any) {
    ElMessage.error('加载关联对象失败')
  }
}

function renderGantt(el: HTMLElement, tasks: any[]) {
  const valid = (tasks || []).filter(t => t.start_date && t.due_date)
  if (!valid.length) return
  const inst = echarts.init(el)
  ganttInstances.push(inst)
  const taskNames = valid.map(t => t.name)
  inst.setOption({
    tooltip: {
      formatter: (p: any) => {
        const d = valid[p.dataIndex]
        return `<b>${d.name}</b><br/>阶段: ${d.phase}<br/>负责人: ${d.owner}<br/>状态: ${d.status}<br/>${d.start_date} ~ ${d.due_date}`
      },
    },
    grid: { left: 10, right: 20, top: 20, bottom: 40, containLabel: true },
    xAxis: { type: 'time', axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: taskNames, inverse: true, axisLabel: { width: 120, overflow: 'truncate', fontSize: 11 } },
    series: [{
      type: 'custom',
      renderItem: (_params: any, api: any) => {
        const catIdx = api.value(0)
        const startTime = api.value(1)
        const endTime = api.value(2)
        const start = api.coord([startTime, catIdx])
        const end = api.coord([endTime, catIdx])
        const height = api.size([0, 1])[1] * 0.5
        const task = valid[catIdx]
        const color = PHASE_COLORS[task.phase] || '#999'
        const opacity = task.status === '已完成' ? 1 : task.status === '进行中' ? 0.8 : 0.5
        return {
          type: 'rect',
          shape: { x: start[0], y: start[1] - height / 2, width: Math.max(end[0] - start[0], 3), height },
          style: { fill: color, opacity, stroke: '#fff', lineWidth: 1 },
        }
      },
      data: valid.map((t, idx) => ({ value: [idx, new Date(t.start_date).getTime(), new Date(t.due_date).getTime()] })),
    }],
  })
}

function phaseDeliverableTotal(row: any): number {
  return (row.deliverables || []).filter((d: any) => d.phase === row.phase).length
}
function phaseDeliverableDone(row: any): number {
  return (row.deliverables || []).filter((d: any) => d.phase === row.phase && ['已完成', '已关闭'].includes(d.status)).length
}
function phaseTaskTotal(row: any): number {
  return (row.tasks || []).filter((t: any) => t.phase === row.phase).length
}
function phaseTaskDone(row: any): number {
  return (row.tasks || []).filter((t: any) => t.phase === row.phase && t.status === '已完成').length
}
function phaseGateReady(row: any): boolean {
  const pending = (row.deliverables || []).filter((d: any) => d.phase === row.phase && !['已完成', '已关闭'].includes(d.status))
  return pending.length === 0
}

const taskDependsIds = ref<number[]>([])
const taskDependencyOptions = computed(() => {
  const row = (items.value || []).find((r: any) => r.id === taskProjectId.value)
  return (row?.tasks || []).filter((t: any) => t.id !== taskEditingId.value)
})
function onDependsChange() {
  taskForm.value.depends_on = taskDependsIds.value.join(',')
}

onBeforeUnmount(() => {
  ganttInstances.forEach(inst => inst.dispose())
  ganttInstances.length = 0
})

async function load() {
  await loadData()
  const tRes = await getProjectTemplates()
  templates.value = tRes.items ?? tRes
}

function openCreate() {
  editingId.value = null
  form.value = { project_no: '', name: '', product_model: '', phase: '概念', progress: 0, owner: currentUser.value?.display_name || '', start_date: '', end_date: '', risk_level: '低' }
  dialogVisible.value = true
}
function openEdit(row: any) { editingId.value = row.id; form.value = { ...row }; dialogVisible.value = true }
async function save() {
  editingId.value ? await updateProject(editingId.value, form.value) : await createProject(form.value)
  ElMessage.success('项目已保存')
  dialogVisible.value = false
  await load()
}
async function remove(row: any) {
  await ElMessageBox.confirm('确认删除此项目？', '删除确认', { type: 'warning' })
  await deleteProject(row.id)
  ElMessage.success('项目已删除')
  await load()
}

function openCreateTask(project: any) {
  taskProjectId.value = project.id
  taskEditingId.value = null
  taskForm.value = { name: '', phase: project.phase || '概念', owner: currentUser.value?.display_name || '', status: '待处理', due_date: '', start_date: '', depends_on: '' }
  taskDependsIds.value = []
  taskDialog.value = true
}
function openEditTask(project: any, t: any) {
  taskProjectId.value = project.id
  taskEditingId.value = t.id
  taskForm.value = { ...t }
  taskDependsIds.value = (t.depends_on || '').split(',').map((s: string) => parseInt(s.trim())).filter((n: number) => !isNaN(n) && n > 0)
  taskDialog.value = true
}
async function saveTask() {
  taskEditingId.value ? await updateProjectTask(taskEditingId.value, taskForm.value) : await createProjectTask(taskProjectId.value, taskForm.value)
  ElMessage.success('任务已保存')
  taskDialog.value = false
  await load()
}
async function removeTask(t: any) {
  await ElMessageBox.confirm('确认删除此任务？', '删除确认', { type: 'warning' })
  await deleteProjectTask(t.id)
  ElMessage.success('任务已删除')
  await load()
}

async function advancePhase(row: any) {
  await ElMessageBox.confirm(`确认将项目「${row.name}」从「${row.phase}」阶段推进到下一阶段？\n当前阶段交付物必须全部完成。`, '阶段门推进', { type: 'warning' })
  const res = await advanceProjectPhase(row.id, { acted_by: currentUser.value?.display_name || '系统用户', comment: '' })
  ElMessage.success(res.message || '阶段门已推进')
  await load()
}

function openCreateDeliverable(project: any) {
  deliverableProjectId.value = project.id
  deliverableEditingId.value = null
  deliverableForm.value = { name: '', deliverable_type: '', phase: project.phase || '', owner: currentUser.value?.display_name || '', status: '待处理', due_date: '', description: '', object_type: '', object_id: undefined }
  updateLinkableObjects('')
  deliverableDialog.value = true
}
function openEditDeliverable(project: any, d: any) { deliverableProjectId.value = project.id; deliverableEditingId.value = d.id; deliverableForm.value = { ...d, object_id: d.object_id || undefined }; updateLinkableObjects(d.object_type || ''); deliverableDialog.value = true }

function onObjectTypeChange() {
  deliverableForm.value.object_id = undefined
  updateLinkableObjects(deliverableForm.value.object_type || '')
}

function updateLinkableObjects(objectType: string) {
  if (objectType === 'BOM') {
    linkableObjects.value = bomList.value.map((b: any) => ({ id: b.id, label: `${b.bom_type}-${b.product_model}-${b.version}` }))
  } else if (objectType === '文档') {
    linkableObjects.value = documentList.value.map((d: any) => ({ id: d.id, label: `${d.doc_no} · ${d.title}` }))
  } else if (objectType === '工艺路线') {
    linkableObjects.value = routeList.value.map((r: any) => ({ id: r.id, label: `${r.route_no} · ${r.name}` }))
  } else {
    linkableObjects.value = []
  }
}
async function saveDeliverable() {
  deliverableEditingId.value ? await updateProjectDeliverable(deliverableEditingId.value, deliverableForm.value) : await createProjectDeliverable(deliverableProjectId.value, deliverableForm.value)
  ElMessage.success('交付物已保存')
  deliverableDialog.value = false
  await load()
}
async function removeDeliverable(d: any) {
  await ElMessageBox.confirm('确认删除此交付物？', '删除确认', { type: 'warning' })
  await deleteProjectDeliverable(d.id)
  ElMessage.success('交付物已删除')
  await load()
}

function openCreateRisk(project: any) {
  riskProjectId.value = project.id
  riskEditingId.value = null
  riskForm.value = { risk_type: '技术', description: '', impact: '中', probability: '中', severity: '中', owner: currentUser.value?.display_name || '', status: '待处理', mitigation: '' }
  riskDialog.value = true
}
function openEditRisk(project: any, r: any) { riskProjectId.value = project.id; riskEditingId.value = r.id; riskForm.value = { ...r }; riskDialog.value = true }
async function saveRisk() {
  riskEditingId.value ? await updateProjectRisk(riskEditingId.value, riskForm.value) : await createProjectRisk(riskProjectId.value, riskForm.value)
  ElMessage.success('风险已保存')
  riskDialog.value = false
  await load()
}
async function removeRisk(r: any) {
  await ElMessageBox.confirm('确认删除此风险记录？', '删除确认', { type: 'warning' })
  await deleteProjectRisk(r.id)
  ElMessage.success('风险已删除')
  await load()
}

function stagesToText(stages: any): string {
  if (!stages) return ''
  if (Array.isArray(stages)) return stages.join(',')
  try {
    const arr = JSON.parse(stages)
    return Array.isArray(arr) ? arr.join(',') : String(stages)
  } catch {
    return String(stages)
  }
}
function openCreateTemplate() { templateEditingId.value = null; templateForm.value = { code: '', name: '', description: '', stages: '概念,设计,流片,验证,试产', status: '启用' }; templateDialogVisible.value = true }
function openEditTemplate(row: any) { templateEditingId.value = row.id; templateForm.value = { ...row, stages: stagesToText(row.stages) }; templateDialogVisible.value = true }
async function saveTemplate() {
  templateEditingId.value ? await updateProjectTemplate(templateEditingId.value, templateForm.value) : await createProjectTemplate(templateForm.value)
  ElMessage.success('模板已保存')
  templateDialogVisible.value = false
  await load()
}
async function removeTemplate(row: any) {
  await ElMessageBox.confirm('确认删除此模板？', '删除确认', { type: 'warning' })
  await deleteProjectTemplate(row.id)
  ElMessage.success('模板已删除')
  await load()
}

function openFromTemplate() {
  fromTemplateForm.value = { template_id: undefined, project_no: '', name: '', product_model: '', owner: currentUser.value?.display_name || '', start_date: '', end_date: '' }
  fromTemplateDialog.value = true
}
async function saveFromTemplate() {
  if (!fromTemplateForm.value.template_id) {
    ElMessage.warning('请选择模板')
    return
  }
  await createProjectFromTemplate(fromTemplateForm.value)
  ElMessage.success('项目已从模板创建')
  fromTemplateDialog.value = false
  await load()
}

onMounted(async () => {
  const pRes = await getProducts()
  products.value = pRes.items ?? pRes
  const [bomRes, docRes, routeRes] = await Promise.all([
    getBoms({ page: 1, page_size: 1000 }),
    getDocuments({ page: 1, page_size: 1000 }),
    getProcessFlows({ page: 1, page_size: 1000 }),
  ])
  bomList.value = bomRes.items ?? bomRes
  documentList.value = docRes.items ?? docRes
  routeList.value = routeRes.items ?? routeRes
  await load()
})
</script>

<style scoped>
.gantt-chart-container {
  height: 320px;
  width: 100%;
}
.gantt-empty {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 13px;
}
.phase-gate-criteria {
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 10px 14px;
  margin-bottom: 10px;
}
.gate-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.gate-title {
  font-weight: 600;
  font-size: 13px;
}
.gate-body {
  font-size: 12px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.gate-item b {
  color: #303133;
}
.gate-sep {
  color: #c0c4cc;
}
.gate-ok {
  color: #67c23a;
}
.gate-pending {
  color: #e6a23c;
}
</style>
