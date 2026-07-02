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
    """对齐 MES ProductDef 26 字段。"""
    product_def_name: str
    product_def_version: str = "001"
    description: str = ""
    product_def_state: str = "Active"
    product_type: str = ""
    production_type: str = ""
    product_group_name: str = ""
    process_flow_name: str = ""
    process_flow_version: str = ""
    bom_name: str = ""
    bom_version: str = ""
    reticle_set_name: str = ""
    gross_die: int | None = None
    start_bank_name: str = ""
    end_bank_name: str = ""
    owner: str = ""
    max_use_count: int | None = None
    max_recycle_count: int | None = None
    owner_group_name: str = ""
    dummy_max_use_time: int | None = None
    dummy_thk_param: str = ""
    dummy_thk_limit: float | None = None
    is_deleted: bool = False
    bin_name: str = ""
    package_qty: int | None = None
    product_usage: str = ""


class ProductVersionPayload(BaseModel):
    version: str
    lifecycle: str = ""
    readiness: int = 0
    released_at: str = ""
    released_by: str = ""
    source_change_no: str = ""
    summary: str = ""


class ProductUpdatePayload(BaseModel):
    description: str | None = None
    product_def_state: str | None = None
    product_type: str | None = None
    production_type: str | None = None
    product_group_name: str | None = None
    process_flow_name: str | None = None
    process_flow_version: str | None = None
    bom_name: str | None = None
    bom_version: str | None = None
    reticle_set_name: str | None = None
    gross_die: int | None = None
    start_bank_name: str | None = None
    end_bank_name: str | None = None
    owner: str | None = None
    max_use_count: int | None = None
    max_recycle_count: int | None = None
    owner_group_name: str | None = None
    dummy_max_use_time: int | None = None
    dummy_thk_param: str | None = None
    dummy_thk_limit: float | None = None
    is_deleted: bool | None = None
    bin_name: str | None = None
    package_qty: int | None = None
    product_usage: str | None = None


# ===== 物料 / 替代料 / 供应商 =====
class MaterialPayload(BaseModel):
    """对齐 MES ConsumableDef 前 11 字段技术规格。"""
    consumable_def_name: str
    description: str = ""
    fab_product_name: str = ""
    consumable_type: str = ""
    primary_unit_name: str = ""
    primary_unit_code: str = ""
    unit_name: str = ""
    unit: str = ""
    unit_conversion_rate: str = ""
    material_standard_qty: int | None = None
    spec: str = ""
    supplier: str = ""
    supplier_id: int | None = None
    risk_level: str = "低"
    lifecycle: str = "有效"


class MaterialUpdatePayload(BaseModel):
    consumable_def_name: str | None = None
    description: str | None = None
    fab_product_name: str | None = None
    consumable_type: str | None = None
    primary_unit_name: str | None = None
    primary_unit_code: str | None = None
    unit_name: str | None = None
    unit: str | None = None
    unit_conversion_rate: str | None = None
    material_standard_qty: int | None = None
    spec: str | None = None
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
    """对齐 MES Bom 5 字段。"""
    bom_state: str = "Active"
    bom_name: str
    bom_version: str = "001"
    description: str = ""
    owner: str = ""


class BomHeaderUpdatePayload(BaseModel):
    bom_state: str | None = None
    bom_name: str | None = None
    bom_version: str | None = None
    description: str | None = None
    owner: str | None = None


class BomItemPayload(BaseModel):
    """对齐 MES BomItem 10 字段，三段式+工步绑定。"""
    idx: int | None = None
    bom_name: str = ""
    bom_version: str = ""
    material_type: str = "Consumable"
    material_def_name: str
    material_def_version: str = ""
    require_quantity: float | None = None
    unit: str = ""
    process_step_name: str = ""
    process_step_version: str = ""


class BomItemUpdatePayload(BaseModel):
    idx: int | None = None
    bom_name: str | None = None
    bom_version: str | None = None
    material_type: str | None = None
    material_def_name: str | None = None
    material_def_version: str | None = None
    require_quantity: float | None = None
    unit: str | None = None
    process_step_name: str | None = None
    process_step_version: str | None = None


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


# ===== 制造流程 / 工艺库（对齐 MES Template V1.2）=====
class ProcessFlowPayload(BaseModel):
    """对齐 MES ProcessFlow 10 字段。"""
    process_flow_name: str
    process_flow_version: str = "001"
    description: str = ""
    process_flow_type1: str = "Main"
    process_flow_type2: str = "Production"
    process_flow_state: str = "Active"
    owner_group_name: str = ""
    owner: str = ""
    process_group_name: str = ""
    is_deleted: bool = False


class ProcessFlowUpdatePayload(BaseModel):
    description: str | None = None
    process_flow_type1: str | None = None
    process_flow_type2: str | None = None
    process_flow_state: str | None = None
    owner_group_name: str | None = None
    owner: str | None = None
    process_group_name: str | None = None
    is_deleted: bool | None = None


class ProcessFlowSeqPayload(BaseModel):
    """对齐 MES ProcessFlowSeq 12 字段。"""
    idx: int | None = None
    step_source: str = "MainFlow"
    process_flow_seq_name: str
    process_flow_name: str = ""
    process_flow_version: str = ""
    process_name: str = ""
    process_version: str = ""
    process_flow_seq_type: str = "ProcessStep"
    process_group1: str = ""
    process_group2: str = ""
    process_stage_name: str = ""
    work_layer: str = ""


class ProcessFlowSeqUpdatePayload(BaseModel):
    idx: int | None = None
    step_source: str | None = None
    process_flow_seq_name: str | None = None
    process_name: str | None = None
    process_version: str | None = None
    process_flow_seq_type: str | None = None
    process_group1: str | None = None
    process_group2: str | None = None
    process_stage_name: str | None = None
    work_layer: str | None = None


class ProcessFlowContentPayload(BaseModel):
    """对齐 MES ProcessFlowContent 22 字段。"""
    process_flow_seq_name: str
    process_flow_name: str = ""
    process_flow_version: str = ""
    process_capability_name: str = ""
    recipe_name: str = ""
    recipe_name_description: str = ""
    dc_spec_name: str = ""
    yield_limit: str = ""
    reticle_group_name: str = ""
    reticle_name: str = ""
    probe_card_name: str = ""
    lot_sampling_rule: str = ""
    is_skip_allowed: bool = False
    is_mandatory_step: bool = False
    sampling_user_group: str = ""
    is_flip: bool = False
    branch_flow_group: str = ""
    branch_flow_name: str = ""
    rework_flow_group: str = ""
    rework_flow_name: str = ""
    wafer_selection_rule: str = ""
    ink_able: str = ""


class ProcessFlowContentUpdatePayload(BaseModel):
    process_capability_name: str | None = None
    recipe_name: str | None = None
    recipe_name_description: str | None = None
    dc_spec_name: str | None = None
    yield_limit: str | None = None
    reticle_group_name: str | None = None
    reticle_name: str | None = None
    probe_card_name: str | None = None
    lot_sampling_rule: str | None = None
    is_skip_allowed: bool | None = None
    is_mandatory_step: bool | None = None
    sampling_user_group: str | None = None
    is_flip: bool | None = None
    branch_flow_group: str | None = None
    branch_flow_name: str | None = None
    rework_flow_group: str | None = None
    rework_flow_name: str | None = None
    wafer_selection_rule: str | None = None
    ink_able: str | None = None


class ProcessFlowMeasurePayload(BaseModel):
    """对齐 MES ProcessFlowMeasure 11 字段。"""
    process_flow_name: str = ""
    process_flow_version: str = ""
    process_flow_seq_name: str
    key_process_flow_seq_name: str = ""
    measure_item: str = ""
    target: float | None = None
    lower_spec_limit: float | None = None
    upper_spec_limit: float | None = None
    sample_count: int | None = None
    sample_slots: str = ""
    sample_count_type: str = ""


class ProcessFlowMeasureUpdatePayload(BaseModel):
    key_process_flow_seq_name: str | None = None
    measure_item: str | None = None
    target: float | None = None
    lower_spec_limit: float | None = None
    upper_spec_limit: float | None = None
    sample_count: int | None = None
    sample_slots: str | None = None
    sample_count_type: str | None = None


class ProcessFlowContaminationPayload(BaseModel):
    """对齐 MES ProcessFlowContamination 5 字段。requireContaminationLevels 是数组，传字符串。"""
    process_flow_name: str = ""
    process_flow_version: str = ""
    process_flow_seq_name: str
    require_contamination_levels: str = ""
    affect_contamination_level: str = ""


class ProcessFlowContaminationUpdatePayload(BaseModel):
    require_contamination_levels: str | None = None
    affect_contamination_level: str | None = None


class ProcessStagePayload(BaseModel):
    """对齐 MES ProcessStage 7 字段。"""
    idx: int | None = None
    process_stage_name: str
    description: str = ""
    process_group1: str = ""
    process_group2: str = ""
    key_process: str = ""
    process_stage_state: str = "Valid"


class ProcessStageUpdatePayload(BaseModel):
    idx: int | None = None
    description: str | None = None
    process_group1: str | None = None
    process_group2: str | None = None
    key_process: str | None = None
    process_stage_state: str | None = None


class ProcessStepPayload(BaseModel):
    """对齐 MES ProcessStep 21 字段。"""
    process_step_name: str
    process_step_version: str = "001"
    description: str = ""
    process_step_state: str = "Active"
    process_step_type: str = "Process"
    process_stage_name: str = ""
    process_group1: str = ""
    process_group2: str = ""
    key_process: str = ""
    bank_name: str = ""
    process_capability_name: str = ""
    recipe_name: str = ""
    is_skip_allowed: bool = False
    is_mandatory_step: bool = False
    sampling_user_group: str = ""
    owner_group_name: str = ""
    owner: str = ""
    cost_center_stage: str = ""
    is_deleted: bool = False
    is_flip: bool = False
    detail_process_step_type: str = "Normal"


class ProcessStepUpdatePayload(BaseModel):
    description: str | None = None
    process_step_state: str | None = None
    process_step_type: str | None = None
    process_stage_name: str | None = None
    process_group1: str | None = None
    process_group2: str | None = None
    key_process: str | None = None
    bank_name: str | None = None
    process_capability_name: str | None = None
    recipe_name: str | None = None
    is_skip_allowed: bool | None = None
    is_mandatory_step: bool | None = None
    sampling_user_group: str | None = None
    owner_group_name: str | None = None
    owner: str | None = None
    cost_center_stage: str | None = None
    is_deleted: bool | None = None
    is_flip: bool | None = None
    detail_process_step_type: str | None = None


class ProcessCapabilityPayload(BaseModel):
    """对齐 MES ProcessCapability 3 字段。"""
    process_capability_name: str
    description: str = ""
    process_capability_state: str = "Valid"


class ProcessCapabilityUpdatePayload(BaseModel):
    description: str | None = None
    process_capability_state: str | None = None


class RecipePayload(BaseModel):
    """对齐 MES Recipe 7 字段。不含物理参数。"""
    process_capability_name: str
    recipe_name: str
    description: str = ""
    object_owner: str = ""
    recipe_state: str = "Valid"
    effective_time: int | None = None
    expir_alarm_id: str = ""


class RecipeUpdatePayload(BaseModel):
    description: str | None = None
    object_owner: str | None = None
    recipe_state: str | None = None
    effective_time: int | None = None
    expir_alarm_id: str | None = None


class EquipmentTypePayload(BaseModel):
    """对齐 MES EquipmentType 12 字段。"""
    equipment_type_name: str
    description: str = ""
    process_type1: str = "Production"
    process_type2: str = "Process"
    construct_type1: str = "Main"
    construct_type2: str = "Normal"
    process_capacity: int | None = None
    process_job_count_min: int | None = None
    process_job_count_max: int | None = None
    batch_capacity: int | None = None
    dummy_unmount_flag: bool = False
    equipment_type_state: str = "Valid"


class EquipmentTypeUpdatePayload(BaseModel):
    description: str | None = None
    process_type1: str | None = None
    process_type2: str | None = None
    construct_type1: str | None = None
    construct_type2: str | None = None
    process_capacity: int | None = None
    process_job_count_min: int | None = None
    process_job_count_max: int | None = None
    batch_capacity: int | None = None
    dummy_unmount_flag: bool | None = None
    equipment_type_state: str | None = None


class EquipmentCapabilityPayload(BaseModel):
    """对齐 MES EquipmentCapability 4 字段。PLM 改造：equipmentName→equipment_type_name。"""
    equipment_type_name: str
    process_capability_name: str
    assign_flag: bool = True
    equipment_capability_state: str = "Valid"


class EquipmentCapabilityUpdatePayload(BaseModel):
    assign_flag: bool | None = None
    equipment_capability_state: str | None = None


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
