# SemiPLM 光电芯片制造 PLM

SemiPLM 是面向光电芯片制造企业的轻量级单机 PLM。目标不是演示玩具，而是按武汉睿码功能清单为主线，参考鼎捷 PLM 的成熟做法，逐步实现可落地的产品、文档、研发物料、设计 BOM、工艺、变更、项目、质量、权限和外部系统集成闭环。

## 当前技术栈

- 后端：FastAPI + SQLAlchemy + SQLite
- 前端：Vue 3 + TypeScript + Arco Design Vue + ECharts
- 部署：目标环境为 Linux + Docker Compose；Windows 仅作为当前开发环境
- 数据库：开发默认 `backend/semiplm.db`；Docker 部署默认 `/data/semiplm.db`

## 阶段优先级

当前阶段优先保证业务功能合理和完善：真实对象、真实 CRUD、流程闭环、对象联动、主数据受控下拉和商用后台交互。事务一致性、高并发、复杂锁、分布式部署、性能分片等工程治理暂缓，待业务主线稳定后再加强。

## 本地开发启动

后端：

```powershell
cd D:\study\plm\backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```powershell
cd D:\study\plm\frontend
npm install
npm run dev
```

访问地址：

- 前端开发环境：http://127.0.0.1:5173/dashboard
- 后端健康检查：http://127.0.0.1:8000/api/health
- API 文档：http://127.0.0.1:8000/docs

## Linux Docker 启动

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

- 当前业务范围按单公司、单部门、单组织管理，不做多组织、多租户。
- 研发数据必须真实可 CRUD，不能只做静态页面。
- BOM、文档、产品、版本、变更、项目、质量之间要能互相追溯。
- MES/ERP 对接先做配置、同步记录、字段映射、状态回写预留，不先做复杂工业 CAD/EDA 集成。
- UI 采用 Arco Design Pro B 端后台风格：浅灰侧栏、白色工作区、紧凑字体、低干扰菜单滚动条、蓝色选中态。

## 重要文档

- `FUNCTION_LIST.md`：功能范围清单。
- `PLM_BLUEPRINT.md`：产品蓝图。
- `PLM_ARCHITECTURE.md`：架构设计。
- `IMPLEMENTATION_ROADMAP.md`：开发路线与闭环标准。
- `ARCO_MIGRATION_PLAN.md`：Arco Design Vue 全站迁移计划与视觉规范。

## 当前验证

- 前端生产构建：`npm run build`
- 后端语法编译：`python -m compileall app`

构建阶段可能出现 Arco/ECharts 相关 chunk 体积提醒，当前不影响运行；全站迁移稳定后再做按需引入和路由分包优化。
