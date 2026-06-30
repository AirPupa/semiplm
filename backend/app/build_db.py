"""SemiPLM 数据库构建脚本（CLI，不在启动时运行）。

两个制品：
- semiplm_clean.db : 建表 + admin 账号 + 系统主数据（角色/组织/流程/编码规则/生命周期/分类属性/数据字典/系统参数/供应商/替代料/项目模板/工艺参数库）
- semiplm_demo.db  : clean 基础上 + 业务演示数据（6用户/物料/5产品/三层BOM/文档/变更/质量/项目/流程/集成/PR）

用法：
    python -m app.build_db --clean    # 生成 semiplm_clean.db
    python -m app.build_db --demo     # 生成 semiplm_demo.db
    python -m app.build_db --all      # 两个都生成

部署时挂载对应 .db 文件即可，启动不跑任何数据灌入逻辑。
"""

import argparse
import os
from datetime import date

from sqlalchemy.orm import Session

from . import models
from .database import Base, SessionLocal, engine as default_engine
from sqlalchemy import create_engine


# ============================================================
# 常量定义
# ============================================================

# clean 只含 admin，demo 含全部 7 个用户
ADMIN_USER = ("admin", "系统管理员", "管理员", "生产部")

DEMO_USERS = [
    ("luofusen", "罗富森", "工艺工程师", "生产部"),
    ("yushuaibing", "于帅兵", "工艺工程师", "生产部"),
    ("zhanghao", "张昊", "工艺工程师", "生产部"),
    ("fanglei", "房磊", "项目经理", "生产部"),
    ("liangweiwei", "梁维维", "IT工程师", "生产部"),
    ("lichao", "李超", "质量工程师", "生产部"),
]

# (code, model, name, type, platform, wafer, package, temp_grade, quality_grade, app, lifecycle, owner, cust_part, internal_part, version, readiness, release_date)
PRODUCTS = [
    ("OPTO-0001", "PD-1550-10G", "1550nm InGaAs 高速光电探测器", "光电探测器", "InP/InGaAs PIN", "4 inch", "TO-CAN / COC", "通信级", "工业级", "光通信接收", "试产", "罗富森", "CUS-PD-1550", "OE-PD1550-10G", "A2", 78, "2026-05-18"),
    ("OPTO-0002", "VCSEL-940-3W", "940nm VCSEL 阵列芯片", "VCSEL", "GaAs VCSEL", "6 inch", "裸 Die / COB", "消费级", "量产级", "3D 感知/照明", "量产", "房磊", "CUS-VCSEL-940", "OE-VCSEL940-3W", "B4", 91, "2026-06-08"),
    ("OPTO-0003", "DFB-1310-25G", "1310nm DFB 激光器芯片", "DFB 激光器", "InP DFB", "4 inch", "COC / Butterfly", "通信级", "工业级", "光模块发射端", "验证", "于帅兵", "CUS-DFB-1310", "OE-DFB1310-25G", "A1", 63, "2026-04-29"),
    ("OPTO-0004", "LED-MICRO-RGB", "Micro LED RGB 外延片", "Micro LED", "GaN on Sapphire", "6 inch", "Wafer / Chiplet", "显示级", "量产导入", "微显示", "设计中", "张昊", "CUS-MLED-RGB", "OE-MLED-RGB", "P3", 42, "2026-03-22"),
    ("OPTO-0005", "SiPh-MZM-400G", "400G 硅光调制器芯片", "硅光芯片", "SOI Silicon Photonics", "8 inch", "裸 Die / CPO", "通信级", "工程样片", "数据中心互连", "流片", "张昊", "CUS-SIPH-400G", "OE-SIPH-MZM400", "T0", 56, "2026-05-30"),
]

MATERIALS = [
    ("MAT-WAF-INP", "InP 外延片", "衬底/外延", "4 inch / InGaAs PIN epi", "华东外延", "高"),
    ("MAT-WAF-GAAS", "GaAs 外延片", "衬底/外延", "6 inch / VCSEL epi", "星源外延", "高"),
    ("MAT-WAF-SOI", "SOI 硅光晶圆", "衬底/外延", "8 inch / SOI", "沪硅产业", "高"),
    ("MAT-WAF-GAN", "GaN on Sapphire 外延片", "衬底/外延", "6 inch / Micro LED", "三安光电", "高"),
    ("MAT-MASK-OPTO", "光刻掩膜版", "Mask", "i-line / Stepper / Rev.A2", "睿芯光罩", "高"),
    ("MAT-PR-365", "正性光刻胶", "光刻材料", "365nm i-line / 1.2um", "科材化学", "中"),
    ("MAT-TIO2", "Ti/Pt/Au 金属靶材", "镀膜材料", "PVD / Ohmic contact", "华材电子", "中"),
    ("MAT-SIO2-PECVD", "SiO2 镀膜材料", "介质膜材料", "PECVD / Passivation", "安捷材料", "中"),
    ("MAT-ICP-GAS", "ICP 刻蚀气体", "刻蚀材料", "Cl2/BCl3/Ar", "中芯气体", "中"),
    ("MAT-TEST-PROBE", "光电测试探针卡", "测试治具", "Wafer-level LIV / IV", "精测科技", "中"),
]

# 工艺路线标准 10 工序
PROCESS_STEPS = [
    ("外延来料", "Epi wafer incoming", "PL Mapping、厚度、载流子浓度、缺陷密度"),
    ("光刻", "涂胶/曝光/显影", "CD、Overlay、曝光剂量、显影时间 SPC 管控"),
    ("刻蚀", "ICP/RIE 干法刻蚀", "Etch depth、侧壁角、选择比、End point"),
    ("镀膜", "PVD/PECVD 金属与介质膜", "膜厚、折射率、片阻、应力"),
    ("清洗", "湿法清洗/去胶", "颗粒、残胶、金属污染控制"),
    ("量测", "膜厚/CD/台阶仪/显微检查", "关键尺寸和膜厚 Cpk 监控"),
    ("晶圆测试", "LIV/IV/光谱/Wafer map", "阈值电流、响应度、暗电流、波长"),
    ("切割封装", "Die attach / Wire bond", "耦合效率、外观全检"),
    ("可靠性", "老化/温循/湿热", "Burn-in、HTOL、TC、HAST 抽样验证"),
    ("出货检验", "OQC", "CoC、Wafer map、光电测试摘要归档"),
]

# EBOM 标准 7 项物料
EBOM_ITEMS = [
    ("MAT-WAF-INP", "外延片", "衬底/外延", "wafer", 1, "片", "EPI", "外延来料"),
    ("MAT-MASK-OPTO", "光刻掩膜版", "Mask", "Rev.A2", 1, "套", "PHOTO", "光刻"),
    ("MAT-PR-365", "i-line 光刻胶", "光刻材料", "1.2um", 1, "批", "PHOTO", "涂胶显影"),
    ("MAT-TIO2", "Ti/Pt/Au 金属靶材", "镀膜材料", "PVD", 1, "批", "PVD", "金属镀膜"),
    ("MAT-SIO2-PECVD", "SiO2 钝化膜材料", "介质膜材料", "PECVD", 1, "批", "FILM", "介质镀膜"),
    ("MAT-ICP-GAS", "ICP 刻蚀气体", "刻蚀材料", "Cl2/BCl3/Ar", 1, "批", "ETCH", "干法刻蚀"),
    ("MAT-TEST-PROBE", "光电测试探针卡", "测试治具", "LIV/IV/Wafer map", 1, "套", "WAT", "晶圆测试"),
]


# ============================================================
# 主入口
# ============================================================

# ============================================================
# 构建入口
# ============================================================

def build_clean(db: Session) -> None:
    """构建 clean 数据库：建表 + admin + 系统主数据。不含业务数据。"""
    _clear_all(db)
    db.add(models.User(username=ADMIN_USER[0], display_name=ADMIN_USER[1], role=ADMIN_USER[2], department=ADMIN_USER[3]))
    _seed_platform(db)
    _seed_foundation(db)
    _seed_process_parameters(db)
    db.commit()


def build_demo(db: Session) -> None:
    """构建 demo 数据库：clean 基础上 + 全部业务演示数据。"""
    build_clean(db)
    # 追加演示用户（admin 已在 clean 中创建）
    for username, display, role, dept in DEMO_USERS:
        db.add(models.User(username=username, display_name=display, role=role, department=dept))
    _seed_materials(db)
    products = _seed_products(db)
    _seed_product_versions(db, products)
    routes_by_product = _seed_process_routes(db, products)
    boms_by_product = _seed_boms(db, products, routes_by_product)
    _seed_documents(db, products)
    changes_by_product = _seed_changes(db, products)
    _seed_quality(db, products)
    _seed_requirements(db, products)
    _seed_baselines(db, products)
    _seed_projects(db, products, boms_by_product)
    _seed_workflow_instances(db, products, changes_by_product, boms_by_product)
    _seed_integration_jobs(db, products, changes_by_product)
    _seed_problem_reports(db, products)
    db.commit()


def _build_to_file(target: str, build_fn) -> str:
    """构建到指定 .db 文件。返回文件路径。"""
    db_path = os.path.join(os.getcwd(), target)
    if os.path.exists(db_path):
        os.remove(db_path)
    tmp_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=tmp_engine)
    from sqlalchemy.orm import sessionmaker
    TmpSession = sessionmaker(autocommit=False, autoflush=False, bind=tmp_engine)
    db = TmpSession()
    try:
        build_fn(db)
    finally:
        db.close()
    print(f"[OK] {target} built ({os.path.getsize(db_path) // 1024} KB)")
    return db_path


def main():
    parser = argparse.ArgumentParser(description="SemiPLM 数据库构建")
    parser.add_argument("--clean", action="store_true", help="构建 semiplm_clean.db（建表+主数据）")
    parser.add_argument("--demo", action="store_true", help="构建 semiplm_demo.db（clean+业务演示数据）")
    parser.add_argument("--all", action="store_true", help="构建两个 .db")
    args = parser.parse_args()

    if not (args.clean or args.demo or args.all):
        parser.print_help()
        return

    if args.clean or args.all:
        _build_to_file("semiplm_clean.db", build_clean)
    if args.demo or args.all:
        _build_to_file("semiplm_demo.db", build_demo)


# ============================================================
# 清空
# ============================================================

def _clear_all(db: Session) -> None:
    for model in [
        models.DocumentDistribution,
        models.Attachment,
        models.ReportSnapshot,
        models.QualityReport,
        models.IntegrationJob,
        models.WorkflowLog,
        models.WorkflowTask,
        models.WorkflowInstance,
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
        models.ProjectDeliverable,
        models.ProjectRisk,
        models.Project,
        models.QualityLot,
        models.QualityIssue,
        models.QualityCAPA,
        models.Material,
        models.ProblemReport,
        models.ProcessParameter,
        models.ProductVersion,
        models.Product,
        models.SubstituteMaterial,
        models.Supplier,
        models.SystemParameter,
        models.ProjectTemplate,
        models.DictionaryItem,
        models.LifecycleState,
        models.LifecycleTemplate,
        models.AttributeTemplate,
        models.CategoryTemplate,
        models.CodingRule,
        models.IntegrationEndpoint,
        models.WorkflowNode,
        models.WorkflowTemplate,
        models.Role,
        models.Organization,
        models.User,
    ]:
        db.query(model).delete()
    db.commit()


# ============================================================
# 平台数据（角色/组织/流程模板/集成端点）
# ============================================================

def _seed_platform(db: Session) -> None:
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
        ("WF-DOC-STD", "文档签核流程", "文档", "通用", "编制、研发审核、质量审核、文控发布",
         [("编制确认", "研发工程师", "提交", 8), ("研发审核", "研发工程师", "审批", 24), ("质量审核", "质量工程师", "审批", 24), ("文控发布", "系统管理员", "发布", 8)]),
        ("WF-BOM-REL", "BOM发布流程", "BOM", "通用", "研发提交、工艺评估、质量审核、ERP下发",
         [("研发提交", "研发工程师", "提交", 8), ("工艺评估", "工艺工程师", "审批", 24), ("质量审核", "质量工程师", "审批", 24), ("ERP下发", "ERP接口账号", "接口", 4)]),
        ("WF-ECR-ECN", "工程变更闭环流程", "变更", "通用", "ECR申请、影响分析、会签、ECN发布、ECA执行",
         [("ECR申请", "研发工程师", "提交", 8), ("影响分析", "工艺工程师", "评估", 24), ("质量会签", "质量工程师", "审批", 24), ("项目批准", "项目经理", "审批", 24), ("ECN发布", "系统管理员", "发布", 8), ("MES/ERP同步", "MES接口账号", "接口", 4)]),
        ("WF-NPI-APQP", "APQP/NPI阶段门流程", "项目", "APQP", "概念、设计、流片、验证、试产、量产导入阶段门",
         [("项目立项", "项目经理", "审批", 24), ("设计冻结", "研发工程师", "审批", 24), ("流片评审", "工艺工程师", "审批", 24), ("可靠性评审", "质量工程师", "审批", 48), ("量产发布", "项目经理", "发布", 24)]),
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
        ("QMS-DOC", "QMS文档/质量接口", "QMS", "http://qms.local/api/plm", "Token", "双向", "李超", "文档、可靠性报告、质量问题、CAPA"),
    ]
    for code, name, system_type, base_url, auth_type, direction, owner, scope in endpoints:
        db.add(models.IntegrationEndpoint(code=code, name=name, system_type=system_type, base_url=base_url, auth_type=auth_type, direction=direction, status="启用", owner=owner, object_scope=scope))


# ============================================================
# 基础配置（编码规则/生命周期/分类属性/数据字典/系统参数/供应商/替代料/项目模板）
# ============================================================

def _seed_foundation(db: Session) -> None:
    # 编码规则
    for row in [
        ("产品", "CR-PRODUCT", "产品型号编码", "OPTO", "OPTO-{yyyy}-{seq:04d}", 5, "OPTO-2026-0006", "系统管理员"),
        ("研发物料", "CR-MATERIAL", "研发物料编码", "MAT", "MAT-{category}-{seq:04d}", 10, "MAT-WAF-0011", "系统管理员"),
        ("文档", "CR-DOCUMENT", "受控文档编码", "DOC", "DOC-{product}-{category}-{seq:03d}", 40, "DOC-PD1550-SPEC-041", "文控"),
        ("BOM", "CR-BOM", "BOM版本编码", "BOM", "{bom_type}-{product}-{version}", 15, "EBOM-PD1550-A3", "系统管理员"),
        ("变更", "CR-CHANGE", "工程变更编码", "ECR", "ECR-{product}-{seq:03d}", 20, "ECR-PD1550-021", "系统管理员"),
        ("项目", "CR-PROJECT", "项目编码", "NPI", "NPI-{yyyy}-{seq:03d}", 5, "NPI-2026-066", "系统管理员"),
    ]:
        db.add(models.CodingRule(object_type=row[0], code=row[1], name=row[2], prefix=row[3], pattern=row[4], current_no=row[5], sample=row[6], status="启用", owner=row[7]))

    # 生命周期
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
    for code, name, object_type, description in lifecycles:
        template = models.LifecycleTemplate(code=code, name=name, object_type=object_type, status="启用", description=description)
        db.add(template)
        db.flush()
        for seq, state in enumerate(state_map[code], start=1):
            db.add(models.LifecycleState(template_id=template.id, sequence=seq, name=state[0], state_type=state[1], allow_edit=state[2], require_workflow=state[3], next_states=state[4]))

    # 分类属性
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

    # 数据字典（原有 + 新增 10 个）
    dictionaries = [
        # 原有
        ("DICT_PROCESS_PLATFORM", "工艺平台", "InP/InGaAs PIN", "InP/InGaAs PIN", "产品/工艺"),
        ("DICT_PROCESS_PLATFORM", "工艺平台", "GaAs VCSEL", "GaAs VCSEL", "产品/工艺"),
        ("DICT_PROCESS_PLATFORM", "工艺平台", "SOI Silicon Photonics", "SOI Silicon Photonics", "产品/工艺"),
        ("DICT_PROCESS_PLATFORM", "工艺平台", "GaN on Sapphire", "GaN on Sapphire", "产品/工艺"),
        ("DICT_WAFER_SIZE", "晶圆尺寸", "4 inch", "4 inch", "产品/物料"),
        ("DICT_WAFER_SIZE", "晶圆尺寸", "6 inch", "6 inch", "产品/物料"),
        ("DICT_WAFER_SIZE", "晶圆尺寸", "8 inch", "8 inch", "产品/物料"),
        ("DICT_PACKAGE_TYPE", "封装形式", "TO-CAN", "TO-CAN", "产品"),
        ("DICT_PACKAGE_TYPE", "封装形式", "COC", "COC", "产品"),
        ("DICT_PACKAGE_TYPE", "封装形式", "CPO", "CPO", "产品"),
        ("DICT_PACKAGE_TYPE", "封装形式", "裸 Die / COB", "裸 Die / COB", "产品"),
        ("DICT_RISK_LEVEL", "风险等级", "高", "高", "物料/变更"),
        ("DICT_RISK_LEVEL", "风险等级", "中", "中", "物料/变更"),
        ("DICT_RISK_LEVEL", "风险等级", "低", "低", "物料/变更"),
        ("DICT_APPROVAL_STATUS", "签核状态", "未提交", "未提交", "文档/BOM"),
        ("DICT_APPROVAL_STATUS", "签核状态", "流转中", "流转中", "文档/BOM"),
        ("DICT_APPROVAL_STATUS", "签核状态", "已签核", "已签核", "文档/BOM"),
        ("DICT_BOM_TYPE", "BOM类型", "EBOM", "设计EBOM", "BOM"),
        ("DICT_BOM_TYPE", "BOM类型", "PBOM", "工艺PBOM", "BOM"),
        ("DICT_BOM_TYPE", "BOM类型", "MBOM", "制造MBOM", "BOM"),
        # 新增 10 个字典
        ("DICT_CHANGE_TYPE", "变更类型", "光刻", "光刻", "工程变更"),
        ("DICT_CHANGE_TYPE", "变更类型", "刻蚀", "刻蚀", "工程变更"),
        ("DICT_CHANGE_TYPE", "变更类型", "镀膜", "镀膜", "工程变更"),
        ("DICT_CHANGE_TYPE", "变更类型", "测试", "测试", "工程变更"),
        ("DICT_CHANGE_TYPE", "变更类型", "封装", "封装", "工程变更"),
        ("DICT_CHANGE_TYPE", "变更类型", "可靠性", "可靠性", "工程变更"),
        ("DICT_CHANGE_TYPE", "变更类型", "物料", "物料", "工程变更"),
        ("DICT_CHANGE_TYPE", "变更类型", "文档", "文档", "工程变更"),
        ("DICT_SEVERITY", "严重度", "高", "高", "质量/变更"),
        ("DICT_SEVERITY", "严重度", "中", "中", "质量/变更"),
        ("DICT_SEVERITY", "严重度", "低", "低", "质量/变更"),
        ("DICT_PROJECT_PHASE", "项目阶段", "概念", "概念", "项目"),
        ("DICT_PROJECT_PHASE", "项目阶段", "设计", "设计", "项目"),
        ("DICT_PROJECT_PHASE", "项目阶段", "流片", "流片", "项目"),
        ("DICT_PROJECT_PHASE", "项目阶段", "验证", "验证", "项目"),
        ("DICT_PROJECT_PHASE", "项目阶段", "试产", "试产", "项目"),
        ("DICT_PROJECT_PHASE", "项目阶段", "量产导入", "量产导入", "项目"),
        ("DICT_PRIORITY", "优先级", "高", "高", "通用"),
        ("DICT_PRIORITY", "优先级", "中", "中", "通用"),
        ("DICT_PRIORITY", "优先级", "低", "低", "通用"),
        ("DICT_DELIVERABLE_TYPE", "交付物类型", "设计文件", "设计文件", "项目"),
        ("DICT_DELIVERABLE_TYPE", "交付物类型", "工艺文件", "工艺文件", "项目"),
        ("DICT_DELIVERABLE_TYPE", "交付物类型", "测试报告", "测试报告", "项目"),
        ("DICT_DELIVERABLE_TYPE", "交付物类型", "可靠性报告", "可靠性报告", "项目"),
        ("DICT_DELIVERABLE_TYPE", "交付物类型", "规格书", "规格书", "项目"),
        ("DICT_RISK_TYPE", "风险类型", "技术风险", "技术风险", "项目"),
        ("DICT_RISK_TYPE", "风险类型", "工艺风险", "工艺风险", "项目"),
        ("DICT_RISK_TYPE", "风险类型", "质量风险", "质量风险", "项目"),
        ("DICT_RISK_TYPE", "风险类型", "进度风险", "进度风险", "项目"),
        ("DICT_ISSUE_STATUS", "问题状态", "新建", "新建", "质量"),
        ("DICT_ISSUE_STATUS", "问题状态", "评估中", "评估中", "质量"),
        ("DICT_ISSUE_STATUS", "问题状态", "处理中", "处理中", "质量"),
        ("DICT_ISSUE_STATUS", "问题状态", "CAPA执行中", "CAPA执行中", "质量"),
        ("DICT_ISSUE_STATUS", "问题状态", "已关闭", "已关闭", "质量"),
        ("DICT_ACTION_TYPE", "操作动作", "新增", "新增", "审计"),
        ("DICT_ACTION_TYPE", "操作动作", "编辑", "编辑", "审计"),
        ("DICT_ACTION_TYPE", "操作动作", "提交", "提交", "审计"),
        ("DICT_ACTION_TYPE", "操作动作", "发布", "发布", "审计"),
        ("DICT_ACTION_TYPE", "操作动作", "驳回", "驳回", "审计"),
        ("DICT_ACTION_TYPE", "操作动作", "关闭", "关闭", "审计"),
        ("DICT_ACTION_TYPE", "操作动作", "删除", "删除", "审计"),
        ("DICT_TASK_STATUS", "任务状态", "待处理", "待处理", "项目"),
        ("DICT_TASK_STATUS", "任务状态", "进行中", "进行中", "项目"),
        ("DICT_TASK_STATUS", "任务状态", "已完成", "已完成", "项目"),
        ("DICT_TASK_STATUS", "任务状态", "已关闭", "已关闭", "项目"),
        ("DICT_DELIVERABLE_STATUS", "交付物状态", "待处理", "待处理", "项目"),
        ("DICT_DELIVERABLE_STATUS", "交付物状态", "进行中", "进行中", "项目"),
        ("DICT_DELIVERABLE_STATUS", "交付物状态", "已完成", "已完成", "项目"),
        ("DICT_DELIVERABLE_STATUS", "交付物状态", "已关闭", "已关闭", "项目"),
        # 补充字典：物料分类/供应商类型/替代料/文档分类/需求/变更状态/PR/集成/通用状态
        ("DICT_MATERIAL_CATEGORY", "物料分类", "衬底/外延", "衬底/外延", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "Mask", "Mask", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "光刻材料", "光刻材料", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "镀膜材料", "镀膜材料", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "介质膜材料", "介质膜材料", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "刻蚀材料", "刻蚀材料", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "测试治具", "测试治具", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "辅料", "辅料", "物料"),
        ("DICT_MATERIAL_CATEGORY", "物料分类", "包材", "包材", "物料"),
        ("DICT_MATERIAL_LIFECYCLE", "物料生命周期", "有效", "有效", "物料"),
        ("DICT_MATERIAL_LIFECYCLE", "物料生命周期", "替代", "替代", "物料"),
        ("DICT_MATERIAL_LIFECYCLE", "物料生命周期", "冻结", "冻结", "物料"),
        ("DICT_MATERIAL_LIFECYCLE", "物料生命周期", "停用", "停用", "物料"),
        ("DICT_SUPPLIER_TYPE", "供应商类型", "外延片", "外延片", "供应商"),
        ("DICT_SUPPLIER_TYPE", "供应商类型", "光罩/Mask", "光罩/Mask", "供应商"),
        ("DICT_SUPPLIER_TYPE", "供应商类型", "测试设备", "测试设备", "供应商"),
        ("DICT_SUPPLIER_TYPE", "供应商类型", "硅片", "硅片", "供应商"),
        ("DICT_SUPPLIER_TYPE", "供应商类型", "GaN外延", "GaN外延", "供应商"),
        ("DICT_SUPPLIER_TYPE", "供应商类型", "材料", "材料", "供应商"),
        ("DICT_SUBSTITUTE_TYPE", "替代料类型", "功能替代", "功能替代", "物料"),
        ("DICT_SUBSTITUTE_TYPE", "替代料类型", "兼容替代", "兼容替代", "物料"),
        ("DICT_SUBSTITUTE_STRATEGY", "替代策略", "一对一", "一对一", "物料"),
        ("DICT_SUBSTITUTE_STRATEGY", "替代策略", "多对一", "多对一", "物料"),
        ("DICT_SUBSTITUTE_STRATEGY", "替代策略", "一对多", "一对多", "物料"),
        ("DICT_DOC_CATEGORY", "文档分类", "产品规格", "产品规格", "文档"),
        ("DICT_DOC_CATEGORY", "文档分类", "工艺文件", "工艺文件", "文档"),
        ("DICT_DOC_CATEGORY", "文档分类", "测试报告", "测试报告", "文档"),
        ("DICT_DOC_CATEGORY", "文档分类", "可靠性报告", "可靠性报告", "文档"),
        ("DICT_DOC_CATEGORY", "文档分类", "设计资料", "设计资料", "文档"),
        ("DICT_REQUIREMENT_SOURCE", "需求来源", "客户规格", "客户规格", "需求"),
        ("DICT_REQUIREMENT_SOURCE", "需求来源", "NPI 阶段门", "NPI 阶段门", "需求"),
        ("DICT_REQUIREMENT_SOURCE", "需求来源", "质量体系", "质量体系", "需求"),
        ("DICT_REQUIREMENT_CATEGORY", "需求类别", "光电性能", "光电性能", "需求"),
        ("DICT_REQUIREMENT_CATEGORY", "需求类别", "制造可行性", "制造可行性", "需求"),
        ("DICT_REQUIREMENT_CATEGORY", "需求类别", "可靠性", "可靠性", "需求"),
        ("DICT_CHANGE_STATUS", "变更状态", "草稿", "草稿", "工程变更"),
        ("DICT_CHANGE_STATUS", "变更状态", "审批中", "审批中", "工程变更"),
        ("DICT_CHANGE_STATUS", "变更状态", "执行中", "执行中", "工程变更"),
        ("DICT_CHANGE_STATUS", "变更状态", "已关闭", "已关闭", "工程变更"),
        ("DICT_CHANGE_FORM_TYPE", "变更单类型", "PR", "PR 问题报告", "工程变更"),
        ("DICT_CHANGE_FORM_TYPE", "变更单类型", "ECR", "ECR 变更申请", "工程变更"),
        ("DICT_CHANGE_FORM_TYPE", "变更单类型", "ECO", "ECO 变更指令", "工程变更"),
        ("DICT_CHANGE_FORM_TYPE", "变更单类型", "ECN", "ECN 变更通知", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "产品", "产品", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "BOM", "BOM", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "文档", "文档", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "工艺路线", "工艺路线", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "物料", "物料", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "项目", "项目", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "质量", "质量", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "Lot", "Lot", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "通知", "通知", "工程变更"),
        ("DICT_CHANGE_TARGET_TYPE", "变更对象类型", "其他", "其他", "工程变更"),
        ("DICT_EFFECTIVITY_TYPE", "生效方式", "日期", "日期", "BOM/工程变更"),
        ("DICT_EFFECTIVITY_TYPE", "生效方式", "批次", "批次", "BOM/工程变更"),
        ("DICT_EFFECTIVITY_TYPE", "生效方式", "项目", "项目", "BOM"),
        ("DICT_EFFECTIVITY_TYPE", "生效方式", "日期+批次", "日期+批次", "工程变更"),
        ("DICT_REQUIREMENT_STATUS", "需求状态", "草稿", "草稿", "需求"),
        ("DICT_REQUIREMENT_STATUS", "需求状态", "验证中", "验证中", "需求"),
        ("DICT_REQUIREMENT_STATUS", "需求状态", "进行中", "进行中", "需求"),
        ("DICT_REQUIREMENT_STATUS", "需求状态", "已确认", "已确认", "需求"),
        ("DICT_RECIPIENT_TYPE", "接收类型", "角色", "角色", "文档"),
        ("DICT_RECIPIENT_TYPE", "接收类型", "部门", "部门", "文档"),
        ("DICT_RECIPIENT_TYPE", "接收类型", "人员", "人员", "文档"),
        ("DICT_CAPA_STATUS", "CAPA状态", "待处理", "待处理", "质量"),
        ("DICT_CAPA_STATUS", "CAPA状态", "执行中", "执行中", "质量"),
        ("DICT_CAPA_STATUS", "CAPA状态", "已关闭", "已关闭", "质量"),
        ("DICT_QUALITY_REPORT_STATUS", "质量报告状态", "草稿", "草稿", "质量"),
        ("DICT_QUALITY_REPORT_STATUS", "质量报告状态", "已归档", "已归档", "质量"),
        ("DICT_PR_TYPE", "PR问题类型", "质量异常", "质量异常", "PR问题"),
        ("DICT_PR_TYPE", "PR问题类型", "工艺问题", "工艺问题", "PR问题"),
        ("DICT_PR_TYPE", "PR问题类型", "设计问题", "设计问题", "PR问题"),
        ("DICT_PR_SOURCE", "PR问题来源", "内部", "内部", "PR问题"),
        ("DICT_PR_SOURCE", "PR问题来源", "客户", "客户", "PR问题"),
        ("DICT_PR_STATUS", "PR问题状态", "新建", "新建", "PR问题"),
        ("DICT_PR_STATUS", "PR问题状态", "评估中", "评估中", "PR问题"),
        ("DICT_PR_STATUS", "PR问题状态", "处理中", "处理中", "PR问题"),
        ("DICT_PR_STATUS", "PR问题状态", "已关闭", "已关闭", "PR问题"),
        ("DICT_INTEGRATION_SYSTEM", "集成系统", "ERP", "ERP", "集成"),
        ("DICT_INTEGRATION_SYSTEM", "集成系统", "MES", "MES", "集成"),
        ("DICT_INTEGRATION_SYSTEM", "集成系统", "QMS", "QMS", "集成"),
        ("DICT_INTEGRATION_STATUS", "集成状态", "等待", "等待", "集成"),
        ("DICT_INTEGRATION_STATUS", "集成状态", "处理中", "处理中", "集成"),
        ("DICT_INTEGRATION_STATUS", "集成状态", "成功", "成功", "集成"),
        ("DICT_INTEGRATION_STATUS", "集成状态", "失败", "失败", "集成"),
        ("DICT_COMMON_STATUS", "通用状态", "启用", "启用", "通用"),
        ("DICT_COMMON_STATUS", "通用状态", "停用", "停用", "通用"),
        ("DICT_PRODUCT_LIFECYCLE", "产品生命周期", "设计中", "设计中", "产品"),
        ("DICT_PRODUCT_LIFECYCLE", "产品生命周期", "验证", "验证", "产品"),
        ("DICT_PRODUCT_LIFECYCLE", "产品生命周期", "试产", "试产", "产品"),
        ("DICT_PRODUCT_LIFECYCLE", "产品生命周期", "量产", "量产", "产品"),
        ("DICT_PRODUCT_LIFECYCLE", "产品生命周期", "停用", "停用", "产品"),
        ("DICT_DOC_STATUS", "文档状态", "编制中", "编制中", "文档"),
        ("DICT_DOC_STATUS", "文档状态", "审批中", "审批中", "文档"),
        ("DICT_DOC_STATUS", "文档状态", "已发布", "已发布", "文档"),
        ("DICT_DOC_STATUS", "文档状态", "作废", "作废", "文档"),
        ("DICT_BOM_STATUS", "BOM状态", "编制中", "编制中", "BOM"),
        ("DICT_BOM_STATUS", "BOM状态", "审批中", "审批中", "BOM"),
        ("DICT_BOM_STATUS", "BOM状态", "已发布", "已发布", "BOM"),
        ("DICT_BOM_STATUS", "BOM状态", "冻结", "冻结", "BOM"),
        ("DICT_BOM_STATUS", "BOM状态", "作废", "作废", "BOM"),
        ("DICT_PROCESS_STATUS", "工艺状态", "编制中", "编制中", "工艺"),
        ("DICT_PROCESS_STATUS", "工艺状态", "审批中", "审批中", "工艺"),
        ("DICT_PROCESS_STATUS", "工艺状态", "有效", "有效", "工艺"),
        ("DICT_PROCESS_STATUS", "工艺状态", "作废", "作废", "工艺"),
        ("DICT_IMPACT_TYPE", "变更影响类型", "Mask 版本", "Mask 版本", "工程变更"),
        ("DICT_IMPACT_TYPE", "变更影响类型", "工艺文件", "工艺文件", "工程变更"),
        ("DICT_IMPACT_TYPE", "变更影响类型", "在制批次", "在制批次", "工程变更"),
        ("DICT_IMPACT_TYPE", "变更影响类型", "客户项目", "客户项目", "工程变更"),
        ("DICT_IMPACT_TYPE", "变更影响类型", "文档", "文档", "工程变更"),
        ("DICT_IMPACT_TYPE", "变更影响类型", "质量体系", "质量体系", "工程变更"),
        ("DICT_ECA_TYPE", "ECA动作类型", "ECN通知", "ECN通知", "工程变更"),
        ("DICT_ECA_TYPE", "ECA动作类型", "BOM更新", "BOM更新", "工程变更"),
        ("DICT_ECA_TYPE", "ECA动作类型", "工艺发布", "工艺发布", "工程变更"),
        ("DICT_ECA_TYPE", "ECA动作类型", "制造切换", "制造切换", "工程变更"),
        ("DICT_ECA_TYPE", "ECA动作类型", "文档升版", "文档升版", "工程变更"),
        ("DICT_ECA_STATUS", "ECA动作状态", "未开始", "未开始", "工程变更"),
        ("DICT_ECA_STATUS", "ECA动作状态", "待处理", "待处理", "工程变更"),
        ("DICT_ECA_STATUS", "ECA动作状态", "进行中", "进行中", "工程变更"),
        ("DICT_ECA_STATUS", "ECA动作状态", "已完成", "已完成", "工程变更"),
        ("DICT_APPROVAL_STEP", "审批步骤状态", "已通过", "已通过", "审批"),
        ("DICT_APPROVAL_STEP", "审批步骤状态", "处理中", "处理中", "审批"),
        ("DICT_APPROVAL_STEP", "审批步骤状态", "待处理", "待处理", "审批"),
        ("DICT_APPROVAL_STEP", "审批步骤状态", "已驳回", "已驳回", "审批"),
    ]
    for seq, row in enumerate(dictionaries, start=1):
        db.add(models.DictionaryItem(dict_code=row[0], dict_name=row[1], item_value=row[2], item_label=row[3], object_scope=row[4], sequence=seq, status="启用"))

    # 系统参数
    for key, value, group, desc in [
        ("COMPANY_NAME", "南智光电", "组织", "公司名称"),
        ("DEFAULT_DEPT", "生产部", "组织", "默认部门"),
        ("FILE_STORAGE", "./data/files", "存储", "文件存储路径"),
        ("DATE_FORMAT", "YYYY-MM-DD", "系统", "日期格式"),
        ("PREFIX_PRODUCT", "OPTO", "编码", "产品编码前缀"),
        ("PREFIX_ECR", "ECR", "编码", "变更单编码前缀"),
        ("REPORT_SNAPSHOT_CRON", "0 2 * * *", "报表", "报表快照计划表达式，默认每日 02:00"),
    ]:
        db.add(models.SystemParameter(param_key=key, param_value=value, param_group=group, description=desc))

    # 供应商
    for code, name, stype, contact, phone, email, address, cert, risk in [
        ("华东外延", "华东外延", "外延片", "王经理", "021-8888", "wang@hdepi.com", "上海临港", "ISO9001", "高"),
        ("星源外延", "星源外延", "外延片", "刘经理", "010-7777", "liu@xingyuan.com", "北京亦庄", "ISO9001", "中"),
        ("睿芯光罩", "睿芯光罩", "光罩/Mask", "陈工", "0755-6666", "chen@ruixin.com", "深圳南山", "ISO9001", "中"),
        ("滨松电子", "滨松电子", "测试设备", "张工", "021-5555", "zhang@hamamatsu.cn", "上海浦东", "ISO13485", "低"),
        ("沪硅产业", "沪硅产业", "硅片", "赵经理", "021-6666", "zhao@huigui.com", "上海嘉定", "ISO9001", "中"),
        ("三安光电", "三安光电", "GaN外延", "孙经理", "0592-9999", "sun@sanan.com", "厦门火炬", "IATF16949", "中"),
    ]:
        db.add(models.Supplier(code=code, name=name, supplier_type=stype, contact=contact, phone=phone, email=email, address=address, certification=cert, risk_level=risk, status="启用"))

    # 替代料
    db.add(models.SubstituteMaterial(material_code="MAT-WAF-INP", material_name="InP 外延片", substitute_code="MAT-WAF-GAAS", substitute_name="GaAs 外延片", substitute_type="功能替代", strategy="一对一", risk_level="高", status="启用", description="用于 PIN 低速探测器的应急替代方案。"))
    db.add(models.SubstituteMaterial(material_code="MAT-MASK-BLANK", material_name="空白掩膜版", substitute_code="MAT-MASK-OPTO", substitute_name="光刻掩膜版", substitute_type="兼容替代", strategy="多对一", risk_level="中", status="启用", description="部分非关键层可使用空白版替代。"))

    # 项目模板
    db.add(models.ProjectTemplate(code="NPI-STANDARD", name="标准 NPI 模板", description="光电芯片标准 NPI 流程", stages='["概念","设计","流片","验证","试产","量产导入"]', status="启用"))


# ============================================================
# 物料
# ============================================================

def _seed_materials(db: Session) -> None:
    for code, name, category, spec, supplier, risk in MATERIALS:
        db.add(models.Material(code=code, name=name, category=category, specification=spec, supplier=supplier, risk_level=risk))


# ============================================================
# 产品
# ============================================================

def _seed_products(db: Session) -> list[models.Product]:
    entities: list[models.Product] = []
    for row in PRODUCTS:
        product = models.Product(
            code=row[0], model=row[1], name=row[2], product_type=row[3], process_platform=row[4],
            wafer_size=row[5], package_type=row[6], temperature_grade=row[7], quality_grade=row[8],
            application=row[9], lifecycle=row[10], owner=row[11], customer_part_no=row[12],
            internal_part_no=row[13], version=row[14], readiness=row[15], latest_release=row[16],
        )
        entities.append(product)
        db.add(product)
    db.flush()
    return entities


def _seed_product_versions(db: Session, products: list[models.Product]) -> None:
    for product in products:
        db.add(models.ProductVersion(product_id=product.id, version="P1", lifecycle="设计中", readiness=30, released_at="2025-11-01", released_by="罗富森", summary="项目启动，完成概念设计评审。"))
        db.add(models.ProductVersion(product_id=product.id, version=product.version, lifecycle=product.lifecycle, readiness=product.readiness, released_at=product.latest_release, released_by=product.owner, source_change_no=f"ECR-{product.model}-001", summary=f"ECR 闭环后升版至 {product.version}。"))


# ============================================================
# 工艺路线
# ============================================================

def _seed_process_routes(db: Session, products: list[models.Product]) -> dict[int, models.ProcessRoute]:
    """返回 product_id -> ProcessRoute 映射"""
    result: dict[int, models.ProcessRoute] = {}
    for product in products:
        route = models.ProcessRoute(product_id=product.id, route_no=f"ROUTE-{product.model}", name=f"{product.model} 光电芯片制造路线", version=product.version, status="有效", owner="罗富森", release_date=product.latest_release)
        db.add(route)
        db.flush()
        result[product.id] = route
        for seq, step in enumerate(PROCESS_STEPS, start=10):
            db.add(models.ProcessStep(route_id=route.id, sequence=seq, stage=step[0], operation=step[1], key_params=step[2], owner="罗富森", status="有效"))
    return result


# ============================================================
# BOM（EBOM + PBOM + MBOM 三层）
# ============================================================

def _seed_boms(db: Session, products: list[models.Product], routes_by_product: dict[int, models.ProcessRoute]) -> dict[int, dict[str, models.BomHeader]]:
    """返回 product_id -> {bom_type: BomHeader} 映射"""
    result: dict[int, dict[str, models.BomHeader]] = {}
    for product in products:
        route = routes_by_product[product.id]
        step_names = [s[0] for s in PROCESS_STEPS]

        # --- EBOM ---
        ebom = models.BomHeader(
            product_id=product.id, bom_type="EBOM", version=product.version,
            status="已发布" if product.readiness >= 80 else "审批中",
            owner=product.owner, release_date=product.latest_release,
        )
        db.add(ebom)
        db.flush()
        for idx, item in enumerate(EBOM_ITEMS, start=1):
            db.add(models.BomItem(
                bom_id=ebom.id, parent_id=None, material_code=item[0],
                material_name=f"{product.model} {item[1]}", category=item[2],
                specification=item[3], quantity=item[4], unit=item[5],
                position=item[6], process_step="", substitute="待评估" if idx == 3 else "",
                status="有效",
            ))

        # --- PBOM（由 EBOM 转换，部分分配工序部分未分配） ---
        pbom = models.BomHeader(
            product_id=product.id, bom_type="PBOM", version=product.version,
            status="已发布" if product.readiness >= 80 else "审批中",
            owner=product.owner, release_date=product.latest_release,
            source_bom_id=ebom.id,
        )
        db.add(pbom)
        db.flush()
        for idx, item in enumerate(EBOM_ITEMS, start=1):
            # 前 5 项分配工序，后 2 项不分配（验证工序校验显示未分配）
            assigned_step = step_names[idx - 1] if idx <= 5 else ""
            step_obj = None
            if assigned_step:
                step_obj = db.query(models.ProcessStep).filter(
                    models.ProcessStep.route_id == route.id,
                    models.ProcessStep.stage == assigned_step,
                ).first()
            db.add(models.BomItem(
                bom_id=pbom.id, parent_id=None, material_code=item[0],
                material_name=f"{product.model} {item[1]}", category=item[2],
                specification=item[3], quantity=item[4], unit=item[5],
                position=item[6], process_step_id=step_obj.id if step_obj else None,
                process_step=assigned_step, substitute="待评估" if idx == 3 else "",
                status="有效",
            ))

        # --- MBOM（由 PBOM 转换，全部分配工序） ---
        mbom = models.BomHeader(
            product_id=product.id, bom_type="MBOM", version=product.version,
            status="已发布" if product.readiness >= 80 else "审批中",
            owner=product.owner, release_date=product.latest_release,
            source_bom_id=pbom.id,
        )
        db.add(mbom)
        db.flush()
        for idx, item in enumerate(EBOM_ITEMS, start=1):
            assigned_step = step_names[idx - 1]
            step_obj = db.query(models.ProcessStep).filter(
                models.ProcessStep.route_id == route.id,
                models.ProcessStep.stage == assigned_step,
            ).first()
            db.add(models.BomItem(
                bom_id=mbom.id, parent_id=None, material_code=item[0],
                material_name=f"{product.model} {item[1]}", category=item[2],
                specification=item[3], quantity=item[4], unit=item[5],
                position=item[6], process_step_id=step_obj.id if step_obj else None,
                process_step=assigned_step, substitute="待评估" if idx == 3 else "",
                status="有效",
            ))

        result[product.id] = {"EBOM": ebom, "PBOM": pbom, "MBOM": mbom}
    return result


# ============================================================
# 文档（8 个/产品，状态分布）
# ============================================================

def _seed_documents(db: Session, products: list[models.Product]) -> None:
    # (prefix, title, category, status, approval_status)
    doc_templates = [
        ("SPEC", "光电性能规格书", "产品规格", "已发布", "已签核"),
        ("PROC", "光刻刻蚀镀膜流程卡", "工艺文件", "审批中", "流转中"),
        ("TEST", "LIV/IV/光谱测试规范", "测试报告", "已发布", "已签核"),
        ("REL", "高温老化可靠性报告", "可靠性报告", "审批中", "流转中"),
        ("MASK", "Mask Layer 对照表", "设计资料", "已发布", "已签核"),
        ("CONTROL", "工艺控制计划", "工艺文件", "编制中", "未提交"),
        ("WI", "标准作业指导书", "工艺文件", "已发布", "已签核"),
        ("ACCEPT", "客户承认书", "产品规格", "审批中", "流转中"),
    ]
    for product in products:
        for prefix, title, category, status, approval_status in doc_templates:
            db.add(models.Document(
                product_id=product.id,
                doc_no=f"DOC-{product.model}-{prefix}",
                title=f"{product.model} {title}",
                category=category,
                version=product.version,
                status=status,
                owner=product.owner,
                approval_status=approval_status,
                updated_at=product.latest_release,
            ))


# ============================================================
# 工程变更（3-4 个/产品）
# ============================================================

def _seed_changes(db: Session, products: list[models.Product]) -> dict[int, list[models.Change]]:
    """返回 product_id -> [Change] 映射"""
    result: dict[int, list[models.Change]] = {}
    for product in products:
        changes: list[models.Change] = []
        is_mass = product.lifecycle == "量产"

        # 变更 1：审批中
        c1 = models.Change(
            product_id=product.id, change_no=f"ECR-{product.model}-001",
            title=f"{product.model} 光刻版图与刻蚀窗口优化", change_type="光刻",
            reason="试产批次边缘 Die 参数离散偏大，需要优化光刻 CD 目标和 ICP 刻蚀窗口。",
            status="审批中", priority="高" if product.lifecycle in ["试产", "量产"] else "中",
            owner=product.owner, submitted_at="2026-06-12",
            before_desc="光刻 CD 目标按 Rev.A1 控制，ICP 刻蚀时间窗口较窄，边缘片良率波动。",
            after_desc="更新 Mask Layer 注记，放宽并重定中心刻蚀窗口，新增膜厚和 CD 联动量测点。",
        )
        db.add(c1)
        db.flush()
        for impact in [
            ("Mask 版本", f"{product.model} Mask {product.version}", "高", "更新光刻层别和版图注记"),
            ("工艺文件", "光刻刻蚀镀膜流程卡", "高", "更新 CD、刻蚀深度和膜厚控制计划"),
            ("在制批次", f"LOT-{product.model}-2606", "中", "试产批隔离追踪并补测 Wafer map"),
        ]:
            db.add(models.ChangeImpact(change_id=c1.id, impact_type=impact[0], target=impact[1], risk=impact[2], action=impact[3]))
        for approval in [
            ("研发评审", product.owner, "已通过", "技术影响可控", "2026-06-13"),
            ("工艺评审", "罗富森", "已通过", "需补充封装参数卡", "2026-06-14"),
            ("质量评审", "李超", "处理中", "", ""),
            ("项目批准", "房磊", "待处理", "", ""),
        ]:
            db.add(models.Approval(change_id=c1.id, step_name=approval[0], approver=approval[1], status=approval[2], comment=approval[3], approved_at=approval[4]))
        changes.append(c1)

        # 变更 2：执行中
        c2 = models.Change(
            product_id=product.id, change_no=f"ECR-{product.model}-002",
            title=f"{product.model} 镀膜应力与膜厚均匀性优化", change_type="镀膜",
            reason="PECVD 介质膜应力偏压，影响后续光刻套刻精度和芯片可靠性。",
            status="执行中", priority="中", owner=product.owner, submitted_at="2026-05-20",
            before_desc="PECVD SiO2 膜厚 500nm，应力 -180MPa，边缘均匀性 ±8%。",
            after_desc="调整 PECVD 温度和压力参数，膜厚目标 480nm，应力控制在 -50MPa 以内，均匀性 ±5%。",
            notification_list="罗富森,于帅兵,李超",
        )
        db.add(c2)
        db.flush()
        for impact in [
            ("工艺文件", "光刻刻蚀镀膜流程卡", "高", "更新 PECVD 膜厚和应力控制窗口"),
            ("在制批次", f"LOT-{product.model}-2605", "中", "按新参数试产验证"),
        ]:
            db.add(models.ChangeImpact(change_id=c2.id, impact_type=impact[0], target=impact[1], risk=impact[2], action=impact[3]))
        for approval in [
            ("研发评审", product.owner, "已通过", "方案可行", "2026-05-22"),
            ("工艺评审", "罗富森", "已通过", "参数调整合理", "2026-05-23"),
            ("质量评审", "李超", "已通过", "需追加可靠性验证", "2026-05-25"),
            ("项目批准", "房磊", "已通过", "批准执行", "2026-05-26"),
        ]:
            db.add(models.Approval(change_id=c2.id, step_name=approval[0], approver=approval[1], status=approval[2], comment=approval[3], approved_at=approval[4]))
        # ECA 动作（执行中）
        for idx, row in enumerate([
            ("ECN通知", "受影响文档/流程卡签收", "生产部", "李超", "已完成", "2026-06-01", "已通知质量、工艺、制造。"),
            ("工艺发布", f"ROUTE-{product.model}", "生产部", "罗富森", "进行中", "2026-06-15", "更新 PECVD 膜厚和应力控制窗口。"),
            ("制造切换", f"LOT-{product.model}-2606", "生产部", "房磊", "待处理", "2026-06-28", "按 ECN 生效批次切换。"),
        ], start=1):
            db.add(models.ChangeAction(
                change_id=c2.id, action_no=f"ECA-{c2.change_no}-{idx:02d}",
                action_type=row[0], target_object=row[1], department=row[2],
                owner=row[3], status=row[4], due_date=row[5], result=row[6],
            ))
        changes.append(c2)

        # 变更 3：已关闭（量产产品含已完成文档 ECA，验证 ECO 联动）
        c3_status = "已关闭" if is_mass else "执行中"
        c3 = models.Change(
            product_id=product.id, change_no=f"ECR-{product.model}-003",
            title=f"{product.model} 测试规范与可靠性报告升版", change_type="文档",
            reason="客户反馈测试覆盖率不足，需补充温循和老化测试项，更新可靠性报告版本。",
            status=c3_status, priority="中", owner=product.owner, submitted_at="2026-04-10",
            before_desc="测试规范 v1.0，可靠性报告覆盖 HTOL 和 TC 两项。",
            after_desc="测试规范 v2.0 新增 HAST 和老化测试项，可靠性报告升版归档。",
            notification_list="罗富森,于帅兵,李超,房磊",
        )
        db.add(c3)
        db.flush()
        for impact in [
            ("文档", f"DOC-{product.model}-TEST", "高", "测试规范升版至 v2.0"),
            ("文档", f"DOC-{product.model}-REL", "高", "可靠性报告升版归档"),
            ("质量体系", "QMS 归档", "中", "新版可靠性报告同步 QMS"),
        ]:
            db.add(models.ChangeImpact(change_id=c3.id, impact_type=impact[0], target=impact[1], risk=impact[2], action=impact[3]))
        for approval in [
            ("研发评审", product.owner, "已通过", "同意升版", "2026-04-12"),
            ("工艺评审", "罗富森", "已通过", "测试项合理", "2026-04-13"),
            ("质量评审", "李超", "已通过", "可靠性覆盖充分", "2026-04-15"),
            ("项目批准", "房磊", "已通过", "批准执行", "2026-04-16"),
        ]:
            db.add(models.Approval(change_id=c3.id, step_name=approval[0], approver=approval[1], status=approval[2], comment=approval[3], approved_at=approval[4]))
        # ECA 动作
        eca3_rows = [
            ("文档升版", f"DOC-{product.model}-TEST", "文档", "生产部", "李超", "已完成" if c3_status == "已关闭" else "进行中", "2026-04-25", "测试规范已升版至 v2.0 并发布。"),
            ("文档升版", f"DOC-{product.model}-REL", "文档", "生产部", "李超", "已完成" if c3_status == "已关闭" else "待处理", "2026-05-10", "可靠性报告已升版归档。"),
            ("ECN通知", "受影响部门签收", "文档", "生产部", "李超", "已完成" if c3_status == "已关闭" else "待处理", "2026-04-28", "已通知所有相关部门。"),
        ]
        # 找到测试文档和可靠性文档作为 target
        test_doc = db.query(models.Document).filter(models.Document.doc_no == f"DOC-{product.model}-TEST").first()
        rel_doc = db.query(models.Document).filter(models.Document.doc_no == f"DOC-{product.model}-REL").first()
        for idx, row in enumerate(eca3_rows, start=1):
            target_id = None
            target_ver = ""
            generated_no = ""
            if row[0] == "文档升版" and "TEST" in row[1] and test_doc:
                target_id = test_doc.id
                target_ver = "v2.0"
                generated_no = f"DOC-{product.model}-TEST"
            elif row[0] == "文档升版" and "REL" in row[1] and rel_doc:
                target_id = rel_doc.id
                target_ver = "v2.0"
                generated_no = f"DOC-{product.model}-REL"
            db.add(models.ChangeAction(
                change_id=c3.id, action_no=f"ECA-{c3.change_no}-{idx:02d}",
                action_type=row[0], target_type=row[2], target_id=target_id,
                target_version=target_ver, target_object=row[1],
                department=row[3], owner=row[4], status=row[5], due_date=row[6], result=row[7],
                generated_object_no=generated_no,
            ))
        # 已关闭的变更创建文档发放/回收记录（ECO 联动结果）
        if c3_status == "已关闭":
            if test_doc:
                db.add(models.DocumentDistribution(
                    document_id=test_doc.id, doc_no=test_doc.doc_no, title=test_doc.title,
                    version="v2.0", recipient_type="角色", recipient="罗富森",
                    status="已发放", distributed_by="系统(ECR-{0}-003)".format(product.model),
                    distributed_at="2026-04-25",
                ))
                db.add(models.DocumentDistribution(
                    document_id=test_doc.id, doc_no=test_doc.doc_no, title=test_doc.title,
                    version="v1.0", recipient_type="角色", recipient="于帅兵",
                    status="已回收", distributed_by="系统(ECR-{0}-003)".format(product.model),
                    distributed_at="2026-04-25", recalled_by="系统", recalled_at="2026-04-25",
                    recall_reason="变更单 ECR-{0}-003 关闭，旧版测试规范 v1.0 回收，新版 v2.0 已发布".format(product.model),
                ))
            if rel_doc:
                db.add(models.DocumentDistribution(
                    document_id=rel_doc.id, doc_no=rel_doc.doc_no, title=rel_doc.title,
                    version="v2.0", recipient_type="角色", recipient="李超",
                    status="已发放", distributed_by="系统(ECR-{0}-003)".format(product.model),
                    distributed_at="2026-05-10",
                ))
        changes.append(c3)

        # 变更 4（非量产产品额外一个审批中变更）
        if not is_mass:
            c4 = models.Change(
                product_id=product.id, change_no=f"ECR-{product.model}-004",
                title=f"{product.model} 封装耦合效率改进", change_type="封装",
                reason="封装耦合功率波动，需优化 Die attach 精度和点胶工艺。",
                status="审批中", priority="中", owner=product.owner, submitted_at="2026-06-25",
                before_desc="耦合效率 85%±5%，Die attach 位置偏差 ±20um。",
                after_desc="优化点胶量和固化参数，Die attach 精度提升至 ±10um，耦合效率目标 90%±3%。",
            )
            db.add(c4)
            db.flush()
            for impact in [
                ("工艺文件", "封装作业指导书", "中", "更新 Die attach 和点胶参数"),
                ("在制批次", f"LOT-{product.model}-2606", "中", "新批次按新工艺验证"),
            ]:
                db.add(models.ChangeImpact(change_id=c4.id, impact_type=impact[0], target=impact[1], risk=impact[2], action=impact[3]))
            for approval in [
                ("研发评审", product.owner, "已通过", "方案可行", "2026-06-26"),
                ("工艺评审", "罗富森", "处理中", "", ""),
                ("质量评审", "李超", "待处理", "", ""),
            ]:
                db.add(models.Approval(change_id=c4.id, step_name=approval[0], approver=approval[1], status=approval[2], comment=approval[3], approved_at=approval[4]))
            changes.append(c4)

        result[product.id] = changes
    return result


# ============================================================
# 质量（批次/问题/CAPA/报告）
# ============================================================

def _seed_quality(db: Session, products: list[models.Product]) -> None:
    for product in products:
        # 批次（4 个/产品）
        for idx, yield_base in enumerate([94.2, 95.1, 93.7, 96.0], start=1):
            db.add(models.QualityLot(
                product_id=product.id,
                lot_no=f"LOT-{product.model}-260{idx}",
                wafer_id=f"W{idx:02d}-{product.model[-3:]}",
                stage="晶圆测试" if idx % 2 == 0 else "量测",
                cp_yield=yield_base, ft_yield=yield_base - 1.8, bin1_rate=yield_base - 0.6,
                issue_count=1 if idx == 3 else 0,
                status="异常跟进" if idx == 3 else "正常",
                tested_at=f"2026-06-{10 + idx}",
            ))

        # 质量问题（2-3 个/产品）
        issues_data = [
            ("QIR-2026-{0:04d}".format(product.id * 10 + 1), f"{product.model} 边缘 Wafer 参数离散",
             "中", "处理中", "罗富森", "边缘 Wafer CD 偏差超管控限，初步定位光刻曝光剂量分布不均。",
             "优化光刻曝光剂量分布和显影时间 SPC 管控，增加边缘 CD 监测频次。"),
            ("QIR-2026-{0:04d}".format(product.id * 10 + 2), f"{product.model} 膜厚均匀性异常",
             "高" if product.lifecycle in ["试产", "量产"] else "中", "CAPA 执行中", "李超",
             "PECVD 介质膜边缘膜厚偏差 ±8%，超出 ±5% 控制限。",
             "调整 PECVD 温度均匀性和压力分布，受影响 Wafer 追加膜厚复测。"),
        ]
        if product.lifecycle in ["试产", "量产", "验证"]:
            issues_data.append((
                "QIR-2026-{0:04d}".format(product.id * 10 + 3), f"{product.model} 可靠性测试异常",
                "高", "新建" if product.lifecycle != "量产" else "已关闭", "李超",
                "HTOL 老化测试中部分样品参数漂移超规格，需排查根因。",
                "追加样品复测，排查钝化膜和金属化层可靠性。",
            ))

        for issue_no, title, severity, status, owner, root_cause, corrective in issues_data:
            db.add(models.QualityIssue(
                issue_no=issue_no, product_model=product.model,
                lot_no=f"LOT-{product.model}-2603",
                title=title, severity=severity, status=status, owner=owner,
                root_cause=root_cause, corrective_action=corrective,
            ))

        # CAPA（对未关闭问题创建 CAPA）
        open_issues = db.query(models.QualityIssue).filter(
            models.QualityIssue.product_model == product.model,
            models.QualityIssue.status != "已关闭",
        ).all()
        for idx, issue in enumerate(open_issues[:2], start=1):
            db.add(models.QualityCAPA(
                capa_no=f"CAPA-{product.id:02d}-{idx:03d}", issue_id=issue.id,
                title=f"CAPA: {issue.title}", source="质量问题",
                root_cause=issue.root_cause, corrective_action=issue.corrective_action,
                owner=issue.owner, status="待处理" if issue.status == "新建" else "执行中",
                due_date="2026-07-30",
            ))

    # 质量报告（已归档，2 个）
    db.add(models.QualityReport(
        report_no="QR-2026-001", title="PD-1550-10G 试产质量归档报告",
        report_type="质量归档", product_model="PD-1550-10G",
        issue_nos="QIR-2026-0011,QIR-2026-0012", capa_nos="CAPA-01-001",
        summary="试产阶段质量数据汇总，含 4 批次良率统计、2 项质量问题闭环。",
        root_cause="边缘 CD 波动和膜厚均匀性问题，已通过工艺优化解决。",
        corrective_action="优化光刻曝光剂量和 PECVD 参数，受影响批次已复测合格。",
        preventive_action="建立边缘 CD 和膜厚 SPC 管控，纳入日常监控。",
        owner="李超", status="已归档", archived_at="2026-06-20", archived_by="李超",
    ))
    db.add(models.QualityReport(
        report_no="QR-2026-002", title="VCSEL-940-3W 量产质量归档报告",
        report_type="质量归档", product_model="VCSEL-940-3W",
        issue_nos="QIR-2026-0021", capa_nos="CAPA-02-001",
        summary="量产导入阶段质量数据汇总，含可靠性验证和客户认定结果。",
        root_cause="光刻 CD 均匀性波动，已通过曝光剂量优化解决。",
        corrective_action="优化曝光剂量分布和显影 SPC，连续三批达标。",
        preventive_action="6 inch 晶圆 CD SPC 管控纳入量产监控。",
        owner="李超", status="已归档", archived_at="2026-06-25", archived_by="李超",
    ))


# ============================================================
# 需求规格（3 个/产品）
# ============================================================

def _seed_requirements(db: Session, products: list[models.Product]) -> None:
    templates = [
        ("客户规格", "光电性能", "暗电流、响应度、带宽满足客户规格书冻结值", "高", "已确认", "规格书指标、CP/FT 测试规范、客户承认书三方一致"),
        ("NPI 阶段门", "制造可行性", "关键工序 Cpk 与良率达到试产放行阈值", "高", "验证中", "光刻 CD、刻蚀深度、膜厚均匀性连续三批达标"),
        ("质量体系", "可靠性", "HTOL、温循、湿热与老化试验按产品等级归档", "中", "进行中", "可靠性报告签核后纳入发布基线"),
    ]
    for product in products:
        for idx, row in enumerate(templates, start=1):
            db.add(models.Requirement(
                product_id=product.id, req_no=f"REQ-{product.model}-{idx:03d}",
                source=row[0], category=row[1], title=f"{product.model} {row[2]}",
                priority=row[3], status=row[4], owner=product.owner,
                acceptance_criteria=row[5],
            ))


# ============================================================
# 产品基线（1 个/产品，含 5 个基线项）
# ============================================================

def _seed_baselines(db: Session, products: list[models.Product]) -> None:
    for product in products:
        baseline = models.ProductBaseline(
            product_id=product.id, baseline_no=f"BL-{product.model}-{product.version}",
            name=f"{product.model} {product.lifecycle} 发布基线", version=product.version,
            status="已发布" if product.readiness >= 80 else "冻结评审中",
            created_by=product.owner, released_at=product.latest_release,
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
            db.add(models.BaselineItem(baseline_id=baseline.id, item_type=item[0], item_no=item[1], title=item[2], version=item[3], status=item[4]))


# ============================================================
# 项目（5 个，062 已归档）
# ============================================================

def _seed_projects(db: Session, products: list[models.Product], boms_by_product: dict[int, dict[str, models.BomHeader]]) -> None:
    product_map = {p.model: p for p in products}

    # 项目 1：PD-1550-10G 试产（主验证项目）
    p1 = models.Project(project_no="NPI-2026-061", name="1550nm 光电探测器工艺导入项目", product_model="PD-1550-10G", phase="试产", progress=68, owner="房磊", start_date="2026-03-01", end_date="2026-09-30", risk_level="中")
    db.add(p1)
    db.flush()
    for task in [
        ("光电规格冻结", "设计", "罗富森", "已完成", date(2026, 4, 15)),
        ("Mask 投版与首批试制", "流片", "罗富森", "已完成", date(2026, 5, 20)),
        ("光刻刻蚀窗口 DOE", "验证", "罗富森", "进行中", date(2026, 6, 28)),
        ("镀膜膜厚均匀性验证", "试产", "罗富森", "进行中", date(2026, 7, 12)),
        ("客户样品与可靠性资料包", "量产导入", "房磊", "待处理", date(2026, 8, 15)),
        ("试产质量归档报告", "试产", "李超", "待处理", date(2026, 7, 30)),
    ]:
        db.add(models.ProjectTask(project_id=p1.id, name=task[0], phase=task[1], owner=task[2], status=task[3], due_date=task[4]))
    prod1 = product_map["PD-1550-10G"]
    bom1 = boms_by_product[prod1.id]["EBOM"]
    db.add(models.ProjectDeliverable(project_id=p1.id, name="光电性能规格书", deliverable_type="规格书", phase="设计", owner="罗富森", status="已完成", due_date="2026-04-20", completed_at="2026-04-18", object_type="BOM", object_id=bom1.id))
    db.add(models.ProjectDeliverable(project_id=p1.id, name="光刻刻蚀工艺验证报告", deliverable_type="测试报告", phase="验证", owner="罗富森", status="进行中", due_date="2026-07-10"))
    db.add(models.ProjectDeliverable(project_id=p1.id, name="可靠性测试报告", deliverable_type="可靠性报告", phase="试产", owner="李超", status="待处理", due_date="2026-08-01"))
    db.add(models.ProjectRisk(project_id=p1.id, risk_type="工艺风险", description="边缘 Wafer 暗电流偏高，需优化刻蚀清洗工艺", impact="中", probability="中", severity="中", owner="罗富森", status="处理中", mitigation="调整 ICP 清洗步骤和 PECVD 钝化膜厚"))

    # 项目 2：VCSEL-940-3W 量产导入（已归档）
    p2 = models.Project(project_no="NPI-2026-062", name="940nm VCSEL 阵列量产导入项目", product_model="VCSEL-940-3W", phase="量产导入", progress=100, owner="房磊", start_date="2026-01-15", end_date="2026-06-30", risk_level="低", archived_at="2026-06-28", archived_by="房磊", archive_summary="VCSEL 阵列量产导入完成，良率达标，客户可靠性认定通过，质量报告已归档。项目数据包含交付物/BOM/文档/工艺/变更/质量/流程记录。")
    db.add(p2)
    db.flush()
    for task in [
        ("外延片规格确认", "设计", "张昊", "已完成", date(2026, 2, 20)),
        ("光刻工艺 DOE", "流片", "张昊", "已完成", date(2026, 3, 25)),
        ("Wafer Map 良率验证", "验证", "罗富森", "已完成", date(2026, 5, 10)),
        ("量产 CD SPC 管控部署", "试产", "罗富森", "已完成", date(2026, 6, 15)),
        ("客户可靠性认定", "量产导入", "房磊", "已完成", date(2026, 6, 25)),
    ]:
        db.add(models.ProjectTask(project_id=p2.id, name=task[0], phase=task[1], owner=task[2], status=task[3], due_date=task[4]))
    prod2 = product_map["VCSEL-940-3W"]
    bom2 = boms_by_product[prod2.id]["EBOM"]
    doc2 = db.query(models.Document).filter(models.Document.doc_no == "DOC-VCSEL-940-3W-SPEC").first()
    db.add(models.ProjectDeliverable(project_id=p2.id, name="VCSEL 阵列工艺规格书", deliverable_type="工艺文件", phase="试产", owner="张昊", status="已完成", due_date="2026-05-15", completed_at="2026-05-12", object_type="BOM", object_id=bom2.id))
    if doc2:
        db.add(models.ProjectDeliverable(project_id=p2.id, name="量产 Wafer Map 良率报告", deliverable_type="测试报告", phase="量产导入", owner="罗富森", status="已完成", due_date="2026-06-20", completed_at="2026-06-18", object_type="Document", object_id=doc2.id))
    db.add(models.ProjectDeliverable(project_id=p2.id, name="客户可靠性认定报告", deliverable_type="可靠性报告", phase="量产导入", owner="李超", status="已完成", due_date="2026-06-25", completed_at="2026-06-24"))
    db.add(models.ProjectRisk(project_id=p2.id, risk_type="工艺风险", description="6 inch 晶圆 CD 均匀性波动可能影响阵列一致性", impact="中", probability="低", severity="中", owner="罗富森", status="已关闭", mitigation="增加边缘 CD 监测频次，SPC 管控曝光剂量，已连续三批达标"))

    # 项目 3：DFB-1310-25G 验证（交付物齐套，可推进阶段门）
    p3 = models.Project(project_no="NPI-2026-063", name="1310nm DFB 激光器验证项目", product_model="DFB-1310-25G", phase="验证", progress=45, owner="于帅兵", start_date="2026-02-10", end_date="2026-10-15", risk_level="中")
    db.add(p3)
    db.flush()
    for task in [
        ("DFB 光栅设计冻结", "设计", "于帅兵", "已完成", date(2026, 3, 15)),
        ("首批流片与晶圆测试", "流片", "于帅兵", "已完成", date(2026, 4, 30)),
        ("封装耦合效率优化", "验证", "于帅兵", "进行中", date(2026, 7, 18)),
        ("高温老化可靠性验证", "验证", "李超", "待处理", date(2026, 8, 30)),
        ("客户样品提交", "试产", "房磊", "待处理", date(2026, 9, 20)),
    ]:
        db.add(models.ProjectTask(project_id=p3.id, name=task[0], phase=task[1], owner=task[2], status=task[3], due_date=task[4]))
    prod3 = product_map["DFB-1310-25G"]
    bom3 = boms_by_product[prod3.id]["EBOM"]
    db.add(models.ProjectDeliverable(project_id=p3.id, name="DFB 激光器设计报告", deliverable_type="设计文件", phase="设计", owner="于帅兵", status="已完成", due_date="2026-03-20", completed_at="2026-03-18", object_type="BOM", object_id=bom3.id))
    db.add(models.ProjectDeliverable(project_id=p3.id, name="耦合效率分析报告", deliverable_type="测试报告", phase="验证", owner="于帅兵", status="已完成", due_date="2026-07-15", completed_at="2026-07-10"))
    db.add(models.ProjectRisk(project_id=p3.id, risk_type="质量风险", description="客户反馈封装耦合功率下降，需排查对准精度", impact="高", probability="中", severity="高", owner="于帅兵", status="处理中", mitigation="核查封装工艺对准精度和点胶量，重新校准耦合台"))

    # 项目 4：LED-MICRO-RGB 设计（早期阶段）
    p4 = models.Project(project_no="NPI-2026-064", name="Micro LED RGB 外延片设计项目", product_model="LED-MICRO-RGB", phase="设计", progress=25, owner="张昊", start_date="2026-03-01", end_date="2026-12-30", risk_level="高")
    db.add(p4)
    db.flush()
    for task in [
        ("RGB 三色外延方案设计", "概念", "张昊", "已完成", date(2026, 4, 10)),
        ("GaN 外延工艺参数 DOE", "设计", "张昊", "进行中", date(2026, 7, 15)),
        ("Micro LED 像素阵列设计", "设计", "梁伟维", "待处理", date(2026, 8, 20)),
        ("首轮流片与光电测试", "流片", "梁伟维", "待处理", date(2026, 10, 15)),
        ("微显示应用验证", "验证", "房磊", "待处理", date(2026, 12, 1)),
    ]:
        db.add(models.ProjectTask(project_id=p4.id, name=task[0], phase=task[1], owner=task[2], status=task[3], due_date=task[4]))
    db.add(models.ProjectDeliverable(project_id=p4.id, name="RGB 外延方案设计书", deliverable_type="设计文件", phase="概念", owner="张昊", status="已完成", due_date="2026-04-15", completed_at="2026-04-12"))
    db.add(models.ProjectDeliverable(project_id=p4.id, name="GaN 外延工艺参数表", deliverable_type="工艺文件", phase="设计", owner="张昊", status="进行中", due_date="2026-07-20"))
    db.add(models.ProjectRisk(project_id=p4.id, risk_type="技术风险", description="GaN on Sapphire 外延位错密度可能影响 Micro LED 发光效率", impact="高", probability="中", severity="高", owner="张昊", status="评估中", mitigation="优化缓冲层结构和退火工艺，增加位错密度监测"))

    # 项目 5：SiPh-MZM-400G 流片（高风险项目）
    p5 = models.Project(project_no="NPI-2026-065", name="400G 硅光调制器流片项目", product_model="SiPh-MZM-400G", phase="流片", progress=38, owner="张昊", start_date="2026-01-20", end_date="2026-11-15", risk_level="高")
    db.add(p5)
    db.flush()
    for task in [
        ("MZM 调制器结构仿真", "设计", "张昊", "已完成", date(2026, 2, 28)),
        ("SOI 流片版图设计", "设计", "张昊", "已完成", date(2026, 3, 25)),
        ("首轮 MPW 流片", "流片", "梁伟维", "已完成", date(2026, 5, 15)),
        ("波导损耗 SEM 分析", "验证", "张昊", "进行中", date(2026, 7, 10)),
        ("刻蚀工艺优化与第二轮流片", "流片", "梁伟维", "待处理", date(2026, 9, 20)),
    ]:
        db.add(models.ProjectTask(project_id=p5.id, name=task[0], phase=task[1], owner=task[2], status=task[3], due_date=task[4]))
    prod5 = product_map["SiPh-MZM-400G"]
    bom5 = boms_by_product[prod5.id]["EBOM"]
    db.add(models.ProjectDeliverable(project_id=p5.id, name="MZM 调制器仿真报告", deliverable_type="设计文件", phase="设计", owner="张昊", status="已完成", due_date="2026-03-05", completed_at="2026-03-03", object_type="BOM", object_id=bom5.id))
    db.add(models.ProjectDeliverable(project_id=p5.id, name="首轮流片测试报告", deliverable_type="测试报告", phase="流片", owner="张昊", status="进行中", due_date="2026-07-15"))
    db.add(models.ProjectRisk(project_id=p5.id, risk_type="技术风险", description="流片后波导插损高于仿真预期，刻蚀粗糙度需优化", impact="高", probability="高", severity="高", owner="张昊", status="处理中", mitigation="对比仿真与实测 SEM 截面，调整刻蚀气体配比和压力"))


# ============================================================
# 流程实例与待办（6-8 条，工作台非空）
# ============================================================

def _seed_workflow_instances(db: Session, products: list[models.Product], changes_by_product: dict[int, list[models.Change]], boms_by_product: dict[int, dict[str, models.BomHeader]]) -> None:
    # 获取流程模板
    tpl_doc = db.query(models.WorkflowTemplate).filter(models.WorkflowTemplate.code == "WF-DOC-STD").first()
    tpl_bom = db.query(models.WorkflowTemplate).filter(models.WorkflowTemplate.code == "WF-BOM-REL").first()
    tpl_chg = db.query(models.WorkflowTemplate).filter(models.WorkflowTemplate.code == "WF-ECR-ECN").first()

    # --- 待办 1-2：文档审批（分配给李超质量工程师） ---
    for product, doc_prefix in [(products[0], "PROC"), (products[2], "REL")]:
        doc = db.query(models.Document).filter(models.Document.doc_no == f"DOC-{product.model}-{doc_prefix}").first()
        if not doc:
            continue
        inst = models.WorkflowInstance(
            template_id=tpl_doc.id, object_type="文档", object_id=doc.id,
            object_no=doc.doc_no, title=f"{doc.title} 签核审批",
            product_model=product.model, status="运行中",
            started_by=product.owner, started_at="2026-06-20",
        )
        db.add(inst)
        db.flush()
        # 节点 1-2 已完成，节点 3 待处理（质量审核 - 李超）
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=1, node_name="编制确认", role_name="研发工程师", action_type="提交", status="已完成", assignee=product.owner, acted_by=product.owner, acted_at="2026-06-20", comment="文档已编制完成，提交审核。", sla_hours=8))
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=2, node_name="研发审核", role_name="研发工程师", action_type="审批", status="已完成", assignee=product.owner, acted_by=product.owner, acted_at="2026-06-21", comment="内容审核通过。", sla_hours=24))
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=3, node_name="质量审核", role_name="质量工程师", action_type="审批", status="待处理", assignee="李超", sla_hours=24))

    # --- 待办 3-4：BOM 发布（分配给工艺工程师） ---
    for product in [products[0], products[2]]:
        boms = boms_by_product[product.id]
        bom = boms["PBOM"]  # PBOM 审批中
        if bom.status != "审批中":
            continue
        inst = models.WorkflowInstance(
            template_id=tpl_bom.id, object_type="BOM", object_id=bom.id,
            object_no=f"{bom.bom_type}-{product.model}-{bom.version}",
            title=f"{product.model} {bom.bom_type} 发布审批",
            product_model=product.model, status="运行中",
            started_by=product.owner, started_at="2026-06-22",
        )
        db.add(inst)
        db.flush()
        # 节点 1 已完成，节点 2 待处理（工艺评估）
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=1, node_name="研发提交", role_name="研发工程师", action_type="提交", status="已完成", assignee=product.owner, acted_by=product.owner, acted_at="2026-06-22", comment="PBOM 已从 EBOM 转换，提交审批。", sla_hours=8))
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=2, node_name="工艺评估", role_name="工艺工程师", action_type="审批", status="待处理", assignee="罗富森" if product.model != "DFB-1310-25G" else "于帅兵", sla_hours=24))

    # --- 待办 5-6：变更审批（分配给项目经理房磊） ---
    for product in [products[0], products[3]]:
        changes = changes_by_product.get(product.id, [])
        # 找审批中的变更
        change = next((c for c in changes if c.status == "审批中"), None)
        if not change:
            continue
        inst = models.WorkflowInstance(
            template_id=tpl_chg.id, object_type="变更", object_id=change.id,
            object_no=change.change_no, title=f"{change.title} 变更审批",
            product_model=product.model, status="运行中",
            started_by=product.owner, started_at=change.submitted_at,
        )
        db.add(inst)
        db.flush()
        # 节点 1-3 已完成，节点 4 待处理（项目批准 - 房磊）
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=1, node_name="ECR申请", role_name="研发工程师", action_type="提交", status="已完成", assignee=product.owner, acted_by=product.owner, acted_at=change.submitted_at, comment="变更申请已提交。", sla_hours=8))
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=2, node_name="影响分析", role_name="工艺工程师", action_type="评估", status="已完成", assignee="罗富森", acted_by="罗富森", acted_at=change.submitted_at, comment="影响分析完成，风险可控。", sla_hours=24))
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=3, node_name="质量会签", role_name="质量工程师", action_type="审批", status="已完成", assignee="李超", acted_by="李超", acted_at=change.submitted_at, comment="质量会签通过。", sla_hours=24))
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=4, node_name="项目批准", role_name="项目经理", action_type="审批", status="待处理", assignee="房磊", sla_hours=24))

    # --- 已完成流程 1-2（历史记录） ---
    # VCSEL BOM 发布已完成
    vcsel = products[1]
    vcsel_bom = boms_by_product[vcsel.id]["EBOM"]
    inst_done1 = models.WorkflowInstance(
        template_id=tpl_bom.id, object_type="BOM", object_id=vcsel_bom.id,
        object_no=f"{vcsel_bom.bom_type}-{vcsel.model}-{vcsel_bom.version}",
        title=f"{vcsel.model} EBOM 发布审批（已完成）",
        product_model=vcsel.model, status="已完成",
        started_by=vcsel.owner, started_at="2026-06-05", completed_at="2026-06-08",
    )
    db.add(inst_done1)
    db.flush()
    for seq, (name, role, action, assignee) in enumerate([
        ("研发提交", "研发工程师", "提交", vcsel.owner),
        ("工艺评估", "工艺工程师", "审批", "罗富森"),
        ("质量审核", "质量工程师", "审批", "李超"),
        ("ERP下发", "ERP接口账号", "接口", "系统"),
    ], start=1):
        db.add(models.WorkflowTask(instance_id=inst_done1.id, sequence=seq, node_name=name, role_name=role, action_type=action, status="已完成", assignee=assignee, acted_by=assignee, acted_at="2026-06-08", comment="审批通过。", sla_hours=24))

    # VCSEL 变更已完成
    vcsel_changes = changes_by_product.get(vcsel.id, [])
    vcsel_closed = next((c for c in vcsel_changes if c.status == "已关闭"), None)
    if vcsel_closed:
        inst_done2 = models.WorkflowInstance(
            template_id=tpl_chg.id, object_type="变更", object_id=vcsel_closed.id,
            object_no=vcsel_closed.change_no, title=f"{vcsel_closed.title}（已完成）",
            product_model=vcsel.model, status="已完成",
            started_by=vcsel.owner, started_at=vcsel_closed.submitted_at, completed_at="2026-05-10",
        )
        db.add(inst_done2)
        db.flush()
        for seq, (name, role, action, assignee) in enumerate([
            ("ECR申请", "研发工程师", "提交", vcsel.owner),
            ("影响分析", "工艺工程师", "评估", "罗富森"),
            ("质量会签", "质量工程师", "审批", "李超"),
            ("项目批准", "项目经理", "审批", "房磊"),
            ("ECN发布", "系统管理员", "发布", "admin"),
            ("MES/ERP同步", "MES接口账号", "接口", "系统"),
        ], start=1):
            db.add(models.WorkflowTask(instance_id=inst_done2.id, sequence=seq, node_name=name, role_name=role, action_type=action, status="已完成", assignee=assignee, acted_by=assignee, acted_at="2026-05-10", comment="流程已完成。", sla_hours=24))


# ============================================================
# 集成队列（ERP/MES/QMS，每个变更 3 条）
# ============================================================

def _seed_integration_jobs(db: Session, products: list[models.Product], changes_by_product: dict[int, list[models.Change]]) -> None:
    for product in products:
        changes = changes_by_product.get(product.id, [])
        for change in changes:
            # 根据变更状态决定集成任务状态
            if change.status == "已关闭":
                statuses = ["成功", "成功", "成功"]
            elif change.status == "执行中":
                statuses = ["成功", "处理中", "等待"]
            else:  # 审批中
                statuses = ["等待", "等待", "等待"]

            for idx, (system, obj_type, obj_no, status, msg) in enumerate([
                ("ERP", "物料/BOM", f"EBOM-{product.model}", statuses[0], "变更签核完成后下发 ERP 物料与 EBOM 版本。"),
                ("MES", "工艺路线", f"ROUTE-{product.model}", statuses[1], "ECN 生效后下发 MES 工艺路线和管制参数。"),
                ("QMS", "质量文件", f"DOC-{product.model}-REL", statuses[2], "可靠性报告签核后同步 QMS 归档。"),
            ], start=1):
                db.add(models.IntegrationJob(
                    job_no=f"INT-{change.change_no}-{idx:02d}",
                    target_system=system, object_type=obj_type, object_no=obj_no,
                    product_model=product.model, direction="下发", status=status,
                    triggered_by=change.change_no, triggered_at=change.submitted_at,
                    message=msg,
                    last_sync_at="2026-06-15" if status == "成功" else "",
                    response_message="同步成功" if status == "成功" else "",
                ))

    # 额外加 1 条失败的集成任务（验证失败/重试）
    product0 = products[0]
    changes0 = changes_by_product.get(product0.id, [])
    if changes0:
        db.add(models.IntegrationJob(
            job_no=f"INT-{changes0[0].change_no}-04",
            target_system="QMS", object_type="质量文件", object_no=f"DOC-{product0.model}-REL",
            product_model=product0.model, direction="下发", status="失败",
            triggered_by=changes0[0].change_no, triggered_at="2026-06-14",
            message="QMS 接口超时，需要重试。",
            attempt_count=2, last_sync_at="2026-06-14",
            response_message="Connection timeout: QMS service unreachable",
        ))


# ============================================================
# PR 问题报告
# ============================================================

def _seed_problem_reports(db: Session, products: list[models.Product]) -> None:
    product_map = {p.model: p for p in products}
    pr_rows = [
        ("PR-2026-001", "PD-1550-10G 边缘 Wafer 暗电流偏高", "质量异常", "高", "内部", "PD-1550-10G", "试产批次边缘 Wafer 暗电流超规格上限，初步定位为刻蚀后侧壁残留与钝化膜覆盖不足共同影响。", "调整 ICP 清洗步骤和 PECVD 钝化膜厚，受影响 Wafer 追加 LIV/暗电流复测。", "评估中", "李超", "2026-06-16", "ECR-PD-1550-10G-001", ""),
        ("PR-2026-002", "VCSEL-940-3W 光刻 CD 均匀性波动", "工艺问题", "中", "内部", "VCSEL-940-3W", "6 inch 晶圆中心与边缘 CD 差异偏大，可能影响阵列一致性及后续 Wafer map 分选。", "优化光刻曝光剂量分布和显影时间 SPC 管控，增加边缘 CD 监测频次。", "已关闭", "罗富森", "2026-05-18", "ECR-VCSEL-940-3W-002", "已通过工艺优化解决。"),
        ("PR-2026-003", "DFB-1310-25G 封装耦合效率下降", "工艺问题", "中", "客户", "DFB-1310-25G", "客户反馈最近一批耦合功率较前批下降约 8%，怀疑光纤耦合对准偏差或 Die attach 位置漂移。", "核查封装工艺对准精度和点胶量，重新校准耦合台。", "处理中", "于帅兵", "2026-06-22", "ECR-DFB-1310-25G-004", "客户要求 7 月初给出分析报告。"),
        ("PR-2026-004", "SiPh-MZM-400G 流片后波导损耗偏大", "设计问题", "高", "内部", "SiPh-MZM-400G", "流片回来测试发现条波导插损高于仿真预期 0.5dB/cm，疑似刻蚀粗糙度或侧壁角偏差。", "对比仿真与实测 SEM 截面，调整刻蚀气体配比和压力。", "评估中", "张昊", "2026-06-25", "ECR-SiPh-MZM-400G-001", ""),
    ]
    for row in pr_rows:
        product = product_map.get(row[5])
        db.add(models.ProblemReport(
            pr_no=row[0], title=row[1], problem_type=row[2], severity=row[3], source=row[4],
            product_id=product.id if product else None, product_model=row[5],
            description=row[6], suggested_action=row[7], status=row[8], reporter=row[9],
            reported_at=row[10], related_change_no=row[11], remark=row[12],
        ))


# ============================================================
# 工艺参数库
# ============================================================

def _seed_process_parameters(db: Session) -> None:
    param_rows = [
        ("PP-CD-001", "光刻关键线宽 CD", "CD", "nm", "光刻", "120", "100", "140", "i-line Stepper 曝光后线宽控制目标值", "启用"),
        ("PP-CD-002", "光刻接触孔 CD", "CD", "nm", "光刻", "3.0", "2.5", "3.5", "接触孔直径控制，影响接触电阻", "启用"),
        ("PP-OVL-001", "Overlay 套刻精度", "Overlay", "nm", "光刻", "30", "0", "50", "层间套刻误差，影响器件性能和良率", "启用"),
        ("PP-ETCH-001", "ICP 刻蚀深度", "刻蚀深度", "nm", "刻蚀", "200", "180", "220", "Cl2/BCl3 干法刻蚀深度目标", "启用"),
        ("PP-ETCH-002", "刻蚀侧壁角", "刻蚀深度", "°", "刻蚀", "88", "85", "90", "刻蚀剖面角度，影响后续镀膜覆盖", "启用"),
        ("PP-FILM-001", "PVD 金属膜厚", "膜厚", "nm", "薄膜", "300", "280", "320", "Ti/Pt/Au 金属层厚度", "启用"),
        ("PP-FILM-002", "PECVD 介质膜厚", "膜厚", "nm", "薄膜", "500", "450", "550", "SiO2 钝化层厚度", "启用"),
        ("PP-FILM-003", "介质膜折射率", "折射率", "-", "薄膜", "1.46", "1.44", "1.48", "SiO2 折射率，反映薄膜致密性", "启用"),
        ("PP-RSH-001", "金属层片阻", "片阻", "Ω/sq", "薄膜", "0.05", "0.03", "0.08", "金属化层方阻，影响欧姆接触", "启用"),
        ("PP-FILM-004", "薄膜应力", "应力", "MPa", "薄膜", "-50", "-200", "100", "PECVD 薄膜残余应力，负值表示压应力", "启用"),
        ("PP-LIV-001", "阈值电流", "LIV/IV", "mA", "晶圆测试", "5.0", "3.0", "8.0", "VCSEL/DFB 激光器阈值电流", "启用"),
        ("PP-LIV-002", "响应度", "LIV/IV", "A/W", "晶圆测试", "0.85", "0.70", "1.00", "光电探测器响应度", "启用"),
        ("PP-LIV-003", "暗电流", "LIV/IV", "nA", "晶圆测试", "5", "0", "20", "PD 反偏暗电流，影响灵敏度", "启用"),
        ("PP-WMAP-001", "Wafer Map Bin1 良率", "Wafer Map", "%", "晶圆测试", "95", "90", "100", "晶圆级 Bin1 分布良率", "启用"),
        ("PP-ROUGH-001", "刻蚀表面粗糙度", "粗糙度", "nm", "刻蚀", "0.8", "0.3", "1.5", "刻蚀后表面 RMS 粗糙度，影响波导损耗", "启用"),
    ]
    for row in param_rows:
        db.add(models.ProcessParameter(
            param_code=row[0], param_name=row[1], param_type=row[2], unit=row[3],
            category=row[4], default_value=row[5], min_value=row[6], max_value=row[7],
            description=row[8], status=row[9],
        ))

if __name__ == "__main__":
    main()
