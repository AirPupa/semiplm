"""流程引擎：启动实例、完成业务对象、撤回、日志、项目交付物联动。"""
from fastapi import HTTPException
from sqlalchemy.orm import selectinload, Session

from .. import models
from .helpers import today_text
from .integration import create_integration_job


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
    """审批通过后完成业务对象：BOM/文档发布、变更进入执行中并尝试关闭。"""
    # 延迟导入避免与 services.change 形成循环依赖
    from .change import close_change_when_actions_done

    instance.status = "已完成"
    instance.completed_at = today_text()
    if instance.object_type == "BOM":
        bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product)).filter(models.BomHeader.id == instance.object_id).first()
        if bom:
            bom.status = "已发布"
            bom.release_date = today_text()
            create_integration_job(db, "ERP", "BOM", f"{bom.bom_type}-{bom.product.model}-{bom.version}", bom.product.model, instance.object_no, "BOM 流程已完成，等待同步 ERP 物料结构和用量。")
            auto_complete_project_deliverable(db, "BOM", bom.id)
    elif instance.object_type == "文档":
        document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == instance.object_id).first()
        if document:
            document.status = "已发布"
            document.approval_status = "已签核"
            document.updated_at = today_text()
            create_integration_job(db, "QMS", "文档", document.doc_no, document.product.model, document.doc_no, "文档流程已完成，等待同步 QMS/文控归档。")
            auto_complete_project_deliverable(db, "文档", document.id)
    elif instance.object_type == "变更":
        change = db.query(models.Change).options(selectinload(models.Change.product)).filter(models.Change.id == instance.object_id).first()
        if change:
            change.status = "执行中"
            if not change.submitted_at:
                change.submitted_at = today_text()
            close_change_when_actions_done(db, change.id, "系统")


def auto_complete_project_deliverable(db: Session, object_type: str, object_id: int) -> None:
    """对象审批发布后，自动完成关联的项目交付物。"""
    deliverables = (
        db.query(models.ProjectDeliverable)
        .filter(
            models.ProjectDeliverable.object_type == object_type,
            models.ProjectDeliverable.object_id == object_id,
            models.ProjectDeliverable.status.notin_(["已完成", "已关闭"]),
        )
        .all()
    )
    for d in deliverables:
        d.status = "已完成"
        d.completed_at = today_text()


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
