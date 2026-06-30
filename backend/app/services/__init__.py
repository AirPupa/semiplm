"""跨域业务逻辑服务层。

按职责拆分：
- helpers: 通用工具（提交、审计日志、用户字典、模型更新、日期、存在性校验）
- versioning: 对象升版与版本号生成
- workflow: 流程引擎（启动/完成/撤回/日志/项目交付物联动）
- change: 工程变更影响分析与 ECA 执行动作
- integration: 集成队列创建
- process: 工艺路线校验与 BOM 工序绑定
- bootstrap: 启动时 schema 与主数据归一化

依赖方向：services/* 只依赖 models.py 与 deps.py，不依赖 routers/。
"""
