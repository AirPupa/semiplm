from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import current_user_context, require_permission
from ..schemas import (
    WorkflowRejectPayload,
    WorkflowTaskActionPayload,
    WorkflowTransferPayload,
    WorkflowWithdrawPayload,
)
from ..serializers import serialize_workflow_instance
from ..services.helpers import today_text
from ..services.workflow import add_workflow_log, complete_business_object, withdraw_business_object


router = APIRouter()


@router.get("/api/workflow-instances")
def workflow_instances(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = (
        db.query(models.WorkflowInstance)
        .options(
            selectinload(models.WorkflowInstance.template),
            selectinload(models.WorkflowInstance.tasks),
            selectinload(models.WorkflowInstance.logs),
        )
    )
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.WorkflowInstance.object_no.ilike(kw) | models.WorkflowInstance.title.ilike(kw))
    total = q.count()
    rows = q.order_by(models.WorkflowInstance.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_workflow_instance(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/api/workflow-tasks")
def workflow_tasks(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    status: str = "",
    mine: bool = False,
    db: Session = Depends(get_db),
    context: dict = Depends(current_user_context),
) -> dict:
    q = (
        db.query(models.WorkflowTask)
        .join(models.WorkflowInstance)
        .options(selectinload(models.WorkflowTask.instance).selectinload(models.WorkflowInstance.template))
    )
    if status:
        q = q.filter(models.WorkflowTask.status == status)
    if mine:
        user = context["user"]
        q = q.filter(models.WorkflowTask.assignee == user.display_name)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            models.WorkflowTask.node_name.ilike(kw)
            | models.WorkflowTask.assignee.ilike(kw)
            | models.WorkflowInstance.object_no.ilike(kw)
            | models.WorkflowInstance.title.ilike(kw)
        )
    total = q.count()
    rows = q.order_by(models.WorkflowTask.status.desc(), models.WorkflowTask.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
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
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/workflow-tasks/{task_id}/approve")
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


@router.post("/api/workflow-tasks/{task_id}/reject")
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


@router.post("/api/workflow-tasks/{task_id}/transfer")
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


@router.post("/api/workflow-instances/{instance_id}/withdraw")
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
