# SemiPLM 代码阅读索引

本文档是接手开发时的第一入口。目标是让后续人员按业务功能精确定位要读的文件，不需要通读全仓。

## 阅读规则

1. 先在「业务功能 -> 文件速查表」找到任务所属业务域。
2. 优先只读该行列出的后端 router、前端 api、前端 view。
3. 只有涉及流程、升版、集成、权限、审计等跨域能力时，才继续读「跨域共享逻辑」中的 service/deps 文件。
4. 不要为了新增接口去读或修改 `backend/app/main.py`，它只负责应用装配。
5. 不要恢复 `frontend/src/api.ts`。新增前端 API 必须写入 `frontend/src/api/{domain}.ts`，并通过 `frontend/src/api/index.ts` 导出。

## 任务类型

| 任务类型 | 必读文件 | 何时额外阅读 |
| --- | --- | --- |
| 新增/修改业务列表页 | 对应 `backend/app/routers/{domain}.py`、`frontend/src/api/{domain}.ts`、`frontend/src/views/{Page}.vue` | 分页标准读 `frontend/src/composables/useListPage.ts` |
| 新增业务字段 | 对应 router、view、`backend/app/schemas.py`、`backend/app/models.py` | 需要示例数据时读 `backend/app/seed.py` |
| 新增业务动作按钮 | 对应 router、api、view | 需要权限控制时读 `backend/app/deps.py` 和角色管理页面 |
| 新增流程提交/审批 | 对应业务 router + `backend/app/services/workflow.py` | 审批完成后发布对象时，再读对象 router |
| 新增变更升版逻辑 | `backend/app/routers/changes.py`、`backend/app/services/change.py`、`backend/app/services/versioning.py` | 影响 BOM/文档/工艺时，再读对应 router |
| 新增 ERP/MES/QMS 同步 | 业务 router + `backend/app/services/integration.py` + `backend/app/routers/integration.py` | 前端队列监控读 `frontend/src/views/IntegrationsView.vue` |
| 新增附件能力 | `backend/app/routers/documents.py`、`frontend/src/api/documents.ts`、`frontend/src/components/AttachmentPanel.vue` | 对象权限不同读 `backend/app/deps.py` |
| 新增报表/导出 | `backend/app/routers/reports.py`、`frontend/src/api/reports.ts`、`frontend/src/views/ReportsView.vue` | Excel 样式参考同文件已有导出函数 |

## 当前结构

### 后端

| 文件/目录 | 职责 |
| --- | --- |
| `backend/app/main.py` | FastAPI app、CORS、startup、health、include_router。禁止放业务逻辑 |
| `backend/app/routers/` | 按业务域拆分的 API 路由 |
| `backend/app/schemas.py` | Pydantic 请求 payload |
| `backend/app/serializers.py` | 对象序列化函数 |
| `backend/app/models.py` | SQLAlchemy 数据模型 |
| `backend/app/deps.py` | 当前用户上下文、权限标签、权限校验 |
| `backend/app/services/` | 跨域业务逻辑 |
| `backend/app/seed.py` | 初始数据和业务样例数据 |

### 前端

| 文件/目录 | 职责 |
| --- | --- |
| `frontend/src/api/index.ts` | API 统一出口，re-export 各业务域 API |
| `frontend/src/api/request.ts` | axios client、API base、当前用户 header |
| `frontend/src/api/download.ts` | Blob 下载工具 |
| `frontend/src/api/{domain}.ts` | 各业务域前端 API |
| `frontend/src/views/` | 业务页面 |
| `frontend/src/components/AttachmentPanel.vue` | 通用附件面板 |
| `frontend/src/components/UserSelect.vue` | 用户主数据下拉 |
| `frontend/src/composables/useListPage.ts` | 列表页分页/搜索通用逻辑 |
| `frontend/src/auth.ts` | 登录态、权限判断 |
| `frontend/src/router.ts` | 页面路由 |

## 业务功能 -> 文件速查表

### 工作台

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 研发驾驶舱 | `routers/dashboard.py` | `api/dashboard.ts` | `views/DashboardView.vue` |
| 我的待办 | `routers/workflow.py` | `api/workflow.ts` | `views/WorkbenchView.vue` |
| 工作台聚合 | `routers/workbench.py` | `api/workbench.ts` | `views/WorkbenchView.vue` |
| 任务日历 | `routers/workbench.py` | `api/workbench.ts` | `views/WorkbenchView.vue` |
| 消息通知 | `routers/workbench.py` | `api/workbench.ts` | `views/WorkbenchView.vue` |
| 闭环验证 | `routers/workbench.py` | `api/workbench.ts` | `views/ClosureCheckView.vue` |

### 基础平台

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 登录/会话 | `routers/session.py` | `api/session.ts` | `views/LoginView.vue` |
| 组织管理 | `routers/admin.py` | `api/admin.ts` | `views/OrganizationManagementView.vue` |
| 用户管理 | `routers/admin.py` | `api/admin.ts` | `views/UserManagementView.vue` |
| 角色管理 | `routers/admin.py` | `api/admin.ts` | `views/RoleManagementView.vue` |
| 流程配置 | `routers/admin.py` | `api/admin.ts` | `views/WorkflowConfigView.vue` |
| 接口端点配置 | `routers/admin.py` | `api/admin.ts` | `views/IntegrationConfigView.vue` |
| 编码规则 | `routers/foundation.py` | `api/foundation.ts` | `views/CodingRulesView.vue` |
| 分类属性 | `routers/foundation.py` | `api/foundation.ts` | `views/CategoryTemplatesView.vue` |
| 生命周期 | `routers/foundation.py` | `api/foundation.ts` | `views/LifecycleTemplatesView.vue` |
| 数据字典 | `routers/foundation.py` | `api/foundation.ts` | `views/DictionaryView.vue` |
| 系统参数 | `routers/foundation.py` | `api/foundation.ts` | `views/SystemParametersView.vue` |

### 产品中心

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 产品库 | `routers/products.py` | `api/products.ts` | `views/ProductsView.vue` |
| 产品详情聚合 | `routers/products.py` | `api/products.ts` | `views/ProductDetailView.vue` |
| 产品版本 | `routers/products.py` | `api/products.ts` | `views/ProductsView.vue` |
| 需求规格 | `routers/requirements.py` | `api/requirements.ts` | `views/RequirementsView.vue` |
| 需求追溯 | `routers/requirements.py` | `api/requirements.ts` | `views/RequirementsView.vue` |
| 物料库 | `routers/materials.py` | `api/materials.ts` | `views/MaterialsView.vue` |
| 替代料管理 | `routers/materials.py` | `api/materials.ts` | `views/SubstituteMaterialsView.vue` |
| 供应商/制造商 | `routers/materials.py` | `api/materials.ts` | `views/SuppliersView.vue` |

### 文档中心

| 功能 | 后端 router | 前端 api | 前端页面/组件 |
| --- | --- | --- | --- |
| 文档库 CRUD | `routers/documents.py` | `api/documents.ts` | `views/DocumentsView.vue` |
| 文档提交/发布 | `routers/documents.py` | `api/documents.ts` | `views/DocumentsView.vue` |
| 文档版本历史 | `routers/documents.py` | `api/documents.ts` | `views/DocumentsView.vue` |
| 文档发放/回收 | `routers/documents.py` | `api/documents.ts` | `views/DocumentsView.vue` |
| ECO 发布联动文档 | `routers/changes.py` + `services/change.py` + `routers/documents.py` | `api/changes.ts` + `api/documents.ts` | `views/ChangesView.vue` + `views/DocumentsView.vue` |
| 文档预览 | `routers/documents.py` | `api/documents.ts` | `views/DocumentsView.vue` |
| 文档关联对象 | `routers/documents.py` | `api/documents.ts` | `views/DocumentsView.vue` |
| 通用附件 | `routers/documents.py` | `api/documents.ts` | `components/AttachmentPanel.vue` |

### BOM 管理

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| BOM 表头/明细 CRUD | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| EBOM -> PBOM/MBOM 转换 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 转换血缘 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 工序分配校验 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 比较 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 反查 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 导入导出 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 批量编辑 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 版本历史 | `routers/boms.py` | `api/boms.ts` | `views/BomView.vue` |
| BOM 基线 | `routers/boms.py` | `api/boms.ts` | `views/BaselinesView.vue` |

### 工艺管理

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 工艺路线/工序 | `routers/processes.py` | `api/processes.ts` | `views/ProcessView.vue` |
| 工艺发布 | `routers/processes.py` | `api/processes.ts` | `views/ProcessView.vue` |
| 工艺版本历史 | `routers/processes.py` | `api/processes.ts` | `views/ProcessView.vue` |
| 工艺参数库 | `routers/processes.py` | `api/processes.ts` | `views/ProcessParametersView.vue` |
| PR 问题报告 | `routers/processes.py` | `api/processes.ts` | `views/PRProblemView.vue` |

### 工程变更

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| ECR/ECO/ECN | `routers/changes.py` | `api/changes.ts` | `views/ChangesView.vue` |
| 影响分析 | `routers/changes.py` + `services/change.py` | `api/changes.ts` | `views/ChangesView.vue` |
| ECA 执行动作 | `routers/changes.py` + `services/change.py` | `api/changes.ts` | `views/ChangesView.vue` |
| 版本归档 | `routers/changes.py` + `services/change.py` | `api/changes.ts` | `views/ChangesView.vue` |
| 生效批次总览 | `routers/changes.py` | `api/changes.ts` | `views/ChangesView.vue` |

### 项目管理

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 项目库 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 项目模板 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 从模板创建项目 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 项目任务 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 阶段门推进 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 交付物 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 交付物齐套校验 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 项目归档 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 项目归档数据包 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 风险 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 甘特图 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |
| 项目跨模块关联 | `routers/projects.py` | `api/projects.ts` | `views/ProjectsView.vue` |

### 质量闭环

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 质量问题 | `routers/quality.py` | `api/quality.ts` | `views/QualityView.vue` |
| CAPA | `routers/quality.py` | `api/quality.ts` | `views/QualityView.vue` |
| 质量报告归档 | `routers/quality.py` | `api/quality.ts` | `views/QualityView.vue` |
| 质量问题触发 ECR | `routers/quality.py` + `routers/changes.py` | `api/quality.ts` | `views/QualityView.vue` |
| Lot/Wafer 追溯 | `routers/quality.py` | `api/quality.ts` | `views/QualityView.vue` |

### 集成中心

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 同步队列 | `routers/integration.py` | `api/integration.ts` | `views/IntegrationsView.vue` |
| 队列汇总 | `routers/integration.py` | `api/integration.ts` | `views/IntegrationsView.vue` |
| 开始/成功/失败/重试 | `routers/integration.py` | `api/integration.ts` | `views/IntegrationsView.vue` |
| 接口端点配置 | `routers/admin.py` | `api/admin.ts` | `views/IntegrationConfigView.vue` |

### 报表与审计

| 功能 | 后端 router | 前端 api | 前端页面 |
| --- | --- | --- | --- |
| 数据完整度报表 | `routers/reports.py` | `api/reports.ts` | `views/ReportsView.vue` |
| 变更周期报表 | `routers/reports.py` | `api/reports.ts` | `views/ReportsView.vue` |
| 项目进度报表 | `routers/reports.py` | `api/reports.ts` | `views/ReportsView.vue` |
| 质量闭环报表 | `routers/reports.py` | `api/reports.ts` | `views/ReportsView.vue` |
| 报表 Excel 导出 | `routers/reports.py` | `api/reports.ts` | `views/ReportsView.vue` |
| 报表快照 | `routers/reports.py` | `api/reports.ts` | `views/ReportsView.vue` |
| 操作日志 | `routers/audit.py` | `api/audit.ts` | `views/AuditLogView.vue` |

## 跨域共享逻辑

| 能力 | 文件 | 说明 |
| --- | --- | --- |
| 请求数据库会话 | `database.py` | `get_db`、engine、Base |
| 用户上下文/权限 | `deps.py` | `current_user_context`、`require_permission`、权限标签 |
| 请求 payload | `schemas.py` | 所有新增/编辑 payload |
| 序列化 | `serializers.py` | 多个 router 复用的对象返回结构 |
| 通用提交/审计/日期/对象存在校验 | `services/helpers.py` | `commit_or_409`、`audit_log`、`update_model`、`today_text` 等 |
| 流程引擎 | `services/workflow.py` | 提交、审批完成、撤回、项目交付物自动完成 |
| 工程变更影响分析/升版 | `services/change.py` | 影响分析、ECA 关闭、生成新版本对象 |
| 版本号生成 | `services/versioning.py` | BOM/文档/工艺下一版号、有效 BOM 判断 |
| 集成队列创建 | `services/integration.py` | ERP/MES/QMS 队列事件 |
| 工艺与 BOM 绑定校验 | `services/process.py` | 工艺路线可编辑校验、工序绑定校验 |
| 轻量迁移/启动修正 | `services/bootstrap.py` | startup 时 schema 补齐和主数据规范化 |

## 维护规则

- 新增业务 API：写入对应 `backend/app/routers/{domain}.py`。
- 新增前端 API：写入对应 `frontend/src/api/{domain}.ts`，并确认 `index.ts` 已导出该模块。
- 新增页面：写入 `frontend/src/views/`，并在 `router.ts` 和菜单中接入。
- 新增跨域 helper：优先放入 `services/`，不要让 router 相互 import。
- 新增数据模型字段：同步更新 `models.py`、`schemas.py`、相关 serializer、router、api、view。
- 修改本文档：新增菜单、页面、router、api 或共享 service 时，同步更新对应表格。

## UI/列表页通用约定

- 产品级 UI、列表、表单、权限、文件和完成标准以 `PRODUCT_SPEC.md` 为准。
- 分页/搜索/排序通用逻辑优先复用 `frontend/src/composables/useListPage.ts`。
- 状态、类型、优先级、严重度、风险等级等选项优先复用 `frontend/src/composables/useDictionary.ts`。
- Element Plus 与 Arco 处于并存期；新增或改版页面优先遵守产品行为和业务密度，再考虑组件迁移。
- 全局表格、操作列、表单网格等 CSS 约束集中在 `frontend/src/styles.css`，避免每个页面重复写一份。
