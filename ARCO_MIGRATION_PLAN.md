# SemiPLM UI 风格规范

## 目标

SemiPLM 的界面以业务可用和高密度为主，不追求统一组件库。现阶段保留 Element Plus 与 Arco 的并存状态，优先保证页面像商用后台，而不是为了迁移而改造。

产品级页面行为、列表契约、表单规则、权限反馈和文件交互以 `PRODUCT_SPEC.md` 为准；本文档只记录组件迁移时的 UI 风格和组件映射。

## 规范原则

- 业务页优先参考现有设计 BOM 页面风格。
- 已稳定且可用的页面，不因为组件库切换而重写。
- 新页面或新改页要保持和现有业务页一致的表格密度、操作列宽度、弹窗表单节奏。
- 页面不做营销风，不做大卡片堆砌；PLM 页面以表格、详情、操作区、状态反馈为主。
- 视觉基准使用浅色、高密度、低干扰的企业后台风格。
- 菜单滚动条、按钮间距、表格行高、标签密度都要控制在业务软件的扫描效率范围内。
- 迁移组件时，必须整页保持业务动作完整，不能出现半页一个体系、半页另一个体系。
- 只有在不破坏页面体验的前提下，才逐步减少 Element Plus 使用。

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

## 当前状态

- 业务页当前允许 Element Plus 与 Arco 并存。
- 设计 BOM 等现有业务页风格作为当前参考基准。
- 新页面和大改页面需要优先保持业务一致性，再谈组件统一。
- 后续如果做 UI 调整，应先验证密度、操作列和弹窗表单是否符合现有业务页节奏。
