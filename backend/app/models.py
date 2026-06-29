from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(40))
    department: Mapped[str] = mapped_column(String(80), default="生产部")


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
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    model: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(120))
    product_type: Mapped[str] = mapped_column(String(40))
    process_platform: Mapped[str] = mapped_column(String(60))
    wafer_size: Mapped[str] = mapped_column(String(30))
    package_type: Mapped[str] = mapped_column(String(40))
    temperature_grade: Mapped[str] = mapped_column(String(40))
    quality_grade: Mapped[str] = mapped_column(String(40))
    application: Mapped[str] = mapped_column(String(100))
    lifecycle: Mapped[str] = mapped_column(String(40), index=True)
    owner: Mapped[str] = mapped_column(String(80))
    customer_part_no: Mapped[str] = mapped_column(String(80))
    internal_part_no: Mapped[str] = mapped_column(String(80))
    version: Mapped[str] = mapped_column(String(20))
    readiness: Mapped[int] = mapped_column(Integer, default=70)
    latest_release: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    bom_headers: Mapped[list["BomHeader"]] = relationship(back_populates="product")
    documents: Mapped[list["Document"]] = relationship(back_populates="product")
    process_routes: Mapped[list["ProcessRoute"]] = relationship(back_populates="product")
    changes: Mapped[list["Change"]] = relationship(back_populates="product")
    quality_lots: Mapped[list["QualityLot"]] = relationship(back_populates="product")


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
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(50))
    specification: Mapped[str] = mapped_column(String(160))
    supplier: Mapped[str] = mapped_column(String(100))
    risk_level: Mapped[str] = mapped_column(String(20), default="低")
    lifecycle: Mapped[str] = mapped_column(String(30), default="有效")


class BomHeader(Base):
    __tablename__ = "bom_headers"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    bom_type: Mapped[str] = mapped_column(String(30))
    version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    owner: Mapped[str] = mapped_column(String(80))
    release_date: Mapped[str] = mapped_column(String(30))
    source_bom_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effective_date: Mapped[str] = mapped_column(String(30), default="")
    expiry_date: Mapped[str] = mapped_column(String(30), default="")
    effectivity_type: Mapped[str] = mapped_column(String(30), default="日期")
    effective_batch: Mapped[str] = mapped_column(String(80), default="")

    product: Mapped["Product"] = relationship(back_populates="bom_headers")
    items: Mapped[list["BomItem"]] = relationship(back_populates="bom", cascade="all, delete-orphan")


class BomItem(Base):
    __tablename__ = "bom_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    bom_id: Mapped[int] = mapped_column(ForeignKey("bom_headers.id"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("bom_items.id"), nullable=True)
    material_code: Mapped[str] = mapped_column(String(64))
    material_name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(50))
    specification: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[float] = mapped_column(Float, default=1)
    unit: Mapped[str] = mapped_column(String(20))
    position: Mapped[str] = mapped_column(String(80), default="")
    process_step_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    process_step: Mapped[str] = mapped_column(String(80), default="")
    substitute: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(30), default="有效")
    effective_date: Mapped[str] = mapped_column(String(30), default="")
    expiry_date: Mapped[str] = mapped_column(String(30), default="")
    effectivity_note: Mapped[str] = mapped_column(String(160), default="")

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

    product: Mapped["Product"] = relationship(back_populates="documents")


class ProcessRoute(Base):
    __tablename__ = "process_routes"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    route_no: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    owner: Mapped[str] = mapped_column(String(80))
    release_date: Mapped[str] = mapped_column(String(30), default="")
    source_route_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    effective_batch: Mapped[str] = mapped_column(String(80), default="")

    product: Mapped["Product"] = relationship(back_populates="process_routes")
    steps: Mapped[list["ProcessStep"]] = relationship(back_populates="route", cascade="all, delete-orphan")


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("process_routes.id"))
    sequence: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str] = mapped_column(String(60))
    operation: Mapped[str] = mapped_column(String(120))
    key_params: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30))

    route: Mapped["ProcessRoute"] = relationship(back_populates="steps")


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

    product: Mapped["Product"] = relationship()


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
