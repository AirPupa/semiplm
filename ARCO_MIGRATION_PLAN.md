# SemiPLM Arco Design Vue 全站迁移计划

## 迁移目标

SemiPLM 全站 UI 统一迁移到 Arco Design Vue，形成更现代、细腻、适合工业研发软件的视觉体系。迁移不是简单替换标签，而是建立一套面向光电芯片 PLM 的界面规范：深色工业导航、浅色高密度工作区、清晰对象关系、克制状态色、紧凑表单。

## 迁移原则

- Arco 作为长期主 UI 库，Element Plus 仅作为过渡依赖保留。
- 新页面优先使用 Arco，不再新增 Element Plus 页面。
- 已有页面逐页迁移，每迁完一页必须完成构建、接口、浏览器检查。
- 迁移不降低业务完整度：CRUD、流程、对象联动、集成队列、权限动作不能丢。
- 页面不做营销风，不做大卡片堆砌；PLM 页面以表格、详情、操作区、状态反馈为主。
- 视觉基准参照 Arco Design Pro B 端后台：浅灰侧栏、白色品牌区、浅色内容画布、轻量蓝色选中态。
- 侧栏菜单采用分组树感，不做大面积深色块；选中项使用浅蓝底和蓝色小圆点。
- 菜单滚动条必须低存在感：窄轨道、浅灰滑块、默认不抢视觉，悬浮时略微增强；不得使用浏览器默认粗重滚动条。
- 字体完全按 Arco Pro B 端密度控制：侧栏分组 13px/600，二级菜单 13px/400，顶部标题 20px/700，正文与表格 13px，辅助信息 12px。
- 行高和间距按参考图控制：侧栏一级 36-38px，二级 34-36px，菜单左右内边距克制，图标 14px，不做粗大图标和大字号菜单。
- 页面内容区保持浅灰画布 + 白色模块，卡片半径 6-8px，边框浅灰，阴影弱化，避免营销卡片感。
- 表格默认紧凑密度，重要状态用 Arco Tag/Badge，危险动作进 Popconfirm/Modal。
- 迁移后统一检查横向溢出、按钮文字溢出、表格列宽、中文显示、空数据状态。

## 组件映射

| 现有 Element Plus | 目标 Arco |
| --- | --- |
| `el-container / el-aside / el-header / el-main` | `a-layout / a-layout-sider / a-layout-header / a-layout-content` |
| `el-menu / el-sub-menu / el-menu-item` | `a-menu / a-sub-menu / a-menu-item` |
| `el-table` | `a-table` |
| `el-dialog` | `a-modal` |
| `el-form / el-form-item` | `a-form / a-form-item` |
| `el-input / el-select / el-input-number` | `a-input / a-select / a-input-number` |
| `el-button` | `a-button` |
| `el-tag` | `a-tag` |
| `el-progress` | `a-progress` |
| `ElMessage / ElMessageBox` | `Message / Modal` |
| `v-loading` | `a-spin` |
| Element Icons | Arco Icons |

## 分阶段路线

### 阶段 A：设计底座

- 引入 `@arco-design/web-vue`。
- 全局注册 Arco。
- 全局 App 壳层迁移到 Arco Layout/Menu/Header。
- 研发驾驶舱迁移为 Arco 样板页。
- 保留 Element Plus 过渡依赖，避免一次性破坏业务页。

验收：
- `/dashboard` 正常显示 Arco 驾驶舱。
- 菜单高亮、二级菜单、顶部栏、搜索、用户菜单正常。
- 页面无乱码、无横向溢出。
- `npm run build` 通过。

### 阶段 B：基础平台

优先迁移系统配置类页面，建立表格、弹窗、表单的标准写法。

- 用户管理
- 角色管理
- 基础配置
- 流程配置
- 接口配置

验收：
- 每个页面保留真实 CRUD。
- 新增、编辑、删除、子表维护可用。
- 表格操作列固定，按钮密度合理。

### 阶段 C：主数据中心

- 产品库
- 产品详情
- 需求规格
- 研发物料
- 文档管理
- 版本基线

验收：
- 产品详情能聚合 BOM、文档、变更、质量摘要。
- 主数据表格支持筛选/搜索入口。
- 分类、生命周期、编码规则逐步接入基础配置。

### 阶段 D：BOM、工艺、流程闭环

- 设计 BOM
- 工艺路线
- 审批工作台
- 工程变更
- 项目管理
- 质量追溯
- 集成队列

验收：
- BOM 明细、提交、流程待办、发布、集成队列不回退。
- 工作流操作使用统一 Arco Modal/Message。
- 工程变更和质量问题页面保持对象联动。

### 阶段 E：清理与优化

- 删除 Element Plus 组件使用。
- 删除 Element Plus 依赖和旧样式。
- Arco 按需引入或手动分包，降低主包体积。
- 暗色能力保留为后续可选主题，不作为默认全局主题。

验收：
- `rg "el-|element-plus|@element-plus" frontend/src frontend/package.json` 无业务依赖。
- `npm run build` 通过。
- 浏览器检查核心页面：dashboard、products、boms、documents、workbench、admin/foundation。

## 当前状态

- 已安装 `@arco-design/web-vue`。
- 已完成研发驾驶舱 Arco 样板页。
- 已完成全局 App 壳层迁移到 Arco。
- 已确认默认视觉方向：Arco Design Pro 风格浅色侧栏 + 浅色高密度工作区。
- 已按参考后台图收紧视觉密度：侧栏 212px、顶部栏 54px、一级菜单 13px、二级菜单 12px、表格/内容区使用浅灰画布与细滚动条；滚动条为 5-6px 浅灰低干扰样式。
- 已启动轻量权限闭环：后端提供当前用户会话和权限包，前端按角色权限过滤菜单；默认单机模式通过右上角切换用户模拟岗位视角。
- 下一步：迁移基础平台页面，优先 `/admin/foundation`，再做用户、角色、流程配置。
