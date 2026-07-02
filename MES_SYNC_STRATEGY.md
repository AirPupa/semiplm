# MES 反向调研与 PLM 同步规划

本文记录从现有 MES 建模页面反向观察得到的产品方向判断。当前阶段先把 MES 的对象结构、字段定义和少量样例落盘，后续由 PLM 负责设计、审批、版本、发布和追溯，再把经过批准的数据同步给 MES 执行。

> 当前开发口径：本文是反向调研记录，保留历史判断。二期开发以 `PHASE2_DEV_PLAN_V2.md` 为准；凡本文中“EquipmentType/EquipmentCapability 仅作 MES 引用或对账”的旧判断，已被 V2 覆盖。当前口径是设备类型和设备能力归 PLM 主控，EquipmentCapability 按 `equipmentTypeName + processCapabilityName` 改造。

## 核心原则

SemiPLM 不是 MES 的只读壳，也不是 MES 全量复刻。正确边界是：

- PLM 是产品定义、产品工艺流程、用料表和 ECN 发布的源头。工艺流程详情页承载流程工序、流程内容、参数、量测、QTime、防污染、动作和分支，对齐 MES 产品页结构。
- MES 是执行平台，也是 PLM 设计时必须遵守的可执行能力约束来源。
- PLM 可以反向导入 MES 现有产品、路线、BOM、制程能力、制程配方和设备配方，作为初始化模板和受控字典。
- 初始化之后，新产品和新版本应在 PLM 设计、审批、发布，再同步到 MES。
- PLM 只“抄” MES 中属于产品定义上游的结构，不抄 MES 的生产执行、设备运行、报警、批次过站和现场消耗。

## 当前结论

MES 建模不是简单表单，而是元数据驱动模型：

- 分页对象返回 `objectDef + attributes + values + keyAttributes`。
- 字段定义包含标题、中英文、数据类型、长度、是否可编辑、控件类型、枚举/API/SQL 数据源、底层表名和列名。
- 产品规格对象是 `ProductDef`，主键是 `productDefName + productDefVersion`。
- 产品详情通过 `type` 切换模块：`Sequences`、`Content`、`Parameter`、`Measure`、`Qtime`、`Contamination`、`Action`、`Alter`。
- 设备配方对象是 `EquipmentRecipe`，主键是 `equipmentName + equipmentRecipeName + recipeName + equipmentRecipeMode`。

产品页深扒后需要修正一处术语：页面上的“流程工序”实际接口参数是 `type=Seq`，不是 `Sequences`。真实产品详情接口会返回一个聚合对象，里面按模块挂载：

- `basicInfo`：产品规格基础信息。
- `seqLo`：流程工序。
- `content`：流程内容。
- `parameter`：动态参数。
- `measure`：量测。
- `qTime`：QTime。
- `contamination`：防污染。
- `action`：动作。
- `alter`：流程分支。

这说明 MES 的产品页不是单纯“产品基础资料”，而是产品版本下的制造定义包。它已经把工序、制程能力、制程配方、量测、防污染、分支和动态参数组织在产品维度里。

本轮已把制造建模中可通过通用建模分页接口读取的对象完整落盘。覆盖结果如下：

| 域 | MES 对象 | 记录数 | PLM 判断 |
| --- | --- | ---: | --- |
| 物料/产品 | `ProductDef` | 3 | PLM 主控 |
| 物料/产品 | `ProductGroup` | 1 | PLM 主控分类，MES 引用 |
| 物料/产品 | `Recipe` | 324 | PLM 主控（设计层：配方命名+版本+生命周期，不含物理参数） |
| 物料/产品 | `RecipeGroup` | 0 | 暂保留映射能力 |
| 物料/产品 | `ReticleSet` / `ReticleGroup` | 0 | 光刻相关产品后续主控引用 |
| 物料/产品 | `CarrierDef` | 2 | MES 主控，PLM 引用 |
| 物料/产品 | `BinDef` | 0 | 测试/质量范围明确后再做 |
| 工艺 | `ProcessFlow` | 3 | PLM 主控版本和发布 |
| 工艺 | `ProcessStep` | 256 | PLM 主控产品路线中的受控步骤引用 |
| 工艺 | `ProcessStage` | 27 | PLM 引用/分类 |
| 工艺 | `ProcessCapability` | 84 | PLM 主控（设计层：工艺设计语言，Recipe 父级，纯命名无设备绑定） |
| 工厂/设备 | `Factory` / `Site` / `Area` | 20 | MES 主控，PLM 引用适用范围 |
| 工厂/设备 | `EquipmentType` | 30 | V2 已调整为 PLM 主控 |
| 工厂/设备 | `EquipmentCapability` | 97 | V2 已调整为 PLM 主控，字段从 equipmentName 改为 equipmentTypeName |
| 工厂/设备 | `EquipmentRecipe` | 331 | MES 主控，PLM 只绑定引用和对账 |
| 工厂/设备 | `FurnaceRecipe` / `EquipmentModel` | 0 | 暂不进入 PLM 主线 |
| 工厂/设备 | `StateModel` | 1 | MES 主控 |
| 公共 | `ReasonCode` | 295 | MES 主控，PLM 引用原因码 |
| 公共 | `OwnerGroup` | 1 | PLM 可引用责任归属 |
| 元数据 | `ObjectDef` / `ViewObjectDef` | 108 | 用于字段映射、校验和菜单理解 |

这说明我们已经不只是看了产品页，而是把制造建模的主要菜单域做了横向扫描和可读对象抓取。仍需注意：部分对象可能只存在专用接口，不在通用 `general/pagination` 暴露，例如 BOM 详细结构、产品详情八个模块、某些规则类对象。因此“全量抓取”是建模通用接口层面的全量，不等于 MES 所有业务接口已经穷尽。

产品页专用接口已补充深扒，当前三个产品版本的真实模块数据如下：

| 产品版本 | 流程 | 用料表 | 流程工序 `Seq` | 流程内容 `Content` | 量测 `Measure` | 防污染 `Contamination` | 参数/QTime/动作/分支 |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `NLA-PROD@001` | `NLAFlow-01@AA` | `BOM-NLA-001` | 103 | 103 | 103 | 103 | 暂无数据，有字段定义 |
| `NWBL0625-01@001` | `JJSFlow-01@AA` | `BOM-NWBL0827@AA` | 220 | 220 | 220 | 220 | 暂无数据，有字段定义 |
| `NWBL0827-01@001` | `JJSFlow-01@AA` | `BOM-NWBL0827` | 220 | 220 | 220 | 220 | 暂无数据，有字段定义 |

关键字段含义：

- `Seq`：`processFlowSeqName`、`processFlowSeqType`、`processName`、`processVersion`、`processStageName`、`processGroup1`、`processGroup2`。
- `Content`：`processCapabilityName`、`recipeName`、`dcSpecName`、`yieldLimit`、`reticleGroupName`、`reticleName`、`probeCardName`、抽检规则、跳站/强制工步。
- `Measure`：量测项、目标值、规格上下限、抽检数量、抽检卡槽、抽检方式。
- `Contamination`：进站允许污染等级、出站污染等级。
- `Qtime`：起止工序、起止事件、QTime 类型、限制分钟、最大 WIP、报警配置。
- `Alter`：分支名称、分支类型、条件表达式、返工路径、返回工步、最大返工次数。

因此 PLM 的产品详情页应按 MES 产品页建模，而不是把“工艺流程、参数、量测、防污染”分散成彼此无关的菜单。

用料表页已补充深扒。MES 的 BOM 不是复杂机械行业那种多层装配 BOM，而是产品版本执行需要的工序用料清单，页面分为三段：

- 原物料列表：`Consumable`。
- 耐用品列表：`Durable`。
- 产品列表：`Product`。

真实接口是 BOM 专用接口，不在通用分页对象里完整展开：

- `/gw/mes-modeling-service/bom/pagination`
- `/gw/mes-modeling-service/bom/{bomName}/{bomVersion}/one`
- `/gw/mes-modeling-service/bom/{bomName}/{bomVersion}/detail?type=Item&materialType={Consumable|Durable|Product}`

当前 MES 样例里有 2 个 BOM 版本：

| BOM | 状态 | 原物料 | 耐用品 | 产品 |
| --- | --- | ---: | ---: | ---: |
| `BOM-NLA-001@001` | Active | 1 | 0 | 0 |
| `BOM-NWBL0827@001` | Active | 1 | 0 | 0 |

BOM 明细字段应按 MES 结构建模：`materialType`、`materialDefName`、`materialDefVersion`、`requireQuantity`、`unit`、`processStepName`、`processStepVersion`。也就是说，PLM 的 BOM 第一阶段应做“产品版本下按工步绑定的用料表”，而不是先做复杂多层 EBOM/MBOM。


所以 PLM 的方向不应只是“产品台账 + 附件”，而要变成半导体产品定义中心：

- 产品规格定义中心：产品、版本、产品组、工艺流、BOM、光罩、Bank、Gross Die、Dummy 策略。
- 产品制造定义：工艺流程详情页聚合流程工序、流程内容、工艺能力、工艺配方、用料表、参数、量测、QTime、防污染、动作和返工分支，对齐 MES 产品页结构。
- 变更与生效中心：ECR/ECO/ECN 负责对象升版、生效条件、批次/日期范围和下发任务。
- 集成控制中心：PLM 产生同步包、MES 回写结果、PLM 保留审计和重试记录。

## 系统职责边界

PLM 负责：

- 设计数据：产品规格、产品版本、产品工艺流程版本（含 8 模块）、用料表版本、关键参数、质量/可靠性要求。
- 版本数据：产品、BOM、工艺、文档、参数、变更包的版本与状态。
- 审批数据：工作流、签核、会签、影响分析、发布记录。
- 生效数据：生效日期、生效批次、适用产品、适用工厂、回滚策略。
- 同步数据包：生成面向 MES 的 `ProductDef`、`ProcessFlow`、`BOM`、`Parameter` 等发布包。

MES 负责：

- 生产执行：Lot/Wafer 运行、派工、过站、追溯。
- 建模运行态：设备、站点、区域、能力、机台配方、实时有效状态。
- 生产控制细节：设备配方（EquipmentRecipe，含 equipmentName+chamberFlow+lifeTime）、Chamber 流程、部分站点/设备依赖选项。
- 执行回写：同步成功/失败、MES 对象 id、运行态状态、异常信息。

PLM 不直接替代 MES 维护所有现场模型。PLM 只接管与产品设计发布强相关的“上游定义”，并通过同步包投递给 MES。

建议把边界固化成三层（配方体系按"设计层 PLM 主控 / 执行层 MES 主控"切分，依据 2026-07-02 字段级核验）：

1. PLM 主控并可同步（设计层 + 产品定义层）
   产品定义、产品版本、产品组、产品到工艺流/BOM/光罩/Bank/Bin 的绑定、工艺流程（含流程工序/流程内容/参数/量测/QTime/污染控制/动作/分支）、**工艺能力 ProcessCapability**（工艺设计语言，Recipe 的父级，纯命名无设备绑定）、**工艺配方 Recipe**（配方命名+版本+生命周期登记，name 编码设计意图，不含物理参数；实际参数在 EquipmentRecipe 侧）、ECN 发布包。

2. PLM 引用并对账（MES 主控，PLM 只读引用+校验+对账）
   工厂、站点、区域、工序库、工艺段、设备类型、**设备能力 EquipmentCapability**（主键含 equipmentName，按物理设备实例建）、**设备配方 EquipmentRecipe**（主键含 equipmentName+equipmentRecipeName+chamberFlow+lifeTime）、**炉管配方 FurnaceRecipe**（主键含 equipmentName+晶圆上下限）、载具 Carrier、原因码 ReasonCode、归属组 OwnerGroup。

3. MES 自治（执行层 + 现场运行）
   物理设备实例、设备配方主体（EquipmentRecipe/FurnaceRecipe）、设备能力主体（EquipmentCapability）、设备状态、报警、批次规则、命名规则、权限用户、Lot/Wafer 执行、现场运行记录。

配方体系切分依据：ProcessCapability/Recipe 是"做什么工艺、用哪个配方版本"的设计意图登记，归 PLM；EquipmentRecipe/EquipmentCapability/FurnaceRecipe 是"哪台设备怎么做、chamber 怎么流、参数多少"的物理执行绑定，归 MES。ECN 换配方版本时 PLM 升 Recipe 版本 → 审批 → 下发 → MES 引用新 Recipe 调整 EquipmentRecipe。

## 需要同步给 MES 的数据

第一优先级，必须同步：

| PLM 对象 | MES 对象/模块 | 同步理由 |
| --- | --- | --- |
| 产品主数据 | `ProductDef.basicInfo` | MES 生产必须识别产品名、版本、产品类型、生产类型、产品组 |
| 产品版本 | `productDefVersion` | MES 按版本执行，不应只按产品型号覆盖 |
| 产品工艺流程 | `ProcessFlow` / `seqLo` | 产品和流程版本必须绑定 |
| 流程工序 | `Product.detail type=Seq` / `seqLo` | MES 产品页按产品版本保存工序序列 |
| 流程内容 | `Product.detail type=Content` / `content` | MES 需要制程能力、制程配方、设备/配方约束、抽检、跳站/强制工步 |
| 制程能力 | `ProcessCapability` | PLM 主控工艺设计语言，下发供 MES Recipe/EquipmentRecipe 引用 |
| 制程配方 | `Recipe` | PLM 主控配方命名+版本+生命周期，下发供 MES EquipmentRecipe 引用；ECN 换配方版本时 PLM 升版下发 |
| 用料表/BOM | `bomName` / `bomVersion` / BOM Item | 生产用料、耐用品、半成品引用和产品工步一致性 |
| 工艺参数 | `Parameter` | 关键参数需随产品版本发布 |
| 量测计划 | `Measure` | CP/FT/膜厚/CD/良率等控制项需下发 |
| QTime | `Qtime` | 半导体制程强依赖等待时间和时限控制 |
| 污染控制 | `Contamination` | 产品/工序污染等级影响可用设备和流转 |
| ECN 生效 | MES 同步队列 | 变更批准后触发对象升版和生效 |

第二优先级，谨慎同步：

| PLM 对象 | MES 对象/模块 | 判断 |
| --- | --- | --- |
| Action / Alter | `Action` / `Alter` | 返工、分支、跳站规则风险高，先建模后审批下发 |
| 光罩集 | `reticleSetName` | 对光刻/曝光强相关产品同步 |
| Bin 策略 | `binName` / BinDef | 与测试分选和质量闭环关联后同步 |
| Dummy 策略 | `dummyMaxUseTime` / `dummyThkParam` / `dummyThkLimit` | 与实际制程控制确认后同步 |
| 设备配方引用 | `EquipmentRecipe` | PLM 先引用或校验，不直接创建全量设备配方 |

暂不同步：

- 用户、组织、权限。
- MES 现场设备层级、端口、实时状态。
- Lot/Wafer 运行数据的主写入。
- ERP 采购/MRP 拆分逻辑。

## 产品方向调整

现有 PLM 应从“光电芯片 PLM 演示系统”调整为“半导体产品定义与发布系统”。业务主线建议改成：

1. 产品规格
   产品型号、产品名、产品类型、生产类型、产品组、版本、状态、Owner、Gross Die、光罩集、Bin、Bank、Dummy 策略。

2. 产品版本包
   一个产品版本包包含 ProductDef、BOM、工艺流程、参数、量测、QTime、污染控制、文档和变更来源。

3. 工艺流程包
   工艺流版本、步骤序列、工序、能力、设备/配方约束、参数、量测、QTime、污染、Action/Alter。

4. ECN 发布包
   审批通过后冻结要同步的对象版本，生成同步任务，记录 MES 返回结果。

5. MES 映射配置
   保存 PLM 字段到 MES 字段的映射、枚举映射、状态映射、必填校验和默认值策略。

## 阶段计划

### 阶段 0：反向快照落盘

已完成初始方向：

- 保存 MES 对象快照到 `mes_discovery/mes_modeling_snapshot.json`。
- 保存候选同步矩阵到 `mes_discovery/mes_sync_candidate_matrix.json`。
- 保存可作为 PLM 初始化来源的数据到 `mes_discovery/plm_initial_seed_from_mes.json`。
- 保存制造建模通用接口全量种子到 `mes_discovery/mes_full_model_seed.json`。
- 保存全量种子数量摘要到 `mes_discovery/mes_full_model_seed_summary.json`。
- 保存 PLM/MES 职责边界白名单到 `mes_discovery/plm_mes_responsibility_boundary.json`。
- 保存产品页专用详情深扒到 `mes_discovery/mes_product_detail_deep_dive.json`。
- 保存产品页专用详情摘要到 `mes_discovery/mes_product_detail_deep_dive_summary.json`。
- 前端产品详情页已先调整成 `ProductDef` 视角。

`plm_initial_seed_from_mes.json` 同时保留两层数据：

- `raw_mes`：MES 原始建模对象、字段定义、产品详情模块和实际 values，用于后续对账、映射和字段补齐。
- `plm_initial_data`：从 MES 映射出来的 PLM 初始化候选数据，包括产品、BOM、工艺流程、MES 引用对象。

这份文件不是最终导入脚本，而是初始化数据源。导入数据库前必须经过字段映射确认、枚举映射确认和重复数据处理。

`mes_full_model_seed.json` 是更宽的初始化底座，包含制造建模对象的字段定义、主键、标题和全部 values。它更适合后续做：

- PLM 初始化引用字典：Factory、Site、Area、ProcessStage、ProcessCapability、EquipmentType、EquipmentCapability、ReasonCode。
- 同步前校验：ProductDef、ProcessFlow、ProcessStep、Recipe、EquipmentRecipe 是否存在、版本是否一致、状态是否允许。
- 字段映射页面：根据 `ObjectDef` / `ViewObjectDef` 和各对象 `attributes` 生成候选映射。
- 对账任务：用 MES 当前值反查 PLM 发布包和同步记录。

MES 字典已先落到 PLM 自己的 `dictionary_items` 表，作为初始化数据使用。当前导入脚本是 `backend/app/import_mes_dictionaries.py`，种子文件是 `mes_discovery/mes_dictionary_seed.json`，已导入 `1728` 条 `MES_*` 字典项，包括枚举、MES 引用对象、对象定义和视图定义。

这些字典不是最终菜单范围。后续需要按 PLM 边界做删减：

- 保留产品定义、产品路线、BOM、工序、制程能力、制程配方、量测、QTime、防污染、发布同步所需字典。
- 保留工厂、区域、设备类型、设备能力、设备配方、原因码等只读引用和校验字典。
- 删除或隐藏报警、批次执行、现场设备状态、权限用户、运行记录等不属于 PLM 主控范围的字典。

### 阶段 1：PLM 数据模型补齐

新增或扩展：

- `ProductDefinition` 或扩展 `Product`：补齐 ProductDef 字段。
- `ProductReleasePackage`：产品版本包。
- `ProductBom` / `ProductBomItem`：按 MES 用料表结构维护原物料、耐用品、产品三类明细，并绑定到工步。
- `ProductMesMapping`：产品到 MES 对象映射。
- `ProcessRouteStepControl`：工序级参数、量测、QTime、污染、Action/Alter。
- `MesSyncPackage` / `MesSyncItem`：同步包、同步项、状态、请求/响应摘要。

优先做的 PLM 功能不是 MES 菜单复刻，而是围绕“发布给 MES 的产品定义包”组织：

- 产品定义工作台：ProductDef 字段、版本、状态、产品组、Gross Die、Bank、光罩、Bin、Dummy 策略。
- 产品制造定义工作台：选择 ProcessFlow，维护产品版本下的流程工序、流程内容、制程能力、制程配方引用、参数、量测、QTime、防污染、动作、分支。
- 受控引用库：从 MES 同步 EquipmentRecipe、EquipmentCapability、FurnaceRecipe 等只读引用（执行层，主键含 equipmentName）。制程能力、制程配方为 PLM 主控设计层对象，不在受控引用库内。
- ECN 发布包：冻结产品、BOM、工艺、参数、量测、文档和生效范围。
- MES 同步中心：生成同步包、执行白名单下发、记录响应、失败重试、差异对账。

### 阶段 2：MES 映射与校验

实现：

- 根据快照中的 `attributes` 生成字段映射页面。
- 校验 MES 必填字段、长度、枚举、数据源依赖。
- 发布前显示“MES 可下发完整度”。
- 只允许已审批/已发布/已冻结对象进入同步包。

### 阶段 3：只读对账

先不写 MES，只做：

- 从 MES 拉取 `ProductDef`、`ProcessFlow`、`BOM`、`EquipmentRecipe` 元数据。
- 对比 PLM 与 MES 的字段差异、版本差异、状态差异。
- 生成同步建议，不直接写入。

### 阶段 4：受控下发

写 MES 前必须具备：

- 沙箱或测试 MES 环境。
- 幂等键：对象名 + 版本 + ECN 编号。
- 回滚策略：停用新版本或重新激活旧版本。
- 审计记录：请求摘要、响应摘要、操作者、审批单、时间。
- 白名单：先只允许 ProductDef 基础字段和产品-流程-BOM 绑定下发。

### 阶段 5：闭环回写

MES 回写：

- 同步成功/失败。
- MES 对象 id。
- MES 当前状态。
- 失败原因和 traceId。
- 对账差异。

## 风险与约束

- 不把 cookie、token、账号密码写入仓库。
- 不在生产 MES 直接试写。
- 不把 PLM 变成 MES 全量复制品。
- 不让未审批数据进入同步包。
- 不用人工编辑 SQL 字符串做字段映射，必须走结构化映射配置。
- 设备配方是现场运行敏感对象，第一阶段只做引用、校验和对账。

## 当前本地快照

详见：

- `mes_discovery/mes_modeling_snapshot.json`
- `mes_discovery/mes_sync_candidate_matrix.json`
- `mes_discovery/plm_initial_seed_from_mes.json`
- `mes_discovery/mes_full_model_seed.json`
- `mes_discovery/mes_full_model_seed_summary.json`
- `mes_discovery/plm_mes_responsibility_boundary.json`
- `mes_discovery/mes_product_detail_deep_dive.json`
- `mes_discovery/mes_product_detail_deep_dive_summary.json`
- `mes_discovery/mes_bom_deep_dive.json`
- `mes_discovery/mes_bom_deep_dive_summary.json`
- `mes_discovery/mes_dictionary_seed.json`
- `mes_discovery/mes_dictionary_seed_summary.json`
