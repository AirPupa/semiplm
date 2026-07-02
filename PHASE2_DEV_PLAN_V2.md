# SemiPLM 二期开发计划 V2（推翻重做版）

> 本文档替代 `PHASE2_MES_ALIGNMENT_PLAN.md`。旧规划作废。
>
> 制定日期：2026-07-02
> 制定依据：用户桌面 `MES_TemplateV1.2(2)(1).xlsx`（21 张表 277 字段官方模板）+ `mes_discovery/` 反向调研快照 + 用户多次定调。
> 核心授权：用户明确"设备类型和设备能力归属 PLM，现有代码可以推翻，现有 MD 也可以推翻，严格按照现在有的资料和需求重新开发"。

---

## 一、定调与原则

### 1.1 用户定调（不可动摇）

1. **PLM 是源头**：所有产品/工艺/配方/设备类型/设备能力的设计、审批、发布在 PLM；MES 接收执行，无编辑权。
2. **设备类型 + 设备能力归 PLM 主控**：作为工艺设计资源，PLM 工艺编排时按设备类型校验能力。
3. **现有代码与 MD 可推翻**：一期以"光电芯片 PLM 演示系统"思路开发的模型/页面，凡与 MES Template V1.2 表结构冲突的，全部推翻重做。
4. **严格按 MES Template V1.2 表结构开发**：字段名、主键、枚举、表关系对齐 MES，保证可双向同步。

### 1.2 切分原则（设计层 PLM 主控 / 执行层 MES 主控）

| 层 | 归属 | 切分依据 |
|---|---|---|
| 设计层 | PLM 主控 | 描述"做什么工艺、用哪个配方版本、什么设备类型能跑什么工艺"——纯设计意图，不绑定物理实例 |
| 执行层 | MES 主控 | 描述"哪台物理设备、chamber 怎么流、参数值多少"——绑定 equipmentName 物理实例，必须现场调试锁定 |

---

## 二、完整表归属清单（21 张表 277 字段）

### 2.1 PLM 主控 14 张表（设计层 + 产品定义层）

| # | MES 表 | 字段数 | PLM 落地菜单 | 关键字段 |
|---|---|---|---|---|
| 1 | **ProductDef** | 26 | 产品中心 > 产品库 | productDefName+Version/state/type(SBD/MOS/NPW)/productionType/productGroupName/**processFlowName+Version**/bomName+Version/reticleSetName/grossDie/startBank/endBank/owner/maxUseCount/maxRecycleCount/ownerGroupName/dummyMaxUseTime/dummyThkParam/dummyThkLimit/binName/packageQty/productUsage |
| 2 | **ProcessFlow** | 10 | 工艺管理 > 工艺流程 | processFlowName+Version/description/flowType1(Main/Sub)/flowType2(Production/Engineering/Monitor)/flowState(Unfrozen/Frozen/Active/Invalid)/ownerGroup/owner/flowGroup/isDeleted |
| 3 | **ProcessFlowSeq** | 12 | 工艺流程 > 工序 tab | idx/stepSource/processFlowSeqName/processFlowName+Version/processName+processVersion/processFlowSeqType(ProcessStep/SubProcessFlow)/processGroup1/processGroup2/workLayer |
| 4 | **ProcessFlowContent** | 22 | 工艺流程 > 制程内容 tab | processFlowSeqName/processCapabilityName/recipeName/dcSpecName/yieldLimit/reticleGroupName/reticleName/probeCardName/lotSamplingRule/isSkipAllowed/isMandatoryStep/samplingUserGroup/isFlip/branchFlowGroup/branchFlowName/reworkFlowGroup/reworkFlowName/waferSelectionRule/inkAble |
| 5 | **ProcessFlowMeasure** | 11 | 工艺流程 > 量测 tab | processFlowSeqName/keyProcessFlowSeqName/measureItem(PARTICLE/TH/RS/CD/OL/DEFECT/T)/target/lowerSpecLimit/upperSpecLimit/sampleCount/sampleSlots/sampleCountType |
| 6 | **ProcessFlowContamination** | 5 | 工艺流程 > 防污染 tab | processFlowSeqName/requireContaminationLevels[1..11]/affectContaminationLevel |
| 7 | **ProcessStage** | 7 | 工艺管理 > 工艺阶段 | idx/processStageName/description/processGroup1(分段)/processGroup2(工艺层)/keyProcess/processStageState |
| 8 | **ProcessStep** | 21 | 工艺管理 > 标准工序 | processStepName+Version/description/state/type(Process/Metrology/Sort/Storage/Transport)/processStageName/processGroup1+2/keyProcess/bankName/processCapabilityName/recipeName/isSkipAllowed/isMandatoryStep/samplingUserGroup/ownerGroup/owner/costCenterStage/isDeleted/isFlip/detailProcessStepType |
| 9 | **ProcessCapability** | 3 | 工艺管理 > 工艺能力 | processCapabilityName/description/processCapabilityState |
| 10 | **Recipe** | 7 | 工艺管理 > 工艺配方 | processCapabilityName/recipeName/description/objectOwner/recipeState/effectiveTime/expirAlarmId |
| 11 | **EquipmentType** | 12 | 工艺管理 > 设备类型 | equipmentTypeName/description/processType1(Production/Inventory)/processType2(Process/Metrology/Sort/Storage/Transport)/constructType1(Main/Sub/Internal)/constructType2(Normal/Internal/Cluster/Inline)/processCapacity/processJobCountMin/Max/batchCapacity/dummyUnmountFlag/equipmentTypeState |
| 12 | **EquipmentCapability** | 4 | 工艺管理 > 设备能力 | **equipmentTypeName**（PLM 改造，MES 原字段为 equipmentName）/processCapabilityName/assignFlag/equipmentCapabilityState |
| 13 | **Bom** | 5 | BOM 管理 > 设计 BOM | bomState(Unfrozen/Frozen/Active/Invalid)/bomName/bomVersion/description/owner |
| 14 | **BomItem** | 10 | BOM 管理 > 设计 BOM > 明细 | idx/bomName+bomVersion/materialType(Consumable/Durable/Product)/materialDefName+Version/requireQuantity/unit/processStepName+Version |

### 2.2 部分 PLM 主控 1 张表

| # | MES 表 | 字段数 | PLM 落地 | 字段切分 |
|---|---|---|---|---|
| 15 | **ConsumableDef** | 28 | 物料库 > 原物料 | **PLM 主控前 11 字段**（技术规格）：name/description/fabProductName/consumableType/primaryUnitName/primaryUnitCode/unitName/unit/unitConversionRate/materialStandardQty/spec<br>**MES 主控后 17 字段**（现场库存/告警）：kitLeadTime/inUsePeriod/splitFlag/deductionFlag/deiceFlag/deiceDuration/deiceUpperLimit/useTimeAlarmLimit/safetyStock/alarmAddress/*alarmId×6/consumableDefState/sourceType |

### 2.3 PLM 引用对账 2 张表（只读同步+校验+对账）

| # | MES 表 | 字段数 | 用途 |
|---|---|---|---|
| 16 | **EquipmentRecipe** | 10 | PLM 工艺设计时引用校验：某设备实例已绑定的设备配方（equipmentName+equipmentRecipeName+recipeName+equipmentRecipeMode+chamberFlow） |
| 17 | **EquipmentRecipeParam** | 12 | PLM 工艺设计时引用校验：设备配方参数值（recipeParameterName+value+validationType+target/lowerlimit/upperlimit） |

### 2.4 MES 自治 4 张表（PLM 不做）

| # | MES 表 | 字段数 | 不做原因 |
|---|---|---|---|
| 18 | CarrierDef | 20 | 载具实物台账+使用寿命告警，PLM 仅按需只读引用 |
| 19 | Area | 7 | 工厂/区域/Bay/Bank 现场配置，PLM 按需只读引用 |
| 20 | EquipmentDef | 37 | 物理设备实例台账，37 字段全是现场属性（设备状态模型/料口/RPA/小瓶化学等） |
| 21 | PortDef | 8 | 设备料口规格，PLM 不涉及 |

---

## 三、PLM 主控菜单结构（11 个主菜单）

### 3.1 产品中心

| 菜单 | 对应表 | 改造说明 |
|---|---|---|
| 产品库 | ProductDef（26字段） | **推翻现有 Product 模型重做**。加 processFlowName+Version 引用字段（架构独立化，不再 product_id 外键）。加 reticleSetName/grossDie/startBank/endBank/maxUseCount/maxRecycleCount/dummyMaxUseTime/dummyThkParam/dummyThkLimit/binName/packageQty/productUsage 等 MES 字段 |

### 3.2 工艺管理（6 个菜单，5 个新建）

| 菜单 | 对应表 | 改造说明 |
|---|---|---|
| **工艺流程** | ProcessFlow + Seq + Content + Measure + Contamination | **推翻现有 ProcessRoute/ProcessStep 模型重做**。ProcessRoute 类改名 ProcessFlow，表 process_routes→process_flows。架构独立化：解耦 product_id 外键，产品通过 processFlowName+version 引用。详情页 5 个 tab（工序/制程内容/量测/防污染）。Content tab 含分支/返工字段（不单设 Alter tab） |
| **标准工序**（新） | ProcessStep | 独立主控菜单，被 ProcessFlowSeq 通过 processName+processVersion 引用。21 字段全建 |
| **工艺阶段**（新） | ProcessStage | 独立主控菜单，7 字段。idx/processStageName/description/processGroup1/processGroup2/keyProcess/state |
| **工艺能力**（新） | ProcessCapability | 独立主控菜单，3 字段。processCapabilityName/description/state |
| **工艺配方**（新） | Recipe | 独立主控菜单，7 字段。不含物理参数（物理参数在 MES EquipmentRecipeParam） |
| **设备类型**（新） | EquipmentType | 独立主控菜单，12 字段。设备族/型号分类，工艺设计资源 |
| **设备能力**（新） | EquipmentCapability | 独立主控菜单，4 字段。**PLM 改造**：equipmentName → equipmentTypeName，按设备类型建能力映射（MES 原表按设备实例） |

### 3.3 BOM 管理

| 菜单 | 对应表 | 改造说明 |
|---|---|---|
| 设计 BOM | Bom + BomItem | **改造 BomItem**：加 materialType/materialDefName+Version/requireQuantity/unit/processStepName+Version 三段式+工步绑定 |

### 3.4 物料管理

| 菜单 | 对应表 | 改造说明 |
|---|---|---|
| 物料库 | ConsumableDef 前 11 字段 | **改造现有 Material 模型**：加 consumableType/fabProductName/primaryUnitName+Code/unitName+Code/unitConversionRate/materialStandardQty/spec 字段。后 17 字段现场库存/告警不进 PLM |

### 3.5 集成中心

| 菜单 | 对应表 | 改造说明 |
|---|---|---|
| 同步队列 | MES 同步包（新） | 新增 MesSyncPackage/MesSyncItem 表。ECN 关闭时自动生成同步包。第一阶段模拟下发（只记状态），不真实调用 MES |

### 3.6 工程变更（保留一期）

| 菜单 | 改造说明 |
|---|---|
| PR/ECR/ECO/ECN | 保留一期成果。补强 ECN 关闭自动生成 MES 同步包（含 Recipe 升版、ProcessFlow 升版） |

### 3.7 基础平台（轻量调整）

| 菜单 | 调整内容 |
|---|---|
| 数据字典 | MES_* 字典裁剪：保留 14 类枚举（产品类型/生产类型/流程类型/流程状态/工步类型/制程类型/分段/工艺层/量测项/抽检规则/抽检方式/物料类型/设备类型/设备构造） |
| 系统参数 | 加 MES 同步配置项（网关地址/超时/重试/白名单开关） |

### 3.8 受控引用（只读，不建独立菜单）

| 对象 | 落地形式 |
|---|---|
| EquipmentRecipe | 集成中心 > MES 受控引用视图（只读列表+对账） |
| EquipmentRecipeParam | 同上，子表展示 |
| Area / CarrierDef | 工艺编排时按需只读引用下拉 |

---

## 四、代码推翻清单

### 4.1 后端必须改造/重写的文件

| 文件 | 推翻范围 | 替代方案 |
|---|---|---|
| `backend/app/models.py` | Product/ProcessRoute/ProcessStep/BomItem/Material 类全部重写 | 按 MES Template V1.2 表结构新建 14 张表模型 |
| `backend/app/schemas.py` | 对应 Schema 全部重写 | 对齐新模型 |
| `backend/app/routers/processes.py` | 全部重写 | 拆为 routers/process_flow.py + routers/process_step.py + routers/process_stage.py + routers/process_capability.py + routers/recipe.py + routers/equipment_type.py + routers/equipment_capability.py |
| `backend/app/routers/products.py` | 重写 | 对齐 ProductDef 26 字段 |
| `backend/app/routers/boms.py` | 部分重写 | BomItem 三段式 |
| `backend/app/routers/materials.py` | 部分重写 | 加 ConsumableDef 前 11 字段 |
| `backend/app/routers/integration.py` | 扩展 | 加 MES 同步包+受控引用视图 |
| `backend/app/build_db.py` | 重写 | 初始化数据从 MES 快照反向导入 |
| `backend/app/bootstrap.py` | 调整 | create_all 包含新表 |

### 4.2 前端必须改造/重写的文件

| 文件 | 推翻范围 | 替代方案 |
|---|---|---|
| `frontend/src/views/ProductsView.vue` | 重写 | ProductDef 26 字段表单+列表 |
| `frontend/src/views/ProductDetailView.vue` | 重写 | 展示引用的 processFlowName+Version、bomName+Version，不内嵌 8 模块 |
| `frontend/src/views/ProcessView.vue` | 重写 | ProcessFlow 主表+5 tab 详情页 |
| 新建 `ProcessStepView.vue` | 新建 | 标准工序独立菜单 |
| 新建 `ProcessStageView.vue` | 新建 | 工艺阶段 |
| 新建 `ProcessCapabilityView.vue` | 新建 | 工艺能力 |
| 新建 `RecipeView.vue` | 新建 | 工艺配方 |
| 新建 `EquipmentTypeView.vue` | 新建 | 设备类型 |
| 新建 `EquipmentCapabilityView.vue` | 新建 | 设备能力 |
| `frontend/src/views/BomView.vue` | 部分重写 | BomItem 三段式 |
| `frontend/src/views/MaterialsView.vue` | 部分重写 | 加 ConsumableDef 字段 |
| `frontend/src/views/IntegrationsView.vue` | 扩展 | 加 MES 同步包+受控引用 |
| `frontend/src/api/*.ts` | 对应重写 | 对齐新 routers |

### 4.3 保留不动的一期成果

| 模块 | 保留理由 |
|---|---|
| User/Role/Organization | 用户权限基础，不涉及 MES |
| WorkflowTemplate/Node/Instance/Task/Log | 通用流程引擎，可复用 |
| Change/ChangeImpact/Approval/ChangeAction | ECN 闭环已实现，补强联动即可 |
| Project/ProjectTask/ProjectTemplate | 项目管理不涉及 MES |
| QualityCAPA/QualityLot/QualityIssue | 质量模块不涉及 MES |
| Document/Attachment | 文档管理不涉及 MES |
| DictionaryItem/SystemParameter | 字典/参数引擎保留，内容裁剪 |
| OperationLog/ReportSnapshot | 审计/报表保留 |

---

## 五、实施顺序（9 个里程碑）

### M1 数据模型重建（推翻重做）
- 删除 models.py 中 Product/ProcessRoute/ProcessStep/BomItem/Material 旧类
- 新建 14 张 PLM 主控表模型，字段严格对齐 MES Template V1.2
- 新建 MesSyncPackage/MesSyncItem 表
- schemas.py 同步重写
- **关键**：ProcessFlow 解耦 product_id，products 表加 processFlowName+Version 引用字段
- **关键**：EquipmentCapability 字段 equipmentName → equipmentTypeName

### M2 工艺流程主菜单 + 5 tab 详情页
- routers/process_flow.py 新建
- ProcessView.vue 重写
- 5 tab：工序/制程内容/量测/防污染（分支/返工字段并入制程内容 tab）
- ProcessFlowContamination 的 requireContaminationLevels 数组字段用 JSON 类型

### M3 5 个工艺库独立菜单
- 标准工序（ProcessStep 21 字段）
- 工艺阶段（ProcessStage 7 字段）
- 工艺能力（ProcessCapability 3 字段）
- 工艺配方（Recipe 7 字段）
- 设备类型（EquipmentType 12 字段）
- 设备能力（EquipmentCapability 4 字段，equipmentTypeName 改造）
- 6 个 View + 6 个 api.ts + 6 个 router

### M4 产品库改造
- ProductsView.vue 重写，ProductDef 26 字段表单
- ProductDetailView.vue 重写，展示引用关系不内嵌
- routers/products.py 重写

### M5 BOM 三段式 + 物料库对齐
- BomItem 加 materialType/materialDefName+Version/requireQuantity/unit/processStepName+Version
- Material 加 ConsumableDef 前 11 字段
- BomView.vue / MaterialsView.vue 改造
- 状态：已完成。当前实现保留 BOM 比较、物料反查、工序覆盖率、Excel 导入导出和批量编辑。

### M6 集成中心 + MES 同步包
- MesSyncPackage/MesSyncItem 表落地
- ECN 关闭自动生成同步包
- 受控引用视图（EquipmentRecipe/EquipmentRecipeParam 只读）
- IntegrationsView.vue 扩展

### M7 ECN 联动
- ECN 关闭时识别受影响对象（ProductDef/ProcessFlow/Recipe/EquipmentType 等）
- 自动升版+生成同步包
- 前端 ECN 详情页加"影响对象"和"同步状态"区

### M8 初始化导入脚本（已完成）
- 从 `mes_discovery/mes_full_model_seed.json`、`mes_product_detail_deep_dive.json`、`mes_bom_deep_dive.json`、`mes_dictionary_seed.json` 反向导入。
- 导入范围：ProductDef + ProcessFlow + ProcessStep + ProcessCapability + Recipe + ProcessStage + EquipmentType + EquipmentCapability + BOM + Seq/Content/Measure/Contamination + MES 字典项。
- `backend/app/build_db.py` 已改为 MES 抓取主数据优先；PLM 仅补文档、项目、质量、流程待办和集成队列演示数据。

### M9 字典裁剪 + 系统参数
- MES_* 字典保留 14 类枚举
- 系统参数加 MES 同步配置项

---

## 六、风险与约束

1. **不写 cookie/token/账号密码到仓库**：MES 同步配置只存网关地址+超时，认证信息运行时注入。
2. **不在生产 MES 直接试写**：第一阶段模拟下发，只记状态。
3. **不把 PLM 变成 MES 全量复制品**：4 张 MES 自治表（CarrierDef/Area/EquipmentDef/PortDef）一行代码不写。
4. **不让未审批数据进入同步包**：同步包只允许已发布/已冻结对象进入。
5. **不用人工编辑 SQL 字符串做字段映射**：必须走结构化映射配置。
6. **设备配方是现场运行敏感对象**：EquipmentRecipe/EquipmentRecipeParam 第一阶段只做引用、校验、对账，不主控。

---

## 七、与旧规划的差异

| 维度 | 旧规划（PHASE2_MES_ALIGNMENT_PLAN.md） | 新规划 V2 |
|---|---|---|
| 改造范围 | 6 菜单 + 2 轻量 | **11 菜单 + 2 轻量** |
| PLM 主控表 | 12 张 | **14 张**（新增 EquipmentType + EquipmentCapability） |
| 工艺路线 | 改造 ProcessRoute 加 MES 字段 | **推翻重做** ProcessRoute→ProcessFlow，架构独立化解耦 product_id |
| 标准工序 | 挂工艺流程工序 tab | **独立菜单**（被 Seq 引用） |
| 设备类型 | 引用对账 | **PLM 主控**（独立菜单） |
| 设备能力 | 引用对账 | **PLM 主控**（独立菜单，equipmentName→equipmentTypeName 改造） |
| 代码策略 | 增量改造 | **推翻重做**（Product/ProcessRoute/ProcessStep/BomItem/Material 5 个模型类） |
| ProcessFlowContent | 8 模块单独 tab | **分支/返工字段并入 Content tab**（MES 实际无 Alter 表） |
| EquipmentRecipeParam | 未识别 | **新发现**，PLM 引用对账 |

---

## 八、已定稿关键决策

1. **EquipmentCapability 字段改造**：MES 原表主键是 equipmentName+processCapabilityName（设备实例+能力），PLM 改为 equipmentTypeName+processCapabilityName（设备类型+能力）。这是必要的语义调整——PLM 工艺设计时按设备类型校验能力，MES 现场按设备实例校验能力。

2. **ProcessFlow 架构独立化**：解耦 product_id 外键，products 表加 processFlowName+Version 引用字段。

3. **ProcessFlowContent 分支/返工字段**：MES 实际无 Alter 表，分支流程(branchFlowGroup/branchFlowName)和返工流程(reworkFlowGroup/reworkFlowName)是 Content tab 的字段，不单设 Alter tab。

4. **推翻范围**：Product/ProcessRoute/ProcessStep/BomItem/Material 5 个模型类全部重写。一期相关数据（演示数据）作废，从 MES 快照反向导入。

5. **实施节奏**：按 M1→M9 顺序推进，每个里程碑完成后集中验证。
