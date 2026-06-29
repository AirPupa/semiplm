from datetime import date

from sqlalchemy.orm import Session

from . import models


PRODUCTS = [
    ("OPTO-0001", "PD-1550-10G", "1550nm InGaAs 高速光电探测器", "光电探测器", "InP/InGaAs PIN", "4 inch", "TO-CAN / COC", "通信级", "工业级", "光通信接收", "试产", "罗富森", "CUS-PD-1550", "OE-PD1550-10G", "A2", 78, "2026-05-18"),
    ("OPTO-0002", "VCSEL-940-3W", "940nm VCSEL 阵列芯片", "VCSEL", "GaAs VCSEL", "6 inch", "裸 Die / COB", "消费级", "量产级", "3D 感知/照明", "量产", "房磊", "CUS-VCSEL-940", "OE-VCSEL940-3W", "B4", 91, "2026-06-08"),
    ("OPTO-0003", "DFB-1310-25G", "1310nm DFB 激光器芯片", "DFB 激光器", "InP DFB", "4 inch", "COC / Butterfly", "通信级", "工业级", "光模块发射端", "验证", "于帅兵", "CUS-DFB-1310", "OE-DFB1310-25G", "A1", 63, "2026-04-29"),
    ("OPTO-0004", "LED-MICRO-RGB", "Micro LED RGB 外延片", "Micro LED", "GaN on Sapphire", "6 inch", "Wafer / Chiplet", "显示级", "量产导入", "微显示", "设计中", "张昊", "CUS-MLED-RGB", "OE-MLED-RGB", "P3", 42, "2026-03-22"),
    ("OPTO-0005", "SiPh-MZM-400G", "400G 硅光调制器芯片", "硅光芯片", "SOI Silicon Photonics", "8 inch", "裸 Die / CPO", "通信级", "工程样片", "数据中心互连", "流片", "张昊", "CUS-SIPH-400G", "OE-SIPH-MZM400", "T0", 56, "2026-05-30"),
]


def seed_database(db: Session) -> None:
    existing = db.query(models.Product).first()
    if existing and existing.code.startswith("OPTO-"):
        if not db.query(models.Role).first():
            seed_platform_data(db)
            db.commit()
        if not db.query(models.CodingRule).first():
            seed_foundation_config(db)
            db.commit()
        if not db.query(models.Requirement).first():
            seed_commercial_plm_data(db, db.query(models.Product).order_by(models.Product.id).all())
            db.commit()
        seed_product_versions(db, db.query(models.Product).order_by(models.Product.id).all())
        db.commit()
        if not db.query(models.ChangeAction).first():
            seed_change_execution_data(db)
            db.commit()
        return
    if existing:
        for model in [
            models.IntegrationEndpoint,
            models.WorkflowLog,
            models.WorkflowTask,
            models.WorkflowInstance,
            models.WorkflowNode,
            models.WorkflowTemplate,
            models.Role,
            models.Organization,
            models.DictionaryItem,
            models.LifecycleState,
            models.LifecycleTemplate,
            models.AttributeTemplate,
            models.CategoryTemplate,
            models.CodingRule,
            models.IntegrationJob,
            models.ChangeAction,
            models.BaselineItem,
            models.ProductBaseline,
            models.Requirement,
            models.Approval,
            models.ChangeImpact,
            models.Change,
            models.BomItem,
            models.BomHeader,
            models.Document,
            models.ProcessStep,
            models.ProcessRoute,
            models.ProjectTask,
            models.Project,
            models.QualityLot,
            models.QualityIssue,
            models.Material,
            models.Product,
            models.User,
        ]:
            db.query(model).delete()
        db.commit()

    users = [
        models.User(username="admin", display_name="系统管理员", role="管理员", department="生产部"),
        models.User(username="luofusen", display_name="罗富森", role="工艺工程师", department="生产部"),
        models.User(username="yushuaibing", display_name="于帅兵", role="工艺工程师", department="生产部"),
        models.User(username="zhanghao", display_name="张昊", role="工艺工程师", department="生产部"),
        models.User(username="fanglei", display_name="房磊", role="项目经理", department="生产部"),
        models.User(username="liangweiwei", display_name="梁维维", role="IT工程师", department="生产部"),
    ]
    db.add_all(users)
    seed_platform_data(db)
    seed_foundation_config(db)

    materials = [
        ("MAT-WAF-INP", "InP 外延片", "衬底/外延", "4 inch / InGaAs PIN epi", "华东外延", "高"),
        ("MAT-WAF-GAAS", "GaAs 外延片", "衬底/外延", "6 inch / VCSEL epi", "星源外延", "高"),
        ("MAT-MASK-OPTO", "光刻掩膜版", "Mask", "i-line / Stepper / Rev.A2", "睿芯光罩", "高"),
        ("MAT-PR-365", "正性光刻胶", "光刻材料", "365nm i-line / 1.2um", "科材化学", "中"),
        ("MAT-TIO2", "Ti/Pt/Au 金属靶材", "镀膜材料", "PVD / Ohmic contact", "华材电子", "中"),
        ("MAT-SIO2-PECVD", "SiO2 镀膜材料", "介质膜材料", "PECVD / Passivation", "安捷材料", "中"),
        ("MAT-ICP-GAS", "ICP 刻蚀气体", "刻蚀材料", "Cl2/BCl3/Ar", "中芯气体", "中"),
        ("MAT-TEST-PROBE", "光电测试探针卡", "测试治具", "Wafer-level LIV / IV", "精测科技", "中"),
    ]
    for row in materials:
        db.add(models.Material(code=row[0], name=row[1], category=row[2], specification=row[3], supplier=row[4], risk_level=row[5]))

    product_entities: list[models.Product] = []
    for row in PRODUCTS:
        product = models.Product(
            code=row[0],
            model=row[1],
            name=row[2],
            product_type=row[3],
            process_platform=row[4],
            wafer_size=row[5],
            package_type=row[6],
            temperature_grade=row[7],
            quality_grade=row[8],
            application=row[9],
            lifecycle=row[10],
            owner=row[11],
            customer_part_no=row[12],
            internal_part_no=row[13],
            version=row[14],
            readiness=row[15],
            latest_release=row[16],
        )
        product_entities.append(product)
        db.add(product)
    db.flush()

    for product in product_entities:
        bom = models.BomHeader(product_id=product.id, bom_type="EBOM", version=product.version, status="已发布" if product.lifecycle == "量产" else "审批中", owner=product.owner, release_date=product.latest_release)
        db.add(bom)
        db.flush()
        for idx, item in enumerate([
            ("MAT-WAF-INP", f"{product.process_platform} 外延片", "衬底/外延", product.wafer_size, 1, "片", "EPI", "外延来料"),
            ("MAT-MASK-OPTO", f"{product.model} 光刻掩膜版", "Mask", product.version, 1, "套", "PHOTO", "光刻"),
            ("MAT-PR-365", "i-line 光刻胶", "光刻材料", "1.2um", 1, "批", "PHOTO", "涂胶显影"),
            ("MAT-TIO2", "Ti/Pt/Au 金属靶材", "镀膜材料", "PVD", 1, "批", "PVD", "金属镀膜"),
            ("MAT-SIO2-PECVD", "SiO2 钝化膜材料", "介质膜材料", "PECVD", 1, "批", "FILM", "介质镀膜"),
            ("MAT-ICP-GAS", "ICP 刻蚀气体", "刻蚀材料", "Cl2/BCl3/Ar", 1, "批", "ETCH", "干法刻蚀"),
            ("MAT-TEST-PROBE", "光电测试探针卡", "测试治具", "LIV/IV/Wafer map", 1, "套", "WAT", "晶圆测试"),
        ], start=1):
            db.add(models.BomItem(
                bom_id=bom.id,
                parent_id=None,
                material_code=item[0],
                material_name=item[1],
                category=item[2],
                specification=item[3],
                quantity=item[4],
                unit=item[5],
                position=item[6],
                process_step=item[7],
                substitute="待评估" if idx == 2 else "",
                status="有效",
            ))

        docs = [
            ("SPEC", "光电性能规格书", "产品规格", "已发布"),
            ("PROC", "光刻刻蚀镀膜流程卡", "工艺文件", "审批中"),
            ("TEST", "LIV/IV/光谱测试规范", "测试报告", "已发布"),
            ("REL", "高温老化可靠性报告", "可靠性报告", "编制中"),
            ("MASK", "Mask Layer 对照表", "设计资料", "已发布"),
        ]
        for prefix, title, category, status in docs:
            db.add(models.Document(
                product_id=product.id,
                doc_no=f"DOC-{product.model}-{prefix}",
                title=f"{product.model} {title}",
                category=category,
                version=product.version,
                status=status,
                owner=product.owner,
                approval_status="已签核" if status == "已发布" else "流转中",
                updated_at=product.latest_release,
            ))

        route = models.ProcessRoute(product_id=product.id, route_no=f"ROUTE-{product.model}", name=f"{product.model} 光电芯片制造路线", version=product.version, status="有效", owner="罗富森")
        db.add(route)
        db.flush()
        for seq, step in enumerate([
            ("外延来料", "Epi wafer incoming", "PL Mapping、厚度、载流子浓度、缺陷密度"),
            ("光刻", "涂胶/曝光/显影", "CD、Overlay、曝光剂量、显影时间 SPC 管控"),
            ("刻蚀", "ICP/RIE 干法刻蚀", "Etch depth、侧壁角、选择比、End point"),
            ("镀膜", "PVD/PECVD 金属与介质膜", "膜厚、折射率、片阻、应力"),
            ("清洗", "湿法清洗/去胶", "颗粒、残胶、金属污染控制"),
            ("量测", "膜厚/CD/台阶仪/显微检查", "关键尺寸和膜厚 Cpk 监控"),
            ("晶圆测试", "LIV/IV/光谱/Wafer map", "阈值电流、响应度、暗电流、波长"),
            ("切割封装", product.package_type, "Die attach、Wire bond、耦合效率、外观全检"),
            ("可靠性", "老化/温循/湿热", "Burn-in、HTOL、TC、HAST 抽样验证"),
            ("出货检验", "OQC", "CoC、Wafer map、光电测试摘要归档"),
        ], start=10):
            db.add(models.ProcessStep(route_id=route.id, sequence=seq, stage=step[0], operation=step[1], key_params=step[2], owner="罗富森", status="有效"))

        change = models.Change(
            product_id=product.id,
            change_no=f"ECR-{product.model}-001",
            title=f"{product.model} 光刻版图与刻蚀窗口优化",
            change_type="光刻/刻蚀工艺变更",
            reason="试产批次边缘 Die 参数离散偏大，需要优化光刻 CD 目标和 ICP 刻蚀窗口。",
            status="审批中" if product.lifecycle != "量产" else "已关闭",
            priority="高" if product.lifecycle in ["试产", "量产"] else "中",
            owner=product.owner,
            submitted_at="2026-06-12",
            before_desc="光刻 CD 目标按 Rev.A1 控制，ICP 刻蚀时间窗口较窄，边缘片良率波动。",
            after_desc="更新 Mask Layer 注记，放宽并重定中心刻蚀窗口，新增膜厚和 CD 联动量测点。",
        )
        db.add(change)
        db.flush()
        for impact in [
            ("Mask 版本", f"{product.model} Mask {product.version}", "高", "更新光刻层别和版图注记"),
            ("工艺文件", "光刻刻蚀镀膜流程卡", "高", "更新 CD、刻蚀深度和膜厚控制计划"),
            ("在制批次", f"LOT-{product.model}-2606", "中", "试产批隔离追踪并补测 Wafer map"),
            ("客户项目", product.customer_part_no, "中", "验证完成后发出工艺变更通知"),
        ]:
            db.add(models.ChangeImpact(change_id=change.id, impact_type=impact[0], target=impact[1], risk=impact[2], action=impact[3]))
        for approval in [
            ("研发评审", product.owner, "已通过", "技术影响可控", "2026-06-13"),
            ("工艺评审", "罗富森", "已通过", "需补充封装参数卡", "2026-06-14"),
            ("质量评审", "于帅兵", "处理中", "", ""),
            ("项目批准", "房磊", "待处理", "", ""),
        ]:
            db.add(models.Approval(change_id=change.id, step_name=approval[0], approver=approval[1], status=approval[2], comment=approval[3], approved_at=approval[4]))

        for idx, yield_base in enumerate([94.2, 95.1, 93.7, 96.0], start=1):
            db.add(models.QualityLot(
                product_id=product.id,
                lot_no=f"LOT-{product.model}-260{idx}",
                wafer_id=f"W{idx:02d}-{product.model[-3:]}",
                stage="晶圆测试" if idx % 2 == 0 else "量测",
                cp_yield=yield_base,
                ft_yield=yield_base - 1.8,
                bin1_rate=yield_base - 0.6,
                issue_count=1 if idx == 3 else 0,
                status="异常跟进" if idx == 3 else "正常",
                tested_at=f"2026-06-{10 + idx}",
            ))

    project = models.Project(
        project_no="NPI-2026-061",
        name="1550nm 光电探测器工艺导入项目",
        product_model="PD-1550-10G",
        phase="试产",
        progress=68,
        owner="房磊",
        start_date="2026-03-01",
        end_date="2026-09-30",
        risk_level="中",
    )
    db.add(project)
    db.flush()
    for task in [
        ("光电规格冻结", "设计", "罗富森", "已完成", date(2026, 4, 15)),
        ("Mask 投版与首批试制", "流片", "罗富森", "已完成", date(2026, 5, 20)),
        ("光刻刻蚀窗口 DOE", "验证", "罗富森", "进行中", date(2026, 6, 28)),
        ("镀膜膜厚均匀性验证", "试产", "罗富森", "进行中", date(2026, 7, 12)),
        ("客户样品与可靠性资料包", "量产导入", "房磊", "未开始", date(2026, 8, 15)),
    ]:
        db.add(models.ProjectTask(project_id=project.id, name=task[0], phase=task[1], owner=task[2], status=task[3], due_date=task[4]))

    db.add(models.QualityIssue(
        issue_no="QIR-2026-0042",
        product_model="PD-1550-10G",
        lot_no="LOT-PD-1550-10G-2603",
        title="边缘 Wafer 暗电流偏高",
        severity="中",
        status="CAPA 执行中",
        owner="于帅兵",
        root_cause="初步定位为刻蚀后侧壁残留与钝化膜覆盖不足共同影响。",
        corrective_action="调整 ICP 清洗步骤和 PECVD 钝化膜厚，受影响 Wafer 追加 LIV/暗电流复测。",
    ))
    seed_commercial_plm_data(db, product_entities)
    seed_product_versions(db, product_entities)
    seed_change_execution_data(db)
    db.commit()


def seed_commercial_plm_data(db: Session, products: list[models.Product]) -> None:
    requirement_templates = [
        ("客户规格", "光电性能", "暗电流、响应度、带宽满足客户规格书冻结值", "高", "已确认", "规格书指标、CP/FT 测试规范、客户承认书三方一致"),
        ("NPI 阶段门", "制造可行性", "关键工序 Cpk 与良率达到试产放行阈值", "高", "验证中", "光刻 CD、刻蚀深度、膜厚均匀性连续三批达标"),
        ("质量体系", "可靠性", "HTOL、温循、湿热与老化试验按产品等级归档", "中", "进行中", "可靠性报告签核后纳入发布基线"),
    ]
    for product in products:
        for idx, row in enumerate(requirement_templates, start=1):
            db.add(models.Requirement(
                product_id=product.id,
                req_no=f"REQ-{product.model}-{idx:03d}",
                source=row[0],
                category=row[1],
                title=f"{product.model} {row[2]}",
                priority=row[3],
                status=row[4],
                owner=product.owner,
                acceptance_criteria=row[5],
            ))

        baseline = models.ProductBaseline(
            product_id=product.id,
            baseline_no=f"BL-{product.model}-{product.version}",
            name=f"{product.model} {product.lifecycle} 发布基线",
            version=product.version,
            status="已发布" if product.readiness >= 80 else "冻结评审中",
            created_by=product.owner,
            released_at=product.latest_release,
        )
        db.add(baseline)
        db.flush()
        for item in [
            ("产品", product.internal_part_no, product.name, product.version, product.lifecycle),
            ("EBOM", f"EBOM-{product.model}", f"{product.model} 工程 BOM", product.version, "已发布" if product.readiness >= 80 else "审批中"),
            ("工艺路线", f"ROUTE-{product.model}", f"{product.model} 光电芯片制造路线", product.version, "有效"),
            ("规格文档", f"DOC-{product.model}-SPEC", f"{product.model} 光电性能规格书", product.version, "已发布"),
            ("变更单", f"ECR-{product.model}-001", f"{product.model} 工艺窗口优化", "001", "已关闭" if product.lifecycle == "量产" else "审批中"),
        ]:
            db.add(models.BaselineItem(
                baseline_id=baseline.id,
                item_type=item[0],
                item_no=item[1],
                title=item[2],
                version=item[3],
                status=item[4],
            ))


def seed_product_versions(db: Session, products: list[models.Product]) -> None:
    if db.query(models.ProductVersion).first():
        return
    for product in products:
        db.add(models.ProductVersion(product_id=product.id, version="P1", lifecycle="设计中", readiness=30, released_at="2025-11-01", released_by="罗富森", summary="项目启动，完成概念设计评审。"))
        db.add(models.ProductVersion(product_id=product.id, version=product.version, lifecycle=product.lifecycle, readiness=product.readiness, released_at=product.latest_release, released_by=product.owner, source_change_no=f"ECR-{product.model}-001", summary=f"ECR 闭环后升版至 {product.version}。"))


def seed_change_execution_data(db: Session) -> None:
    changes = db.query(models.Change).join(models.Product).order_by(models.Change.id).all()
    for change in changes:
        product = change.product
        action_rows = [
            ("ECN通知", "受影响文档/流程卡签收", "生产部", "于帅兵", "进行中", "2026-06-20", "已通知质量、工艺、制造，等待可靠性报告复核。"),
            ("BOM更新", f"EBOM-{product.model}", "生产部", product.owner, "待处理", "2026-06-22", "根据影响分析更新 Mask 与工艺材料版本。"),
            ("工艺发布", f"ROUTE-{product.model}", "生产部", "罗富森", "待处理", "2026-06-24", "更新光刻 CD、ICP 刻蚀深度和 PECVD 膜厚控制窗口。"),
            ("制造切换", f"LOT-{product.model}-2606", "生产部", "房磊", "未开始", "2026-06-28", "按 ECN 生效批次隔离在制 Lot，并记录切换前后良率。"),
        ]
        for idx, row in enumerate(action_rows, start=1):
            db.add(models.ChangeAction(
                change_id=change.id,
                action_no=f"ECA-{change.change_no}-{idx:02d}",
                action_type=row[0],
                target_object=row[1],
                department=row[2],
                owner=row[3],
                status=row[4],
                due_date=row[5],
                result=row[6],
            ))

        for idx, row in enumerate([
            ("ERP", "物料/BOM", f"EBOM-{product.model}", "下发", "等待", "变更签核完成后下发 ERP 物料与 EBOM 版本。"),
            ("MES", "工艺路线", f"ROUTE-{product.model}", "下发", "等待", "ECN 生效后下发 MES 工艺路线和管制参数。"),
            ("QMS", "质量文件", f"DOC-{product.model}-REL", "下发", "等待", "可靠性报告签核后同步 QMS 归档。"),
        ], start=1):
            db.add(models.IntegrationJob(
                job_no=f"INT-{change.change_no}-{idx:02d}",
                target_system=row[0],
                object_type=row[1],
                object_no=row[2],
                product_model=product.model,
                direction=row[3],
                status=row[4],
                triggered_by=change.change_no,
                triggered_at=change.submitted_at,
                message=row[5],
            ))


def seed_platform_data(db: Session) -> None:
    roles = [
        ("ADMIN", "系统管理员", "系统配置、组织角色、接口配置、所有对象维护", "system,user,role,workflow,integration,all"),
        ("RD_ENGINEER", "研发工程师", "产品、需求、BOM、文档、变更申请维护", "product,requirement,bom,document,change"),
        ("PE_ENGINEER", "工艺工程师", "工艺路线、工艺参数、变更影响评估", "process,material,change,approval"),
        ("QA_ENGINEER", "质量工程师", "质量追溯、CAPA、文档/变更质量签核", "quality,document,change,approval"),
        ("PM_MANAGER", "项目经理", "NPI 项目、阶段门、计划和风险", "project,workflow,approval"),
        ("IT_ENGINEER", "IT工程师", "系统配置、组织用户角色、流程和接口维护", "organization,system,user,role,workflow,integration"),
        ("MES_INTERFACE", "MES接口账号", "工艺路线、ECN、Lot追溯数据接口", "integration,mes"),
        ("ERP_INTERFACE", "ERP接口账号", "物料、BOM、发布基线数据接口", "integration,erp"),
    ]
    for code, name, description, permissions in roles:
        db.add(models.Role(code=code, name=name, description=description, permissions=permissions, status="启用"))
    db.add(models.Organization(code="NZGD", name="南智光电", org_type="公司", parent_code="", manager="梁维维", status="启用", description="公司主体"))
    db.add(models.Organization(code="PROD", name="生产部", org_type="部门", parent_code="NZGD", manager="房磊", status="启用", description="生产运营部门"))

    templates = [
        (
            "WF-DOC-STD",
            "文档签核流程",
            "文档",
            "通用",
            "编制、研发审核、质量审核、文控发布",
            [("编制确认", "研发工程师", "提交", 8), ("研发审核", "研发工程师", "审批", 24), ("质量审核", "质量工程师", "审批", 24), ("文控发布", "系统管理员", "发布", 8)],
        ),
        (
            "WF-BOM-REL",
            "BOM发布流程",
            "BOM",
            "通用",
            "研发提交、工艺评估、质量审核、ERP下发",
            [("研发提交", "研发工程师", "提交", 8), ("工艺评估", "工艺工程师", "审批", 24), ("质量审核", "质量工程师", "审批", 24), ("ERP下发", "ERP接口账号", "接口", 4)],
        ),
        (
            "WF-ECR-ECN",
            "工程变更闭环流程",
            "变更",
            "通用",
            "ECR申请、影响分析、会签、ECN发布、ECA执行",
            [("ECR申请", "研发工程师", "提交", 8), ("影响分析", "工艺工程师", "评估", 24), ("质量会签", "质量工程师", "审批", 24), ("项目批准", "项目经理", "审批", 24), ("ECN发布", "系统管理员", "发布", 8), ("MES/ERP同步", "MES接口账号", "接口", 4)],
        ),
        (
            "WF-NPI-APQP",
            "APQP/NPI阶段门流程",
            "项目",
            "APQP",
            "概念、设计、流片、验证、试产、量产导入阶段门",
            [("项目立项", "项目经理", "审批", 24), ("设计冻结", "研发工程师", "审批", 24), ("流片评审", "工艺工程师", "审批", 24), ("可靠性评审", "质量工程师", "审批", 48), ("量产发布", "项目经理", "发布", 24)],
        ),
    ]
    for code, name, object_type, project_type, description, nodes in templates:
        template = models.WorkflowTemplate(code=code, name=name, object_type=object_type, project_type=project_type, status="启用", description=description)
        db.add(template)
        db.flush()
        for seq, node in enumerate(nodes, start=1):
            db.add(models.WorkflowNode(template_id=template.id, sequence=seq, name=node[0], role_name=node[1], action_type=node[2], sla_hours=node[3]))

    endpoints = [
        ("ERP-K3", "ERP物料/BOM接口", "ERP", "http://erp.local/api/plm", "Token", "下发", "罗富森", "物料、BOM、产品基线、ECN"),
        ("MES-MFG", "MES工艺/批次接口", "MES", "http://mes.local/api/plm", "Token", "双向", "罗富森", "工艺路线、ECN、生效批次、Lot/Wafer追溯"),
        ("QMS-DOC", "QMS文档/质量接口", "QMS", "http://qms.local/api/plm", "Token", "双向", "于帅兵", "文档、可靠性报告、质量问题、CAPA"),
    ]
    for code, name, system_type, base_url, auth_type, direction, owner, scope in endpoints:
        db.add(models.IntegrationEndpoint(code=code, name=name, system_type=system_type, base_url=base_url, auth_type=auth_type, direction=direction, status="启用", owner=owner, object_scope=scope))


def seed_foundation_config(db: Session) -> None:
    coding_rules = [
        ("产品", "CR-PRODUCT", "产品型号编码", "OPTO", "OPTO-{yyyy}-{seq:04d}", 5, "OPTO-2026-0006", "系统管理员"),
        ("研发物料", "CR-MATERIAL", "研发物料编码", "MAT", "MAT-{category}-{seq:04d}", 8, "MAT-WAF-0009", "系统管理员"),
        ("文档", "CR-DOCUMENT", "受控文档编码", "DOC", "DOC-{product}-{category}-{seq:03d}", 25, "DOC-PD1550-SPEC-026", "文控"),
        ("BOM", "CR-BOM", "BOM版本编码", "BOM", "{bom_type}-{product}-{version}", 5, "EBOM-PD1550-A3", "系统管理员"),
        ("变更", "CR-CHANGE", "工程变更编码", "ECR", "ECR-{product}-{seq:03d}", 5, "ECR-PD1550-006", "系统管理员"),
    ]
    for row in coding_rules:
        db.add(models.CodingRule(object_type=row[0], code=row[1], name=row[2], prefix=row[3], pattern=row[4], current_no=row[5], sample=row[6], status="启用", owner=row[7]))

    lifecycles = [
        ("LC-PRODUCT", "产品生命周期", "产品", "从设计、验证、试产到量产和停用"),
        ("LC-DOC", "文档生命周期", "文档", "编制、流转、发布、作废"),
        ("LC-BOM", "BOM生命周期", "BOM", "编制、审批、发布、冻结、作废"),
        ("LC-MATERIAL", "物料生命周期", "研发物料", "候选、有效、受限、停用"),
    ]
    state_map = {
        "LC-PRODUCT": [("设计中", "初始态", "是", "否", "验证"), ("验证", "中间态", "是", "是", "试产"), ("试产", "中间态", "是", "是", "量产"), ("量产", "发布态", "否", "是", "停用"), ("停用", "终止态", "否", "是", "")],
        "LC-DOC": [("编制中", "初始态", "是", "否", "审批中"), ("审批中", "流转态", "否", "是", "已发布,编制中"), ("已发布", "发布态", "否", "是", "作废"), ("作废", "终止态", "否", "是", "")],
        "LC-BOM": [("编制中", "初始态", "是", "否", "审批中"), ("审批中", "流转态", "否", "是", "已发布,编制中"), ("已发布", "发布态", "否", "是", "冻结,作废"), ("冻结", "锁定态", "否", "是", "作废"), ("作废", "终止态", "否", "是", "")],
        "LC-MATERIAL": [("候选", "初始态", "是", "否", "有效"), ("有效", "发布态", "是", "是", "受限,停用"), ("受限", "中间态", "是", "是", "有效,停用"), ("停用", "终止态", "否", "是", "")],
    }
    lifecycle_by_code: dict[str, models.LifecycleTemplate] = {}
    for code, name, object_type, description in lifecycles:
        template = models.LifecycleTemplate(code=code, name=name, object_type=object_type, status="启用", description=description)
        db.add(template)
        db.flush()
        lifecycle_by_code[code] = template
        for seq, state in enumerate(state_map[code], start=1):
            db.add(models.LifecycleState(template_id=template.id, sequence=seq, name=state[0], state_type=state[1], allow_edit=state[2], require_workflow=state[3], next_states=state[4]))

    categories = [
        ("产品", "CAT-PROD-PD", "光电探测器", "", "LC-PRODUCT", "CR-PRODUCT", "InP/InGaAs PIN、APD、SiPM 等探测器类产品"),
        ("产品", "CAT-PROD-LASER", "激光器/VCSEL", "", "LC-PRODUCT", "CR-PRODUCT", "DFB、VCSEL、EML 等发射类芯片"),
        ("研发物料", "CAT-MAT-WAFER", "衬底/外延", "", "LC-MATERIAL", "CR-MATERIAL", "InP、GaAs、SOI、GaN 外延片"),
        ("研发物料", "CAT-MAT-PHOTO", "光刻材料", "", "LC-MATERIAL", "CR-MATERIAL", "光刻胶、显影液、掩膜版"),
        ("文档", "CAT-DOC-SPEC", "产品规格", "", "LC-DOC", "CR-DOCUMENT", "客户规格、内部规格、承认书"),
        ("文档", "CAT-DOC-PROC", "工艺文件", "", "LC-DOC", "CR-DOCUMENT", "流程卡、控制计划、作业指导书"),
        ("BOM", "CAT-BOM-EBOM", "设计EBOM", "", "LC-BOM", "CR-BOM", "研发设计物料结构"),
    ]
    category_by_code: dict[str, models.CategoryTemplate] = {}
    for row in categories:
        category = models.CategoryTemplate(object_type=row[0], code=row[1], name=row[2], parent_code=row[3], lifecycle_template=row[4], coding_rule=row[5], status="启用", description=row[6])
        db.add(category)
        db.flush()
        category_by_code[row[1]] = category

    attributes = {
        "CAT-PROD-PD": [("工艺平台", "process_platform", "枚举", "是", "DICT_PROCESS_PLATFORM", "InP/InGaAs PIN"), ("晶圆尺寸", "wafer_size", "枚举", "是", "DICT_WAFER_SIZE", "4 inch"), ("封装形式", "package_type", "枚举", "否", "DICT_PACKAGE_TYPE", "")],
        "CAT-PROD-LASER": [("发射波长", "wavelength", "文本", "是", "", "1310nm"), ("输出功率", "optical_power", "文本", "否", "", ""), ("工艺平台", "process_platform", "枚举", "是", "DICT_PROCESS_PLATFORM", "")],
        "CAT-MAT-WAFER": [("规格", "specification", "文本", "是", "", ""), ("供应商", "supplier", "文本", "是", "", ""), ("风险等级", "risk_level", "枚举", "是", "DICT_RISK_LEVEL", "高")],
        "CAT-MAT-PHOTO": [("有效期", "shelf_life", "文本", "否", "", ""), ("存储条件", "storage", "文本", "否", "", ""), ("风险等级", "risk_level", "枚举", "是", "DICT_RISK_LEVEL", "中")],
        "CAT-DOC-SPEC": [("文档版本", "version", "文本", "是", "", "A0"), ("签核状态", "approval_status", "枚举", "是", "DICT_APPROVAL_STATUS", "未提交")],
        "CAT-DOC-PROC": [("适用工艺平台", "process_platform", "枚举", "是", "DICT_PROCESS_PLATFORM", ""), ("签核状态", "approval_status", "枚举", "是", "DICT_APPROVAL_STATUS", "未提交")],
        "CAT-BOM-EBOM": [("BOM类型", "bom_type", "枚举", "是", "DICT_BOM_TYPE", "EBOM"), ("版本", "version", "文本", "是", "", "A0")],
    }
    for category_code, rows in attributes.items():
        category = category_by_code[category_code]
        for seq, row in enumerate(rows, start=1):
            db.add(models.AttributeTemplate(category_id=category.id, name=row[0], field_key=row[1], data_type=row[2], required=row[3], dictionary_code=row[4], default_value=row[5], sequence=seq))

    dictionaries = [
        ("DICT_PROCESS_PLATFORM", "工艺平台", "InP/InGaAs PIN", "InP/InGaAs PIN", "产品/工艺"),
        ("DICT_PROCESS_PLATFORM", "工艺平台", "GaAs VCSEL", "GaAs VCSEL", "产品/工艺"),
        ("DICT_PROCESS_PLATFORM", "工艺平台", "SOI Silicon Photonics", "SOI Silicon Photonics", "产品/工艺"),
        ("DICT_WAFER_SIZE", "晶圆尺寸", "4 inch", "4 inch", "产品/物料"),
        ("DICT_WAFER_SIZE", "晶圆尺寸", "6 inch", "6 inch", "产品/物料"),
        ("DICT_WAFER_SIZE", "晶圆尺寸", "8 inch", "8 inch", "产品/物料"),
        ("DICT_PACKAGE_TYPE", "封装形式", "TO-CAN", "TO-CAN", "产品"),
        ("DICT_PACKAGE_TYPE", "封装形式", "COC", "COC", "产品"),
        ("DICT_PACKAGE_TYPE", "封装形式", "CPO", "CPO", "产品"),
        ("DICT_RISK_LEVEL", "风险等级", "高", "高", "物料/变更"),
        ("DICT_RISK_LEVEL", "风险等级", "中", "中", "物料/变更"),
        ("DICT_RISK_LEVEL", "风险等级", "低", "低", "物料/变更"),
        ("DICT_APPROVAL_STATUS", "签核状态", "未提交", "未提交", "文档/BOM"),
        ("DICT_APPROVAL_STATUS", "签核状态", "流转中", "流转中", "文档/BOM"),
        ("DICT_APPROVAL_STATUS", "签核状态", "已签核", "已签核", "文档/BOM"),
        ("DICT_BOM_TYPE", "BOM类型", "EBOM", "设计EBOM", "BOM"),
        ("DICT_BOM_TYPE", "BOM类型", "PBOM", "工艺PBOM", "BOM"),
    ]
    for seq, row in enumerate(dictionaries, start=1):
        db.add(models.DictionaryItem(dict_code=row[0], dict_name=row[1], item_value=row[2], item_label=row[3], object_scope=row[4], sequence=seq, status="启用"))

    if not db.query(models.SystemParameter).first():
        params = [
            ("COMPANY_NAME", "南智光电", "组织", "公司名称"),
            ("DEFAULT_DEPT", "生产部", "组织", "默认部门"),
            ("FILE_STORAGE", "./data/files", "存储", "文件存储路径"),
            ("DATE_FORMAT", "YYYY-MM-DD", "系统", "日期格式"),
            ("PREFIX_PRODUCT", "OPTO", "编码", "产品编码前缀"),
            ("PREFIX_ECR", "ECR", "编码", "变更单编码前缀"),
        ]
        for key, value, group, desc in params:
            db.add(models.SystemParameter(param_key=key, param_value=value, param_group=group, description=desc))

    if not db.query(models.Supplier).first():
        suppliers = [
            ("华东外延", "华东外延", "外延片", "王经理", "021-8888", "wang@hdepi.com", "上海临港", "ISO9001", "高"),
            ("星源外延", "星源外延", "外延片", "刘经理", "010-7777", "liu@xingyuan.com", "北京亦庄", "ISO9001", "中"),
            ("睿芯光罩", "睿芯光罩", "光罩/Mask", "陈工", "0755-6666", "chen@ruixin.com", "深圳南山", "ISO9001", "中"),
            ("滨松电子", "滨松电子", "测试设备", "张工", "021-5555", "zhang@hamamatsu.cn", "上海浦东", "ISO13485", "低"),
        ]
        for code, name, stype, contact, phone, email, address, cert, risk in suppliers:
            db.add(models.Supplier(code=code, name=name, supplier_type=stype, contact=contact, phone=phone, email=email, address=address, certification=cert, risk_level=risk, status="启用"))

    if not db.query(models.SubstituteMaterial).first():
        db.add(models.SubstituteMaterial(material_code="MAT-WAF-INP", material_name="InP 外延片", substitute_code="MAT-WAF-GAAS", substitute_name="GaAs 外延片", substitute_type="功能替代", strategy="一对一", risk_level="高", status="启用", description="用于 PIN 低速探测器的应急替代方案。"))
        db.add(models.SubstituteMaterial(material_code="MAT-MASK-BLANK", material_name="空白掩膜版", substitute_code="MAT-MASK-OPTO", substitute_name="光刻掩膜版", substitute_type="兼容替代", strategy="多对一", risk_level="中", status="启用", description="部分非关键层可使用空白版替代。"))

    if not db.query(models.ProjectTemplate).first():
        db.add(models.ProjectTemplate(code="NPI-STANDARD", name="标准 NPI 模板", description="光电芯片标准 NPI 流程", stages='["概念","设计","流片","验证","试产","量产导入"]', status="启用"))

    if not db.query(models.QualityCAPA).first():
        issues = db.query(models.QualityIssue).filter(models.QualityIssue.status != "已关闭").order_by(models.QualityIssue.id).limit(3).all()
        for idx, issue in enumerate(issues, start=1):
            db.add(models.QualityCAPA(capa_no=f"CAPA-{idx:04d}", issue_id=issue.id, title=f"CAPA: {issue.title}", source="质量问题", root_cause=issue.root_cause, corrective_action=issue.corrective_action, owner=issue.owner, status="待处理"))

