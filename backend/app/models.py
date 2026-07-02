from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(128), default="")
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(40))
    department: Mapped[str] = mapped_column(String(80), default="生产部")
    avatar_url: Mapped[str] = mapped_column(String(500), default="")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(200), default="")
    permissions: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="启用")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    org_type: Mapped[str] = mapped_column(String(40), default="公司")
    parent_code: Mapped[str] = mapped_column(String(64), default="")
    manager: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="启用")
    description: Mapped[str] = mapped_column(String(240), default="")


class CodingRule(Base):
    __tablename__ = "coding_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(60), index=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    prefix: Mapped[str] = mapped_column(String(40))
    pattern: Mapped[str] = mapped_column(String(160))
    current_no: Mapped[int] = mapped_column(Integer, default=0)
    sample: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(30), default="启用")
    owner: Mapped[str] = mapped_column(String(80), default="")


class CategoryTemplate(Base):
    __tablename__ = "category_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(60), index=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    parent_code: Mapped[str] = mapped_column(String(64), default="")
    lifecycle_template: Mapped[str] = mapped_column(String(80), default="")
    coding_rule: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="启用")
    description: Mapped[str] = mapped_column(String(240), default="")

    attributes: Mapped[list["AttributeTemplate"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class AttributeTemplate(Base):
    __tablename__ = "attribute_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category_templates.id"))
    name: Mapped[str] = mapped_column(String(100))
    field_key: Mapped[str] = mapped_column(String(80))
    data_type: Mapped[str] = mapped_column(String(40), default="文本")
    required: Mapped[str] = mapped_column(String(10), default="否")
    dictionary_code: Mapped[str] = mapped_column(String(64), default="")
    default_value: Mapped[str] = mapped_column(String(120), default="")
    sequence: Mapped[int] = mapped_column(Integer, default=1)

    category: Mapped["CategoryTemplate"] = relationship(back_populates="attributes")


class LifecycleTemplate(Base):
    __tablename__ = "lifecycle_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    object_type: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[str] = mapped_column(String(30), default="启用")
    description: Mapped[str] = mapped_column(String(240), default="")

    states: Mapped[list["LifecycleState"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class LifecycleState(Base):
    __tablename__ = "lifecycle_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("lifecycle_templates.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(80))
    state_type: Mapped[str] = mapped_column(String(40), default="中间态")
    allow_edit: Mapped[str] = mapped_column(String(10), default="是")
    require_workflow: Mapped[str] = mapped_column(String(10), default="否")
    next_states: Mapped[str] = mapped_column(String(200), default="")

    template: Mapped["LifecycleTemplate"] = relationship(back_populates="states")


class DictionaryItem(Base):
    __tablename__ = "dictionary_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    dict_code: Mapped[str] = mapped_column(String(64), index=True)
    dict_name: Mapped[str] = mapped_column(String(120))
    item_value: Mapped[str] = mapped_column(String(120))
    item_label: Mapped[str] = mapped_column(String(120))
    object_scope: Mapped[str] = mapped_column(String(120), default="")
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="启用")


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    object_type: Mapped[str] = mapped_column(String(60))
    project_type: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="启用")
    description: Mapped[str] = mapped_column(String(240), default="")

    nodes: Mapped[list["WorkflowNode"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(100))
    role_name: Mapped[str] = mapped_column(String(80))
    action_type: Mapped[str] = mapped_column(String(40), default="审批")
    sla_hours: Mapped[int] = mapped_column(Integer, default=24)

    template: Mapped["WorkflowTemplate"] = relationship(back_populates="nodes")


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"))
    object_type: Mapped[str] = mapped_column(String(60))
    object_id: Mapped[int] = mapped_column(Integer)
    object_no: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(180))
    product_model: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="运行中")
    started_by: Mapped[str] = mapped_column(String(80), default="")
    started_at: Mapped[str] = mapped_column(String(30), default="")
    completed_at: Mapped[str] = mapped_column(String(30), default="")

    template: Mapped["WorkflowTemplate"] = relationship()
    tasks: Mapped[list["WorkflowTask"]] = relationship(back_populates="instance", cascade="all, delete-orphan")
    logs: Mapped[list["WorkflowLog"]] = relationship(cascade="all, delete-orphan")


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("workflow_instances.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    node_name: Mapped[str] = mapped_column(String(100))
    role_name: Mapped[str] = mapped_column(String(80))
    action_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="待处理")
    assignee: Mapped[str] = mapped_column(String(80), default="")
    acted_by: Mapped[str] = mapped_column(String(80), default="")
    acted_at: Mapped[str] = mapped_column(String(30), default="")
    comment: Mapped[str] = mapped_column(String(240), default="")
    sla_hours: Mapped[int] = mapped_column(Integer, default=24)

    instance: Mapped["WorkflowInstance"] = relationship(back_populates="tasks")


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("workflow_instances.id"))
    task_id: Mapped[int | None] = mapped_column(ForeignKey("workflow_tasks.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    actor: Mapped[str] = mapped_column(String(80))
    acted_at: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str] = mapped_column(String(240), default="")
    from_status: Mapped[str] = mapped_column(String(30), default="")
    to_status: Mapped[str] = mapped_column(String(30), default="")


class IntegrationEndpoint(Base):
    __tablename__ = "integration_endpoints"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    system_type: Mapped[str] = mapped_column(String(40))
    base_url: Mapped[str] = mapped_column(String(200))
    auth_type: Mapped[str] = mapped_column(String(40), default="Token")
    direction: Mapped[str] = mapped_column(String(30), default="双向")
    status: Mapped[str] = mapped_column(String(30), default="启用")
    owner: Mapped[str] = mapped_column(String(80), default="")
    object_scope: Mapped[str] = mapped_column(String(200), default="")


class Product(Base):
    """PLM 主控 - 对齐 MES ProductDef 26 字段。
    架构独立化：通过 processFlowName+Version 引用制造流程，不再 product_id 外键绑定流程。"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_def_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    product_def_version: Mapped[str] = mapped_column(String(30), index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    product_def_state: Mapped[str] = mapped_column(String(30), default="Active")
    product_type: Mapped[str] = mapped_column(String(40), default="")
    production_type: Mapped[str] = mapped_column(String(40), default="")
    product_group_name: Mapped[str] = mapped_column(String(30), default="")
    process_flow_name: Mapped[str] = mapped_column(String(30), default="", index=True)
    process_flow_version: Mapped[str] = mapped_column(String(30), default="")
    bom_name: Mapped[str] = mapped_column(String(60), default="")
    bom_version: Mapped[str] = mapped_column(String(60), default="")
    reticle_set_name: Mapped[str] = mapped_column(String(30), default="")
    gross_die: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_bank_name: Mapped[str] = mapped_column(String(30), default="")
    end_bank_name: Mapped[str] = mapped_column(String(30), default="")
    owner: Mapped[str] = mapped_column(String(30), default="")
    max_use_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_recycle_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_group_name: Mapped[str] = mapped_column(String(30), default="")
    dummy_max_use_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dummy_thk_param: Mapped[str] = mapped_column(String(100), default="")
    dummy_thk_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    bin_name: Mapped[str] = mapped_column(String(60), default="")
    package_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product_usage: Mapped[str] = mapped_column(String(60), default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="product")
    changes: Mapped[list["Change"]] = relationship(back_populates="product")
    quality_lots: Mapped[list["QualityLot"]] = relationship(back_populates="product")
    requirements: Mapped[list["Requirement"]] = relationship(back_populates="product")

    @property
    def model(self) -> str:
        return self.product_def_name

    @property
    def name(self) -> str:
        return self.description

    @property
    def version(self) -> str:
        return self.product_def_version

    @property
    def lifecycle(self) -> str:
        return self.product_def_state

    @property
    def readiness(self) -> int:
        return 100 if self.product_def_state == "Active" else 0


class ProductVersion(Base):
    __tablename__ = "product_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    version: Mapped[str] = mapped_column(String(20))
    lifecycle: Mapped[str] = mapped_column(String(40))
    readiness: Mapped[int] = mapped_column(Integer, default=0)
    released_at: Mapped[str] = mapped_column(String(30))
    released_by: Mapped[str] = mapped_column(String(80), default="")
    source_change_no: Mapped[str] = mapped_column(String(80), default="")
    summary: Mapped[str] = mapped_column(Text, default="")


class Material(Base):
    """PLM 部分主控 - 对齐 MES ConsumableDef 前 11 字段技术规格。
    后 17 字段（kitLeadTime/inUsePeriod/splitFlag/deductionFlag/deice*/alarm*/safetyStock/sourceType）留 MES。"""
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    consumable_def_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    fab_product_name: Mapped[str] = mapped_column(String(30), default="")
    consumable_type: Mapped[str] = mapped_column(String(40), default="")
    primary_unit_name: Mapped[str] = mapped_column(String(30), default="")
    primary_unit_code: Mapped[str] = mapped_column(String(30), default="")
    unit_name: Mapped[str] = mapped_column(String(30), default="")
    unit: Mapped[str] = mapped_column(String(30), default="")
    unit_conversion_rate: Mapped[str] = mapped_column(String(30), default="")
    material_standard_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spec: Mapped[str] = mapped_column(String(300), default="")
    # 保留 PLM 侧用字段
    supplier: Mapped[str] = mapped_column(String(100), default="")
    supplier_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="低")
    lifecycle: Mapped[str] = mapped_column(String(30), default="有效")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class BomHeader(Base):
    """PLM 主控 - 对齐 MES Bom 5 字段。
    架构独立化：不再绑定 product_id，通过 ProductDef.bomName+Version 引用。"""
    __tablename__ = "bom_headers"

    id: Mapped[int] = mapped_column(primary_key=True)
    bom_state: Mapped[str] = mapped_column(String(30), default="Active")
    bom_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    bom_version: Mapped[str] = mapped_column(String(30), index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    owner: Mapped[str] = mapped_column(String(30), default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[list["BomItem"]] = relationship(back_populates="bom", cascade="all, delete-orphan")


class BomItem(Base):
    """PLM 主控 - 对齐 MES BomItem 10 字段，三段式（Consumable/Durable/Product）+工步绑定。"""
    __tablename__ = "bom_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    idx: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bom_name: Mapped[str] = mapped_column(String(30), index=True)
    bom_version: Mapped[str] = mapped_column(String(30), default="")
    material_type: Mapped[str] = mapped_column(String(30), default="Consumable")
    material_def_name: Mapped[str] = mapped_column(String(30), default="")
    material_def_version: Mapped[str] = mapped_column(String(30), default="")
    require_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(30), default="")
    process_step_name: Mapped[str] = mapped_column(String(30), default="")
    process_step_version: Mapped[str] = mapped_column(String(30), default="")
    bom_id: Mapped[int] = mapped_column(ForeignKey("bom_headers.id"))

    bom: Mapped["BomHeader"] = relationship(back_populates="items")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    doc_no: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(60))
    version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    owner: Mapped[str] = mapped_column(String(80))
    approval_status: Mapped[str] = mapped_column(String(30))
    updated_at: Mapped[str] = mapped_column(String(30))
    file_name: Mapped[str] = mapped_column(String(255), default="")
    file_path: Mapped[str] = mapped_column(String(500), default="")
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str] = mapped_column(String(100), default="")

    product: Mapped["Product"] = relationship(back_populates="documents")


class ProcessFlow(Base):
    """PLM 主控 - 对齐 MES ProcessFlow 10 字段。独立主控对象，被 ProductDef 引用。"""
    __tablename__ = "process_flows"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_flow_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    process_flow_version: Mapped[str] = mapped_column(String(30), index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    process_flow_type1: Mapped[str] = mapped_column(String(30), default="Main")
    process_flow_type2: Mapped[str] = mapped_column(String(40), default="Production")
    process_flow_state: Mapped[str] = mapped_column(String(30), default="Active")
    owner_group_name: Mapped[str] = mapped_column(String(30), default="")
    owner: Mapped[str] = mapped_column(String(30), default="")
    process_group_name: Mapped[str] = mapped_column(String(30), default="")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    seqs: Mapped[list["ProcessFlowSeq"]] = relationship(back_populates="flow", cascade="all, delete-orphan")
    contents: Mapped[list["ProcessFlowContent"]] = relationship(back_populates="flow", cascade="all, delete-orphan")
    measures: Mapped[list["ProcessFlowMeasure"]] = relationship(back_populates="flow", cascade="all, delete-orphan")
    contaminations: Mapped[list["ProcessFlowContamination"]] = relationship(back_populates="flow", cascade="all, delete-orphan")


class ProcessFlowSeq(Base):
    """PLM 主控 - 对齐 MES ProcessFlowSeq 12 字段。流程工序序列，引用 ProcessStep。"""
    __tablename__ = "process_flow_seqs"

    id: Mapped[int] = mapped_column(primary_key=True)
    idx: Mapped[int | None] = mapped_column(Integer, nullable=True)
    step_source: Mapped[str] = mapped_column(String(30), default="MainFlow")
    process_flow_seq_name: Mapped[str] = mapped_column(String(30), index=True)
    process_flow_name: Mapped[str] = mapped_column(String(30), index=True)
    process_flow_version: Mapped[str] = mapped_column(String(30), default="")
    process_name: Mapped[str] = mapped_column(String(30), default="")
    process_version: Mapped[str] = mapped_column(String(30), default="")
    process_flow_seq_type: Mapped[str] = mapped_column(String(30), default="ProcessStep")
    process_group1: Mapped[str] = mapped_column(String(30), default="")
    process_group2: Mapped[str] = mapped_column(String(30), default="")
    process_stage_name: Mapped[str] = mapped_column(String(30), default="")
    work_layer: Mapped[str] = mapped_column(String(30), default="")
    flow_id: Mapped[int] = mapped_column(ForeignKey("process_flows.id"))

    flow: Mapped["ProcessFlow"] = relationship(back_populates="seqs")


class ProcessFlowContent(Base):
    """PLM 主控 - 对齐 MES ProcessFlowContent 22 字段。含分支/返工字段（MES 无 Alter 表）。"""
    __tablename__ = "process_flow_contents"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_flow_seq_name: Mapped[str] = mapped_column(String(30), index=True)
    process_flow_name: Mapped[str] = mapped_column(String(30), index=True)
    process_flow_version: Mapped[str] = mapped_column(String(30), default="")
    process_capability_name: Mapped[str] = mapped_column(String(30), default="")
    recipe_name: Mapped[str] = mapped_column(String(30), default="")
    recipe_name_description: Mapped[str] = mapped_column(String(100), default="")
    dc_spec_name: Mapped[str] = mapped_column(String(30), default="")
    yield_limit: Mapped[str] = mapped_column(String(30), default="")
    reticle_group_name: Mapped[str] = mapped_column(String(30), default="")
    reticle_name: Mapped[str] = mapped_column(String(60), default="")
    probe_card_name: Mapped[str] = mapped_column(String(30), default="")
    lot_sampling_rule: Mapped[str] = mapped_column(String(30), default="")
    is_skip_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mandatory_step: Mapped[bool] = mapped_column(Boolean, default=False)
    sampling_user_group: Mapped[str] = mapped_column(String(30), default="")
    is_flip: Mapped[bool] = mapped_column(Boolean, default=False)
    branch_flow_group: Mapped[str] = mapped_column(String(30), default="")
    branch_flow_name: Mapped[str] = mapped_column(String(30), default="")
    rework_flow_group: Mapped[str] = mapped_column(String(30), default="")
    rework_flow_name: Mapped[str] = mapped_column(String(30), default="")
    wafer_selection_rule: Mapped[str] = mapped_column(String(30), default="")
    ink_able: Mapped[str] = mapped_column(String(30), default="")
    flow_id: Mapped[int] = mapped_column(ForeignKey("process_flows.id"))

    flow: Mapped["ProcessFlow"] = relationship(back_populates="contents")


class ProcessFlowMeasure(Base):
    """PLM 主控 - 对齐 MES ProcessFlowMeasure 11 字段。"""
    __tablename__ = "process_flow_measures"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_flow_name: Mapped[str] = mapped_column(String(30), index=True)
    process_flow_version: Mapped[str] = mapped_column(String(30), default="")
    process_flow_seq_name: Mapped[str] = mapped_column(String(30), default="")
    key_process_flow_seq_name: Mapped[str] = mapped_column(String(30), default="")
    measure_item: Mapped[str] = mapped_column(String(30), default="")
    target: Mapped[float | None] = mapped_column(Float, nullable=True)
    lower_spec_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_spec_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_slots: Mapped[str] = mapped_column(String(30), default="")
    sample_count_type: Mapped[str] = mapped_column(String(30), default="")
    flow_id: Mapped[int] = mapped_column(ForeignKey("process_flows.id"))

    flow: Mapped["ProcessFlow"] = relationship(back_populates="measures")


class ProcessFlowContamination(Base):
    """PLM 主控 - 对齐 MES ProcessFlowContamination 5 字段。
    requireContaminationLevels 是数组[1..11]，用 JSON 字符串存。"""
    __tablename__ = "process_flow_contaminations"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_flow_name: Mapped[str] = mapped_column(String(30), index=True)
    process_flow_version: Mapped[str] = mapped_column(String(30), default="")
    process_flow_seq_name: Mapped[str] = mapped_column(String(30), default="")
    require_contamination_levels: Mapped[str] = mapped_column(String(100), default="")
    affect_contamination_level: Mapped[str] = mapped_column(String(30), default="")
    flow_id: Mapped[int] = mapped_column(ForeignKey("process_flows.id"))

    flow: Mapped["ProcessFlow"] = relationship(back_populates="contaminations")


class ProcessStage(Base):
    """PLM 主控 - 对齐 MES ProcessStage 7 字段。工艺大段分类。"""
    __tablename__ = "process_stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    idx: Mapped[int | None] = mapped_column(Integer, nullable=True)
    process_stage_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    process_group1: Mapped[str] = mapped_column(String(30), default="")
    process_group2: Mapped[str] = mapped_column(String(30), default="")
    key_process: Mapped[str] = mapped_column(String(30), default="")
    process_stage_state: Mapped[str] = mapped_column(String(30), default="Valid")


class ProcessStep(Base):
    """PLM 主控 - 对齐 MES ProcessStep 21 字段。独立主控菜单，被 ProcessFlowSeq 引用。"""
    __tablename__ = "process_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_step_name: Mapped[str] = mapped_column(String(30), index=True)
    process_step_version: Mapped[str] = mapped_column(String(30), default="001")
    description: Mapped[str] = mapped_column(String(300), default="")
    process_step_state: Mapped[str] = mapped_column(String(30), default="Active")
    process_step_type: Mapped[str] = mapped_column(String(30), default="Process")
    process_stage_name: Mapped[str] = mapped_column(String(30), default="")
    process_group1: Mapped[str] = mapped_column(String(30), default="")
    process_group2: Mapped[str] = mapped_column(String(30), default="")
    key_process: Mapped[str] = mapped_column(String(30), default="")
    bank_name: Mapped[str] = mapped_column(String(30), default="")
    process_capability_name: Mapped[str] = mapped_column(String(30), default="")
    recipe_name: Mapped[str] = mapped_column(String(30), default="")
    is_skip_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_mandatory_step: Mapped[bool] = mapped_column(Boolean, default=False)
    sampling_user_group: Mapped[str] = mapped_column(String(30), default="")
    owner_group_name: Mapped[str] = mapped_column(String(30), default="")
    owner: Mapped[str] = mapped_column(String(30), default="")
    cost_center_stage: Mapped[str] = mapped_column(String(30), default="")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_flip: Mapped[bool] = mapped_column(Boolean, default=False)
    detail_process_step_type: Mapped[str] = mapped_column(String(30), default="Normal")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class ProcessCapability(Base):
    """PLM 主控 - 对齐 MES ProcessCapability 3 字段。工艺设计语言，Recipe 父级。"""
    __tablename__ = "process_capabilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_capability_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    process_capability_state: Mapped[str] = mapped_column(String(30), default="Valid")


class Recipe(Base):
    """PLM 主控 - 对齐 MES Recipe 7 字段。配方命名+版本+生命周期，不含物理参数。
    物理参数在 MES EquipmentRecipeParam（PLM 引用对账）。"""
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    process_capability_name: Mapped[str] = mapped_column(String(30), index=True)
    recipe_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    object_owner: Mapped[str] = mapped_column(String(100), default="")
    recipe_state: Mapped[str] = mapped_column(String(30), default="Valid")
    effective_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expir_alarm_id: Mapped[str] = mapped_column(String(40), default="")


class EquipmentType(Base):
    """PLM 主控 - 对齐 MES EquipmentType 12 字段。设备族/型号分类，工艺设计资源。"""
    __tablename__ = "equipment_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_type_name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(300), default="")
    process_type1: Mapped[str] = mapped_column(String(30), default="Production")
    process_type2: Mapped[str] = mapped_column(String(30), default="Process")
    construct_type1: Mapped[str] = mapped_column(String(30), default="Main")
    construct_type2: Mapped[str] = mapped_column(String(30), default="Normal")
    process_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    process_job_count_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    process_job_count_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    batch_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dummy_unmount_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    equipment_type_state: Mapped[str] = mapped_column(String(30), default="Valid")

    capabilities: Mapped[list["EquipmentCapability"]] = relationship(back_populates="equipment_type", cascade="all, delete-orphan")


class EquipmentCapability(Base):
    """PLM 主控 - 对齐 MES EquipmentCapability 4 字段。
    PLM 改造：MES 原表 equipmentName（设备实例）→ PLM equipment_type_name（设备类型）。
    PLM 工艺设计按设备类型校验能力，MES 现场按设备实例校验能力。"""
    __tablename__ = "equipment_capabilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_type_name: Mapped[str] = mapped_column(String(30), index=True)
    process_capability_name: Mapped[str] = mapped_column(String(30), index=True)
    assign_flag: Mapped[bool] = mapped_column(Boolean, default=True)
    equipment_capability_state: Mapped[str] = mapped_column(String(30), default="Valid")
    equipment_type_id: Mapped[int] = mapped_column(ForeignKey("equipment_types.id"))

    equipment_type: Mapped["EquipmentType"] = relationship(back_populates="capabilities")


class MesSyncPackage(Base):
    """PLM 主控 - MES 同步包。ECN 关闭时生成，记录下发状态。"""
    __tablename__ = "mes_sync_packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    package_no: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    change_no: Mapped[str] = mapped_column(String(80), default="", index=True)
    target_system: Mapped[str] = mapped_column(String(40), default="MES")
    status: Mapped[str] = mapped_column(String(30), default="待下发")
    triggered_by: Mapped[str] = mapped_column(String(80), default="")
    triggered_at: Mapped[str] = mapped_column(String(30), default="")
    response_message: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str] = mapped_column(String(120), default="")
    remark: Mapped[str] = mapped_column(Text, default="")

    items: Mapped[list["MesSyncItem"]] = relationship(back_populates="package", cascade="all, delete-orphan")


class MesSyncItem(Base):
    """PLM 主控 - MES 同步项。记录单个对象的同步状态。"""
    __tablename__ = "mes_sync_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("mes_sync_packages.id"))
    object_type: Mapped[str] = mapped_column(String(60))
    object_no: Mapped[str] = mapped_column(String(120))
    object_version: Mapped[str] = mapped_column(String(30), default="")
    action: Mapped[str] = mapped_column(String(30), default="create")
    status: Mapped[str] = mapped_column(String(30), default="待下发")
    request_summary: Mapped[str] = mapped_column(Text, default="")
    response_summary: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str] = mapped_column(String(120), default="")
    fail_reason: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    package: Mapped["MesSyncPackage"] = relationship(back_populates="items")


class Change(Base):
    __tablename__ = "changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    change_no: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    change_type: Mapped[str] = mapped_column(String(60))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30))
    priority: Mapped[str] = mapped_column(String(20))
    owner: Mapped[str] = mapped_column(String(80))
    submitted_at: Mapped[str] = mapped_column(String(30))
    before_desc: Mapped[str] = mapped_column(Text)
    after_desc: Mapped[str] = mapped_column(Text)
    implementation_plan: Mapped[str] = mapped_column(Text, default="")
    notification_list: Mapped[str] = mapped_column(Text, default="")

    product: Mapped["Product"] = relationship(back_populates="changes")
    impacts: Mapped[list["ChangeImpact"]] = relationship(back_populates="change", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship(back_populates="change", cascade="all, delete-orphan")


class ChangeImpact(Base):
    __tablename__ = "change_impacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("changes.id"))
    impact_type: Mapped[str] = mapped_column(String(60))
    target: Mapped[str] = mapped_column(String(160))
    risk: Mapped[str] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(160))

    change: Mapped["Change"] = relationship(back_populates="impacts")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("changes.id"))
    step_name: Mapped[str] = mapped_column(String(80))
    approver: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str] = mapped_column(String(200), default="")
    approved_at: Mapped[str] = mapped_column(String(30), default="")

    change: Mapped["Change"] = relationship(back_populates="approvals")


class ChangeAction(Base):
    __tablename__ = "change_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    change_id: Mapped[int] = mapped_column(ForeignKey("changes.id"))
    action_no: Mapped[str] = mapped_column(String(80), unique=True)
    action_type: Mapped[str] = mapped_column(String(60))
    target_type: Mapped[str] = mapped_column(String(40), default="")
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_version: Mapped[str] = mapped_column(String(30), default="")
    target_object: Mapped[str] = mapped_column(String(160))
    effectivity_type: Mapped[str] = mapped_column(String(30), default="日期")
    effectivity_scope: Mapped[str] = mapped_column(String(80), default="")
    effective_date: Mapped[str] = mapped_column(String(30), default="")
    effective_batch: Mapped[str] = mapped_column(String(80), default="")
    generated_object_no: Mapped[str] = mapped_column(String(160), default="")
    department: Mapped[str] = mapped_column(String(80))
    owner: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30))
    due_date: Mapped[str] = mapped_column(String(30))
    result: Mapped[str] = mapped_column(Text)

    change: Mapped["Change"] = relationship()


class IntegrationJob(Base):
    __tablename__ = "integration_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_no: Mapped[str] = mapped_column(String(80), unique=True)
    target_system: Mapped[str] = mapped_column(String(40))
    object_type: Mapped[str] = mapped_column(String(60))
    object_no: Mapped[str] = mapped_column(String(120))
    product_model: Mapped[str] = mapped_column(String(80))
    direction: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    triggered_by: Mapped[str] = mapped_column(String(80))
    triggered_at: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(String(240))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_sync_at: Mapped[str] = mapped_column(String(30), default="")
    response_message: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str] = mapped_column(String(120), default="")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_no: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    product_model: Mapped[str] = mapped_column(String(80))
    phase: Mapped[str] = mapped_column(String(40))
    progress: Mapped[int] = mapped_column(Integer)
    owner: Mapped[str] = mapped_column(String(80))
    start_date: Mapped[str] = mapped_column(String(30))
    end_date: Mapped[str] = mapped_column(String(30))
    risk_level: Mapped[str] = mapped_column(String(20))
    archived_at: Mapped[str] = mapped_column(String(30), default="")
    archived_by: Mapped[str] = mapped_column(String(80), default="")
    archive_summary: Mapped[str] = mapped_column(Text, default="")

    tasks: Mapped[list["ProjectTask"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    deliverables: Mapped[list["ProjectDeliverable"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    risks: Mapped[list["ProjectRisk"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(140))
    phase: Mapped[str] = mapped_column(String(40))
    owner: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30))
    due_date: Mapped[str] = mapped_column(String(30))
    start_date: Mapped[str] = mapped_column(String(30), default="")
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depends_on: Mapped[str] = mapped_column(String(200), default="")

    project: Mapped["Project"] = relationship(back_populates="tasks")


class ProjectTemplate(Base):
    __tablename__ = "project_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(240), default="")
    stages: Mapped[str] = mapped_column(Text, default="")  # JSON: ["概念","设计","流片","验证","试产","量产导入"]
    status: Mapped[str] = mapped_column(String(30), default="启用")


class ProjectDeliverable(Base):
    __tablename__ = "project_deliverables"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(140))
    deliverable_type: Mapped[str] = mapped_column(String(60))
    phase: Mapped[str] = mapped_column(String(40))
    owner: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="待处理")
    due_date: Mapped[str] = mapped_column(String(30), default="")
    completed_at: Mapped[str] = mapped_column(String(30), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    object_type: Mapped[str] = mapped_column(String(40), default="")
    object_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="deliverables")


class ProjectRisk(Base):
    __tablename__ = "project_risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    risk_type: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(String(30), default="中")
    probability: Mapped[str] = mapped_column(String(30), default="中")
    severity: Mapped[str] = mapped_column(String(30), default="中")
    owner: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="待处理")
    mitigation: Mapped[str] = mapped_column(Text, default="")

    project: Mapped["Project"] = relationship(back_populates="risks")


class QualityCAPA(Base):
    __tablename__ = "quality_capas"

    id: Mapped[int] = mapped_column(primary_key=True)
    capa_no: Mapped[str] = mapped_column(String(80), unique=True)
    issue_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(160))
    source: Mapped[str] = mapped_column(String(60), default="质量问题")
    root_cause: Mapped[str] = mapped_column(Text)
    corrective_action: Mapped[str] = mapped_column(Text)
    preventive_action: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="待处理")
    due_date: Mapped[str] = mapped_column(String(30), default="")
    closed_at: Mapped[str] = mapped_column(String(30), default="")
    result: Mapped[str] = mapped_column(Text, default="")


class QualityLot(Base):
    __tablename__ = "quality_lots"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    lot_no: Mapped[str] = mapped_column(String(80), unique=True)
    wafer_id: Mapped[str] = mapped_column(String(80))
    stage: Mapped[str] = mapped_column(String(60))
    cp_yield: Mapped[float] = mapped_column(Float)
    ft_yield: Mapped[float] = mapped_column(Float)
    bin1_rate: Mapped[float] = mapped_column(Float)
    issue_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30))
    tested_at: Mapped[str] = mapped_column(String(30))

    product: Mapped["Product"] = relationship(back_populates="quality_lots")


class QualityIssue(Base):
    __tablename__ = "quality_issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_no: Mapped[str] = mapped_column(String(80), unique=True)
    product_model: Mapped[str] = mapped_column(String(80))
    lot_no: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(160))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    owner: Mapped[str] = mapped_column(String(80))
    root_cause: Mapped[str] = mapped_column(Text)
    corrective_action: Mapped[str] = mapped_column(Text)


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    req_no: Mapped[str] = mapped_column(String(80), unique=True)
    source: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(180))
    priority: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    owner: Mapped[str] = mapped_column(String(80))
    acceptance_criteria: Mapped[str] = mapped_column(Text)

    product: Mapped["Product"] = relationship(back_populates="requirements")


class SystemParameter(Base):
    __tablename__ = "system_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    param_key: Mapped[str] = mapped_column(String(100), unique=True)
    param_value: Mapped[str] = mapped_column(String(240), default="")
    param_group: Mapped[str] = mapped_column(String(60), default="系统")
    description: Mapped[str] = mapped_column(String(240), default="")


class ProductBaseline(Base):
    __tablename__ = "product_baselines"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    baseline_no: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    created_by: Mapped[str] = mapped_column(String(80))
    released_at: Mapped[str] = mapped_column(String(30))

    product: Mapped["Product"] = relationship()
    items: Mapped[list["BaselineItem"]] = relationship(back_populates="baseline", cascade="all, delete-orphan")


class BaselineItem(Base):
    __tablename__ = "baseline_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    baseline_id: Mapped[int] = mapped_column(ForeignKey("product_baselines.id"))
    item_type: Mapped[str] = mapped_column(String(50))
    item_no: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(180))
    version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))

    baseline: Mapped["ProductBaseline"] = relationship(back_populates="items")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(60))
    object_type: Mapped[str] = mapped_column(String(60))
    object_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    object_no: Mapped[str] = mapped_column(String(120), default="")
    summary: Mapped[str] = mapped_column(String(240), default="")
    operated_by: Mapped[str] = mapped_column(String(80))
    operated_at: Mapped[str] = mapped_column(String(30))


class SubstituteMaterial(Base):
    __tablename__ = "substitute_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_code: Mapped[str] = mapped_column(String(64))
    material_name: Mapped[str] = mapped_column(String(120))
    substitute_code: Mapped[str] = mapped_column(String(64))
    substitute_name: Mapped[str] = mapped_column(String(120))
    material_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    substitute_material_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    substitute_type: Mapped[str] = mapped_column(String(40), default="功能替代")
    strategy: Mapped[str] = mapped_column(String(30), default="一对一")
    risk_level: Mapped[str] = mapped_column(String(20), default="中")
    status: Mapped[str] = mapped_column(String(30), default="启用")
    effective_date: Mapped[str] = mapped_column(String(30), default="")
    expiry_date: Mapped[str] = mapped_column(String(30), default="")
    description: Mapped[str] = mapped_column(Text, default="")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    supplier_type: Mapped[str] = mapped_column(String(40))
    contact: Mapped[str] = mapped_column(String(80), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[str] = mapped_column(String(80), default="")
    address: Mapped[str] = mapped_column(String(200), default="")
    certification: Mapped[str] = mapped_column(String(80), default="")
    risk_level: Mapped[str] = mapped_column(String(20), default="中")
    status: Mapped[str] = mapped_column(String(30), default="启用")
    description: Mapped[str] = mapped_column(Text, default="")


class ProblemReport(Base):
    __tablename__ = "problem_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    pr_no: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    problem_type: Mapped[str] = mapped_column(String(60), default="设计问题")
    severity: Mapped[str] = mapped_column(String(20), default="中")
    source: Mapped[str] = mapped_column(String(60), default="内部")
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product_model: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    suggested_action: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="新建")
    reporter: Mapped[str] = mapped_column(String(80))
    reported_at: Mapped[str] = mapped_column(String(30))
    related_change_no: Mapped[str] = mapped_column(String(80), default="")
    remark: Mapped[str] = mapped_column(Text, default="")


class ProcessParameter(Base):
    __tablename__ = "process_parameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    param_code: Mapped[str] = mapped_column(String(64), unique=True)
    param_name: Mapped[str] = mapped_column(String(120))
    param_type: Mapped[str] = mapped_column(String(40), default="CD")
    unit: Mapped[str] = mapped_column(String(40), default="")
    category: Mapped[str] = mapped_column(String(60), default="")
    default_value: Mapped[str] = mapped_column(String(80), default="")
    min_value: Mapped[str] = mapped_column(String(80), default="")
    max_value: Mapped[str] = mapped_column(String(80), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="启用")


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_no: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    report_type: Mapped[str] = mapped_column(String(60), default="质量归档")
    product_model: Mapped[str] = mapped_column(String(80), default="")
    issue_nos: Mapped[str] = mapped_column(String(240), default="")
    capa_nos: Mapped[str] = mapped_column(String(240), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    root_cause: Mapped[str] = mapped_column(Text, default="")
    corrective_action: Mapped[str] = mapped_column(Text, default="")
    preventive_action: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(30), default="已归档")
    archived_at: Mapped[str] = mapped_column(String(30), default="")
    archived_by: Mapped[str] = mapped_column(String(80), default="")


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_no: Mapped[str] = mapped_column(String(80), unique=True)
    report_type: Mapped[str] = mapped_column(String(60))
    report_name: Mapped[str] = mapped_column(String(120))
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    generated_by: Mapped[str] = mapped_column(String(80), default="")
    generated_at: Mapped[str] = mapped_column(String(30), default="")
    schedule_key: Mapped[str] = mapped_column(String(80), default="")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    object_type: Mapped[str] = mapped_column(String(60))
    object_id: Mapped[int] = mapped_column(Integer)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str] = mapped_column(String(100), default="")
    description: Mapped[str] = mapped_column(String(240), default="")
    uploaded_by: Mapped[str] = mapped_column(String(80), default="")
    uploaded_at: Mapped[str] = mapped_column(String(30), default="")


class DocumentDistribution(Base):
    __tablename__ = "document_distributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer)
    doc_no: Mapped[str] = mapped_column(String(80), default="")
    title: Mapped[str] = mapped_column(String(160), default="")
    version: Mapped[str] = mapped_column(String(20), default="")
    recipient_type: Mapped[str] = mapped_column(String(30), default="角色")
    recipient: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(30), default="已发放")
    distributed_by: Mapped[str] = mapped_column(String(80), default="")
    distributed_at: Mapped[str] = mapped_column(String(30), default="")
    recalled_by: Mapped[str] = mapped_column(String(80), default="")
    recalled_at: Mapped[str] = mapped_column(String(30), default="")
    recall_reason: Mapped[str] = mapped_column(String(240), default="")
