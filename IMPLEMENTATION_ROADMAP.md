# SemiPLM 实施路线图

本文档只记录当前基线和下一步计划。产品级规则、接口契约、权限边界、页面交互和完成标准以 `PRODUCT_SPEC.md` 为准；接手代码先读 `FILE_INDEX.md` 定位最小阅读集。

## 项目规则

- 产品级通用规范：先读 `PRODUCT_SPEC.md`，它是新增功能、接口、页面和数据初始化的总约束。
- 代码定位：新增业务功能先查 `FILE_INDEX.md`，只读对应 `routers/{domain}.py`、`frontend/src/api/{domain}.ts`、相关 `views/*.vue`；只有跨域能力才读 `services/` 或 `deps.py`。
- 代码落点：后端业务 API 不写入 `main.py`；前端不恢复 `src/api.ts`，新增 API 写入 `frontend/src/api/{domain}.ts`。
- 部署目标：Linux + Docker Compose；Windows 只作为开发调试环境。生产脚本和文档不得绑定 Windows 盘符或 PowerShell 专属路径。
- 验证节奏：功能开发可以集中验证，最后统一跑后端编译、前端构建、关键接口和页面检查。

## 当前基线

当前系统已经具备一条可演示、可继续深化的 PLM 主链路：

- 基础平台：登录、用户、角色、组织、流程配置、接口端点、编码规则、分类属性、生命周期、数据字典、系统参数。
- 主数据：产品、产品版本、需求规格、物料、替代料、供应商。
- 文档：文档 CRUD、提交/发布、版本历史、PDF/图片预览、发放/回收、通用附件。
- BOM：EBOM/PBOM/MBOM 转换基础、明细维护、有效期、版本约束、比较、反查、导入导出、批量编辑、基线、版本历史。
- 工艺：工艺流程、标准工序、工艺参数、工序物料绑定、提交/发布、MES 队列、版本历史。
- 变更：PR、ECR/ECO/ECN、影响分析、ECA 动作、执行关闭、对象升版、版本归档、生效批次、ERP/MES ECN 队列。
- 项目：项目、模板、任务、交付物、风险、阶段门推进、甘特图、交付物关联对象并在审批发布后自动完成。
- 质量：质量问题、CAPA、质量报告归档、质量问题触发 ECR、Lot/Wafer 追溯引用。
- 工作台/报表：研发驾驶舱、待办、个人聚合、任务日历、通知、闭环验证、4 类报表、Excel 导出、报表快照、操作日志。
- 集成中心：ERP/MES/QMS 队列、汇总、处理、成功/失败回写、重试、对象同步记录。
- 架构：后端已按 `backend/app/routers/` 业务域拆分；前端 API 已按 `frontend/src/api/` 业务域拆分。

## 完成与列表标准

- 功能完成标准以 `PRODUCT_SPEC.md` 的“完成标准”为准。
- 列表 API、分页、搜索、排序、批量操作以 `PRODUCT_SPEC.md` 的“接口与列表契约”和“搜索、筛选与排序”为准。
- 具体代码落点和通用组合函数参考 `FILE_INDEX.md`。

## 下一步计划

一期深化已完成，以下 6 项全部交付：

1. BOM MBOM/PBOM 转换深化  
   补齐转换后的差异对比、工序物料分配完整性、转换结果可追溯。

2. 项目跨模块关联展示  
   项目详情聚合展示关联 BOM、文档、变更、质量问题、工艺流程。

3. 交付物与 BOM/文档联动深化  
   交付物绑定具体 BOM 版本或文档版本；阶段门/结项校验交付物齐套。

4. 项目归档  
   项目结案后归档关联 BOM、文档、流程记录和质量报告，形成项目数据包。

5. 文档与对象关联展示  
   文档详情集中展示关联产品、BOM、工艺、项目、变更。

6. ECO 发布联动文档  
   ECO 审批通过后关联文档自动升版，并按发放规则触发发放记录。

原计划的「BOM 打印/采购清单拆分」已移除：采购清单拆分归属 ERP 职责，PLM 仅负责 BOM 结构与发布，发布后通过集成队列推送 ERP 由其执行 MRP 与采购拆分。BOM Excel 导出能力已满足研发阶段的人工筛选需求。

## 二期：MES 对齐改造（V2 推翻重做版）

> ⚠️ 二期规划已升级为 V2，详见 `PHASE2_DEV_PLAN_V2.md`。旧 `PHASE2_MES_ALIGNMENT_PLAN.md` 已标注作废。
> V2 核心变化：设备类型+设备能力归 PLM 主控（PLM 主控表从 12 张扩到 14 张），改造范围从 6 菜单扩到 11 菜单，代码策略从增量改造改为推翻重做。

一期深化已完成，二期目标是让 PLM 产品、工艺、BOM、集成的结构对齐 MES Template V1.2 制造建模（21 张表 277 字段），支持初始化从 MES 反向导入，支持发布后同步给 MES。

核心原则：PLM 是源头，严格按 MES Template V1.2 表结构开发，现有代码/MD 可推翻重做。

### 改造范围（11 菜单 + 2 轻量调整）

1. 产品中心 > 产品库：ProductDef 26 字段推翻重做，加 processFlowName+Version 引用字段（架构独立化解耦 product_id）
2. 工艺管理 > 工艺流程：ProcessFlow 10 字段，详情页 5 tab（工序/制程内容/量测/防污染，分支返工并入 Content tab）
3. 工艺管理 > 标准工序（新）：ProcessStep 21 字段，独立菜单被 Seq 引用
4. 工艺管理 > 工艺阶段（新）：ProcessStage 7 字段
5. 工艺管理 > 工艺能力（新）：ProcessCapability 3 字段
6. 工艺管理 > 工艺配方（新）：Recipe 7 字段，不含物理参数
7. 工艺管理 > 设备类型（新）：EquipmentType 12 字段
8. 工艺管理 > 设备能力（新）：EquipmentCapability 4 字段，equipmentName→equipment_type_name 改造
9. BOM 管理 > 设计 BOM：Bom 5 字段 + BomItem 10 字段三段式 + 工步绑定，解耦 product_id
10. 物料库：ConsumableDef 前 11 字段技术规格 PLM 主控
11. 集成中心 > 同步队列：MesSyncPackage/MesSyncItem，ECN 关闭生成同步包
12. 基础平台：MES_* 字典裁剪保留 14 类枚举 + 系统参数加 MES 同步配置

### 实施顺序（9 个里程碑）

| # | 里程碑 | 内容 | 状态 |
|---|---|---|---|
| M1 | 数据模型重建 | 推翻 Product/Material/BomHeader/BomItem/ProcessRoute/ProcessStep 6 个旧类，新建 14 张 PLM 主控表 + MesSyncPackage/MesSyncItem。schemas.py 同步重写 | ✅ 完成 |
| M2 | 工艺流程主菜单+5tab | routers/processes.py 重写 ProcessFlow CRUD + 5 tab（Seq/Content/Measure/Contamination）CRUD。Content tab 含分支/返工字段。ProcessView.vue 4 tab 详情页 | ✅ 完成 |
| M3 | 6个工艺主数据菜单 | routers/process_lib.py + 6 个 View：标准工序/工艺阶段/工艺能力/工艺配方/设备类型/设备能力 全部 CRUD | ✅ 完成 |
| M4 | 产品库改造 | routers/products.py 重写（ProductDef 26 字段过滤+引用对象查询）。ProductsView.vue 重写（26 字段表单+引用下拉）。ProductDetailView.vue 重写（引用关系双卡+规格KV+统计tile，不再内嵌8模块） | ✅ 完成 |
| M5 | BOM三段式+物料库对齐 | BomView/MaterialsView 改造。routers/boms.py/materials.py 适配 MES Bom/BomItem 与 ConsumableDef 前 11 字段；保留比较、反查、工序覆盖率、导入导出和批量编辑 | ✅ 完成 |
| M6 | 集成中心+MES同步包 | MesSyncPackage/MesSyncItem 落地。受控引用视图（EquipmentRecipe/Param 只读）。IntegrationsView 扩展 | ⏳ 待做 |
| M7 | ECN联动 | ECN 关闭识别受影响对象+自动升版+生成同步包 | ⏳ 待做 |
| M8 | 初始化导入脚本 | build_db.py 重写，主数据从 mes_discovery/mes_full_model_seed.json、mes_product_detail_deep_dive.json、mes_bom_deep_dive.json、mes_dictionary_seed.json 反向导入；PLM 仅补文档/项目/质量/待办/集成演示数据 | ✅ 完成 |
| M9 | 字典裁剪+系统参数 | MES_* 字典保留 14 类枚举。系统参数加 MES 同步配置 | ⏳ 待做 |

### M1-M4 已落地的代码变更

**后端**：
- `backend/app/models.py`：推翻 6 个旧类，新建 ProcessFlow/ProcessFlowSeq/ProcessFlowContent/ProcessFlowMeasure/ProcessFlowContamination/ProcessStage/ProcessStep(独立)/ProcessCapability/Recipe/EquipmentType/EquipmentCapability/MesSyncPackage/MesSyncItem + Product/Material/BomHeader/BomItem 重写
- `backend/app/schemas.py`：14 张表 + Product/Material/Bom 的 Payload/UpdatePayload 全部新建
- `backend/app/routers/processes.py`：重写为工艺流程+5tab+问题报告+工艺参数
- `backend/app/routers/process_lib.py`：新建，6 个工艺库独立菜单 API
- `backend/app/main.py`：注册 process_lib router
- `backend/app/services/versioning.py`：ProcessRoute→ProcessFlow，BomHeader 字段对齐
- `backend/app/services/process.py`：重写用 ProcessFlow
- `backend/app/services/bootstrap.py`：清理旧表补列
- `backend/app/serializers.py`：全部对齐新字段

**验证**：app import OK / startup OK（60 张表 create_all）/ 8 个新端点烟雾测试全部 201

**M2/M3 前端已完成**：ProcessView.vue 重写（4 tab 详情页）+ 6 个新 View + api/processes.ts 重写 + api/process_lib.ts 新建

**M4 已落地的代码变更**：

后端：
- `backend/app/routers/products.py`：重写，过滤字段对齐 ProductDef（product_def_name/description/product_type/product_group_name/owner），新增 state+product_type 过滤；详情接口删除 selectinload(process_routes)，改为字符串引用查询 referenced_flow/referenced_bom，返回业务关联统计 + projects
- `backend/app/services/bootstrap.py`：ensure_admin 扩展，自动补 5 个默认角色种子（ADMIN/PE_ENGINEER/PM_MANAGER/IT_ENGINEER/QE_ENGINEER），修复空库启动 admin permissions=[] 导致菜单隐藏
- `backend/app/routers/dashboard.py`：bom_ready 过滤 BomHeader.status→BomHeader.bom_state=="Released"，修复仪表盘 500

前端：
- `frontend/src/views/ProductsView.vue`：重写，列表+表单对齐 ProductDef 26 字段，引用对象双下拉（ProcessFlow+Bom），state+type 双过滤
- `frontend/src/views/ProductDetailView.vue`：重写，推翻原"内嵌 8 模块 tab"设计，改为引用关系双卡+规格 KV+统计 tile+项目表+版本历史

**M4 架构要点**：详情页不再内嵌所有业务模块，遵循"PLM 是源头，各业务对象在自己菜单维护"原则；产品通过字符串字段引用 ProcessFlow/Bom，不外键绑定

## 生产模拟数据与数据字典改造（3 轮）

### 问题

1. seed.py 数据量不足，无法覆盖 UI 各分支：无 PBOM/MBOM、无已归档项目、无 ECA 已完成变更、工作台待办为空。
2. seed.py 幂等性有 bug：已有数据则跳过大部分 seed，不删库则新 seed 不生效。
3. 前端硬编码枚举：项目阶段/风险等级/交付物状态/变更类型/严重度/优先级等前后端各写一份。
4. 数据字典不完整：缺变更类型/严重度/项目阶段/优先级/交付物类型/风险类型等。

### 第一轮：数据制品构建 + 生产模拟数据（最高优先级）

**操作步骤：**
1. 停后端（避免 Windows 文件锁占用 .db）
2. 执行 `python -m app.build_db --all` 生成两个数据制品
3. 重启后端，默认连接 `backend/semiplm_demo.db`（开发态）
4. 验证各页面数据填充效果

**数据制品说明：**

| 文件 | 内容 | 用途 |
| --- | --- | --- |
| `backend/semiplm_clean.db` | 建表 + admin + 角色/数据字典/系统参数等主数据 | 生产部署起点 |
| `backend/semiplm_demo.db` | clean + MES 爬虫主数据（3 产品、2 工艺流程、323 流程明细、256 标准工序、84 工艺能力、324 配方、30+ 设备类型、97 设备能力、2 BOM、1746 字典项）+ PLM 协同演示数据（文档/变更/质量/项目/待办/集成队列） | 开发演示、页面验收 |

`backend/app/build_db.py` 是 CLI 构建入口，**不在启动时执行**。启动流程（`backend/app/main.py`）只跑 `create_all + ensure_lightweight_schema + ensure_admin`，不灌任何业务/主数据。

#### 用户（7 个真实用户，删掉虚拟用户）
| username | display_name | role | department |
| --- | --- | --- | --- |
| admin | 系统管理员 | 管理员 | 生产部 |
| luofusen | 罗富森 | 工艺工程师 | 生产部 |
| yushuaibing | 于帅兵 | 工艺工程师 | 生产部 |
| zhanghao | 张昊 | 工艺工程师 | 生产部 |
| fanglei | 房磊 | 项目经理 | 生产部 |
| liangweiwei | 梁维维 | IT工程师 | 生产部 |
| lichao | 李超 | 质量工程师 | 生产部 |

#### 产品（5 个，保留现有型号）
PD-1550-10G / VCSEL-940-3W / DFB-1310-25G / LED-MICRO-RGB / SiPh-MZM-400G

#### 每个产品的数据配套
| 对象 | 数量 | 说明 |
| --- | --- | --- |
| EBOM | 1 | 已发布或审批中 |
| PBOM | 1 | 由 EBOM 转换，部分已分配工序部分未分配（验证工序校验） |
| MBOM | 1 | 由 PBOM 转换（验证转换血缘 3 层链路） |
| 文档 | 8 | 规格/工艺/测试/可靠性/Mask/控制计划/作业指导/承认书，状态分布 |
| 工艺流程 | 1 | 含 10 工序 |
| 变更 | 3-4 | 覆盖审批中/执行中/已关闭，其中 1 个含已完成的文档 ECA（验证 ECO 联动） |
| 质量问题 | 2-3 | 覆盖高/中/低严重度，处理中/CAPA执行中/已关闭 |
| 质量报告 | 1-2 | 已归档 |
| 需求规格 | 3 | 客户规格/NPI阶段门/质量体系 |
| 产品基线 | 1 | 含 5 个基线项 |
| 质量批次 | 4 | 覆盖正常/异常跟进 |

#### 项目（5 个，每个都有完整子对象）
| 项目编号 | 产品 | 阶段 | 归档 | 说明 |
| --- | --- | --- | --- | --- |
| NPI-2026-061 | PD-1550-10G | 试产 | 否 | 主验证项目，交付物部分完成 |
| NPI-2026-062 | VCSEL-940-3W | 量产导入 | 是 | 已归档，验证归档数据包 |
| NPI-2026-063 | DFB-1310-25G | 验证 | 否 | 交付物齐套，可推进阶段门 |
| NPI-2026-064 | LED-MICRO-RGB | 设计 | 否 | 早期阶段，交付物少 |
| NPI-2026-065 | SiPh-MZM-400G | 流片 | 否 | 高风险项目 |

每个项目配套：
- 任务 5-6 个（覆盖已完成/进行中/未开始，含日期用于甘特图和日历）
- 交付物 3-4 个（覆盖待处理/进行中/已完成，部分绑定 BOM/文档对象）
- 风险 1-2 个（覆盖技术/工艺/质量风险）

#### 流程待办（5-8 条，现在工作台是空的）
构造真实的 workflow_instance + workflow_task：
- 2 条文档审批待办（分配给质量工程师/文控）
- 2 条 BOM 发布待办（分配给工艺工程师）
- 2 条变更审批待办（分配给项目经理）
- 1-2 条已完成的流程（历史记录）

#### 集成队列（每个变更 3 条）
- ERP ECN 同步任务
- MES ECN 同步任务
- QMS 文档同步任务
- 状态分布：等待/成功/失败

#### 数据字典补全
| dict_code | 名称 | 项 |
| --- | --- | --- |
| DICT_CHANGE_TYPE | 变更类型 | 光刻/刻蚀/镀膜/测试/封装/可靠性/物料/文档 |
| DICT_SEVERITY | 严重度 | 高/中/低 |
| DICT_PROJECT_PHASE | 项目阶段 | 概念/设计/流片/验证/试产/量产导入 |
| DICT_PRIORITY | 优先级 | 高/中/低 |
| DICT_DELIVERABLE_TYPE | 交付物类型 | 设计文件/工艺文件/测试报告/可靠性报告/规格书 |
| DICT_RISK_TYPE | 风险类型 | 技术风险/工艺风险/质量风险/进度风险 |
| DICT_ISSUE_STATUS | 问题状态 | 新建/评估中/处理中/CAPA执行中/已关闭 |
| DICT_ACTION_TYPE | 操作动作 | 新增/编辑/提交/发布/驳回/关闭/删除 |
| DICT_TASK_STATUS | 任务状态 | 待处理/进行中/已完成/已关闭 |
| DICT_DELIVERABLE_STATUS | 交付物状态 | 待处理/进行中/已完成/已关闭 |

#### 验证清单
- [ ] 工作台 8 个统计卡片都有数字
- [ ] 流程待办有 5+ 条
- [ ] BOM 管理能看到 EBOM/PBOM/MBOM 三层
- [ ] BOM 转换血缘能看到向上溯源+向下派生
- [ ] BOM 工序校验能看到已分配/未分配
- [ ] 项目管理 5 个项目，1 个已归档
- [ ] 项目展开有任务/交付物/风险/关联对象
- [ ] 项目归档数据包 8 个 tab 都有数据
- [ ] 交付物齐套校验有未齐套项
- [ ] 文档中心 40 个文档，各种状态
- [ ] 文档关联对象 5 个 tab 都有数据
- [ ] 工程变更 15-20 个，各种状态
- [ ] 质量管理 10+ 个问题，各种严重度
- [ ] 集成中心有 ERP/MES/QMS 队列
- [ ] 报表有数据可导出
- [ ] 日历有任务可显示

### 第二轮：数据字典驱动前端（已完成）

**目标：** 前端不再硬编码枚举，所有下拉选项从数据字典 API 读取。

**已改造范围：**
- `ProjectsView.vue` - 阶段/风险等级/交付物状态/任务状态/风险类型
- `BomView.vue` - BOM 类型/状态/生效方式/转换目标类型
- `DocumentsView.vue` - 文档分类/文件状态/签核状态/接收类型
- `ChangesView.vue` - 变更类型/状态/优先级/影响对象/ECA 动作/目标对象/生效方式/ECA 状态
- `QualityView.vue` - 严重度/问题状态/CAPA 状态/质量报告状态
- `WorkbenchView.vue` - 通知动作类型
- `ProductsView.vue` - 生命周期/工艺平台/晶圆尺寸/封装形式
- `MaterialsView.vue` - 物料类别/风险等级/生命周期
- `SubstituteMaterialsView.vue` - 替代类型/替代策略/风险等级/状态
- `IntegrationsView.vue` - 集成系统/集成状态
- `AuditLogView.vue` - 操作动作
- `PRProblemView.vue` - 问题类型/严重度/来源/状态
- `SuppliersView.vue` - 供应商类型/风险等级/状态

**实现方式：**
- `composables/useDictionary.ts` 封装字典 API 调用与 module 级缓存
- 各 view 在 setup 时按需 `useDictionary('DICT_XXX')` 获取选项
- 标签颜色映射改为 computed 映射表

**剩余硬编码：** 基础配置/管理类页面（用户组织/编码规则/流程配置/工艺参数类型/系统参数分类）以及少量技术枚举，按实际验收情况逐步清理。

### 第三轮：UI 布局验收（当前重点）

**目标：** 项目已从「从零开发」进入「验收、固化、清债」阶段，先启动前后端，用页面逐项验收数据与字典改造效果，再修复真实可用性问题，而非继续加新功能。

**验收清单：**
1. 数据库构建：`python -m app.build_db --all` 稳定生成 `semiplm_clean.db` + `semiplm_demo.db`
2. 启动后端 + 前端，确认默认连接 `semiplm_demo.db`
3. 按第一轮验证清单逐项过页面（工作台/BOM/项目/文档/变更/质量/集成/报表）
4. 重点检查：表格密度、卡片高度、操作列溢出、弹窗表单对齐、横向滚动、排序真实生效

**已知问题：**
1. 工作台 dashboard 卡片高度不齐 → CSS Grid 严格定行高
2. 表格在卡片内塌陷 → `flex: 1 + min-height: 0` 防塌陷
3. 弹窗表单对齐 → 已修复 .form-grid 全控件 width:100%
4. 操作列按钮过多溢出 → 已精简 DocumentsView 操作列，核心平铺 + 更多下拉

**待检查页面：**
- DashboardView（研发驾驶舱）
- ReportsView（报表）
- 各基础配置页（编码规则/分类属性/生命周期/数据字典/系统参数）
- 用户/角色/组织管理页

## 暂缓范围

- 真实 ERP/MES/QMS 字段级映射、接口日志平台和下游回调，等实际对接时再做。
- CAD/EDA 文件深集成、Office/CAD 在线预览、Autovue/eDrawings 类能力。
- 多组织、多租户、多法人、多站点隔离。
- 移动端、数据大屏、个性化看板。
- 高并发、复杂事务、分布式部署、性能分片等工程治理。
