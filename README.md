# SemiPLM 半导体产品定义 PLM

SemiPLM 是面向半导体制造企业的轻量级单机 PLM。当前产品方向已根据现有 MES 制造建模页面修正：PLM 不复刻 MES 全部菜单，而是负责产品定义、工艺流程、用料表、变更审批和 MES 同步包，结构对齐 MES 制造建模以便发布后同步。MES 继续负责生产执行、设备运行态、设备配方主体、Lot/Wafer 过站和现场消耗。

## 当前技术栈

- 后端：FastAPI + SQLAlchemy + SQLite
- 前端：Vue 3 + TypeScript + Arco Design Vue + ECharts
- 部署：目标环境为 Linux + Docker Compose；Windows 仅作为当前开发环境
- 数据库：开发默认 `backend/semiplm_demo.db`；Docker 部署默认 `/data/semiplm.db`

## 阶段优先级

当前阶段优先保证业务功能合理和完善：真实对象、真实 CRUD、流程闭环、对象联动、主数据受控下拉和商用后台交互。事务一致性、高并发、复杂锁、分布式部署、性能分片等工程治理暂缓，待业务主线稳定后再加强。

## 本地开发启动

后端：

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

Windows PowerShell 如果禁止执行 `npm.ps1`，可改用 `npm.cmd run dev`。Codex/受限沙盒环境如遇到 Vite/esbuild 读取配置被拦截，可在确认命令安全后提权启动开发服务。

访问地址：

- 前端开发环境：http://127.0.0.1:5173/dashboard
- 后端健康检查：http://127.0.0.1:8000/api/health
- API 文档：http://127.0.0.1:8000/docs

## Linux Docker 启动

目标部署环境为 Linux + Docker Compose，Windows 只作为开发和调试环境。

```bash
cd /opt/semiplm
docker compose up --build
```

访问地址：

- 前端：http://127.0.0.1:8080
- API：http://127.0.0.1:8000/api/health

Docker 部署时后端数据库由环境变量控制：

```bash
SEMIPLM_DATABASE_URL=sqlite:////data/semiplm.db
```

`docker-compose.yml` 默认将命名卷 `semiplm-data` 挂载到后端容器 `/data`，用于持久化 SQLite 数据库。不要把数据卷挂到 `/app`，避免覆盖应用代码。

## 产品原则

- 产品级规则以 `PRODUCT_SPEC.md` 为准，覆盖产品边界、业务对象、状态流转、主数据、权限、接口契约、页面交互、文件附件和集成队列。
- 当前业务范围按单公司、单工厂、单组织管理；部门仅作为用户属性、流程路由和统计维度。
- 研发数据必须真实可 CRUD，不能只做静态页面；产品、工艺流程、用料表、文档、变更、项目、质量之间要能互相追溯。
- MES 对接以产品建模为主线：ProductDef 基础信息、工艺流程（含工序/制程内容/参数/量测/QTime/防污染/动作/分支）、BOM 用料表、ECN 生效和同步结果回写。8 模块挂在工艺流程详情页，不单独建菜单。
- 工艺流程是 PLM 主控源头，发布后同步给 MES；标准工序、工艺阶段、工艺能力（ProcessCapability）、工艺配方（Recipe）、设备类型（EquipmentType）和设备能力（EquipmentCapability，按 equipmentTypeName 改造）为 PLM 主控设计层对象。设备配方（EquipmentRecipe）、设备配方参数（EquipmentRecipeParam）、炉管配方（FurnaceRecipe）、物理设备实例、原因码、工厂区域等仍属 MES 执行层或受控引用数据，PLM 只引用、校验、对账。
- MES/ERP/QMS 对接先做配置、同步队列、同步记录、状态回写预留，不先做复杂工业 CAD/EDA 集成。
- UI 以紧凑商用后台风格为准，Element Plus 与 Arco 可在过渡期并存；不要为了迁移组件库破坏业务页密度和可用性。

## 文档权威层级

根目录只保留当前开发需要的 7 个文档：

1. `README.md`：启动、交接入口和最高层原则。
2. `PRODUCT_SPEC.md`：产品边界、页面/API/状态/权限的通用约束。
3. `IMPLEMENTATION_ROADMAP.md`：当前进度、下一步和验收节奏。
4. `PHASE2_DEV_PLAN_V2.md`：二期 MES Template V1.2 改造的详细方案。
5. `MES_SYNC_STRATEGY.md`：MES 反向调研记录；若与 V2 冲突，以 V2 为准。
6. `MENU_ARCHITECTURE.md`：当前菜单和能力归属。
7. `FILE_INDEX.md`：按业务域定位代码文件。

历史蓝图、旧架构、旧功能清单、旧二期计划和 UI 迁移说明已归档到 `docs/archive/`，只作为背景材料，不作为当前开发依据。

## 交接阅读顺序

后续接手开发不要通读全仓，按以下顺序读文档：

1. `PRODUCT_SPEC.md`：产品级通用规范和功能完成标准。
2. `IMPLEMENTATION_ROADMAP.md`：当前基线和下一步计划。
3. `PHASE2_DEV_PLAN_V2.md`：二期当前主线和字段归属。
4. `FILE_INDEX.md`：按业务功能定位要读的后端 router、前端 api 和页面文件。
5. `MENU_ARCHITECTURE.md`：确认菜单边界和功能归属。

## 当前验证

- 前端生产构建：`npm run build`
- 后端语法编译：`python -m compileall app`

构建阶段可能出现 Arco/ECharts 相关 chunk 体积提醒，当前不影响运行；后续如需优化包体积，再做按需引入和路由分包优化。
