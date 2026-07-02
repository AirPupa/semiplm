# SemiPLM 功能范围清单

本文档记录产品能力范围和当前缺口，不记录历史完成流水。具体代码文件见 `FILE_INDEX.md`，菜单边界见 `MENU_ARCHITECTURE.md`。

## 已落地的主链路能力

- 工作台：研发驾驶舱、我的待办、个人业务聚合、任务日历、消息通知、闭环验证。
- 产品中心：产品库、产品版本、产品详情聚合、需求规格、需求追溯、物料、替代料、供应商。
- 文档管理：文档 CRUD、版本、提交发布、PDF/图片预览、发放回收、附件。
- BOM 管理：EBOM/PBOM/MBOM 基础转换、明细维护、有效性、比较、反查、导入导出、批量编辑、基线、版本历史。
- 工艺管理：制造流程、工序、工艺参数、工序物料绑定、提交发布、MES 队列、版本历史。
- 工程变更：PR、ECR/ECO/ECN、影响分析、ECA、对象升版、版本归档、生效批次、ERP/MES ECN 队列。
- 项目管理：项目、模板、任务、交付物、风险、阶段门、甘特图、交付物关联对象。
- 质量闭环：质量问题、CAPA、质量报告、Lot/Wafer 追溯引用、质量问题触发 ECR。
- 集成中心：ERP/MES/QMS 队列、状态回写、失败重试、对象同步记录。
- 报表与审计：数据完整度、变更周期、项目进度、质量闭环、Excel 导出、报表快照、操作日志。
- 基础平台：组织、用户、角色、权限、流程配置、编码规则、分类属性、生命周期、数据字典、系统参数、接口端点。

## 一期继续深化

### BOM

- MBOM/PBOM 转换结果差异对比。
- 工序物料分配完整性校验。
- 转换血缘向上溯源与向下派生追溯。

### 文档

- 文档详情展示关联产品、BOM、工艺、项目、变更。
- ECO 审批通过后关联文档自动升版并触发发放。
- 文档模板管理。

### 项目

- 项目详情聚合关联 BOM、文档、变更、工艺、质量问题。
- 交付物绑定具体 BOM 版本或文档版本。
- 项目结案归档关联 BOM、文档、流程记录和质量报告。

### 工艺

- 工装辅料。
- 工序检验标准。

### 集成

- 真实 ERP/MES/QMS 对接前，只维护轻量队列和状态。
- 真实对接时再补对象映射、字段映射、接口日志、下游回调。

## 二期：MES 对齐改造（V2 推翻重做版）

> ⚠️ 二期规划已升级为 V2，详见 `PHASE2_DEV_PLAN_V2.md`。旧 `PHASE2_MES_ALIGNMENT_PLAN.md` 已标注作废。
> V2 依据：用户桌面 `MES_TemplateV1.2(2)(1).xlsx`（21 张表 277 字段官方模板）+ `mes_discovery/` 反向调研快照。

二期目标是让 PLM 严格按 MES Template V1.2 表结构重新开发，支持初始化从 MES 反向导入，支持发布后同步给 MES。

核心原则：PLM 是源头，严格按 MES Template V1.2 表结构开发，现有代码/MD 可推翻重做。

### 改造范围（11 菜单 + 2 个轻量调整）

- 产品中心 > 产品库：ProductDef 26 字段推翻重做，加 processFlowName+Version 引用字段（架构独立化解耦 product_id）
- 工艺管理 > 制造流程：ProcessFlow 10 字段，详情页 5 tab（工序/制程内容/量测/防污染，分支返工并入 Content tab）
- 工艺管理 > 工序库（新）：ProcessStep 21 字段，独立菜单被 Seq 引用
- 工艺管理 > 制程阶段库（新）：ProcessStage 7 字段
- 工艺管理 > 制程能力库（新）：ProcessCapability 3 字段
- 工艺管理 > 制程配方库（新）：Recipe 7 字段，不含物理参数（物理参数在 MES EquipmentRecipeParam）
- 工艺管理 > 设备类型库（新）：EquipmentType 12 字段
- 工艺管理 > 设备能力库（新）：EquipmentCapability 4 字段，equipmentName→equipment_type_name 改造（PLM 按设备类型校验能力，MES 按设备实例）
- BOM 管理 > 设计 BOM：Bom 5 字段 + BomItem 10 字段三段式 + 工步绑定，解耦 product_id
- 物料库：ConsumableDef 前 11 字段技术规格 PLM 主控，后 17 字段现场库存/告警留 MES
- 集成中心 > 同步队列：MesSyncPackage/MesSyncItem，ECN 关闭生成同步包
- 基础平台 > 数据字典：MES_* 字典裁剪（保留 14 类枚举）
- 基础平台 > 系统参数：加 MES 同步配置项

### 不做的 MES 菜单（4 张表 MES 自治）

CarrierDef（载具）/ Area（区域）/ EquipmentDef（设备实例）/ PortDef（料口）。PLM 按需只读引用。

### PLM 引用对账（2 张表，只读同步+校验）

EquipmentRecipe（设备配方）/ EquipmentRecipeParam（设备配方参数，含物理参数值）。PLM 工艺设计时引用校验，不主控。

### 实施进度（9 个里程碑）

| # | 里程碑 | 状态 | 说明 |
|---|---|---|---|
| M1 | 数据模型重建 | ✅ 完成 | 推翻 6 个旧类，新建 14 张 PLM 主控表 + MesSyncPackage/MesSyncItem。schemas.py 同步重写 |
| M2 | 制造流程主菜单+5tab | ✅ 完成 | routers/processes.py 重写 + ProcessView.vue 4 tab 详情页 |
| M3 | 6个工艺库独立菜单 | ✅ 完成 | routers/process_lib.py + 6 个 View 全部 CRUD |
| M4 | 产品库改造 | ✅ 完成 | routers/products.py 重写（26 字段+引用查询）+ ProductsView.vue 重写 + ProductDetailView.vue 重写（引用关系双卡，不再内嵌8模块）|
| M5 | BOM三段式+物料库对齐 | ✅ 完成 | BomView/MaterialsView 改造 + routers 适配 MES Bom/BomItem 与 ConsumableDef 字段 |
| M6 | 集成中心+MES同步包 | ⏳ 待做 | MesSyncPackage 落地 + 受控引用视图 |
| M7 | ECN联动 | ⏳ 待做 | ECN 关闭识别受影响对象+自动升版+生成同步包 |
| M8 | 初始化导入脚本 | ⏳ 待做 | build_db.py 重写，从 MES 快照反向导入 |
| M9 | 字典裁剪+系统参数 | ⏳ 待做 | MES_* 字典保留 14 类 + 系统参数加 MES 同步配置 |

## 暂缓能力

- CAD/EDA 深集成。
- Office/CAD 全格式在线预览。
- 多组织、多租户、多法人、多站点权限隔离。
- 移动端、大屏、个性化看板。
- 高并发、复杂事务、分布式部署、性能分片。

## 核心验收口径

- 产品/需求 -> 文档 -> EBOM -> 工艺/PBOM/MBOM -> 变更 -> 发布 -> 集成队列 -> 质量/项目追溯。
- 文档、BOM、工艺、变更、项目阶段门接入统一流程。
- 发布对象进入 ERP/MES/QMS 队列。
- 主数据字段来自受控下拉。
- 页面符合紧凑商用后台风格。
