# SemiPLM 二期：MES 对齐改造规划

> **⚠️ 已作废（2026-07-02）**：本文档已被 `PHASE2_DEV_PLAN_V2.md` 替代。
> 作废原因：用户定调"设备类型+设备能力归 PLM 主控，现有代码/MD 可推翻，严格按 MES Template V1.2 重新开发"。新规划将 PLM 主控表从 12 张扩到 14 张（新增 EquipmentType + EquipmentCapability），改造范围从 6 菜单扩到 11 菜单，代码策略从增量改造改为推翻重做。请参阅 `PHASE2_DEV_PLAN_V2.md`。

---

本文档是二期 MES 对齐改造的总纲。一期深化已完成（BOM 转换血缘、项目跨模块、文档关联、ECO 联动等 6 项），二期目标是让 PLM 产品定义、制造流程、用料表的结构满足 MES 制造建模需求，支持初始化从 MES 反向导入，支持发布后同步给 MES。

## 核心原则

1. **PLM 是源头。** 用户在 PLM 进行产品、工艺、用料的设计、审批、发布。PLM 不依赖 MES 作为运行态数据源。
2. **按 MES 数据结构开发，但不迎合 MES 菜单。** 字段命名和层级对齐 MES 制造建模，保证能同步；但 PLM 菜单按商用 PLM 方法论组织，不复刻 MES 菜单。
3. **先做核心业务。** 产品、工艺、BOM、集成 4 块先做；光刻图、载具、NPW、设备配方等非核心菜单一期不做。
4. **不新增"制造定义包"术语和菜单。** MES 8 模块（Seq/Content/Parameter/Measure/QTime/Contamination/Action/Alter）挂到制造流程详情页的 tab，不单独建菜单、不挂在产品详情页。
5. **制造流程是 PLM 主控源头。** 不是引用库、不是模板库，是 PLM 设计、审批、发布的对象，发布后同步给 MES。

## 改造范围（6 个菜单 + 2 个轻量调整）

### 必须改造的菜单

| PLM 菜单 | 对齐 MES 对象 | 改造内容 |
|---|---|---|
| 产品中心 > 产品库 | ProductDef.basicInfo | Product 表加 MES 对齐字段（product_def_name / mes_product_type / mes_production_type / product_group / gross_die / bank_count / reticle_set / bin_strategy / dummy_strategy / mes_state / mes_mapping_id）；产品详情页增加 MES 字段区，不承载 8 模块 |
| 工艺管理 > 制造流程 | ProcessFlow + Seq + 8 模块中的 6 个 | **三层对齐**：①模型类 ProcessRoute→ProcessFlow 重命名，表 process_routes→process_flows；②字段对齐 MES（process_flow_name/version/description/flow_type1/flow_type2/flow_state/owner_group/flow_group_name/is_deleted + 审计四件套）；③架构独立化——解耦 product_id 外键，流程成为独立主控对象，products 表加 process_flow_name+process_flow_version 引用字段。ProcessStep 加 process_flow_seq_name/type/stage_name/group1/group2。制造流程详情页增加 6 个 tab（制程内容/量测/QTime/防污染/动作/分支），参数挂工艺参数库。代码影响：models.py/schemas.py/routers/processes.py/api/processes.ts/ProcessView.vue/路由菜单配置/现有数据迁移 |
| 工艺管理 > 制程能力库（新增） | ProcessCapability | PLM 主控制程能力目录（processCapabilityName / description / state / owner / 审计），制造流程编排时的能力下拉源；初始化从 MES 反向导入 84 条。设计层对象，无设备绑定 |
| 工艺管理 > 制程配方库（新增） | Recipe | PLM 主控制程配方命名+版本+生命周期登记（processCapabilityName + recipeName / state / owner / effectiveTime / expirAlarmId / 审计），不含物理参数；初始化从 MES 反向导入 324 条。设计层对象，物理参数在 MES EquipmentRecipe 侧 |
| BOM 管理 > 设计 BOM | bom/detail 三段式 | BomItem 加 materialType（Consumable/Durable/Product）/ materialDefName / materialDefVersion / requireQuantity / unit / processStepName / processStepVersion |
| 集成中心 > 同步队列 | MES 同步包 | 新增「MES 同步包」子视图，展示同步包 + 同步项状态；ECN 关闭时自动生成同步包 |

### 轻量调整

| PLM 菜单 | 调整内容 |
|---|---|
| 基础平台 > 数据字典 | MES_* 字典裁剪：保留 11 类枚举，删除报警/批次/设备状态/权限类 |
| 基础平台 > 系统参数 | 加 MES 同步配置项（网关地址/超时/重试/白名单开关） |

### 明确不做的 MES 菜单

| MES 菜单 | 不做原因 |
|---|---|
| 光刻图 ReticleSet / 光源基 | 光刻产品专用，第一阶段非所有产品涉及 |
| 载具 CarrierDef | MES 主控物流载体，PLM 只引用 |
| NPW 模装 / NPW 组织 | NPW=非产品晶圆，MES 自治工程片管理 |
| 设备 / 设备配方 / 设备能力 / 炉管配方 | MES 自治执行层：主键含 equipmentName+chamberFlow，物理设备绑定，必须现场调试锁定 |
| 工厂 / 站点 / 区域 | MES 主控，PLM 引用 |
| 原物料 / 耐用品独立菜单 | 已并入 PLM 物料库，通过 materialType 区分 |

## 8 模块挂载方式

MES 产品详情页的 8 模块在 PLM 中的挂载：

| MES 模块 | PLM 挂载位置 | 说明 |
|---|---|---|
| Seq 流程工序 | 工艺管理 > 制造流程 > 工序 tab（主表） | 制造流程的工序序列，PLM 主控 |
| Content 流程内容 | 工艺管理 > 制造流程 > 制程内容 tab | 制程能力/配方/光罩/抽检规则 |
| Parameter 参数 | 工艺管理 > 工艺参数库（已有菜单） | 工艺参数定义 |
| Measure 量测 | 工艺管理 > 制造流程 > 量测 tab | 量测项/目标/上下限/抽检 |
| QTime | 工艺管理 > 制造流程 > QTime tab | 起止工序/限制分钟/最大 WIP |
| Contamination 防污染 | 工艺管理 > 制造流程 > 防污染 tab | 进出站污染等级 |
| Action 动作 | 工艺管理 > 制造流程 > 动作 tab | 谨慎开放 |
| Alter 分支 | 工艺管理 > 制造流程 > 分支 tab | 谨慎开放 |

产品详情页只展示关联的制造流程版本和用料表版本，不重复承载 8 模块。

## 初始化与同步

### 初始化导入（一次性）

| 数据来源 | 导入到 PLM | 用途 |
|---|---|---|
| MES 3 个 ProductDef | Product 表 | 初始化产品模板 |
| MES 84 个 ProcessCapability | 制程能力库 | PLM 主控，工艺设计语言，Recipe 父级 |
| MES 324 个 Recipe | 制程配方库 | PLM 主控，配方命名+版本+生命周期，不含物理参数 |
| MES 3 个 ProcessFlow + 256 个 ProcessStep | ProcessRoute + ProcessStep | 初始化制造流程模板 |
| MES 2 个 BOM | BomHeader + BomItem | 初始化用料表样例 |
| MES 543 行 Seq/Content/Measure/Contamination | 制造流程详情页各 tab | 初始化 8 模块样例 |
| MES 1728 条字典 | dictionary_items（MES_* 前缀） | 裁剪后保留 11 类枚举 |

初始化后，新产品和新版本在 PLM 自主设计，不再从 MES 拉取。

### 同步给 MES（发布后）

| PLM 对象 | MES 目标 | 触发时机 |
|---|---|---|
| Product 基础信息 | ProductDef.basicInfo | 产品发布 |
| 制程能力 | ProcessCapability | 制程能力发布/生效 |
| 制程配方 | Recipe | 制程配方发布/升版（ECN 换配方版本时 PLM 升版下发，MES 引用新 Recipe 调整 EquipmentRecipe） |
| 制造流程 + 8 模块 | ProcessFlow + Product.detail | 制造流程发布 |
| BOM 用料表 | bom/detail | BOM 发布 |
| ECN 生效 | MES 同步队列 | ECN 关闭 |

同步包记录：目标系统、对象类型、对象编号、动作、状态、请求摘要、响应摘要、MES 对象 id 回写、失败原因、重试次数。第一阶段模拟下发（只记状态），不真实调用 MES 接口。

## 实施顺序

1. **数据模型对齐**：Product 加 MES 字段、ProcessRoute→ProcessFlow 重命名+字段对齐+架构独立化（解耦 product_id，products 表加引用字段）、新建 ProcessCapability 表（制程能力库）、新建 Recipe 表（制程配方库）、BomItem 加三段式、新建 8 模块表（挂制造流程）、新建 MesSyncPackage/MesSyncItem
2. **制程能力库 + 制程配方库页面**：新增两个 PLM 主控菜单，CRUD+版本+状态+审批，初始化从 MES 反向导入
3. **制造流程详情页改造**：加 6 个 tab，承载 Content/Measure/QTime/Contamination/Action/Alter；Content tab 的制程能力/配方下拉源改为 PLM 自有的制程能力库/制程配方库
4. **产品详情页改造**：加 MES 字段区，展示关联制造流程版本（引用关系，不再内嵌）
5. **BOM 改造**：BomItem 三段式 + 工步绑定
6. **集成中心改造**：MES 同步包子视图
7. **ECN 联动**：变更关闭生成同步包（含 Recipe 升版同步、制造流程升版同步）
8. **初始化导入脚本**：从 MES 快照反向导入（含 ProcessCapability 84 条、Recipe 324 条、ProcessFlow 3 条、ProcessStep 256 条）
9. **字典裁剪**：MES_* 字典保留 11 类

## 原因出处

- 原则：`MES_SYNC_STRATEGY.md` 第 5-13 行
- 三层边界：`MES_SYNC_STRATEGY.md` 第 114-132 行
- 同步清单：`MES_SYNC_STRATEGY.md` 第 145-178 行
- 制造流程 PLM 主控：`MES_SYNC_STRATEGY.md` 第 51 行、第 117 行、第 137 行
- 8 模块字段定义：`mes_discovery/mes_product_detail_deep_dive_summary.json`
- BOM 三段式字段：`mes_discovery/mes_bom_deep_dive_summary.json`
- 产品规范：`PRODUCT_SPEC.md` 第二章、第十二章
