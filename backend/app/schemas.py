"""所有 Pydantic 请求体模型（*Payload）。

按业务域分组，与 routers/ 拆分一一对应。所有 router 通过
`from ..schemas import XxxPayload` 引用。
"""
from pydantic import BaseModel


# ===== 会话 =====
class LoginPayload(BaseModel):
    username: str
    password: str


class ProfileUpdatePayload(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None


# ===== 产品 =====
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


# ===== 物料 / 替代料 / 供应商 =====
class MaterialPayload(BaseModel):
    code: str
    name: str
    category: str
    specification: str = ""
    supplier: str = ""
    supplier_id: int | None = None
    risk_level: str = "低"
    lifecycle: str = "有效"


class MaterialUpdatePayload(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    specification: str | None = None
    supplier: str | None = None
    supplier_id: int | None = None
    risk_level: str | None = None
    lifecycle: str | None = None


class SubstituteMaterialPayload(BaseModel):
    material_code: str
    material_name: str
    substitute_code: str
    substitute_name: str
    material_id: int | None = None
    substitute_material_id: int | None = None
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
    material_id: int | None = None
    substitute_material_id: int | None = None
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


# ===== 需求规格 =====
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


# ===== 文档 =====
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


class DocumentDistributionPayload(BaseModel):
    document_id: int
    recipient_type: str = "角色"
    recipient: str
    distributed_by: str = ""


class DocumentDistributionRecallPayload(BaseModel):
    recalled_by: str = ""
    recall_reason: str = ""


# ===== BOM =====
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


class BomBatchReplacePayload(BaseModel):
    from_code: str
    to_code: str
    to_name: str = ""
    to_category: str = ""
    to_specification: str = ""


class BomBatchQuantityPayload(BaseModel):
    item_ids: list[int]
    quantity: float


class BomBatchDeletePayload(BaseModel):
    item_ids: list[int]


# ===== 工艺路线 / 工序 / 工艺参数 =====
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


class ProcessParameterPayload(BaseModel):
    param_code: str = ""
    param_name: str
    param_type: str = "CD"
    unit: str = ""
    category: str = ""
    default_value: str = ""
    min_value: str = ""
    max_value: str = ""
    description: str = ""
    status: str = "启用"


class ProcessParameterUpdatePayload(BaseModel):
    param_code: str | None = None
    param_name: str | None = None
    param_type: str | None = None
    unit: str | None = None
    category: str | None = None
    default_value: str | None = None
    min_value: str | None = None
    max_value: str | None = None
    description: str | None = None
    status: str | None = None


# ===== PR 问题报告 =====
class ProblemReportPayload(BaseModel):
    pr_no: str = ""
    title: str
    problem_type: str = "设计问题"
    severity: str = "中"
    source: str = "内部"
    product_id: int | None = None
    product_model: str = ""
    description: str = ""
    suggested_action: str = ""
    status: str = "新建"
    reporter: str = ""
    reported_at: str = ""
    related_change_no: str = ""
    remark: str = ""


class ProblemReportUpdatePayload(BaseModel):
    title: str | None = None
    problem_type: str | None = None
    severity: str | None = None
    source: str | None = None
    product_id: int | None = None
    product_model: str | None = None
    description: str | None = None
    suggested_action: str | None = None
    status: str | None = None
    reporter: str | None = None
    reported_at: str | None = None
    related_change_no: str | None = None
    remark: str | None = None


# ===== 工程变更 / 影响分析 / ECA =====
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
    implementation_plan: str = ""
    notification_list: str = ""


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
    implementation_plan: str | None = None
    notification_list: str | None = None


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


# ===== 项目 / 模板 / 任务 / 交付物 / 风险 / 阶段门 =====
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


class ProjectFromTemplatePayload(BaseModel):
    template_id: int
    project_no: str
    name: str
    product_model: str = ""
    owner: str = ""
    start_date: str = ""
    end_date: str = ""


class ProjectDeliverablePayload(BaseModel):
    name: str
    deliverable_type: str
    phase: str
    owner: str = ""
    status: str = "待处理"
    due_date: str = ""
    description: str = ""
    object_type: str = ""
    object_id: int | None = None


class ProjectDeliverableUpdatePayload(BaseModel):
    name: str | None = None
    deliverable_type: str | None = None
    phase: str | None = None
    owner: str | None = None
    status: str | None = None
    due_date: str | None = None
    completed_at: str | None = None
    description: str | None = None
    object_type: str | None = None
    object_id: int | None = None


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


class ProjectTaskPayload(BaseModel):
    name: str
    phase: str = ""
    owner: str = ""
    status: str = "待处理"
    due_date: str = ""
    start_date: str = ""
    parent_id: int | None = None
    depends_on: str = ""


class ProjectTaskUpdatePayload(BaseModel):
    name: str | None = None
    phase: str | None = None
    owner: str | None = None
    status: str | None = None
    due_date: str | None = None
    start_date: str | None = None
    parent_id: int | None = None
    depends_on: str | None = None


class ProjectPhaseGatePayload(BaseModel):
    acted_by: str = "系统用户"
    comment: str = ""


class ProjectArchivePayload(BaseModel):
    archived_by: str = ""
    summary: str = ""


# ===== 质量问题 / CAPA / 报告 =====
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


class QualityIssuePayload(BaseModel):
    issue_no: str = ""
    product_model: str = ""
    lot_no: str = ""
    title: str
    severity: str = "中"
    status: str = "新建"
    owner: str = ""
    root_cause: str = ""
    corrective_action: str = ""


class QualityIssueUpdatePayload(BaseModel):
    product_model: str | None = None
    lot_no: str | None = None
    title: str | None = None
    severity: str | None = None
    status: str | None = None
    owner: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None


class QualityReportPayload(BaseModel):
    report_no: str = ""
    title: str
    report_type: str = "质量归档"
    product_model: str = ""
    issue_nos: str = ""
    capa_nos: str = ""
    summary: str = ""
    root_cause: str = ""
    corrective_action: str = ""
    preventive_action: str = ""
    owner: str = ""
    status: str = "已归档"


class QualityReportUpdatePayload(BaseModel):
    title: str | None = None
    report_type: str | None = None
    summary: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    preventive_action: str | None = None
    owner: str | None = None
    status: str | None = None


class QualityReportArchiveFromIssuePayload(BaseModel):
    issue_ids: list[int] = []
    title: str = ""
    owner: str = ""


# ===== 集成 =====
class IntegrationJobActionPayload(BaseModel):
    acted_by: str = "系统用户"
    response_message: str = ""
    external_id: str = ""


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


# ===== 基础平台 =====
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
    avatar_url: str = ""


class UserUpdatePayload(BaseModel):
    username: str | None = None
    display_name: str | None = None
    role: str | None = None
    department: str | None = None
    avatar_url: str | None = None


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


# ===== 流程 =====
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


# ===== 报表 =====
class ReportSnapshotPayload(BaseModel):
    report_type: str
    generated_by: str = "系统用户"
    schedule_key: str = "manual"
