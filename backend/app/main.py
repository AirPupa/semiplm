from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from datetime import date

from . import models
from .database import Base, engine, get_db
from .seed import seed_database

app = FastAPI(title="SemiPLM API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PERMISSION_LABELS = {
    "all": "全部权限",
    "system": "系统设置",
    "organization": "组织管理",
    "user": "用户管理",
    "role": "角色权限",
    "workflow": "流程配置",
    "integration": "集成配置",
    "product": "产品主数据",
    "requirement": "需求规格",
    "material": "研发物料",
    "bom": "设计 BOM",
    "document": "文档管理",
    "process": "工艺路线",
    "change": "工程变更",
    "project": "项目管理",
    "quality": "质量闭环",
    "approval": "审批处理",
    "erp": "ERP 接口",
    "mes": "MES 接口",
}

USER_ROLE_FALLBACKS = {
    "admin": "ADMIN",
    "luofusen": "PE_ENGINEER",
    "yushuaibing": "PE_ENGINEER",
    "zhanghao": "PE_ENGINEER",
    "fanglei": "PM_MANAGER",
    "liangweiwei": "IT_ENGINEER",
}


def split_permissions(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]


def current_user_context(
    db: Session = Depends(get_db),
    username: str = Header("admin", alias="X-SemiPLM-User"),
) -> dict:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        user = db.query(models.User).filter(models.User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="No active user")
    role = db.query(models.Role).filter(models.Role.name == user.role, models.Role.status == "启用").first()
    if not role:
        fallback_code = USER_ROLE_FALLBACKS.get(user.username)
        if fallback_code:
            role = db.query(models.Role).filter(models.Role.code == fallback_code, models.Role.status == "启用").first()
    if not role:
        role_keyword = user.role.replace("整合", "")
        role = (
            db.query(models.Role)
            .filter(models.Role.name.like(f"%{role_keyword}%"), models.Role.status == "启用")
            .first()
        )
    permissions = split_permissions(role.permissions if role else "")
    return {"user": user, "role": role, "permissions": permissions}


def has_permission(context: dict, required: str | list[str] | tuple[str, ...]) -> bool:
    permissions = set(context.get("permissions", []))
    if "all" in permissions:
        return True
    required_items = [required] if isinstance(required, str) else list(required)
    return any(item in permissions for item in required_items)


def require_permission(required: str | list[str] | tuple[str, ...]):
    def dependency(context: dict = Depends(current_user_context)) -> dict:
        if not has_permission(context, required):
            raise HTTPException(status_code=403, detail="Permission denied")
        return context

    return dependency


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_lightweight_schema()
    db = next(get_db())
    try:
        seed_database(db)
        normalize_single_org_master_data(db)
    finally:
        db.close()


def ensure_lightweight_schema() -> None:
    columns = {
        "bom_headers": {
            "source_bom_id": "INTEGER",
            "effective_date": "VARCHAR(30) DEFAULT ''",
            "expiry_date": "VARCHAR(30) DEFAULT ''",
            "effectivity_type": "VARCHAR(30) DEFAULT '日期'",
            "effective_batch": "VARCHAR(80) DEFAULT ''",
        },
        "bom_items": {
            "process_step_id": "INTEGER",
            "effective_date": "VARCHAR(30) DEFAULT ''",
            "expiry_date": "VARCHAR(30) DEFAULT ''",
            "effectivity_note": "VARCHAR(160) DEFAULT ''",
        },
        "process_routes": {
            "release_date": "VARCHAR(30) DEFAULT ''",
            "source_route_id": "INTEGER",
            "effective_batch": "VARCHAR(80) DEFAULT ''",
        },
        "integration_jobs": {
            "attempt_count": "INTEGER DEFAULT 0",
            "last_sync_at": "VARCHAR(30) DEFAULT ''",
            "response_message": "TEXT DEFAULT ''",
            "external_id": "VARCHAR(120) DEFAULT ''",
        },
        "change_actions": {
            "target_type": "VARCHAR(40) DEFAULT ''",
            "target_id": "INTEGER",
            "target_version": "VARCHAR(30) DEFAULT ''",
            "effectivity_type": "VARCHAR(30) DEFAULT '日期'",
            "effectivity_scope": "VARCHAR(80) DEFAULT ''",
            "effective_date": "VARCHAR(30) DEFAULT ''",
            "effective_batch": "VARCHAR(80) DEFAULT ''",
            "generated_object_no": "VARCHAR(160) DEFAULT ''",
        },
        "operation_logs": {
            "object_id": "INTEGER",
        },
    }
    with engine.begin() as conn:
        for table, table_columns in columns.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}
            for column, definition in table_columns.items():
                if column not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def normalize_single_org_master_data(db: Session) -> None:
    role_rows = [
        ("ADMIN", "系统管理员", "系统配置、组织角色、接口配置、所有对象维护", "system,user,role,workflow,integration,all"),
        ("PE_ENGINEER", "工艺工程师", "工艺路线、工艺参数、变更影响评估", "process,material,change,approval"),
        ("PM_MANAGER", "项目经理", "NPI 项目、阶段门、计划和风险", "project,workflow,approval"),
        ("IT_ENGINEER", "IT工程师", "系统配置、组织用户角色、流程和接口维护", "organization,system,user,role,workflow,integration"),
    ]
    for code, name, description, permissions in role_rows:
        role = db.query(models.Role).filter(models.Role.code == code).first()
        if role:
            role.name = name
            role.description = description
            role.permissions = permissions
            role.status = "启用"
        else:
            db.add(models.Role(code=code, name=name, description=description, permissions=permissions, status="启用"))

    org = db.query(models.Organization).filter(models.Organization.code == "NZGD").first()
    if org:
        org.name = "南智光电"
        org.org_type = "公司"
        org.parent_code = ""
        org.manager = "梁维维"
        org.status = "启用"
        org.description = "公司主体"
    else:
        db.add(models.Organization(code="NZGD", name="南智光电", org_type="公司", parent_code="", manager="梁维维", status="启用", description="公司主体"))
    dept = db.query(models.Organization).filter(models.Organization.code == "PROD").first()
    if dept:
        dept.name = "生产部"
        dept.org_type = "部门"
        dept.parent_code = "NZGD"
        dept.manager = "房磊"
        dept.status = "启用"
        dept.description = "生产运营部门"
    else:
        db.add(models.Organization(code="PROD", name="生产部", org_type="部门", parent_code="NZGD", manager="房磊", status="启用", description="生产运营部门"))

    stale_users = {"rd01", "pe01", "qa01", "pm01"}
    db.query(models.User).filter(models.User.username.in_(stale_users)).delete(synchronize_session=False)
    user_rows = [
        ("admin", "系统管理员", "管理员", "生产部"),
        ("luofusen", "罗富森", "工艺工程师", "生产部"),
        ("yushuaibing", "于帅兵", "工艺工程师", "生产部"),
        ("zhanghao", "张昊", "工艺工程师", "生产部"),
        ("fanglei", "房磊", "项目经理", "生产部"),
        ("liangweiwei", "梁维维", "IT工程师", "生产部"),
    ]
    for username, display_name, role, department in user_rows:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user:
            user.display_name = display_name
            user.role = role
            user.department = department
        else:
            db.add(models.User(username=username, display_name=display_name, role=role, department=department))

    name_map = {
        "林晨": "罗富森",
        "宋工": "罗富森",
        "许沐": "于帅兵",
        "周宁": "房磊",
        "陈知": "张昊",
        "罗远": "张昊",
    }
    department_map = {
        "平台管理": "生产部",
        "光电工艺部": "生产部",
        "光刻刻蚀镀膜工程部": "生产部",
        "工艺部": "生产部",
        "质量部": "生产部",
        "研发中心": "生产部",
        "工艺工程部": "生产部",
        "制造部": "生产部",
        "文控中心": "生产部",
        "项目管理部": "生产部",
        "IT部": "生产部",
        "项目/制造/质量": "生产部",
    }

    def normalize_text(value: str) -> str:
        for old, new in {**name_map, **department_map}.items():
            value = value.replace(old, new)
        return value

    for model, columns in [
        (models.Product, ["owner"]),
        (models.BomHeader, ["owner"]),
        (models.Document, ["owner"]),
        (models.ProcessRoute, ["owner"]),
        (models.ProcessStep, ["owner"]),
        (models.Change, ["owner", "reason", "before_desc", "after_desc"]),
        (models.ChangeImpact, ["target", "action"]),
        (models.Approval, ["approver", "comment"]),
        (models.ChangeAction, ["department", "owner", "result"]),
        (models.IntegrationEndpoint, ["owner"]),
        (models.Project, ["owner"]),
        (models.ProjectTask, ["owner"]),
        (models.QualityIssue, ["owner"]),
        (models.Requirement, ["owner"]),
        (models.ProductBaseline, ["created_by"]),
        (models.BaselineItem, ["object_no", "title"]),
        (models.CodingRule, ["owner"]),
        (models.WorkflowTask, ["assignee", "acted_by", "comment"]),
        (models.WorkflowInstance, ["started_by"]),
        (models.WorkflowLog, ["actor", "comment"]),
        (models.IntegrationJob, ["triggered_by", "message", "response_message"]),
    ]:
        for row in db.query(model).all():
            for column in columns:
                value = getattr(row, column, "")
                if isinstance(value, str) and value:
                    setattr(row, column, normalize_text(value))

    for action in db.query(models.ChangeAction).all():
        if not action.effectivity_type:
            action.effectivity_type = "日期"
        if not action.effective_date and "日期" in action.effectivity_type:
            action.effective_date = action.due_date or today_text()
        if not action.effective_batch and "LOT-" in action.target_object:
            action.effectivity_type = "日期+批次" if "日期" in action.effectivity_type else "批次"
            action.effective_batch = action.target_object[action.target_object.find("LOT-") :].split()[0]

    test_prefixes = ("ECR-API-VERIFY", "ECR-IMPACT-VERIFY", "ECR-CLOSE-FLOW")
    test_changes = db.query(models.Change).filter(
        (models.Change.change_no.like(f"{test_prefixes[0]}%"))
        | (models.Change.change_no.like(f"{test_prefixes[1]}%"))
        | (models.Change.change_no.like(f"{test_prefixes[2]}%"))
    ).all()
    test_change_ids = [row.id for row in test_changes]
    test_change_nos = [row.change_no for row in test_changes]
    if test_change_ids:
        db.query(models.ChangeAction).filter(models.ChangeAction.change_id.in_(test_change_ids)).delete(synchronize_session=False)
        db.query(models.ChangeImpact).filter(models.ChangeImpact.change_id.in_(test_change_ids)).delete(synchronize_session=False)
        db.query(models.Approval).filter(models.Approval.change_id.in_(test_change_ids)).delete(synchronize_session=False)
        db.query(models.Change).filter(models.Change.id.in_(test_change_ids)).delete(synchronize_session=False)
    if test_change_nos:
        workflow_ids = [
            row.id
            for row in db.query(models.WorkflowInstance.id).filter(models.WorkflowInstance.object_no.in_(test_change_nos)).all()
        ]
        if workflow_ids:
            db.query(models.WorkflowLog).filter(models.WorkflowLog.instance_id.in_(workflow_ids)).delete(synchronize_session=False)
            db.query(models.WorkflowTask).filter(models.WorkflowTask.instance_id.in_(workflow_ids)).delete(synchronize_session=False)
            db.query(models.WorkflowInstance).filter(models.WorkflowInstance.id.in_(workflow_ids)).delete(synchronize_session=False)
        db.query(models.IntegrationJob).filter(models.IntegrationJob.object_no.in_(test_change_nos)).delete(synchronize_session=False)
    db.commit()


def serialize_product(product: models.Product) -> dict:
    return {
        "id": product.id,
        "code": product.code,
        "model": product.model,
        "name": product.name,
        "product_type": product.product_type,
        "process_platform": product.process_platform,
        "wafer_size": product.wafer_size,
        "package_type": product.package_type,
        "temperature_grade": product.temperature_grade,
        "quality_grade": product.quality_grade,
        "application": product.application,
        "lifecycle": product.lifecycle,
        "owner": product.owner,
        "customer_part_no": product.customer_part_no,
        "internal_part_no": product.internal_part_no,
        "version": product.version,
        "readiness": product.readiness,
        "latest_release": product.latest_release,
    }


class ProductPayload(BaseModel):
    code: str
    model: str
    name: str
    product_type: str = "光电芯片"
    process_platform: str = ""
    wafer_size: str = ""
    package_type: str = ""
    temperature_grade: str = ""
    quality_grade: str = ""
    application: str = ""
    lifecycle: str = "设计中"
    owner: str = ""
    customer_part_no: str = ""
    internal_part_no: str = ""
    version: str = "A0"
    readiness: int = 0
    latest_release: str = ""


class ProductVersionPayload(BaseModel):
    version: str
    lifecycle: str = ""
    readiness: int = 0
    released_at: str = ""
    released_by: str = ""
    source_change_no: str = ""
    summary: str = ""


class ProductUpdatePayload(BaseModel):
    code: str | None = None
    model: str | None = None
    name: str | None = None
    product_type: str | None = None
    process_platform: str | None = None
    wafer_size: str | None = None
    package_type: str | None = None
    temperature_grade: str | None = None
    quality_grade: str | None = None
    application: str | None = None
    lifecycle: str | None = None
    owner: str | None = None
    customer_part_no: str | None = None
    internal_part_no: str | None = None
    version: str | None = None
    readiness: int | None = None
    latest_release: str | None = None


class MaterialPayload(BaseModel):
    code: str
    name: str
    category: str
    specification: str = ""
    supplier: str = ""
    risk_level: str = "低"
    lifecycle: str = "有效"


class MaterialUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    specification: str | None = None
    supplier: str | None = None
    risk_level: str | None = None
    lifecycle: str | None = None


class RequirementPayload(BaseModel):
    product_id: int
    req_no: str
    source: str
    category: str
    title: str
    priority: str = "中"
    status: str = "草稿"
    owner: str = ""
    acceptance_criteria: str = ""


class RequirementUpdatePayload(BaseModel):
    product_id: int | None = None
    req_no: str | None = None
    source: str | None = None
    category: str | None = None
    title: str | None = None
    priority: str | None = None
    status: str | None = None
    owner: str | None = None
    acceptance_criteria: str | None = None


class DocumentPayload(BaseModel):
    product_id: int
    doc_no: str
    title: str
    category: str
    version: str = "A0"
    status: str = "编制中"
    owner: str = ""
    approval_status: str = "未提交"
    updated_at: str = ""


class DocumentUpdatePayload(BaseModel):
    product_id: int | None = None
    doc_no: str | None = None
    title: str | None = None
    category: str | None = None
    version: str | None = None
    status: str | None = None
    owner: str | None = None
    approval_status: str | None = None
    updated_at: str | None = None


class BomHeaderPayload(BaseModel):
    product_id: int
    bom_type: str = "EBOM"
    version: str = "A0"
    status: str = "编制中"
    owner: str = ""
    release_date: str = ""
    source_bom_id: int | None = None
    effective_date: str = ""
    expiry_date: str = ""
    effectivity_type: str = "日期"
    effective_batch: str = ""


class BomHeaderUpdatePayload(BaseModel):
    product_id: int | None = None
    bom_type: str | None = None
    version: str | None = None
    status: str | None = None
    owner: str | None = None
    release_date: str | None = None
    source_bom_id: int | None = None
    effective_date: str | None = None
    expiry_date: str | None = None
    effectivity_type: str | None = None
    effective_batch: str | None = None


class BomItemPayload(BaseModel):
    material_code: str
    material_name: str
    category: str = ""
    specification: str = ""
    quantity: float = 1
    unit: str = "件"
    position: str = ""
    process_step_id: int | None = None
    process_step: str = ""
    substitute: str = ""
    status: str = "有效"
    effective_date: str = ""
    expiry_date: str = ""
    effectivity_note: str = ""


class BomItemUpdatePayload(BaseModel):
    material_code: str | None = None
    material_name: str | None = None
    category: str | None = None
    specification: str | None = None
    quantity: float | None = None
    unit: str | None = None
    position: str | None = None
    process_step_id: int | None = None
    process_step: str | None = None
    substitute: str | None = None
    status: str | None = None
    effective_date: str | None = None
    expiry_date: str | None = None
    effectivity_note: str | None = None


class BomTransformPayload(BaseModel):
    target_type: str = "PBOM"
    version: str = "A0"
    owner: str = ""
    effective_date: str = ""
    effectivity_type: str = "日期"
    effective_batch: str = ""


class ProcessRouteActionPayload(BaseModel):
    acted_by: str = "系统用户"
    comment: str = ""


class ProcessRoutePayload(BaseModel):
    product_id: int
    route_no: str
    name: str
    version: str = "A0"
    status: str = "编制中"
    owner: str = ""
    release_date: str = ""
    source_route_id: int | None = None
    effective_batch: str = ""


class ProcessRouteUpdatePayload(BaseModel):
    product_id: int | None = None
    route_no: str | None = None
    name: str | None = None
    version: str | None = None
    status: str | None = None
    owner: str | None = None
    release_date: str | None = None
    source_route_id: int | None = None
    effective_batch: str | None = None


class ProcessStepPayload(BaseModel):
    sequence: int
    stage: str
    operation: str
    key_params: str = ""
    owner: str = ""
    status: str = "有效"


class ProcessStepUpdatePayload(BaseModel):
    sequence: int | None = None
    stage: str | None = None
    operation: str | None = None
    key_params: str | None = None
    owner: str | None = None
    status: str | None = None


class IntegrationJobActionPayload(BaseModel):
    acted_by: str = "系统用户"
    response_message: str = ""
    external_id: str = ""


class ChangePayload(BaseModel):
    product_id: int
    change_no: str
    title: str
    change_type: str = "ECR"
    reason: str = ""
    status: str = "草稿"
    priority: str = "中"
    owner: str = ""
    submitted_at: str = ""
    before_desc: str = ""
    after_desc: str = ""


class ChangeUpdatePayload(BaseModel):
    product_id: int | None = None
    change_no: str | None = None
    title: str | None = None
    change_type: str | None = None
    reason: str | None = None
    status: str | None = None
    priority: str | None = None
    owner: str | None = None
    submitted_at: str | None = None
    before_desc: str | None = None
    after_desc: str | None = None


class ChangeImpactPayload(BaseModel):
    impact_type: str
    target: str
    risk: str = "中"
    action: str = ""


class ChangeImpactUpdatePayload(BaseModel):
    impact_type: str | None = None
    target: str | None = None
    risk: str | None = None
    action: str | None = None


class ChangeActionPayload(BaseModel):
    action_no: str = ""
    action_type: str = "资料更新"
    target_type: str = ""
    target_id: int | None = None
    target_version: str = ""
    target_object: str
    effectivity_type: str = "日期"
    effectivity_scope: str = ""
    effective_date: str = ""
    effective_batch: str = ""
    generated_object_no: str = ""
    department: str = ""
    owner: str = ""
    status: str = "待处理"
    due_date: str = ""
    result: str = ""


class ChangeActionUpdatePayload(BaseModel):
    action_no: str | None = None
    action_type: str | None = None
    target_type: str | None = None
    target_id: int | None = None
    target_version: str | None = None
    target_object: str | None = None
    effectivity_type: str | None = None
    effectivity_scope: str | None = None
    effective_date: str | None = None
    effective_batch: str | None = None
    generated_object_no: str | None = None
    department: str | None = None
    owner: str | None = None
    status: str | None = None
    due_date: str | None = None
    result: str | None = None


class ChangeActionClosePayload(BaseModel):
    acted_by: str = "系统用户"
    result: str = "已完成"


class OrganizationPayload(BaseModel):
    code: str
    name: str
    org_type: str = "部门"
    parent_code: str = "NZGD"
    manager: str = ""
    status: str = "启用"
    description: str = ""


class OrganizationUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    org_type: str | None = None
    parent_code: str | None = None
    manager: str | None = None
    status: str | None = None
    description: str | None = None


class UserPayload(BaseModel):
    username: str
    display_name: str
    role: str
    department: str = "生产部"


class UserUpdatePayload(BaseModel):
    username: str | None = None
    display_name: str | None = None
    role: str | None = None
    department: str | None = None


class RolePayload(BaseModel):
    code: str
    name: str
    description: str = ""
    permissions: str = ""
    status: str = "启用"


class RoleUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    permissions: str | None = None
    status: str | None = None


class CodingRulePayload(BaseModel):
    object_type: str
    code: str
    name: str
    prefix: str
    pattern: str
    current_no: int = 0
    sample: str = ""
    status: str = "启用"
    owner: str = ""


class CodingRuleUpdatePayload(BaseModel):
    object_type: str | None = None
    code: str | None = None
    name: str | None = None
    prefix: str | None = None
    pattern: str | None = None
    current_no: int | None = None
    sample: str | None = None
    status: str | None = None
    owner: str | None = None


class CategoryTemplatePayload(BaseModel):
    object_type: str
    code: str
    name: str
    parent_code: str = ""
    lifecycle_template: str = ""
    coding_rule: str = ""
    status: str = "启用"
    description: str = ""


class CategoryTemplateUpdatePayload(BaseModel):
    object_type: str | None = None
    code: str | None = None
    name: str | None = None
    parent_code: str | None = None
    lifecycle_template: str | None = None
    coding_rule: str | None = None
    status: str | None = None
    description: str | None = None


class AttributeTemplatePayload(BaseModel):
    name: str
    field_key: str
    data_type: str = "文本"
    required: str = "否"
    dictionary_code: str = ""
    default_value: str = ""
    sequence: int = 1


class AttributeTemplateUpdatePayload(BaseModel):
    name: str | None = None
    field_key: str | None = None
    data_type: str | None = None
    required: str | None = None
    dictionary_code: str | None = None
    default_value: str | None = None
    sequence: int | None = None


class LifecycleTemplatePayload(BaseModel):
    code: str
    name: str
    object_type: str
    status: str = "启用"
    description: str = ""


class LifecycleTemplateUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    object_type: str | None = None
    status: str | None = None
    description: str | None = None


class LifecycleStatePayload(BaseModel):
    sequence: int
    name: str
    state_type: str = "中间态"
    allow_edit: str = "是"
    require_workflow: str = "否"
    next_states: str = ""


class LifecycleStateUpdatePayload(BaseModel):
    sequence: int | None = None
    name: str | None = None
    state_type: str | None = None
    allow_edit: str | None = None
    require_workflow: str | None = None
    next_states: str | None = None


class DictionaryItemPayload(BaseModel):
    dict_code: str
    dict_name: str
    item_value: str
    item_label: str
    object_scope: str = ""
    sequence: int = 1
    status: str = "启用"


class DictionaryItemUpdatePayload(BaseModel):
    dict_code: str | None = None
    dict_name: str | None = None
    item_value: str | None = None
    item_label: str | None = None
    object_scope: str | None = None
    sequence: int | None = None
    status: str | None = None


class WorkflowTemplatePayload(BaseModel):
    code: str
    name: str
    object_type: str
    project_type: str = ""
    status: str = "启用"
    description: str = ""


class WorkflowTemplateUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    object_type: str | None = None
    project_type: str | None = None
    status: str | None = None
    description: str | None = None


class WorkflowNodePayload(BaseModel):
    sequence: int
    name: str
    role_name: str
    action_type: str = "审批"
    sla_hours: int = 24


class WorkflowNodeUpdatePayload(BaseModel):
    sequence: int | None = None
    name: str | None = None
    role_name: str | None = None
    action_type: str | None = None
    sla_hours: int | None = None


class IntegrationEndpointPayload(BaseModel):
    code: str
    name: str
    system_type: str
    base_url: str
    auth_type: str = "Token"
    direction: str = "双向"
    status: str = "启用"
    owner: str = ""
    object_scope: str = ""


class IntegrationEndpointUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    system_type: str | None = None
    base_url: str | None = None
    auth_type: str | None = None
    direction: str | None = None
    status: str | None = None
    owner: str | None = None
    object_scope: str | None = None


class SystemParameterPayload(BaseModel):
    param_key: str
    param_value: str = ""
    param_group: str = "系统"
    description: str = ""


class SystemParameterUpdatePayload(BaseModel):
    param_key: str | None = None
    param_value: str | None = None
    param_group: str | None = None
    description: str | None = None


class SubstituteMaterialPayload(BaseModel):
    material_code: str
    material_name: str
    substitute_code: str
    substitute_name: str
    substitute_type: str = "功能替代"
    strategy: str = "一对一"
    risk_level: str = "中"
    status: str = "启用"
    effective_date: str = ""
    expiry_date: str = ""
    description: str = ""


class SubstituteMaterialUpdatePayload(BaseModel):
    material_code: str | None = None
    material_name: str | None = None
    substitute_code: str | None = None
    substitute_name: str | None = None
    substitute_type: str | None = None
    strategy: str | None = None
    risk_level: str | None = None
    status: str | None = None
    effective_date: str | None = None
    expiry_date: str | None = None
    description: str | None = None


class SupplierPayload(BaseModel):
    code: str
    name: str
    supplier_type: str = "材料"
    contact: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    certification: str = ""
    risk_level: str = "中"
    status: str = "启用"
    description: str = ""


class SupplierUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    supplier_type: str | None = None
    contact: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    certification: str | None = None
    risk_level: str | None = None
    status: str | None = None
    description: str | None = None


class ProjectPayload(BaseModel):
    project_no: str
    name: str
    product_model: str = ""
    phase: str = "概念"
    progress: int = 0
    owner: str = ""
    start_date: str = ""
    end_date: str = ""
    risk_level: str = "低"


class ProjectUpdatePayload(BaseModel):
    name: str | None = None
    product_model: str | None = None
    phase: str | None = None
    progress: int | None = None
    owner: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    risk_level: str | None = None


class ProjectTemplatePayload(BaseModel):
    code: str
    name: str
    description: str = ""
    stages: str = '["概念","设计","流片","验证","试产"]'
    status: str = "启用"


class ProjectTemplateUpdatePayload(BaseModel):
    name: str | None = None
    description: str | None = None
    stages: str | None = None
    status: str | None = None


class ProjectDeliverablePayload(BaseModel):
    name: str
    deliverable_type: str
    phase: str
    owner: str = ""
    status: str = "待处理"
    due_date: str = ""
    description: str = ""


class ProjectDeliverableUpdatePayload(BaseModel):
    name: str | None = None
    deliverable_type: str | None = None
    phase: str | None = None
    owner: str | None = None
    status: str | None = None
    due_date: str | None = None
    completed_at: str | None = None
    description: str | None = None


class ProjectRiskPayload(BaseModel):
    risk_type: str = "技术"
    description: str = ""
    impact: str = "中"
    probability: str = "中"
    severity: str = "中"
    owner: str = ""
    status: str = "待处理"
    mitigation: str = ""


class ProjectRiskUpdatePayload(BaseModel):
    risk_type: str | None = None
    description: str | None = None
    impact: str | None = None
    probability: str | None = None
    severity: str | None = None
    owner: str | None = None
    status: str | None = None
    mitigation: str | None = None


class QualityCAPAPayload(BaseModel):
    capa_no: str = ""
    issue_id: int | None = None
    title: str
    source: str = "质量问题"
    root_cause: str = ""
    corrective_action: str = ""
    preventive_action: str = ""
    owner: str = ""
    status: str = "待处理"
    due_date: str = ""
    result: str = ""


class QualityCAPAUpdatePayload(BaseModel):
    title: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    owner: str | None = None
    status: str | None = None
    due_date: str | None = None
    closed_at: str | None = None
    result: str | None = None


class WorkflowTaskActionPayload(BaseModel):
    acted_by: str = "系统用户"
    comment: str = ""


class WorkflowRejectPayload(BaseModel):
    acted_by: str = "系统用户"
    comment: str = ""
    target_sequence: int | None = None


class WorkflowTransferPayload(BaseModel):
    acted_by: str = "系统用户"
    assignee: str
    comment: str = ""


class WorkflowWithdrawPayload(BaseModel):
    acted_by: str = "系统用户"
    comment: str = ""


def commit_or_409(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=message) from exc


def audit_log(db: Session, action: str, object_type: str, object_id: int | None, object_no: str, summary: str, operated_by: str) -> None:
    db.add(models.OperationLog(action=action, object_type=object_type, object_id=object_id, object_no=object_no, summary=summary, operated_by=operated_by, operated_at=today_text()))


def update_model(instance: object, payload: BaseModel) -> None:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, key, value)


def ensure_product_exists(db: Session, product_id: int) -> None:
    if not db.query(models.Product.id).filter(models.Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")


def ensure_project_exists(db: Session, project_id: int) -> None:
    if not db.query(models.Project.id).filter(models.Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")


def today_text() -> str:
    return date.today().isoformat()


def day_before(value: str) -> str:
    if not value:
        return today_text()
    try:
        return date.fromordinal(date.fromisoformat(value).toordinal() - 1).isoformat()
    except ValueError:
        return today_text()


def is_current_effective_bom(row: models.BomHeader) -> bool:
    today = today_text()
    if row.status != "已发布":
        return False
    if row.effective_date and row.effective_date > today:
        return False
    if row.expiry_date and row.expiry_date < today:
        return False
    return True


def next_revision(value: str) -> str:
    text_value = (value or "").strip()
    if not text_value:
        return "A1"
    tail_digits = ""
    for char in reversed(text_value):
        if not char.isdigit():
            break
        tail_digits = char + tail_digits
    if tail_digits:
        prefix = text_value[: len(text_value) - len(tail_digits)]
        width = len(tail_digits)
        return f"{prefix}{int(tail_digits) + 1:0{width}d}"
    if len(text_value) == 1 and "A" <= text_value.upper() <= "Y":
        return chr(ord(text_value.upper()) + 1)
    return f"{text_value}-1"


def next_unique_bom_version(db: Session, source: models.BomHeader) -> str:
    version = next_revision(source.version)
    while db.query(models.BomHeader.id).filter(
        models.BomHeader.product_id == source.product_id,
        models.BomHeader.bom_type == source.bom_type,
        models.BomHeader.version == version,
    ).first():
        version = next_revision(version)
    return version


def next_unique_document_no(db: Session, source: models.Document, version: str) -> str:
    base_no = f"{source.doc_no}-R{version}"
    doc_no = base_no
    suffix = 1
    while db.query(models.Document.id).filter(models.Document.doc_no == doc_no).first():
        suffix += 1
        doc_no = f"{base_no}-{suffix}"
    return doc_no


def next_unique_process_version(db: Session, source: models.ProcessRoute) -> str:
    version = next_revision(source.version)
    while db.query(models.ProcessRoute.id).filter(
        models.ProcessRoute.product_id == source.product_id,
        models.ProcessRoute.version == version,
    ).first():
        version = next_revision(version)
    return version


def next_unique_route_no(db: Session, source: models.ProcessRoute, version: str) -> str:
    base_no = f"{source.route_no}-R{version}"
    route_no = base_no
    suffix = 1
    while db.query(models.ProcessRoute.id).filter(models.ProcessRoute.route_no == route_no).first():
        suffix += 1
        route_no = f"{base_no}-{suffix}"
    return route_no


def close_previous_effective_boms(db: Session, bom: models.BomHeader) -> list[dict]:
    cutoff = day_before(bom.effective_date or today_text())
    rows = (
        db.query(models.BomHeader)
        .filter(
            models.BomHeader.id != bom.id,
            models.BomHeader.product_id == bom.product_id,
            models.BomHeader.bom_type == bom.bom_type,
            models.BomHeader.status == "已发布",
        )
        .all()
    )
    closed = []
    for row in rows:
        if row.effective_date and bom.effective_date and row.effective_date > bom.effective_date:
            continue
        if row.expiry_date and row.expiry_date <= cutoff:
            continue
        row.expiry_date = cutoff
        closed.append({"id": row.id, "type": row.bom_type, "version": row.version, "expiry_date": row.expiry_date})
    return closed


def serialize_bom_item(item: models.BomItem) -> dict:
    return {
        "id": item.id,
        "parent_id": item.parent_id,
        "material_code": item.material_code,
        "material_name": item.material_name,
        "category": item.category,
        "specification": item.specification,
        "quantity": item.quantity,
        "unit": item.unit,
        "position": item.position,
        "process_step_id": item.process_step_id,
        "process_step": item.process_step,
        "substitute": item.substitute,
        "status": item.status,
        "effective_date": item.effective_date,
        "expiry_date": item.expiry_date,
        "effectivity_note": item.effectivity_note,
    }


def serialize_bom(row: models.BomHeader) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "product_model": row.product.model,
        "product_name": row.product.name,
        "bom_type": row.bom_type,
        "type": row.bom_type,
        "version": row.version,
        "status": row.status,
        "owner": row.owner,
        "release_date": row.release_date,
        "source_bom_id": row.source_bom_id,
        "effective_date": row.effective_date,
        "expiry_date": row.expiry_date,
        "effectivity_type": row.effectivity_type,
        "is_current": is_current_effective_bom(row),
        "effective_batch": row.effective_batch,
        "items": [serialize_bom_item(item) for item in sorted(row.items, key=lambda item: item.id)],
    }


def bom_item_compare_key(item: models.BomItem) -> tuple[str, str]:
    return (item.material_code, item.process_step or "")


def serialize_bom_compare_item(kind: str, item: models.BomItem | None, base: models.BomItem | None = None) -> dict:
    active = item or base
    assert active is not None
    return {
        "change_type": kind,
        "material_code": active.material_code,
        "material_name": active.material_name,
        "process_step": active.process_step,
        "from_quantity": base.quantity if base else None,
        "to_quantity": item.quantity if item else None,
        "from_status": base.status if base else "",
        "to_status": item.status if item else "",
        "from_effective_date": base.effective_date if base else "",
        "to_effective_date": item.effective_date if item else "",
    }


def serialize_process_route(row: models.ProcessRoute) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "route_no": row.route_no,
        "name": row.name,
        "product_model": row.product.model,
        "version": row.version,
        "status": row.status,
        "owner": row.owner,
        "release_date": row.release_date,
        "source_route_id": row.source_route_id,
        "effective_batch": row.effective_batch,
        "steps": [
            {
                "id": step.id,
                "sequence": step.sequence,
                "stage": step.stage,
                "operation": step.operation,
                "key_params": step.key_params,
                "owner": step.owner,
                "status": step.status,
            }
            for step in sorted(row.steps, key=lambda item: item.sequence)
        ],
    }


def ensure_route_editable(route: models.ProcessRoute) -> None:
    if route.status == "已发布":
        raise HTTPException(status_code=409, detail="Released process route cannot be modified")


def validate_process_route_ready(route: models.ProcessRoute) -> None:
    if not route.steps:
        raise HTTPException(status_code=409, detail="Process route has no steps")
    sequences = [step.sequence for step in route.steps]
    if len(sequences) != len(set(sequences)):
        raise HTTPException(status_code=409, detail="Process route has duplicate step sequence")
    for step in route.steps:
        if not step.stage.strip() or not step.operation.strip() or not step.key_params.strip():
            raise HTTPException(status_code=409, detail="Process route step is incomplete")


def apply_bom_item_process_binding(db: Session, payload: BomItemPayload | BomItemUpdatePayload, product_id: int) -> dict:
    data = payload.model_dump(exclude_unset=True)
    step_id = data.get("process_step_id")
    if step_id:
        step = (
            db.query(models.ProcessStep)
            .join(models.ProcessRoute)
            .filter(models.ProcessStep.id == step_id, models.ProcessRoute.product_id == product_id)
            .first()
        )
        if not step:
            raise HTTPException(status_code=404, detail="Process step not found for this product")
        data["process_step"] = f"{step.sequence}-{step.stage}"
    return data


def create_integration_job(
    db: Session,
    target_system: str,
    object_type: str,
    object_no: str,
    product_model: str,
    triggered_by: str,
    message: str,
) -> None:
    count = db.query(models.IntegrationJob).count() + 1
    db.add(models.IntegrationJob(
        job_no=f"INT-{today_text().replace('-', '')}-{count:04d}",
        target_system=target_system,
        object_type=object_type,
        object_no=object_no,
        product_model=product_model,
        direction="下发",
        status="等待",
        triggered_by=triggered_by,
        triggered_at=today_text(),
        message=message,
    ))
    db.flush()


def serialize_integration_job(row: models.IntegrationJob) -> dict:
    return {
        "id": row.id,
        "job_no": row.job_no,
        "target_system": row.target_system,
        "object_type": row.object_type,
        "object_no": row.object_no,
        "product_model": row.product_model,
        "direction": row.direction,
        "status": row.status,
        "triggered_by": row.triggered_by,
        "triggered_at": row.triggered_at,
        "message": row.message,
        "attempt_count": row.attempt_count,
        "last_sync_at": row.last_sync_at,
        "response_message": row.response_message,
        "external_id": row.external_id,
    }


def serialize_change_action(row: models.ChangeAction) -> dict:
    return {
        "id": row.id,
        "action_no": row.action_no,
        "action_type": row.action_type,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "target_version": row.target_version,
        "target_object": row.target_object,
        "effectivity_type": row.effectivity_type,
        "effectivity_scope": row.effectivity_scope,
        "effective_date": row.effective_date,
        "effective_batch": row.effective_batch,
        "generated_object_no": row.generated_object_no,
        "department": row.department,
        "owner": row.owner,
        "status": row.status,
        "due_date": row.due_date,
        "result": row.result,
    }


def serialize_change(row: models.Change, db: Session) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "change_no": row.change_no,
        "title": row.title,
        "product_model": row.product.model if row.product else "",
        "change_type": row.change_type,
        "reason": row.reason,
        "status": row.status,
        "priority": row.priority,
        "owner": row.owner,
        "submitted_at": row.submitted_at,
        "before_desc": row.before_desc,
        "after_desc": row.after_desc,
        "impacts": [{"id": impact.id, "type": impact.impact_type, "impact_type": impact.impact_type, "target": impact.target, "risk": impact.risk, "action": impact.action} for impact in row.impacts],
        "approvals": [{"step": approval.step_name, "approver": approval.approver, "status": approval.status, "comment": approval.comment, "approved_at": approval.approved_at} for approval in row.approvals],
        "actions": [
            serialize_change_action(action)
            for action in db.query(models.ChangeAction).filter(models.ChangeAction.change_id == row.id).order_by(models.ChangeAction.id).all()
        ],
    }


def analyze_change_impacts(db: Session, change: models.Change) -> None:
    existing_impacts = db.query(models.ChangeImpact).filter(models.ChangeImpact.change_id == change.id).count()
    existing_actions = db.query(models.ChangeAction).filter(models.ChangeAction.change_id == change.id).count()
    if existing_impacts or existing_actions:
        return

    product = change.product or db.query(models.Product).filter(models.Product.id == change.product_id).first()
    product_model = product.model if product else ""
    boms = (
        db.query(models.BomHeader)
        .filter(models.BomHeader.product_id == change.product_id)
        .order_by(models.BomHeader.bom_type, models.BomHeader.version.desc())
        .all()
    )
    routes = (
        db.query(models.ProcessRoute)
        .filter(models.ProcessRoute.product_id == change.product_id)
        .order_by(models.ProcessRoute.version.desc())
        .all()
    )
    documents = (
        db.query(models.Document)
        .filter(models.Document.product_id == change.product_id)
        .order_by(models.Document.category, models.Document.version.desc())
        .all()
    )

    impacts: list[tuple[str, str, str, str]] = [("产品", product_model, "中", "确认型号主数据、生命周期和版本基线是否需要更新。")]
    impacts.extend((f"{bom.bom_type} BOM", f"{bom.bom_type}-{product_model}-{bom.version}", "高", "评估物料结构、用量、替代料和有效期。") for bom in boms[:4])
    impacts.extend(("工艺路线", route.route_no, "高", "评估工序、工艺参数、站点控制和 MES 下发内容。") for route in routes[:3])
    impacts.extend(("文档", f"{doc.doc_no} / {doc.title}", "中", "评估规格书、流程卡、检验规范和文控发布。") for doc in documents[:4])
    for impact_type, target, risk, action in impacts:
        db.add(models.ChangeImpact(change_id=change.id, impact_type=impact_type, target=target, risk=risk, action=action))

    action_defs: list[dict] = []
    if boms:
        bom = boms[0]
        action_defs.append({
            "action_type": "BOM升版",
            "target_type": "BOM",
            "target_id": bom.id,
            "target_version": bom.version,
            "target_object": f"{bom.bom_type}-{product_model}-{bom.version}",
            "effectivity_type": "日期+批次",
            "effectivity_scope": "版本升版",
            "effective_date": today_text(),
            "effective_batch": f"LOT-{product_model}-2606",
            "department": "生产部",
            "owner": change.owner or "罗富森",
            "result": "根据影响分析生成下一版 BOM 草稿并维护有效期。",
        })
    if routes:
        route = routes[0]
        action_defs.append({
            "action_type": "工艺更新",
            "target_type": "工艺路线",
            "target_id": route.id,
            "target_version": route.version,
            "target_object": route.route_no,
            "effectivity_type": "日期+批次",
            "effectivity_scope": "工艺切换",
            "effective_date": today_text(),
            "effective_batch": f"LOT-{product_model}-2606",
            "department": "生产部",
            "owner": "罗富森",
            "result": "更新工艺路线、工序参数和站点控制。",
        })
    if documents:
        document = documents[0]
        action_defs.append({
            "action_type": "文档发布",
            "target_type": "文档",
            "target_id": document.id,
            "target_version": document.version,
            "target_object": f"{document.doc_no} / {document.title}",
            "effectivity_type": "日期",
            "effectivity_scope": "文档升版",
            "effective_date": today_text(),
            "effective_batch": "",
            "department": "生产部",
            "owner": "于帅兵",
            "result": "生成受影响文档下一版草稿并完成文控发布准备。",
        })
    action_defs.append({
        "action_type": "ECN通知",
        "target_type": "通知",
        "target_id": None,
        "target_version": "",
        "target_object": f"{change.change_no} 变更通知",
        "effectivity_type": "批次",
        "effectivity_scope": "签收跟踪",
        "effective_date": "",
        "effective_batch": f"LOT-{product_model}-2606",
        "department": "生产部",
        "owner": change.owner or "房磊",
        "result": "通知受影响部门并跟踪签收结果。",
    })
    for index, action_data in enumerate(action_defs, start=1):
        db.add(models.ChangeAction(
            change_id=change.id,
            action_no=f"ECA-{change.change_no}-{index:02d}",
            action_type=action_data["action_type"],
            target_type=action_data["target_type"],
            target_id=action_data["target_id"],
            target_version=action_data["target_version"],
            target_object=action_data["target_object"],
            effectivity_type=action_data["effectivity_type"],
            effectivity_scope=action_data["effectivity_scope"],
            effective_date=action_data["effective_date"],
            effective_batch=action_data["effective_batch"],
            department=action_data["department"],
            owner=action_data["owner"],
            status="待处理",
            due_date=today_text(),
            result=action_data["result"],
        ))


def create_change_release_jobs(db: Session, change: models.Change) -> None:
    existing_targets = {
        row.target_system
        for row in db.query(models.IntegrationJob)
        .filter(models.IntegrationJob.object_type == "ECN", models.IntegrationJob.object_no == change.change_no)
        .all()
    }
    if "ERP" not in existing_targets:
        create_integration_job(db, "ERP", "ECN", change.change_no, change.product.model, change.change_no, "工程变更执行完成，等待同步 ERP 物料/BOM 变更通知。")
    if "MES" not in existing_targets:
        create_integration_job(db, "MES", "ECN", change.change_no, change.product.model, change.change_no, "工程变更执行完成，等待同步 MES 工艺和制造切换要求。")


def validate_action_effectivity(action: models.ChangeAction) -> None:
    effectivity_type = action.effectivity_type or "日期"
    if "日期" in effectivity_type and not action.effective_date:
        raise HTTPException(status_code=409, detail="Date-based ECA action requires effective date")
    if "批次" in effectivity_type and not action.effective_batch:
        raise HTTPException(status_code=409, detail="Batch-based ECA action requires effective batch")
    if action.effective_date:
        try:
            date.fromisoformat(action.effective_date)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail="Effective date must use YYYY-MM-DD") from exc


def validate_change_action_target(db: Session, action: models.ChangeAction) -> None:
    validate_action_effectivity(action)
    if action.target_type in {"BOM", "文档", "工艺路线"} and not action.target_id:
        raise HTTPException(status_code=409, detail="Revision ECA action requires target object")

    if action.target_type == "BOM" and action.target_id:
        source = (
            db.query(models.BomHeader)
            .options(selectinload(models.BomHeader.items))
            .filter(models.BomHeader.id == action.target_id)
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="Target BOM not found")
        if action.target_version and action.target_version != source.version:
            raise HTTPException(status_code=409, detail="ECA target version does not match current BOM version")
        if source.status != "已发布":
            raise HTTPException(status_code=409, detail="Only released BOM can be revised by ECA")
        if not source.items:
            raise HTTPException(status_code=409, detail="Target BOM has no items")
        return

    if action.target_type == "文档" and action.target_id:
        source = db.query(models.Document).filter(models.Document.id == action.target_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Target document not found")
        if action.target_version and action.target_version != source.version:
            raise HTTPException(status_code=409, detail="ECA target version does not match current document version")
        if source.status == "已废止":
            raise HTTPException(status_code=409, detail="Obsolete document cannot be revised by ECA")
        return

    if action.target_type == "工艺路线" and action.target_id:
        source = (
            db.query(models.ProcessRoute)
            .options(selectinload(models.ProcessRoute.steps))
            .filter(models.ProcessRoute.id == action.target_id)
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="Target process route not found")
        if action.target_version and action.target_version != source.version:
            raise HTTPException(status_code=409, detail="ECA target version does not match current process route version")
        if source.status not in {"已发布", "有效"}:
            raise HTTPException(status_code=409, detail="Only released process route can be revised by ECA")
        validate_process_route_ready(source)


def validate_eca_generated_object_ready(db: Session, object_type: str, object_id: int, generated_object_no: str) -> None:
    """校验 ECA 生成的对象草稿在提交前已完成 ECA 关闭。"""
    action = (
        db.query(models.ChangeAction)
        .filter(
            models.ChangeAction.target_type == object_type,
            models.ChangeAction.generated_object_no == generated_object_no,
        )
        .first()
    )
    if action and action.status != "已完成":
        change = db.query(models.Change).filter(models.Change.id == action.change_id).first()
        raise HTTPException(
            status_code=409,
            detail=f"Object was generated by ECA action {action.action_no} (change: {change.change_no if change else 'N/A'}), "
            f"which has status '{action.status}'. Close the ECA action first before submitting.",
        )



def apply_change_action_revision(db: Session, action: models.ChangeAction) -> str:
    if action.generated_object_no:
        return action.generated_object_no

    validate_change_action_target(db, action)
    effective_date = action.effective_date or today_text()
    if action.target_type == "BOM" and action.target_id:
        source = db.query(models.BomHeader).options(selectinload(models.BomHeader.items), selectinload(models.BomHeader.product)).filter(models.BomHeader.id == action.target_id).first()
        if not source:
            return ""
        new_version = next_unique_bom_version(db, source)
        new_bom = models.BomHeader(
            product_id=source.product_id,
            bom_type=source.bom_type,
            version=new_version,
            status="编制中",
            owner=action.owner or source.owner,
            release_date="",
            source_bom_id=source.id,
            effective_date=effective_date,
            expiry_date="",
            effectivity_type=action.effectivity_type or "变更生效",
            effective_batch=action.effective_batch or "",
        )
        db.add(new_bom)
        db.flush()
        item_id_map: dict[int, int] = {}
        for source_item in sorted(source.items, key=lambda item: item.id):
            new_item = models.BomItem(
                bom_id=new_bom.id,
                parent_id=item_id_map.get(source_item.parent_id),
                material_code=source_item.material_code,
                material_name=source_item.material_name,
                category=source_item.category,
                specification=source_item.specification,
                quantity=source_item.quantity,
                unit=source_item.unit,
                position=source_item.position,
                process_step_id=source_item.process_step_id,
                process_step=source_item.process_step,
                substitute=source_item.substitute,
                status=source_item.status,
                effective_date=source_item.effective_date or effective_date,
                expiry_date=source_item.expiry_date,
                effectivity_note=source_item.effectivity_note or action.effective_batch,
            )
            db.add(new_item)
            db.flush()
            item_id_map[source_item.id] = new_item.id
        product_model = source.product.model if source.product else str(source.product_id)
        action.generated_object_no = f"{source.bom_type}-{product_model}-{new_version}"
        action.target_version = source.version
        return action.generated_object_no

    if action.target_type == "文档" and action.target_id:
        source = db.query(models.Document).filter(models.Document.id == action.target_id).first()
        if not source:
            return ""
        new_version = next_revision(source.version)
        new_doc_no = next_unique_document_no(db, source, new_version)
        db.add(models.Document(
            product_id=source.product_id,
            doc_no=new_doc_no,
            title=source.title,
            category=source.category,
            version=new_version,
            status="编制中",
            owner=action.owner or source.owner,
            approval_status="未提交",
            updated_at=effective_date,
        ))
        db.flush()
        action.generated_object_no = new_doc_no
        action.target_version = source.version
        return action.generated_object_no

    if action.target_type == "工艺路线" and action.target_id:
        source = (
            db.query(models.ProcessRoute)
            .options(selectinload(models.ProcessRoute.steps), selectinload(models.ProcessRoute.product))
            .filter(models.ProcessRoute.id == action.target_id)
            .first()
        )
        if not source:
            return ""
        new_version = next_unique_process_version(db, source)
        new_route_no = next_unique_route_no(db, source, new_version)
        new_route = models.ProcessRoute(
            product_id=source.product_id,
            route_no=new_route_no,
            name=source.name,
            version=new_version,
            status="编制中",
            owner=action.owner or source.owner,
            release_date="",
            source_route_id=source.id,
            effective_batch=action.effective_batch or "",
        )
        db.add(new_route)
        db.flush()
        for source_step in sorted(source.steps, key=lambda item: item.sequence):
            db.add(models.ProcessStep(
                route_id=new_route.id,
                sequence=source_step.sequence,
                stage=source_step.stage,
                operation=source_step.operation,
                key_params=source_step.key_params,
                owner=action.owner or source_step.owner,
                status=source_step.status,
            ))
        db.flush()
        action.generated_object_no = new_route_no
        action.target_version = source.version
        return action.generated_object_no

    return ""


def close_change_when_actions_done(db: Session, change_id: int, acted_by: str) -> bool:
    change = db.query(models.Change).options(selectinload(models.Change.product)).filter(models.Change.id == change_id).first()
    if not change or change.status == "已关闭":
        return False
    actions = db.query(models.ChangeAction).filter(models.ChangeAction.change_id == change_id).all()
    if not actions or any(action.status != "已完成" for action in actions):
        return False
    change.status = "已关闭"
    create_change_release_jobs(db, change)
    instance = (
        db.query(models.WorkflowInstance)
        .filter(models.WorkflowInstance.object_type == "变更", models.WorkflowInstance.object_id == change_id)
        .order_by(models.WorkflowInstance.id.desc())
        .first()
    )
    if instance:
        add_workflow_log(db, instance.id, None, "变更关闭", acted_by, "全部 ECA 执行动作已关闭", "执行中", "已关闭")
    return True


def add_workflow_log(
    db: Session,
    instance_id: int,
    task_id: int | None,
    action: str,
    actor: str,
    comment: str,
    from_status: str,
    to_status: str,
) -> None:
    db.add(models.WorkflowLog(
        instance_id=instance_id,
        task_id=task_id,
        action=action,
        actor=actor,
        acted_at=today_text(),
        comment=comment,
        from_status=from_status,
        to_status=to_status,
    ))


def serialize_workflow_instance(row: models.WorkflowInstance) -> dict:
    return {
        "id": row.id,
        "template_id": row.template_id,
        "template_name": row.template.name if row.template else "",
        "object_type": row.object_type,
        "object_id": row.object_id,
        "object_no": row.object_no,
        "title": row.title,
        "product_model": row.product_model,
        "status": row.status,
        "started_by": row.started_by,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "tasks": [
            {
                "id": task.id,
                "sequence": task.sequence,
                "node_name": task.node_name,
                "role_name": task.role_name,
                "action_type": task.action_type,
                "status": task.status,
                "assignee": task.assignee,
                "acted_by": task.acted_by,
                "acted_at": task.acted_at,
                "comment": task.comment,
                "sla_hours": task.sla_hours,
            }
            for task in sorted(row.tasks, key=lambda item: item.sequence)
        ],
        "logs": [
            {
                "id": log.id,
                "task_id": log.task_id,
                "action": log.action,
                "actor": log.actor,
                "acted_at": log.acted_at,
                "comment": log.comment,
                "from_status": log.from_status,
                "to_status": log.to_status,
            }
            for log in sorted(getattr(row, "logs", []), key=lambda item: item.id)
        ],
    }


def serialize_coding_rule(row: models.CodingRule) -> dict:
    return {
        "id": row.id,
        "object_type": row.object_type,
        "code": row.code,
        "name": row.name,
        "prefix": row.prefix,
        "pattern": row.pattern,
        "current_no": row.current_no,
        "sample": row.sample,
        "status": row.status,
        "owner": row.owner,
    }


def serialize_category_template(row: models.CategoryTemplate) -> dict:
    return {
        "id": row.id,
        "object_type": row.object_type,
        "code": row.code,
        "name": row.name,
        "parent_code": row.parent_code,
        "lifecycle_template": row.lifecycle_template,
        "coding_rule": row.coding_rule,
        "status": row.status,
        "description": row.description,
        "attributes": [
            {
                "id": item.id,
                "name": item.name,
                "field_key": item.field_key,
                "data_type": item.data_type,
                "required": item.required,
                "dictionary_code": item.dictionary_code,
                "default_value": item.default_value,
                "sequence": item.sequence,
            }
            for item in sorted(row.attributes, key=lambda attr: attr.sequence)
        ],
    }


def serialize_lifecycle_template(row: models.LifecycleTemplate) -> dict:
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "object_type": row.object_type,
        "status": row.status,
        "description": row.description,
        "states": [
            {
                "id": item.id,
                "sequence": item.sequence,
                "name": item.name,
                "state_type": item.state_type,
                "allow_edit": item.allow_edit,
                "require_workflow": item.require_workflow,
                "next_states": item.next_states,
            }
            for item in sorted(row.states, key=lambda state: state.sequence)
        ],
    }


def serialize_dictionary_item(row: models.DictionaryItem) -> dict:
    return {
        "id": row.id,
        "dict_code": row.dict_code,
        "dict_name": row.dict_name,
        "item_value": row.item_value,
        "item_label": row.item_label,
        "object_scope": row.object_scope,
        "sequence": row.sequence,
        "status": row.status,
    }


def start_workflow(
    db: Session,
    template_code: str,
    object_type: str,
    object_id: int,
    object_no: str,
    title: str,
    product_model: str,
    started_by: str,
) -> models.WorkflowInstance:
    existing = (
        db.query(models.WorkflowInstance)
        .filter(
            models.WorkflowInstance.object_type == object_type,
            models.WorkflowInstance.object_id == object_id,
            models.WorkflowInstance.status == "运行中",
        )
        .first()
    )
    if existing:
        return existing
    template = (
        db.query(models.WorkflowTemplate)
        .options(selectinload(models.WorkflowTemplate.nodes))
        .filter(models.WorkflowTemplate.code == template_code, models.WorkflowTemplate.status == "启用")
        .first()
    )
    if not template:
        raise HTTPException(status_code=409, detail=f"Workflow template {template_code} is not enabled")
    instance = models.WorkflowInstance(
        template_id=template.id,
        object_type=object_type,
        object_id=object_id,
        object_no=object_no,
        title=title,
        product_model=product_model,
        status="运行中",
        started_by=started_by,
        started_at=today_text(),
    )
    db.add(instance)
    db.flush()
    for index, node in enumerate(sorted(template.nodes, key=lambda item: item.sequence)):
        db.add(models.WorkflowTask(
            instance_id=instance.id,
            sequence=node.sequence,
            node_name=node.name,
            role_name=node.role_name,
            action_type=node.action_type,
            status="待处理" if index == 0 else "未开始",
            sla_hours=node.sla_hours,
        ))
    return instance


def complete_business_object(db: Session, instance: models.WorkflowInstance) -> None:
    instance.status = "已完成"
    instance.completed_at = today_text()
    if instance.object_type == "BOM":
        bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product)).filter(models.BomHeader.id == instance.object_id).first()
        if bom:
            bom.status = "已发布"
            bom.release_date = today_text()
            create_integration_job(db, "ERP", "BOM", f"{bom.bom_type}-{bom.product.model}-{bom.version}", bom.product.model, instance.object_no, "BOM 流程已完成，等待同步 ERP 物料结构和用量。")
    elif instance.object_type == "文档":
        document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == instance.object_id).first()
        if document:
            document.status = "已发布"
            document.approval_status = "已签核"
            document.updated_at = today_text()
            create_integration_job(db, "QMS", "文档", document.doc_no, document.product.model, document.doc_no, "文档流程已完成，等待同步 QMS/文控归档。")
    elif instance.object_type == "变更":
        change = db.query(models.Change).options(selectinload(models.Change.product)).filter(models.Change.id == instance.object_id).first()
        if change:
            change.status = "执行中"
            if not change.submitted_at:
                change.submitted_at = today_text()
            close_change_when_actions_done(db, change.id, "系统")


def withdraw_business_object(db: Session, instance: models.WorkflowInstance) -> None:
    if instance.object_type == "BOM":
        bom = db.query(models.BomHeader).filter(models.BomHeader.id == instance.object_id).first()
        if bom and bom.status != "已发布":
            bom.status = "编制中"
    elif instance.object_type == "文档":
        document = db.query(models.Document).filter(models.Document.id == instance.object_id).first()
        if document and document.status != "已发布":
            document.status = "编制中"
            document.approval_status = "未提交"
            document.updated_at = today_text()
    elif instance.object_type == "变更":
        change = db.query(models.Change).filter(models.Change.id == instance.object_id).first()
        if change and change.status != "已关闭":
            change.status = "草稿"


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/session/current")
def session_current(context: dict = Depends(current_user_context)) -> dict:
    user = context["user"]
    role = context["role"]
    permissions = context["permissions"]
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "department": user.department,
        },
        "role": {
            "id": role.id if role else None,
            "code": role.code if role else "",
            "name": role.name if role else user.role,
            "description": role.description if role else "",
            "status": role.status if role else "未配置",
        },
        "permissions": permissions,
        "permission_labels": {key: PERMISSION_LABELS.get(key, key) for key in permissions},
    }


@app.get("/api/admin/roles")
def roles(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": row.id, "code": row.code, "name": row.name, "description": row.description, "permissions": row.permissions, "status": row.status}
        for row in db.query(models.Role).order_by(models.Role.id).all()
    ]


@app.get("/api/admin/organizations")
def organizations(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": row.id, "code": row.code, "name": row.name, "org_type": row.org_type, "parent_code": row.parent_code, "manager": row.manager, "status": row.status, "description": row.description}
        for row in db.query(models.Organization).order_by(models.Organization.org_type, models.Organization.id).all()
    ]


@app.post("/api/admin/organizations", status_code=201)
def create_organization(payload: OrganizationPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("organization"))) -> dict:
    row = models.Organization(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Organization code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code, "name": row.name, "org_type": row.org_type, "parent_code": row.parent_code, "manager": row.manager, "status": row.status, "description": row.description}


@app.put("/api/admin/organizations/{org_id}")
def update_organization(org_id: int, payload: OrganizationUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("organization"))) -> dict:
    row = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    update_model(row, payload)
    commit_or_409(db, "Organization code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code, "name": row.name, "org_type": row.org_type, "parent_code": row.parent_code, "manager": row.manager, "status": row.status, "description": row.description}


@app.delete("/api/admin/organizations/{org_id}")
def delete_organization(org_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("organization"))) -> dict:
    row = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    if row.code in {"NZGD", "PROD"}:
        raise HTTPException(status_code=409, detail="Built-in single organization cannot be deleted")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@app.post("/api/admin/roles", status_code=201)
def create_role(payload: RolePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("role"))) -> dict:
    role = models.Role(**payload.model_dump())
    db.add(role)
    commit_or_409(db, "Role code already exists")
    db.refresh(role)
    return {"id": role.id, "code": role.code, "name": role.name, "description": role.description, "permissions": role.permissions, "status": role.status}


@app.put("/api/admin/roles/{role_id}")
def update_role(role_id: int, payload: RoleUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("role"))) -> dict:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    update_model(role, payload)
    commit_or_409(db, "Role code already exists")
    db.refresh(role)
    return {"id": role.id, "code": role.code, "name": role.name, "description": role.description, "permissions": role.permissions, "status": role.status}


@app.delete("/api/admin/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("role"))) -> dict:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if db.query(models.User).filter(models.User.role == role.name).count():
        raise HTTPException(status_code=409, detail="Role is used by users")
    db.delete(role)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/foundation/coding-rules")
def coding_rules(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.CodingRule).order_by(models.CodingRule.object_type, models.CodingRule.id).all()
    return [serialize_coding_rule(row) for row in rows]


@app.post("/api/admin/foundation/coding-rules", status_code=201)
def create_coding_rule(payload: CodingRulePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = models.CodingRule(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Coding rule code already exists")
    db.refresh(row)
    return serialize_coding_rule(row)


@app.put("/api/admin/foundation/coding-rules/{rule_id}")
def update_coding_rule(rule_id: int, payload: CodingRuleUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.CodingRule).filter(models.CodingRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Coding rule not found")
    update_model(row, payload)
    commit_or_409(db, "Coding rule code already exists")
    db.refresh(row)
    return serialize_coding_rule(row)


@app.delete("/api/admin/foundation/coding-rules/{rule_id}")
def delete_coding_rule(rule_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.CodingRule).filter(models.CodingRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Coding rule not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/foundation/categories")
def category_templates(db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(models.CategoryTemplate)
        .options(selectinload(models.CategoryTemplate.attributes))
        .order_by(models.CategoryTemplate.object_type, models.CategoryTemplate.id)
        .all()
    )
    return [serialize_category_template(row) for row in rows]


@app.post("/api/admin/foundation/categories", status_code=201)
def create_category_template(payload: CategoryTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = models.CategoryTemplate(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Category code already exists")
    db.refresh(row)
    return serialize_category_template(row)


@app.put("/api/admin/foundation/categories/{category_id}")
def update_category_template(category_id: int, payload: CategoryTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = (
        db.query(models.CategoryTemplate)
        .options(selectinload(models.CategoryTemplate.attributes))
        .filter(models.CategoryTemplate.id == category_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Category not found")
    update_model(row, payload)
    commit_or_409(db, "Category code already exists")
    db.refresh(row)
    return serialize_category_template(row)


@app.delete("/api/admin/foundation/categories/{category_id}")
def delete_category_template(category_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.CategoryTemplate).filter(models.CategoryTemplate.id == category_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@app.post("/api/admin/foundation/categories/{category_id}/attributes", status_code=201)
def create_attribute_template(category_id: int, payload: AttributeTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    if not db.query(models.CategoryTemplate.id).filter(models.CategoryTemplate.id == category_id).first():
        raise HTTPException(status_code=404, detail="Category not found")
    row = models.AttributeTemplate(category_id=category_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "field_key": row.field_key, "data_type": row.data_type, "required": row.required, "dictionary_code": row.dictionary_code, "default_value": row.default_value, "sequence": row.sequence}


@app.put("/api/admin/foundation/attributes/{attribute_id}")
def update_attribute_template(attribute_id: int, payload: AttributeTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.AttributeTemplate).filter(models.AttributeTemplate.id == attribute_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Attribute not found")
    update_model(row, payload)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "field_key": row.field_key, "data_type": row.data_type, "required": row.required, "dictionary_code": row.dictionary_code, "default_value": row.default_value, "sequence": row.sequence}


@app.delete("/api/admin/foundation/attributes/{attribute_id}")
def delete_attribute_template(attribute_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.AttributeTemplate).filter(models.AttributeTemplate.id == attribute_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Attribute not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/foundation/lifecycles")
def lifecycle_templates(db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(models.LifecycleTemplate)
        .options(selectinload(models.LifecycleTemplate.states))
        .order_by(models.LifecycleTemplate.object_type, models.LifecycleTemplate.id)
        .all()
    )
    return [serialize_lifecycle_template(row) for row in rows]


@app.post("/api/admin/foundation/lifecycles", status_code=201)
def create_lifecycle_template(payload: LifecycleTemplatePayload, db: Session = Depends(get_db)) -> dict:
    row = models.LifecycleTemplate(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Lifecycle code already exists")
    db.refresh(row)
    return serialize_lifecycle_template(row)


@app.put("/api/admin/foundation/lifecycles/{template_id}")
def update_lifecycle_template(template_id: int, payload: LifecycleTemplateUpdatePayload, db: Session = Depends(get_db)) -> dict:
    row = (
        db.query(models.LifecycleTemplate)
        .options(selectinload(models.LifecycleTemplate.states))
        .filter(models.LifecycleTemplate.id == template_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle not found")
    update_model(row, payload)
    commit_or_409(db, "Lifecycle code already exists")
    db.refresh(row)
    return serialize_lifecycle_template(row)


@app.delete("/api/admin/foundation/lifecycles/{template_id}")
def delete_lifecycle_template(template_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.LifecycleTemplate).filter(models.LifecycleTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@app.post("/api/admin/foundation/lifecycles/{template_id}/states", status_code=201)
def create_lifecycle_state(template_id: int, payload: LifecycleStatePayload, db: Session = Depends(get_db)) -> dict:
    if not db.query(models.LifecycleTemplate.id).filter(models.LifecycleTemplate.id == template_id).first():
        raise HTTPException(status_code=404, detail="Lifecycle not found")
    row = models.LifecycleState(template_id=template_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "sequence": row.sequence, "name": row.name, "state_type": row.state_type, "allow_edit": row.allow_edit, "require_workflow": row.require_workflow, "next_states": row.next_states}


@app.put("/api/admin/foundation/lifecycle-states/{state_id}")
def update_lifecycle_state(state_id: int, payload: LifecycleStateUpdatePayload, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.LifecycleState).filter(models.LifecycleState.id == state_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle state not found")
    update_model(row, payload)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "sequence": row.sequence, "name": row.name, "state_type": row.state_type, "allow_edit": row.allow_edit, "require_workflow": row.require_workflow, "next_states": row.next_states}


@app.delete("/api/admin/foundation/lifecycle-states/{state_id}")
def delete_lifecycle_state(state_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.LifecycleState).filter(models.LifecycleState.id == state_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle state not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/foundation/dictionaries")
def dictionary_items(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.DictionaryItem).order_by(models.DictionaryItem.dict_code, models.DictionaryItem.sequence, models.DictionaryItem.id).all()
    return [serialize_dictionary_item(row) for row in rows]


@app.post("/api/admin/foundation/dictionaries", status_code=201)
def create_dictionary_item(payload: DictionaryItemPayload, db: Session = Depends(get_db)) -> dict:
    row = models.DictionaryItem(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_dictionary_item(row)


@app.put("/api/admin/foundation/dictionaries/{item_id}")
def update_dictionary_item(item_id: int, payload: DictionaryItemUpdatePayload, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.DictionaryItem).filter(models.DictionaryItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Dictionary item not found")
    update_model(row, payload)
    db.commit()
    db.refresh(row)
    return serialize_dictionary_item(row)


@app.delete("/api/admin/foundation/dictionaries/{item_id}")
def delete_dictionary_item(item_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.DictionaryItem).filter(models.DictionaryItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Dictionary item not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/users")
def users(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": row.id, "username": row.username, "display_name": row.display_name, "role": row.role, "department": row.department}
        for row in db.query(models.User).order_by(models.User.id).all()
    ]


@app.post("/api/admin/users", status_code=201)
def create_user(payload: UserPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("user"))) -> dict:
    user = models.User(**payload.model_dump())
    db.add(user)
    commit_or_409(db, "Username already exists")
    db.refresh(user)
    return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role, "department": user.department}


@app.put("/api/admin/users/{user_id}")
def update_user(user_id: int, payload: UserUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("user"))) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_model(user, payload)
    commit_or_409(db, "Username already exists")
    db.refresh(user)
    return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role, "department": user.department}


@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("user"))) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == "admin":
        raise HTTPException(status_code=409, detail="Built-in admin cannot be deleted")
    db.delete(user)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/workflows")
def workflow_templates(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.WorkflowTemplate).options(selectinload(models.WorkflowTemplate.nodes)).order_by(models.WorkflowTemplate.id).all()
    return [
        {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "object_type": row.object_type,
            "project_type": row.project_type,
            "status": row.status,
            "description": row.description,
            "nodes": [
                {"id": node.id, "sequence": node.sequence, "name": node.name, "role_name": node.role_name, "action_type": node.action_type, "sla_hours": node.sla_hours}
                for node in sorted(row.nodes, key=lambda item: item.sequence)
            ],
        }
        for row in rows
    ]


@app.post("/api/admin/workflows", status_code=201)
def create_workflow_template(payload: WorkflowTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    template = models.WorkflowTemplate(**payload.model_dump())
    db.add(template)
    commit_or_409(db, "Workflow code already exists")
    db.refresh(template)
    return {"id": template.id, "code": template.code, "name": template.name, "object_type": template.object_type, "project_type": template.project_type, "status": template.status, "description": template.description, "nodes": []}


@app.put("/api/admin/workflows/{workflow_id}")
def update_workflow_template(workflow_id: int, payload: WorkflowTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    template = db.query(models.WorkflowTemplate).filter(models.WorkflowTemplate.id == workflow_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Workflow not found")
    update_model(template, payload)
    commit_or_409(db, "Workflow code already exists")
    db.refresh(template)
    return {"id": template.id, "code": template.code, "name": template.name, "object_type": template.object_type, "project_type": template.project_type, "status": template.status, "description": template.description}


@app.delete("/api/admin/workflows/{workflow_id}")
def delete_workflow_template(workflow_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    template = db.query(models.WorkflowTemplate).filter(models.WorkflowTemplate.id == workflow_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db.delete(template)
    db.commit()
    return {"deleted": True}


@app.post("/api/admin/workflows/{workflow_id}/nodes", status_code=201)
def create_workflow_node(workflow_id: int, payload: WorkflowNodePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    if not db.query(models.WorkflowTemplate.id).filter(models.WorkflowTemplate.id == workflow_id).first():
        raise HTTPException(status_code=404, detail="Workflow not found")
    node = models.WorkflowNode(template_id=workflow_id, **payload.model_dump())
    db.add(node)
    db.commit()
    db.refresh(node)
    return {"id": node.id, "sequence": node.sequence, "name": node.name, "role_name": node.role_name, "action_type": node.action_type, "sla_hours": node.sla_hours}


@app.put("/api/admin/workflow-nodes/{node_id}")
def update_workflow_node(node_id: int, payload: WorkflowNodeUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    node = db.query(models.WorkflowNode).filter(models.WorkflowNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Workflow node not found")
    update_model(node, payload)
    db.commit()
    db.refresh(node)
    return {"id": node.id, "sequence": node.sequence, "name": node.name, "role_name": node.role_name, "action_type": node.action_type, "sla_hours": node.sla_hours}


@app.delete("/api/admin/workflow-nodes/{node_id}")
def delete_workflow_node(node_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    node = db.query(models.WorkflowNode).filter(models.WorkflowNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Workflow node not found")
    db.delete(node)
    db.commit()
    return {"deleted": True}


@app.get("/api/admin/integration-endpoints")
def integration_endpoints(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "system_type": row.system_type,
            "base_url": row.base_url,
            "auth_type": row.auth_type,
            "direction": row.direction,
            "status": row.status,
            "owner": row.owner,
            "object_scope": row.object_scope,
        }
        for row in db.query(models.IntegrationEndpoint).order_by(models.IntegrationEndpoint.id).all()
    ]


@app.post("/api/admin/integration-endpoints", status_code=201)
def create_integration_endpoint(payload: IntegrationEndpointPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    endpoint = models.IntegrationEndpoint(**payload.model_dump())
    db.add(endpoint)
    commit_or_409(db, "Endpoint code already exists")
    db.refresh(endpoint)
    return {"id": endpoint.id, "code": endpoint.code, "name": endpoint.name, "system_type": endpoint.system_type, "base_url": endpoint.base_url, "auth_type": endpoint.auth_type, "direction": endpoint.direction, "status": endpoint.status, "owner": endpoint.owner, "object_scope": endpoint.object_scope}


@app.put("/api/admin/integration-endpoints/{endpoint_id}")
def update_integration_endpoint(endpoint_id: int, payload: IntegrationEndpointUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    endpoint = db.query(models.IntegrationEndpoint).filter(models.IntegrationEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    update_model(endpoint, payload)
    commit_or_409(db, "Endpoint code already exists")
    db.refresh(endpoint)
    return {"id": endpoint.id, "code": endpoint.code, "name": endpoint.name, "system_type": endpoint.system_type, "base_url": endpoint.base_url, "auth_type": endpoint.auth_type, "direction": endpoint.direction, "status": endpoint.status, "owner": endpoint.owner, "object_scope": endpoint.object_scope}


@app.delete("/api/admin/integration-endpoints/{endpoint_id}")
def delete_integration_endpoint(endpoint_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    endpoint = db.query(models.IntegrationEndpoint).filter(models.IntegrationEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    db.delete(endpoint)
    db.commit()
    return {"deleted": True}


@app.get("/api/workflow-instances")
def workflow_instances(db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(models.WorkflowInstance)
        .options(
            selectinload(models.WorkflowInstance.template),
            selectinload(models.WorkflowInstance.tasks),
            selectinload(models.WorkflowInstance.logs),
        )
        .order_by(models.WorkflowInstance.id.desc())
        .all()
    )
    return [serialize_workflow_instance(row) for row in rows]


@app.get("/api/workflow-tasks")
def workflow_tasks(db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(models.WorkflowTask)
        .join(models.WorkflowInstance)
        .options(selectinload(models.WorkflowTask.instance).selectinload(models.WorkflowInstance.template))
        .order_by(models.WorkflowTask.status.desc(), models.WorkflowTask.id)
        .all()
    )
    return [
        {
            "id": row.id,
            "instance_id": row.instance_id,
            "object_type": row.instance.object_type,
            "object_no": row.instance.object_no,
            "title": row.instance.title,
            "product_model": row.instance.product_model,
            "template_name": row.instance.template.name if row.instance.template else "",
            "sequence": row.sequence,
            "node_name": row.node_name,
            "role_name": row.role_name,
            "action_type": row.action_type,
            "status": row.status,
            "assignee": row.assignee,
            "acted_by": row.acted_by,
            "acted_at": row.acted_at,
            "comment": row.comment,
            "sla_hours": row.sla_hours,
        }
        for row in rows
    ]


@app.post("/api/workflow-tasks/{task_id}/approve")
def approve_workflow_task(task_id: int, payload: WorkflowTaskActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("approval"))) -> dict:
    task = (
        db.query(models.WorkflowTask)
        .options(selectinload(models.WorkflowTask.instance).selectinload(models.WorkflowInstance.tasks))
        .filter(models.WorkflowTask.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    if task.status != "待处理":
        raise HTTPException(status_code=409, detail="Only pending workflow task can be approved")
    old_status = task.status
    task.status = "已通过"
    task.acted_by = payload.acted_by
    task.acted_at = today_text()
    task.comment = payload.comment
    add_workflow_log(db, task.instance_id, task.id, "通过", payload.acted_by, payload.comment, old_status, task.status)

    next_task = (
        db.query(models.WorkflowTask)
        .filter(
            models.WorkflowTask.instance_id == task.instance_id,
            models.WorkflowTask.sequence > task.sequence,
            models.WorkflowTask.status == "未开始",
        )
        .order_by(models.WorkflowTask.sequence)
        .first()
    )
    if next_task:
        old_next_status = next_task.status
        next_task.status = "待处理"
        add_workflow_log(db, next_task.instance_id, next_task.id, "激活节点", payload.acted_by, f"上一节点 {task.node_name} 已通过", old_next_status, next_task.status)
    else:
        old_instance_status = task.instance.status
        complete_business_object(db, task.instance)
        add_workflow_log(db, task.instance_id, None, "流程完成", payload.acted_by, "全部节点已通过", old_instance_status, task.instance.status)

    db.commit()
    db.refresh(task)
    return {"id": task.id, "status": task.status, "instance_status": task.instance.status}


@app.post("/api/workflow-tasks/{task_id}/reject")
def reject_workflow_task(task_id: int, payload: WorkflowRejectPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("approval"))) -> dict:
    task = (
        db.query(models.WorkflowTask)
        .options(selectinload(models.WorkflowTask.instance).selectinload(models.WorkflowInstance.tasks))
        .filter(models.WorkflowTask.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    if task.status != "待处理":
        raise HTTPException(status_code=409, detail="Only pending workflow task can be rejected")
    old_status = task.status
    task.status = "已驳回"
    task.acted_by = payload.acted_by
    task.acted_at = today_text()
    task.comment = payload.comment
    add_workflow_log(db, task.instance_id, task.id, "驳回", payload.acted_by, payload.comment, old_status, task.status)

    if payload.target_sequence:
        target = (
            db.query(models.WorkflowTask)
            .filter(
                models.WorkflowTask.instance_id == task.instance_id,
                models.WorkflowTask.sequence == payload.target_sequence,
            )
            .first()
        )
        if not target:
            raise HTTPException(status_code=404, detail="Reject target node not found")
        old_target_status = target.status
        target.status = "待处理"
        add_workflow_log(db, task.instance_id, target.id, "退回节点", payload.acted_by, f"从 {task.node_name} 驳回", old_target_status, target.status)
    else:
        old_instance_status = task.instance.status
        task.instance.status = "已驳回"
        withdraw_business_object(db, task.instance)
        add_workflow_log(db, task.instance_id, None, "流程驳回结束", payload.acted_by, payload.comment, old_instance_status, task.instance.status)
    db.commit()
    return {"id": task.id, "status": task.status, "instance_status": task.instance.status}


@app.post("/api/workflow-tasks/{task_id}/transfer")
def transfer_workflow_task(task_id: int, payload: WorkflowTransferPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("approval"))) -> dict:
    task = db.query(models.WorkflowTask).filter(models.WorkflowTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    if task.status != "待处理":
        raise HTTPException(status_code=409, detail="Only pending workflow task can be transferred")
    old_assignee = task.assignee
    task.assignee = payload.assignee
    add_workflow_log(db, task.instance_id, task.id, "转办", payload.acted_by, payload.comment or f"转办给 {payload.assignee}", old_assignee, payload.assignee)
    db.commit()
    return {"id": task.id, "assignee": task.assignee, "status": task.status}


@app.post("/api/workflow-instances/{instance_id}/withdraw")
def withdraw_workflow_instance(instance_id: int, payload: WorkflowWithdrawPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("approval"))) -> dict:
    instance = (
        db.query(models.WorkflowInstance)
        .options(selectinload(models.WorkflowInstance.tasks))
        .filter(models.WorkflowInstance.id == instance_id)
        .first()
    )
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
    if instance.status != "运行中":
        raise HTTPException(status_code=409, detail="Only running workflow can be withdrawn")
    old_status = instance.status
    instance.status = "已撤回"
    instance.completed_at = today_text()
    for task in instance.tasks:
        if task.status in ["待处理", "未开始"]:
            task.status = "已取消"
    withdraw_business_object(db, instance)
    add_workflow_log(db, instance.id, None, "撤回", payload.acted_by, payload.comment, old_status, instance.status)
    db.commit()
    return {"id": instance.id, "status": instance.status}


@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    product_count = db.query(models.Product).count()
    active_projects = db.query(models.Project).filter(models.Project.phase != "量产").count()
    pending_changes = db.query(models.Change).filter(models.Change.status.in_(["审批中", "执行中"])).count()
    docs = db.query(models.Document).count()
    signed_docs = db.query(models.Document).filter(models.Document.approval_status == "已签核").count()
    bom_total = db.query(models.BomHeader).count()
    bom_ready = db.query(models.BomHeader).filter(models.BomHeader.status == "已发布").count()

    lifecycle_rows = db.query(models.Product.lifecycle, func.count(models.Product.id)).group_by(models.Product.lifecycle).all()
    changes_rows = db.query(models.Change.change_type, func.count(models.Change.id)).group_by(models.Change.change_type).all()
    quality_rows = db.query(models.QualityLot.tested_at, func.avg(models.QualityLot.cp_yield), func.avg(models.QualityLot.ft_yield)).group_by(models.QualityLot.tested_at).order_by(models.QualityLot.tested_at).all()

    return {
        "metrics": {
            "products": product_count,
            "active_projects": active_projects,
            "pending_changes": pending_changes,
            "document_readiness": round((signed_docs / docs) * 100) if docs else 0,
            "bom_readiness": round((bom_ready / bom_total) * 100) if bom_total else 0,
        },
        "lifecycle": [{"name": name, "value": value} for name, value in lifecycle_rows],
        "changes": [{"name": name, "value": value} for name, value in changes_rows],
        "quality_trend": [{"date": date, "cp": round(cp, 1), "ft": round(ft, 1)} for date, cp, ft in quality_rows],
        "recent_tasks": [
            {
                "name": task.name,
                "phase": task.phase,
                "owner": task.owner,
                "status": task.status,
                "due_date": task.due_date,
            }
            for task in db.query(models.ProjectTask).order_by(models.ProjectTask.due_date).limit(6)
        ],
    }


@app.get("/api/products")
def products(db: Session = Depends(get_db)) -> list[dict]:
    return [serialize_product(product) for product in db.query(models.Product).order_by(models.Product.id).all()]


@app.post("/api/products", status_code=201)
def create_product(payload: ProductPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = models.Product(**payload.model_dump())
    db.add(product)
    commit_or_409(db, "Product code or model already exists")
    db.refresh(product)
    return serialize_product(product)


@app.get("/api/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = (
        db.query(models.Product)
        .options(
            selectinload(models.Product.bom_headers),
            selectinload(models.Product.documents),
            selectinload(models.Product.process_routes).selectinload(models.ProcessRoute.steps),
            selectinload(models.Product.changes).selectinload(models.Change.impacts),
            selectinload(models.Product.quality_lots),
        )
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    data = serialize_product(product)
    data.update(
        {
            "boms": [{"id": bom.id, "type": bom.bom_type, "version": bom.version, "status": bom.status, "owner": bom.owner, "release_date": bom.release_date} for bom in product.bom_headers],
            "documents": [{"id": doc.id, "doc_no": doc.doc_no, "title": doc.title, "category": doc.category, "version": doc.version, "status": doc.status, "approval_status": doc.approval_status} for doc in product.documents],
            "routes": [{"id": route.id, "route_no": route.route_no, "name": route.name, "version": route.version, "status": route.status, "steps": len(route.steps)} for route in product.process_routes],
            "changes": [{"id": change.id, "change_no": change.change_no, "title": change.title, "status": change.status, "priority": change.priority} for change in product.changes],
            "quality": [{"lot_no": lot.lot_no, "stage": lot.stage, "cp_yield": lot.cp_yield, "ft_yield": lot.ft_yield, "status": lot.status} for lot in product.quality_lots],
        }
    )
    return data


@app.put("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_model(product, payload)
    commit_or_409(db, "Product code or model already exists")
    db.refresh(product)
    return serialize_product(product)


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    linked_count = (
        db.query(models.BomHeader).filter(models.BomHeader.product_id == product_id).count()
        + db.query(models.Document).filter(models.Document.product_id == product_id).count()
        + db.query(models.ProcessRoute).filter(models.ProcessRoute.product_id == product_id).count()
        + db.query(models.Change).filter(models.Change.product_id == product_id).count()
        + db.query(models.QualityLot).filter(models.QualityLot.product_id == product_id).count()
        + db.query(models.Requirement).filter(models.Requirement.product_id == product_id).count()
        + db.query(models.ProductBaseline).filter(models.ProductBaseline.product_id == product_id).count()
    )
    if linked_count:
        raise HTTPException(status_code=409, detail="Product has linked PLM data and cannot be deleted")
    db.delete(product)
    db.commit()
    return {"deleted": True}


@app.get("/api/products/{product_id}/versions")
def product_versions(product_id: int, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.ProductVersion).filter(models.ProductVersion.product_id == product_id).order_by(models.ProductVersion.id.desc()).all()
    return [
        {"id": r.id, "version": r.version, "lifecycle": r.lifecycle, "readiness": r.readiness, "released_at": r.released_at, "released_by": r.released_by, "source_change_no": r.source_change_no, "summary": r.summary}
        for r in rows
    ]


@app.post("/api/products/{product_id}/versions", status_code=201)
def create_product_version(product_id: int, payload: ProductVersionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    ensure_product_exists(db, product_id)
    row = models.ProductVersion(product_id=product_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "version": row.version}


@app.get("/api/boms")
def boms(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).all()
    return [serialize_bom(row) for row in rows]


@app.post("/api/boms", status_code=201)
def create_bom(payload: BomHeaderPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    ensure_product_exists(db, payload.product_id)
    exists = (
        db.query(models.BomHeader.id)
        .filter(
            models.BomHeader.product_id == payload.product_id,
            models.BomHeader.bom_type == payload.bom_type,
            models.BomHeader.version == payload.version,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="BOM version already exists for this product and type")
    bom = models.BomHeader(**payload.model_dump())
    db.add(bom)
    db.commit()
    db.refresh(bom)
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom.id).first()
    return serialize_bom(bom)


@app.put("/api/boms/{bom_id}")
def update_bom(bom_id: int, payload: BomHeaderUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be edited")
    if payload.product_id is not None:
        ensure_product_exists(db, payload.product_id)
    next_product_id = payload.product_id if payload.product_id is not None else bom.product_id
    next_type = payload.bom_type if payload.bom_type is not None else bom.bom_type
    next_version = payload.version if payload.version is not None else bom.version
    exists = (
        db.query(models.BomHeader.id)
        .filter(
            models.BomHeader.id != bom.id,
            models.BomHeader.product_id == next_product_id,
            models.BomHeader.bom_type == next_type,
            models.BomHeader.version == next_version,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="BOM version already exists for this product and type")
    update_model(bom, payload)
    db.commit()
    db.refresh(bom)
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom.id).first()
    return serialize_bom(bom)


@app.delete("/api/boms/{bom_id}")
def delete_bom(bom_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be deleted")
    db.delete(bom)
    db.commit()
    return {"deleted": True}


@app.post("/api/boms/{bom_id}/items", status_code=201)
def create_bom_item(bom_id: int, payload: BomItemPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be edited")
    data = apply_bom_item_process_binding(db, payload, bom.product_id)
    item = models.BomItem(bom_id=bom_id, parent_id=None, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_bom_item(item)


@app.put("/api/bom-items/{item_id}")
def update_bom_item(item_id: int, payload: BomItemUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    item = db.query(models.BomItem).options(selectinload(models.BomItem.bom)).filter(models.BomItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    if item.bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be edited")
    data = apply_bom_item_process_binding(db, payload, item.bom.product_id)
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return serialize_bom_item(item)


@app.post("/api/boms/{bom_id}/transform", status_code=201)
def transform_bom(bom_id: int, payload: BomTransformPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    source = (
        db.query(models.BomHeader)
        .options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items))
        .filter(models.BomHeader.id == bom_id)
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Source BOM not found")
    if source.bom_type not in ["EBOM", "PBOM"] and payload.target_type in ["PBOM", "MBOM"]:
        raise HTTPException(status_code=409, detail="Only EBOM/PBOM can be transformed to downstream BOM")
    target = models.BomHeader(
        product_id=source.product_id,
        bom_type=payload.target_type,
        version=payload.version,
        status="编制中",
        owner=payload.owner or source.owner,
        release_date="",
        source_bom_id=source.id,
        effective_date=payload.effective_date,
        expiry_date="",
        effectivity_type=payload.effectivity_type,
        effective_batch=payload.effective_batch or source.effective_batch or "",
    )
    db.add(target)
    db.flush()
    for item in source.items:
        db.add(models.BomItem(
            bom_id=target.id,
            parent_id=None,
            material_code=item.material_code,
            material_name=item.material_name,
            category=item.category,
            specification=item.specification,
            quantity=item.quantity,
            unit=item.unit,
            position=item.position,
            process_step_id=item.process_step_id,
            process_step=item.process_step or "待工艺分配",
            substitute=item.substitute,
            status=item.status,
            effective_date=payload.effective_date or item.effective_date,
            expiry_date=item.expiry_date,
            effectivity_note=f"由 {source.bom_type} {source.version} 转换",
        ))
    db.commit()
    created = (
        db.query(models.BomHeader)
        .options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items))
        .filter(models.BomHeader.id == target.id)
        .first()
    )
    return serialize_bom(created)


@app.get("/api/boms/{bom_id}/compare/{target_bom_id}")
def compare_bom(bom_id: int, target_bom_id: int, db: Session = Depends(get_db)) -> dict:
    base = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom_id).first()
    target = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == target_bom_id).first()
    if not base or not target:
        raise HTTPException(status_code=404, detail="BOM not found")
    base_map = {bom_item_compare_key(item): item for item in base.items}
    target_map = {bom_item_compare_key(item): item for item in target.items}
    changes = []
    for key in sorted(set(base_map) | set(target_map)):
        base_item = base_map.get(key)
        target_item = target_map.get(key)
        if base_item and not target_item:
            changes.append(serialize_bom_compare_item("删除", None, base_item))
        elif target_item and not base_item:
            changes.append(serialize_bom_compare_item("新增", target_item, None))
        elif base_item and target_item and (
            base_item.quantity != target_item.quantity
            or base_item.status != target_item.status
            or base_item.effective_date != target_item.effective_date
            or base_item.expiry_date != target_item.expiry_date
        ):
            changes.append(serialize_bom_compare_item("变更", target_item, base_item))
    return {
        "base": {"id": base.id, "type": base.bom_type, "version": base.version, "product_model": base.product.model},
        "target": {"id": target.id, "type": target.bom_type, "version": target.version, "product_model": target.product.model},
        "summary": {
            "added": len([item for item in changes if item["change_type"] == "新增"]),
            "removed": len([item for item in changes if item["change_type"] == "删除"]),
            "changed": len([item for item in changes if item["change_type"] == "变更"]),
        },
        "changes": changes,
    }


@app.get("/api/boms/where-used/{material_code}")
def bom_where_used(material_code: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(models.BomItem)
        .join(models.BomHeader)
        .options(selectinload(models.BomItem.bom).selectinload(models.BomHeader.product))
        .filter(models.BomItem.material_code == material_code)
        .order_by(models.BomHeader.product_id, models.BomHeader.bom_type, models.BomHeader.version)
        .all()
    )
    return [
        {
            "bom_id": item.bom_id,
            "product_model": item.bom.product.model,
            "product_name": item.bom.product.name,
            "bom_type": item.bom.bom_type,
            "version": item.bom.version,
            "bom_status": item.bom.status,
            "material_code": item.material_code,
            "material_name": item.material_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "process_step": item.process_step,
            "effective_date": item.effective_date,
            "expiry_date": item.expiry_date,
        }
        for item in rows
    ]


@app.delete("/api/bom-items/{item_id}")
def delete_bom_item(item_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    item = db.query(models.BomItem).options(selectinload(models.BomItem.bom)).filter(models.BomItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    if item.bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be edited")
    db.delete(item)
    db.commit()
    return {"deleted": True}


@app.post("/api/boms/{bom_id}/submit")
def submit_bom(bom_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if not bom.items:
        raise HTTPException(status_code=409, detail="BOM has no items")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be submitted")
    # ECA 生成对象校验：如果 BOM 有 source_bom_id，说明是 ECA 升版生成的草案
    if bom.source_bom_id:
        generated_no = f"{bom.bom_type}-{bom.product.model}-{bom.version}"
        validate_eca_generated_object_ready(db, "BOM", bom.id, generated_no)
    bom.status = "审批中"
    instance = start_workflow(
        db,
        template_code="WF-BOM-REL",
        object_type="BOM",
        object_id=bom.id,
        object_no=f"{bom.bom_type}-{bom.product.model}-{bom.version}",
        title=f"{bom.product.model} {bom.bom_type} {bom.version} 发布",
        product_model=bom.product.model,
        started_by=bom.owner,
    )
    db.commit()
    return {"id": bom.id, "status": bom.status, "workflow_id": instance.id}


@app.post("/api/boms/{bom_id}/approve")
def approve_bom(bom_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission(["approval", "bom"]))) -> dict:
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if not bom.items:
        raise HTTPException(status_code=409, detail="BOM has no items")
    if bom.status == "已发布" and is_current_effective_bom(bom):
        return {"id": bom.id, "status": bom.status, "release_date": bom.release_date, "effective_date": bom.effective_date, "expiry_date": bom.expiry_date, "closed_versions": []}
    if not bom.effective_date:
        bom.effective_date = today_text()
    bom.status = "已发布"
    bom.release_date = today_text()
    bom.expiry_date = ""
    closed_versions = close_previous_effective_boms(db, bom)
    create_integration_job(
        db,
        target_system="ERP",
        object_type="BOM",
        object_no=f"{bom.bom_type}-{bom.product.model}-{bom.version}",
        product_model=bom.product.model,
        triggered_by=f"BOM-{bom.id}",
        message="BOM 已发布，等待同步 ERP 物料结构和用量。",
    )
    db.commit()
    return {"id": bom.id, "status": bom.status, "release_date": bom.release_date, "effective_date": bom.effective_date, "expiry_date": bom.expiry_date, "closed_versions": closed_versions}


@app.get("/api/materials")
def materials(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.Material).order_by(models.Material.category, models.Material.code).all()
    return [
        {
            "id": row.id,
            "code": row.code,
            "name": row.name,
            "category": row.category,
            "specification": row.specification,
            "supplier": row.supplier,
            "risk_level": row.risk_level,
            "lifecycle": row.lifecycle,
        }
        for row in rows
    ]


@app.post("/api/materials", status_code=201)
def create_material(payload: MaterialPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    material = models.Material(**payload.model_dump())
    db.add(material)
    commit_or_409(db, "Material code already exists")
    db.refresh(material)
    return {
        "id": material.id,
        "code": material.code,
        "name": material.name,
        "category": material.category,
        "specification": material.specification,
        "supplier": material.supplier,
        "risk_level": material.risk_level,
        "lifecycle": material.lifecycle,
    }


@app.put("/api/materials/{material_id}")
def update_material(material_id: int, payload: MaterialUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    update_model(material, payload)
    commit_or_409(db, "Material code already exists")
    db.refresh(material)
    return {
        "id": material.id,
        "code": material.code,
        "name": material.name,
        "category": material.category,
        "specification": material.specification,
        "supplier": material.supplier,
        "risk_level": material.risk_level,
        "lifecycle": material.lifecycle,
    }


@app.delete("/api/materials/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    bom_refs = db.query(models.BomItem).filter(models.BomItem.material_code == material.code).count()
    if bom_refs:
        raise HTTPException(status_code=409, detail="Material is used by BOM and cannot be deleted")
    db.delete(material)
    db.commit()
    return {"deleted": True}


@app.get("/api/documents")
def documents(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.Document).options(selectinload(models.Document.product)).order_by(models.Document.id).all()
    return [
        {
            "id": row.id,
            "doc_no": row.doc_no,
            "title": row.title,
            "category": row.category,
            "version": row.version,
            "status": row.status,
            "approval_status": row.approval_status,
            "owner": row.owner,
            "updated_at": row.updated_at,
            "product_model": row.product.model,
            "product_id": row.product_id,
        }
        for row in rows
    ]


@app.post("/api/documents", status_code=201)
def create_document(payload: DocumentPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    ensure_product_exists(db, payload.product_id)
    document = models.Document(**payload.model_dump())
    db.add(document)
    commit_or_409(db, "Document number already exists")
    db.refresh(document)
    return {
        "id": document.id,
        "doc_no": document.doc_no,
        "title": document.title,
        "category": document.category,
        "version": document.version,
        "status": document.status,
        "approval_status": document.approval_status,
        "owner": document.owner,
        "updated_at": document.updated_at,
        "product_model": document.product.model,
        "product_id": document.product_id,
    }


@app.put("/api/documents/{document_id}")
def update_document(document_id: int, payload: DocumentUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if payload.product_id is not None:
        ensure_product_exists(db, payload.product_id)
    update_model(document, payload)
    commit_or_409(db, "Document number already exists")
    db.refresh(document)
    return {
        "id": document.id,
        "doc_no": document.doc_no,
        "title": document.title,
        "category": document.category,
        "version": document.version,
        "status": document.status,
        "approval_status": document.approval_status,
        "owner": document.owner,
        "updated_at": document.updated_at,
        "product_model": document.product.model,
        "product_id": document.product_id,
    }


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status == "已发布":
        raise HTTPException(status_code=409, detail="Released document cannot be deleted")
    db.delete(document)
    db.commit()
    return {"deleted": True}


@app.post("/api/documents/{document_id}/submit")
def submit_document(document_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status == "已发布":
        raise HTTPException(status_code=409, detail="Released document cannot be submitted")
    # ECA 生成对象校验：检查文档是否由 ECA 动作生成
    validate_eca_generated_object_ready(db, "文档", document.id, document.doc_no)
    document.status = "审批中"
    document.approval_status = "流转中"
    document.updated_at = today_text()
    instance = start_workflow(
        db,
        template_code="WF-DOC-STD",
        object_type="文档",
        object_id=document.id,
        object_no=document.doc_no,
        title=document.title,
        product_model=document.product.model,
        started_by=document.owner,
    )
    db.commit()
    return {"id": document.id, "status": document.status, "approval_status": document.approval_status, "workflow_id": instance.id}


@app.post("/api/documents/{document_id}/approve")
def approve_document(document_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission(["approval", "document"]))) -> dict:
    document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document.status = "已发布"
    document.approval_status = "已签核"
    document.updated_at = today_text()
    create_integration_job(
        db,
        target_system="QMS",
        object_type="文档",
        object_no=document.doc_no,
        product_model=document.product.model,
        triggered_by=document.doc_no,
        message="文档已签核发布，等待同步 QMS/文控归档。",
    )
    db.commit()
    return {"id": document.id, "status": document.status, "approval_status": document.approval_status, "updated_at": document.updated_at}


@app.get("/api/requirements")
def requirements(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.Requirement).options(selectinload(models.Requirement.product)).order_by(models.Requirement.id).all()
    return [
        {
            "id": row.id,
            "req_no": row.req_no,
            "source": row.source,
            "category": row.category,
            "title": row.title,
            "priority": row.priority,
            "status": row.status,
            "owner": row.owner,
            "acceptance_criteria": row.acceptance_criteria,
            "product_model": row.product.model,
            "product_id": row.product_id,
        }
        for row in rows
    ]


@app.post("/api/requirements", status_code=201)
def create_requirement(payload: RequirementPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("requirement"))) -> dict:
    ensure_product_exists(db, payload.product_id)
    requirement = models.Requirement(**payload.model_dump())
    db.add(requirement)
    commit_or_409(db, "Requirement number already exists")
    db.refresh(requirement)
    return {
        "id": requirement.id,
        "req_no": requirement.req_no,
        "source": requirement.source,
        "category": requirement.category,
        "title": requirement.title,
        "priority": requirement.priority,
        "status": requirement.status,
        "owner": requirement.owner,
        "acceptance_criteria": requirement.acceptance_criteria,
        "product_model": requirement.product.model,
        "product_id": requirement.product_id,
    }


@app.put("/api/requirements/{requirement_id}")
def update_requirement(requirement_id: int, payload: RequirementUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("requirement"))) -> dict:
    requirement = db.query(models.Requirement).options(selectinload(models.Requirement.product)).filter(models.Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if payload.product_id is not None:
        ensure_product_exists(db, payload.product_id)
    update_model(requirement, payload)
    commit_or_409(db, "Requirement number already exists")
    db.refresh(requirement)
    return {
        "id": requirement.id,
        "req_no": requirement.req_no,
        "source": requirement.source,
        "category": requirement.category,
        "title": requirement.title,
        "priority": requirement.priority,
        "status": requirement.status,
        "owner": requirement.owner,
        "acceptance_criteria": requirement.acceptance_criteria,
        "product_model": requirement.product.model,
        "product_id": requirement.product_id,
    }


@app.delete("/api/requirements/{requirement_id}")
def delete_requirement(requirement_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("requirement"))) -> dict:
    requirement = db.query(models.Requirement).filter(models.Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if requirement.status in ["已确认", "已发布"]:
        raise HTTPException(status_code=409, detail="Confirmed requirement cannot be deleted")
    db.delete(requirement)
    db.commit()
    return {"deleted": True}


@app.get("/api/baselines")
def baselines(db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(models.ProductBaseline)
        .options(selectinload(models.ProductBaseline.product), selectinload(models.ProductBaseline.items))
        .order_by(models.ProductBaseline.id)
        .all()
    )
    return [
        {
            "id": row.id,
            "baseline_no": row.baseline_no,
            "name": row.name,
            "product_model": row.product.model,
            "version": row.version,
            "status": row.status,
            "created_by": row.created_by,
            "released_at": row.released_at,
            "items": [
                {
                    "id": item.id,
                    "item_type": item.item_type,
                    "item_no": item.item_no,
                    "title": item.title,
                    "version": item.version,
                    "status": item.status,
                }
                for item in row.items
            ],
        }
        for row in rows
    ]


@app.get("/api/workbench")
def workbench(db: Session = Depends(get_db)) -> dict:
    approvals = (
        db.query(models.Approval)
        .join(models.Change)
        .join(models.Product)
        .filter(models.Approval.status.in_(["处理中", "待处理", "流转中"]))
        .order_by(models.Approval.id)
        .limit(12)
        .all()
    )
    gate_rows = db.query(models.Product).order_by(models.Product.readiness).limit(8).all()
    return {
        "todo_approvals": [
            {
                "id": row.id,
                "change_no": row.change.change_no,
                "product_model": row.change.product.model,
                "step_name": row.step_name,
                "approver": row.approver,
                "status": row.status,
                "priority": row.change.priority,
                "submitted_at": row.change.submitted_at,
            }
            for row in approvals
        ],
        "stage_gates": [
            {
                "id": product.id,
                "model": product.model,
                "lifecycle": product.lifecycle,
                "owner": product.owner,
                "readiness": product.readiness,
                "next_gate": "量产发布" if product.readiness >= 80 else "资料齐套评审",
                "blocker": "可靠性报告/变更签核未闭环" if product.readiness < 80 else "客户承认书归档",
            }
            for product in gate_rows
        ],
    }


@app.get("/api/process-routes")
def process_routes(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.ProcessRoute).options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps)).all()
    return [serialize_process_route(row) for row in rows]


@app.post("/api/process-routes", status_code=201)
def create_process_route(payload: ProcessRoutePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    ensure_product_exists(db, payload.product_id)
    if payload.status == "已发布":
        raise HTTPException(status_code=409, detail="Process route must be released through approval")
    route = models.ProcessRoute(**payload.model_dump())
    db.add(route)
    commit_or_409(db, "Process route number already exists")
    db.refresh(route)
    route = (
        db.query(models.ProcessRoute)
        .options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps))
        .filter(models.ProcessRoute.id == route.id)
        .first()
    )
    assert route is not None
    return serialize_process_route(route)


@app.put("/api/process-routes/{route_id}")
def update_process_route(route_id: int, payload: ProcessRouteUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    route = (
        db.query(models.ProcessRoute)
        .options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps))
        .filter(models.ProcessRoute.id == route_id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=404, detail="Process route not found")
    ensure_route_editable(route)
    if payload.status == "已发布":
        raise HTTPException(status_code=409, detail="Process route must be released through approval")
    if payload.product_id is not None:
        ensure_product_exists(db, payload.product_id)
    update_model(route, payload)
    commit_or_409(db, "Process route number already exists")
    route = (
        db.query(models.ProcessRoute)
        .options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps))
        .filter(models.ProcessRoute.id == route_id)
        .first()
    )
    assert route is not None
    return serialize_process_route(route)


@app.delete("/api/process-routes/{route_id}")
def delete_process_route(route_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    route = db.query(models.ProcessRoute).filter(models.ProcessRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Process route not found")
    ensure_route_editable(route)
    db.delete(route)
    db.commit()
    return {"ok": True}


@app.post("/api/process-routes/{route_id}/steps", status_code=201)
def create_process_step(route_id: int, payload: ProcessStepPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    route = (
        db.query(models.ProcessRoute)
        .options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps))
        .filter(models.ProcessRoute.id == route_id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=404, detail="Process route not found")
    ensure_route_editable(route)
    if any(step.sequence == payload.sequence for step in route.steps):
        raise HTTPException(status_code=409, detail="Process step sequence already exists")
    step = models.ProcessStep(route_id=route_id, **payload.model_dump())
    db.add(step)
    db.commit()
    db.refresh(step)
    return {"id": step.id, "sequence": step.sequence, "stage": step.stage, "operation": step.operation, "key_params": step.key_params, "owner": step.owner, "status": step.status}


@app.put("/api/process-steps/{step_id}")
def update_process_step(step_id: int, payload: ProcessStepUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    step = (
        db.query(models.ProcessStep)
        .options(selectinload(models.ProcessStep.route))
        .filter(models.ProcessStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(status_code=404, detail="Process step not found")
    ensure_route_editable(step.route)
    if payload.sequence is not None:
        exists = (
            db.query(models.ProcessStep.id)
            .filter(models.ProcessStep.route_id == step.route_id, models.ProcessStep.sequence == payload.sequence, models.ProcessStep.id != step.id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=409, detail="Process step sequence already exists")
    update_model(step, payload)
    db.commit()
    db.refresh(step)
    return {"id": step.id, "sequence": step.sequence, "stage": step.stage, "operation": step.operation, "key_params": step.key_params, "owner": step.owner, "status": step.status}


@app.delete("/api/process-steps/{step_id}")
def delete_process_step(step_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    step = (
        db.query(models.ProcessStep)
        .options(selectinload(models.ProcessStep.route))
        .filter(models.ProcessStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(status_code=404, detail="Process step not found")
    ensure_route_editable(step.route)
    db.delete(step)
    db.commit()
    return {"ok": True}


@app.post("/api/process-routes/{route_id}/submit")
def submit_process_route(route_id: int, payload: ProcessRouteActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    route = (
        db.query(models.ProcessRoute)
        .options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps))
        .filter(models.ProcessRoute.id == route_id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=404, detail="Process route not found")
    validate_process_route_ready(route)
    if route.status == "已发布":
        raise HTTPException(status_code=409, detail="Released process route cannot be submitted")
    # ECA 生成对象校验：如果工艺路线有 source_route_id，说明是 ECA 升版生成的草案
    if route.source_route_id:
        validate_eca_generated_object_ready(db, "工艺路线", route.id, route.route_no)
    route.status = "审批中"
    db.commit()
    db.refresh(route)
    return serialize_process_route(route)


@app.post("/api/process-routes/{route_id}/approve")
def approve_process_route(route_id: int, payload: ProcessRouteActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission(["approval", "process"]))) -> dict:
    route = (
        db.query(models.ProcessRoute)
        .options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps))
        .filter(models.ProcessRoute.id == route_id)
        .first()
    )
    if not route:
        raise HTTPException(status_code=404, detail="Process route not found")
    validate_process_route_ready(route)
    route.status = "已发布"
    route.release_date = today_text()
    create_integration_job(
        db,
        target_system="MES",
        object_type="工艺路线",
        object_no=route.route_no,
        product_model=route.product.model,
        triggered_by=route.route_no,
        message=f"工艺路线已发布，等待同步 MES 工艺流程、工序参数和站点控制。发布人：{payload.acted_by}",
    )
    db.commit()
    db.refresh(route)
    return serialize_process_route(route)


@app.get("/api/products/{product_id}/process-steps")
def product_process_steps(product_id: int, db: Session = Depends(get_db)) -> list[dict]:
    ensure_product_exists(db, product_id)
    rows = (
        db.query(models.ProcessStep)
        .join(models.ProcessRoute)
        .filter(models.ProcessRoute.product_id == product_id)
        .order_by(models.ProcessRoute.version.desc(), models.ProcessStep.sequence)
        .all()
    )
    return [
        {
            "id": step.id,
            "route_id": step.route_id,
            "sequence": step.sequence,
            "stage": step.stage,
            "operation": step.operation,
            "key_params": step.key_params,
            "owner": step.owner,
            "status": step.status,
            "label": f"{step.sequence}-{step.stage} / {step.operation}",
        }
        for step in rows
    ]


@app.get("/api/changes")
def changes(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).order_by(models.Change.id).all()
    return [serialize_change(row, db) for row in rows]


@app.post("/api/changes", status_code=201)
def create_change(payload: ChangePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    if not db.query(models.Product.id).filter(models.Product.id == payload.product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")
    change = models.Change(**payload.model_dump())
    if not change.submitted_at and change.status != "草稿":
        change.submitted_at = today_text()
    db.add(change)
    commit_or_409(db, "Change number already exists")
    db.refresh(change)
    analyze_change_impacts(db, change)
    db.commit()
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change.id).first()
    return serialize_change(change, db)


@app.put("/api/changes/{change_id}")
def update_change(change_id: int, payload: ChangeUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    change = db.query(models.Change).filter(models.Change.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    if change.status not in {"草稿", "已驳回"}:
        raise HTTPException(status_code=409, detail="Only draft or rejected change can be edited")
    data = payload.model_dump(exclude_unset=True)
    if "product_id" in data and not db.query(models.Product.id).filter(models.Product.id == data["product_id"]).first():
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.items():
        setattr(change, key, value)
    commit_or_409(db, "Change number already exists")
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change_id).first()
    return serialize_change(change, db)


@app.delete("/api/changes/{change_id}")
def delete_change(change_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    change = db.query(models.Change).filter(models.Change.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    if change.status != "草稿":
        raise HTTPException(status_code=409, detail="Only draft changes can be deleted")
    db.delete(change)
    db.commit()
    return {"ok": True}


@app.post("/api/changes/{change_id}/submit")
def submit_change(change_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    if change.status == "已关闭":
        raise HTTPException(status_code=409, detail="Closed change cannot be submitted")
    analyze_change_impacts(db, change)
    change.status = "审批中"
    change.submitted_at = change.submitted_at or today_text()
    start_workflow(
        db,
        template_code="WF-ECR-ECN",
        object_type="变更",
        object_id=change.id,
        object_no=change.change_no,
        title=change.title,
        product_model=change.product.model,
        started_by=change.owner or "系统用户",
    )
    db.commit()
    db.refresh(change)
    return serialize_change(change, db)


@app.post("/api/changes/{change_id}/analyze")
def analyze_change(change_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    analyze_change_impacts(db, change)
    db.commit()
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change_id).first()
    return serialize_change(change, db)


@app.post("/api/changes/{change_id}/impacts", status_code=201)
def create_change_impact(change_id: int, payload: ChangeImpactPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    if not db.query(models.Change.id).filter(models.Change.id == change_id).first():
        raise HTTPException(status_code=404, detail="Change not found")
    impact = models.ChangeImpact(change_id=change_id, **payload.model_dump())
    db.add(impact)
    db.commit()
    db.refresh(impact)
    return {"id": impact.id, "type": impact.impact_type, "impact_type": impact.impact_type, "target": impact.target, "risk": impact.risk, "action": impact.action}


@app.put("/api/change-impacts/{impact_id}")
def update_change_impact(impact_id: int, payload: ChangeImpactUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    impact = db.query(models.ChangeImpact).filter(models.ChangeImpact.id == impact_id).first()
    if not impact:
        raise HTTPException(status_code=404, detail="Change impact not found")
    update_model(impact, payload)
    db.commit()
    db.refresh(impact)
    return {"id": impact.id, "type": impact.impact_type, "impact_type": impact.impact_type, "target": impact.target, "risk": impact.risk, "action": impact.action}


@app.delete("/api/change-impacts/{impact_id}")
def delete_change_impact(impact_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    impact = db.query(models.ChangeImpact).filter(models.ChangeImpact.id == impact_id).first()
    if not impact:
        raise HTTPException(status_code=404, detail="Change impact not found")
    db.delete(impact)
    db.commit()
    return {"ok": True}


@app.post("/api/changes/{change_id}/actions", status_code=201)
def create_change_action(change_id: int, payload: ChangeActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    if not db.query(models.Change.id).filter(models.Change.id == change_id).first():
        raise HTTPException(status_code=404, detail="Change not found")
    count = db.query(models.ChangeAction).filter(models.ChangeAction.change_id == change_id).count() + 1
    action_no = payload.action_no or f"ECA-{change_id}-{count:02d}"
    action = models.ChangeAction(change_id=change_id, **{**payload.model_dump(), "action_no": action_no})
    validate_change_action_target(db, action)
    db.add(action)
    commit_or_409(db, "Change action number already exists")
    db.refresh(action)
    return serialize_change_action(action)


@app.get("/api/changes/{change_id}/revision-archive")
def change_revision_archive(change_id: int, db: Session = Depends(get_db)) -> list[dict]:
    if not db.query(models.Change.id).filter(models.Change.id == change_id).first():
        raise HTTPException(status_code=404, detail="Change not found")
    rows = (
        db.query(models.ChangeAction)
        .filter(models.ChangeAction.change_id == change_id, models.ChangeAction.generated_object_no != "")
        .order_by(models.ChangeAction.id)
        .all()
    )
    return [
        {
            "action_no": row.action_no,
            "action_type": row.action_type,
            "target_type": row.target_type,
            "source_object": row.target_object,
            "source_version": row.target_version,
            "effectivity_type": row.effectivity_type,
            "effectivity_scope": row.effectivity_scope,
            "effective_date": row.effective_date,
            "effective_batch": row.effective_batch,
            "generated_object_no": row.generated_object_no,
            "owner": row.owner,
            "status": row.status,
            "target_url": (
                f"/boms?highlight={row.target_id}" if row.target_type == "BOM"
                else f"/documents?highlight={row.target_id}" if row.target_type == "文档"
                else f"/process?highlight={row.target_id}" if row.target_type == "工艺路线"
                else ""
            ),
            "generated_url": (
                f"/boms?highlight={row.generated_object_no}" if "BOM" in (row.generated_object_no or "")
                else f"/documents?highlight={row.generated_object_no}" if "DOC-" in (row.generated_object_no or "")
                else f"/process?highlight={row.generated_object_no}" if "ROUTE" in (row.generated_object_no or "")
                else ""
            ),
        }
        for row in rows
    ]


@app.put("/api/change-actions/{action_id}")
def update_change_action(action_id: int, payload: ChangeActionUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    action = db.query(models.ChangeAction).filter(models.ChangeAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Change action not found")
    update_model(action, payload)
    validate_change_action_target(db, action)
    commit_or_409(db, "Change action number already exists")
    db.refresh(action)
    return serialize_change_action(action)


@app.post("/api/change-actions/{action_id}/close")
def close_change_action(action_id: int, payload: ChangeActionClosePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    action = db.query(models.ChangeAction).filter(models.ChangeAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Change action not found")
    if action.status == "已完成":
        raise HTTPException(status_code=409, detail="ECA action is already closed")

    # 批次一致性校验：同一变更中相同批次的所有 ECA 动作必须使用一致格式
    if "批次" in (action.effectivity_type or ""):
        if not action.effective_batch:
            raise HTTPException(status_code=409, detail="Batch-based ECA action requires effective batch")
        siblings = (
            db.query(models.ChangeAction)
            .filter(
                models.ChangeAction.change_id == action.change_id,
                models.ChangeAction.id != action.id,
                models.ChangeAction.effective_batch != "",
            )
            .all()
        )
        for sibling in siblings:
            if sibling.effective_batch != action.effective_batch and "批次" in (sibling.effectivity_type or ""):
                raise HTTPException(
                    status_code=409,
                    detail=f"Batch inconsistency: action {action.action_no} batch '{action.effective_batch}' "
                    f"does not match sibling {sibling.action_no} batch '{sibling.effective_batch}'",
                )

    generated_object_no = apply_change_action_revision(db, action)
    action.status = "已完成"
    generated_note = f"，生成对象：{generated_object_no}" if generated_object_no else ""
    action.result = f"{payload.result}（关闭人：{payload.acted_by}，日期：{today_text()}{generated_note}）"
    closed_change = close_change_when_actions_done(db, action.change_id, payload.acted_by)
    db.commit()
    db.refresh(action)
    result = serialize_change_action(action)
    result["closed_change"] = closed_change
    return result


@app.get("/api/change-actions")
def change_actions(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.ChangeAction).join(models.Change).join(models.Product).order_by(models.ChangeAction.id).all()
    return [
        {
            "id": row.id,
            "action_no": row.action_no,
            "change_no": row.change.change_no,
            "product_model": row.change.product.model,
            "action_type": row.action_type,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "target_version": row.target_version,
            "target_object": row.target_object,
            "effectivity_type": row.effectivity_type,
            "effectivity_scope": row.effectivity_scope,
            "effective_date": row.effective_date,
            "effective_batch": row.effective_batch,
            "generated_object_no": row.generated_object_no,
            "department": row.department,
            "owner": row.owner,
            "status": row.status,
            "due_date": row.due_date,
            "result": row.result,
        }
        for row in rows
    ]


@app.get("/api/integration-jobs")
def integration_jobs(
    status: str = "",
    target_system: str = "",
    object_type: str = "",
    keyword: str = "",
    db: Session = Depends(get_db),
) -> list[dict]:
    query = db.query(models.IntegrationJob)
    if status:
        query = query.filter(models.IntegrationJob.status == status)
    if target_system:
        query = query.filter(models.IntegrationJob.target_system == target_system)
    if object_type:
        query = query.filter(models.IntegrationJob.object_type == object_type)
    if keyword:
        like_value = f"%{keyword}%"
        query = query.filter(
            (models.IntegrationJob.object_no.like(like_value))
            | (models.IntegrationJob.product_model.like(like_value))
            | (models.IntegrationJob.job_no.like(like_value))
        )
    rows = query.order_by(models.IntegrationJob.id.desc()).all()
    return [serialize_integration_job(row) for row in rows]


@app.get("/api/integration-jobs/summary")
def integration_jobs_summary(db: Session = Depends(get_db)) -> dict:
    rows = db.query(models.IntegrationJob.status, func.count(models.IntegrationJob.id)).group_by(models.IntegrationJob.status).all()
    status_counts = {status: count for status, count in rows}
    target_rows = db.query(models.IntegrationJob.target_system, func.count(models.IntegrationJob.id)).group_by(models.IntegrationJob.target_system).all()
    return {
        "total": sum(status_counts.values()),
        "waiting": status_counts.get("等待", 0),
        "processing": status_counts.get("处理中", 0),
        "failed": status_counts.get("失败", 0),
        "success": status_counts.get("成功", 0),
        "target_systems": [{"target_system": target, "count": count} for target, count in target_rows],
    }


@app.post("/api/integration-jobs/{job_id}/start")
def start_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    if job.status == "成功":
        raise HTTPException(status_code=409, detail="Successful integration job cannot be restarted")
    job.status = "处理中"
    job.attempt_count += 1
    job.last_sync_at = today_text()
    job.response_message = payload.response_message or f"{payload.acted_by} 已开始同步"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)


@app.post("/api/integration-jobs/{job_id}/success")
def complete_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    job.status = "成功"
    job.last_sync_at = today_text()
    job.external_id = payload.external_id or job.external_id
    job.response_message = payload.response_message or "下游系统已确认接收"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)


@app.post("/api/integration-jobs/{job_id}/fail")
def fail_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    job.status = "失败"
    job.last_sync_at = today_text()
    job.response_message = payload.response_message or "下游系统返回失败"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)


@app.post("/api/integration-jobs/{job_id}/retry")
def retry_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    if job.status == "成功":
        raise HTTPException(status_code=409, detail="Successful integration job cannot be retried")
    job.status = "等待"
    job.response_message = payload.response_message or f"{payload.acted_by} 已加入重试队列"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)


@app.get("/api/admin/foundation/system-parameters")
def system_parameters(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {"id": row.id, "param_key": row.param_key, "param_value": row.param_value, "param_group": row.param_group, "description": row.description}
        for row in db.query(models.SystemParameter).order_by(models.SystemParameter.param_group, models.SystemParameter.id).all()
    ]


@app.post("/api/admin/foundation/system-parameters", status_code=201)
def create_system_parameter(payload: SystemParameterPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = models.SystemParameter(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "System parameter key already exists")
    db.refresh(row)
    return {"id": row.id, "param_key": row.param_key, "param_value": row.param_value, "param_group": row.param_group, "description": row.description}


@app.put("/api/admin/foundation/system-parameters/{param_id}")
def update_system_parameter(param_id: int, payload: SystemParameterUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.SystemParameter).filter(models.SystemParameter.id == param_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="System parameter not found")
    update_model(row, payload)
    commit_or_409(db, "System parameter key already exists")
    db.refresh(row)
    return {"id": row.id, "param_key": row.param_key, "param_value": row.param_value, "param_group": row.param_group, "description": row.description}


@app.delete("/api/admin/foundation/system-parameters/{param_id}")
def delete_system_parameter(param_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.SystemParameter).filter(models.SystemParameter.id == param_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="System parameter not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/audit-logs")
def audit_logs(db: Session = Depends(get_db), object_type: str | None = None, action: str | None = None, limit: int = 200) -> list[dict]:
    query = db.query(models.OperationLog)
    if object_type:
        query = query.filter(models.OperationLog.object_type == object_type)
    if action:
        query = query.filter(models.OperationLog.action == action)
    rows = query.order_by(models.OperationLog.id.desc()).limit(limit).all()
    return [
        {"id": row.id, "action": row.action, "object_type": row.object_type, "object_id": row.object_id, "object_no": row.object_no, "summary": row.summary, "operated_by": row.operated_by, "operated_at": row.operated_at}
        for row in rows
    ]


@app.get("/api/substitute-materials")
def substitute_materials(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.SubstituteMaterial).order_by(models.SubstituteMaterial.material_code).all()
    return [{"id": r.id, "material_code": r.material_code, "material_name": r.material_name, "substitute_code": r.substitute_code, "substitute_name": r.substitute_name, "substitute_type": r.substitute_type, "strategy": r.strategy, "risk_level": r.risk_level, "status": r.status, "effective_date": r.effective_date, "expiry_date": r.expiry_date, "description": r.description} for r in rows]


@app.post("/api/substitute-materials", status_code=201)
def create_substitute_material(payload: SubstituteMaterialPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = models.SubstituteMaterial(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@app.put("/api/substitute-materials/{row_id}")
def update_substitute_material(row_id: int, payload: SubstituteMaterialUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.SubstituteMaterial).filter(models.SubstituteMaterial.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Substitute material not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@app.delete("/api/substitute-materials/{row_id}")
def delete_substitute_material(row_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.SubstituteMaterial).filter(models.SubstituteMaterial.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Substitute material not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/suppliers")
def suppliers(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.Supplier).order_by(models.Supplier.code).all()
    return [{"id": r.id, "code": r.code, "name": r.name, "supplier_type": r.supplier_type, "contact": r.contact, "phone": r.phone, "email": r.email, "address": r.address, "certification": r.certification, "risk_level": r.risk_level, "status": r.status, "description": r.description} for r in rows]


@app.post("/api/suppliers", status_code=201)
def create_supplier(payload: SupplierPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = models.Supplier(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Supplier code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code, "name": row.name}


@app.put("/api/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")
    update_model(row, payload)
    commit_or_409(db, "Supplier code already exists")
    return {"ok": True}


@app.delete("/api/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/projects")
def projects(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.Project).options(selectinload(models.Project.tasks), selectinload(models.Project.deliverables), selectinload(models.Project.risks)).order_by(models.Project.id).all()
    return [
        {
            "id": row.id,
            "project_no": row.project_no,
            "name": row.name,
            "product_model": row.product_model,
            "phase": row.phase,
            "progress": row.progress,
            "owner": row.owner,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "risk_level": row.risk_level,
            "tasks": [{"name": task.name, "phase": task.phase, "owner": task.owner, "status": task.status, "due_date": task.due_date} for task in row.tasks],
            "deliverables": [{"id": d.id, "name": d.name, "deliverable_type": d.deliverable_type, "phase": d.phase, "owner": d.owner, "status": d.status, "due_date": d.due_date, "completed_at": d.completed_at, "description": d.description} for d in row.deliverables],
            "risks": [{"id": r.id, "risk_type": r.risk_type, "description": r.description, "impact": r.impact, "probability": r.probability, "severity": r.severity, "owner": r.owner, "status": r.status, "mitigation": r.mitigation} for r in row.risks],
        }
        for row in rows
    ]


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = models.Project(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Project number already exists")
    db.refresh(row)
    return {"id": row.id, "project_no": row.project_no}


@app.put("/api/projects/{project_id}")
def update_project(project_id: int, payload: ProjectUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/project-templates")
def project_templates(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.ProjectTemplate).order_by(models.ProjectTemplate.code).all()
    return [{"id": r.id, "code": r.code, "name": r.name, "description": r.description, "stages": r.stages, "status": r.status} for r in rows]


@app.post("/api/project-templates", status_code=201)
def create_project_template(payload: ProjectTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = models.ProjectTemplate(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Template code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code}


@app.put("/api/project-templates/{template_id}")
def update_project_template(template_id: int, payload: ProjectTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectTemplate).filter(models.ProjectTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@app.delete("/api/project-templates/{template_id}")
def delete_project_template(template_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectTemplate).filter(models.ProjectTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/projects/{project_id}/deliverables")
def project_deliverables(project_id: int, db: Session = Depends(get_db)) -> list[dict]:
    ensure_project_exists(db, project_id)
    rows = db.query(models.ProjectDeliverable).filter(models.ProjectDeliverable.project_id == project_id).order_by(models.ProjectDeliverable.id).all()
    return [{"id": r.id, "name": r.name, "deliverable_type": r.deliverable_type, "phase": r.phase, "owner": r.owner, "status": r.status, "due_date": r.due_date, "completed_at": r.completed_at, "description": r.description} for r in rows]


@app.post("/api/projects/{project_id}/deliverables", status_code=201)
def create_project_deliverable(project_id: int, payload: ProjectDeliverablePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    ensure_project_exists(db, project_id)
    row = models.ProjectDeliverable(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@app.put("/api/project-deliverables/{deliverable_id}")
def update_project_deliverable(deliverable_id: int, payload: ProjectDeliverableUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectDeliverable).filter(models.ProjectDeliverable.id == deliverable_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@app.delete("/api/project-deliverables/{deliverable_id}")
def delete_project_deliverable(deliverable_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectDeliverable).filter(models.ProjectDeliverable.id == deliverable_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/projects/{project_id}/risks")
def project_risks(project_id: int, db: Session = Depends(get_db)) -> list[dict]:
    ensure_project_exists(db, project_id)
    rows = db.query(models.ProjectRisk).filter(models.ProjectRisk.project_id == project_id).order_by(models.ProjectRisk.id).all()
    return [{"id": r.id, "risk_type": r.risk_type, "description": r.description, "impact": r.impact, "probability": r.probability, "severity": r.severity, "owner": r.owner, "status": r.status, "mitigation": r.mitigation} for r in rows]


@app.post("/api/projects/{project_id}/risks", status_code=201)
def create_project_risk(project_id: int, payload: ProjectRiskPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    ensure_project_exists(db, project_id)
    row = models.ProjectRisk(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@app.put("/api/project-risks/{risk_id}")
def update_project_risk(risk_id: int, payload: ProjectRiskUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectRisk).filter(models.ProjectRisk.id == risk_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Risk not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@app.delete("/api/project-risks/{risk_id}")
def delete_project_risk(risk_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectRisk).filter(models.ProjectRisk.id == risk_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Risk not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.get("/api/quality")
def quality(db: Session = Depends(get_db)) -> dict:
    lots = db.query(models.QualityLot).options(selectinload(models.QualityLot.product)).order_by(models.QualityLot.id).all()
    issues = db.query(models.QualityIssue).order_by(models.QualityIssue.id).all()
    return {
        "lots": [
            {
                "id": lot.id,
                "product_model": lot.product.model,
                "lot_no": lot.lot_no,
                "wafer_id": lot.wafer_id,
                "stage": lot.stage,
                "cp_yield": lot.cp_yield,
                "ft_yield": lot.ft_yield,
                "bin1_rate": lot.bin1_rate,
                "issue_count": lot.issue_count,
                "status": lot.status,
                "tested_at": lot.tested_at,
            }
            for lot in lots
        ],
        "issues": [
            {
                "id": issue.id,
                "issue_no": issue.issue_no,
                "product_model": issue.product_model,
                "lot_no": issue.lot_no,
                "title": issue.title,
                "severity": issue.severity,
                "status": issue.status,
                "owner": issue.owner,
                "root_cause": issue.root_cause,
                "corrective_action": issue.corrective_action,
            }
            for issue in issues
        ],
    }


@app.get("/api/quality/capas")
def quality_capas(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.QualityCAPA).order_by(models.QualityCAPA.id.desc()).all()
    return [
        {"id": r.id, "capa_no": r.capa_no, "issue_id": r.issue_id, "title": r.title, "source": r.source, "root_cause": r.root_cause, "corrective_action": r.corrective_action, "preventive_action": r.preventive_action, "owner": r.owner, "status": r.status, "due_date": r.due_date, "closed_at": r.closed_at, "result": r.result}
        for r in rows
    ]


@app.post("/api/quality/capas", status_code=201)
def create_quality_capa(payload: QualityCAPAPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    if not payload.capa_no:
        count = db.query(models.QualityCAPA).count() + 1
        payload.capa_no = f"CAPA-{count:04d}"
    row = models.QualityCAPA(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "capa_no": row.capa_no}


@app.put("/api/quality/capas/{capa_id}")
def update_quality_capa(capa_id: int, payload: QualityCAPAUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityCAPA).filter(models.QualityCAPA.id == capa_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="CAPA not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@app.delete("/api/quality/capas/{capa_id}")
def delete_quality_capa(capa_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityCAPA).filter(models.QualityCAPA.id == capa_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="CAPA not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@app.post("/api/quality/issues/{issue_id}/create-capa", status_code=201)
def create_capa_from_issue(issue_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    count = db.query(models.QualityCAPA).count() + 1
    capa = models.QualityCAPA(
        capa_no=f"CAPA-{count:04d}",
        issue_id=issue.id,
        title=f"CAPA: {issue.title}",
        source="质量问题",
        root_cause=issue.root_cause or "",
        corrective_action=issue.corrective_action or "",
        owner=issue.owner,
        status="待处理",
    )
    db.add(capa)
    issue.status = "CAPA 执行中"
    db.commit()
    db.refresh(capa)
    return {"id": capa.id, "capa_no": capa.capa_no}

