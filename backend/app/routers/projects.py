import io
import os
from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import current_user_context, has_permission, require_permission
from ..schemas import *  # noqa: F401,F403
from ..serializers import *  # noqa: F401,F403
from ..services.change import (
    analyze_change_impacts,
    apply_change_action_revision,
    close_change_when_actions_done,
    create_change_release_jobs,
    get_eca_generated_object_gate,
    validate_action_effectivity,
    validate_change_action_target,
    validate_eca_generated_object_ready,
)
from ..services.helpers import (
    audit_log,
    commit_or_409,
    day_before,
    ensure_product_exists,
    ensure_project_exists,
    today_text,
    update_model,
)
from ..services.integration import create_integration_job
from ..services.process import (
    apply_bom_item_process_binding,
    ensure_route_editable,
    validate_process_route_ready,
)
from ..services.versioning import (
    close_previous_effective_boms,
    is_current_effective_bom,
    next_revision,
    next_unique_bom_version,
    next_unique_document_no,
    next_unique_process_version,
    next_unique_route_no,
)
from ..services.workflow import start_workflow


router = APIRouter()


@router.get("/api/projects")
def projects(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Project).options(selectinload(models.Project.tasks), selectinload(models.Project.deliverables), selectinload(models.Project.risks))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Project.project_no.ilike(kw) | models.Project.name.ilike(kw) | models.Project.product_model.ilike(kw))
    total = q.count()
    rows = q.order_by(models.Project.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
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
                "archived_at": row.archived_at,
                "archived_by": row.archived_by,
                "is_archived": bool(row.archived_at),
                "tasks": [{"id": task.id, "name": task.name, "phase": task.phase, "owner": task.owner, "status": task.status, "due_date": task.due_date} for task in row.tasks],
                "deliverables": [_serialize_deliverable(d, db) for d in row.deliverables],
                "risks": [{"id": r.id, "risk_type": r.risk_type, "description": r.description, "impact": r.impact, "probability": r.probability, "severity": r.severity, "owner": r.owner, "status": r.status, "mitigation": r.mitigation} for r in row.risks],
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/projects", status_code=201)
def create_project(payload: ProjectPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = models.Project(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Project number already exists")
    db.refresh(row)
    return {"id": row.id, "project_no": row.project_no}


@router.put("/api/projects/{project_id}")
def update_project(project_id: int, payload: ProjectUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    if row.archived_at:
        raise HTTPException(status_code=409, detail="项目已归档，不可修改")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    if row.archived_at:
        raise HTTPException(status_code=409, detail="项目已归档，不可删除")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/api/project-templates")
def project_templates(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.ProjectTemplate)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.ProjectTemplate.code.ilike(kw) | models.ProjectTemplate.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.ProjectTemplate.code).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": r.id, "code": r.code, "name": r.name, "description": r.description, "stages": r.stages, "status": r.status} for r in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/project-templates", status_code=201)
def create_project_template(payload: ProjectTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = models.ProjectTemplate(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Template code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code}


@router.put("/api/project-templates/{template_id}")
def update_project_template(template_id: int, payload: ProjectTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectTemplate).filter(models.ProjectTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/project-templates/{template_id}")
def delete_project_template(template_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectTemplate).filter(models.ProjectTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/api/projects/from-template", status_code=201)
def create_project_from_template(payload: ProjectFromTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    import json
    template = db.query(models.ProjectTemplate).filter(models.ProjectTemplate.id == payload.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    try:
        stages = json.loads(template.stages) if template.stages else ["概念", "设计", "流片", "验证", "试产"]
    except (json.JSONDecodeError, TypeError):
        stages = ["概念", "设计", "流片", "验证", "试产"]
    first_phase = stages[0] if stages else "概念"
    project = models.Project(
        project_no=payload.project_no,
        name=payload.name,
        product_model=payload.product_model,
        phase=first_phase,
        progress=0,
        owner=payload.owner,
        start_date=payload.start_date,
        end_date=payload.end_date,
        risk_level="低",
    )
    db.add(project)
    commit_or_409(db, "Project number already exists")
    db.refresh(project)
    for stage in stages:
        task = models.ProjectTask(
            project_id=project.id,
            name=f"{stage}阶段任务",
            phase=stage,
            owner=payload.owner,
            status="待处理" if stage != first_phase else "进行中",
            due_date="",
            start_date=payload.start_date if stage == first_phase else "",
        )
        db.add(task)
    db.commit()
    return {"id": project.id, "project_no": project.project_no, "phase": project.phase, "tasks_created": len(stages)}


def _deliverable_object_brief(db: Session, object_type: str, object_id: int | None) -> dict:
    """查询交付物绑定对象的关键信息（编号/版本/状态），供交付物列表和齐套校验复用。"""
    if not object_type or not object_id:
        return {}
    if object_type == "BOM":
        row = db.query(models.BomHeader).filter(models.BomHeader.id == object_id).first()
        if not row:
            return {"object_label": "BOM 已删除", "object_version": "", "object_status": "", "object_released": False}
        return {
            "object_label": f"{row.bom_type} {row.version}",
            "object_version": row.version,
            "object_status": row.status,
            "object_released": row.status == "已发布",
        }
    if object_type == "文档":
        row = db.query(models.Document).filter(models.Document.id == object_id).first()
        if not row:
            return {"object_label": "文档已删除", "object_version": "", "object_status": "", "object_released": False}
        return {
            "object_label": f"{row.doc_no} {row.version}",
            "object_version": row.version,
            "object_status": row.status,
            "object_released": row.status == "已发布",
        }
    if object_type == "工艺路线":
        row = db.query(models.ProcessRoute).filter(models.ProcessRoute.id == object_id).first()
        if not row:
            return {"object_label": "工艺路线已删除", "object_version": "", "object_status": "", "object_released": False}
        return {
            "object_label": f"{row.route_no} {row.version}",
            "object_version": row.version,
            "object_status": row.status,
            "object_released": row.status == "已发布",
        }
    return {}


def _serialize_deliverable(r: models.ProjectDeliverable, db: Session) -> dict:
    base = {
        "id": r.id, "name": r.name, "deliverable_type": r.deliverable_type, "phase": r.phase,
        "owner": r.owner, "status": r.status, "due_date": r.due_date, "completed_at": r.completed_at,
        "description": r.description, "object_type": r.object_type, "object_id": r.object_id,
    }
    base.update(_deliverable_object_brief(db, r.object_type, r.object_id))
    return base


@router.get("/api/projects/{project_id}/deliverables")
def project_deliverables(project_id: int, db: Session = Depends(get_db)) -> list[dict]:
    ensure_project_exists(db, project_id)
    rows = db.query(models.ProjectDeliverable).filter(models.ProjectDeliverable.project_id == project_id).order_by(models.ProjectDeliverable.id).all()
    return [_serialize_deliverable(r, db) for r in rows]


def _ensure_project_editable(db: Session, project_id: int) -> models.Project:
    """校验项目存在且未归档，归档后禁止增删改子对象。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.archived_at:
        raise HTTPException(status_code=409, detail="项目已归档，不可修改")
    return project


@router.post("/api/projects/{project_id}/deliverables", status_code=201)
def create_project_deliverable(project_id: int, payload: ProjectDeliverablePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    _ensure_project_editable(db, project_id)
    row = models.ProjectDeliverable(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.put("/api/project-deliverables/{deliverable_id}")
def update_project_deliverable(deliverable_id: int, payload: ProjectDeliverableUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectDeliverable).filter(models.ProjectDeliverable.id == deliverable_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    _ensure_project_editable(db, row.project_id)
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/project-deliverables/{deliverable_id}")
def delete_project_deliverable(deliverable_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectDeliverable).filter(models.ProjectDeliverable.id == deliverable_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    _ensure_project_editable(db, row.project_id)
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/api/projects/{project_id}/risks")
def project_risks(project_id: int, db: Session = Depends(get_db)) -> list[dict]:
    ensure_project_exists(db, project_id)
    rows = db.query(models.ProjectRisk).filter(models.ProjectRisk.project_id == project_id).order_by(models.ProjectRisk.id).all()
    return [{"id": r.id, "risk_type": r.risk_type, "description": r.description, "impact": r.impact, "probability": r.probability, "severity": r.severity, "owner": r.owner, "status": r.status, "mitigation": r.mitigation} for r in rows]


@router.post("/api/projects/{project_id}/risks", status_code=201)
def create_project_risk(project_id: int, payload: ProjectRiskPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    _ensure_project_editable(db, project_id)
    row = models.ProjectRisk(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.put("/api/project-risks/{risk_id}")
def update_project_risk(risk_id: int, payload: ProjectRiskUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectRisk).filter(models.ProjectRisk.id == risk_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Risk not found")
    _ensure_project_editable(db, row.project_id)
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/project-risks/{risk_id}")
def delete_project_risk(risk_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectRisk).filter(models.ProjectRisk.id == risk_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Risk not found")
    _ensure_project_editable(db, row.project_id)
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/api/projects/{project_id}/cross-modules")
def project_cross_modules(project_id: int, db: Session = Depends(get_db)) -> dict:
    """项目跨模块关联聚合：通过 product_model 关联产品，再聚合 BOM、文档、工艺路线、工程变更、质量问题。
    用于项目详情页「关联对象」tab，避免前端发起多次请求拼装。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    product_model = project.product_model or ""
    product = (
        db.query(models.Product)
        .filter(models.Product.model == product_model)
        .first()
    ) if product_model else None
    product_id = product.id if product else None

    # BOM：通过 product_id 关联
    boms: list[dict] = []
    if product_id:
        rows = (
            db.query(models.BomHeader)
            .options(selectinload(models.BomHeader.product))
            .filter(models.BomHeader.product_id == product_id)
            .order_by(models.BomHeader.bom_type, models.BomHeader.version)
            .all()
        )
        for r in rows:
            boms.append({
                "id": r.id, "bom_type": r.bom_type, "version": r.version,
                "status": r.status, "owner": r.owner, "release_date": r.release_date,
                "effective_date": r.effective_date, "is_current": is_current_effective_bom(r),
            })

    # 文档：通过 product_id 关联
    documents: list[dict] = []
    if product_id:
        rows = (
            db.query(models.Document)
            .filter(models.Document.product_id == product_id)
            .order_by(models.Document.category, models.Document.doc_no)
            .all()
        )
        for r in rows:
            documents.append({
                "id": r.id, "doc_no": r.doc_no, "title": r.title,
                "category": r.category, "version": r.version, "status": r.status,
                "owner": r.owner, "updated_at": r.updated_at,
            })

    # 工艺路线：通过 product_id 关联
    process_routes: list[dict] = []
    if product_id:
        rows = (
            db.query(models.ProcessRoute)
            .options(selectinload(models.ProcessRoute.product))
            .filter(models.ProcessRoute.product_id == product_id)
            .order_by(models.ProcessRoute.version)
            .all()
        )
        for r in rows:
            process_routes.append({
                "id": r.id, "route_no": r.route_no, "name": r.name,
                "version": r.version, "status": r.status, "owner": r.owner,
                "release_date": r.release_date,
            })

    # 工程变更：通过 product_id 关联
    changes: list[dict] = []
    if product_id:
        rows = (
            db.query(models.Change)
            .filter(models.Change.product_id == product_id)
            .order_by(models.Change.id.desc())
            .all()
        )
        for r in rows:
            changes.append({
                "id": r.id, "change_no": r.change_no, "title": r.title,
                "change_type": r.change_type, "status": r.status, "priority": r.priority,
                "owner": r.owner, "submitted_at": r.submitted_at,
            })

    # 质量问题：通过 product_model 字符串关联
    quality_issues: list[dict] = []
    if product_model:
        rows = (
            db.query(models.QualityIssue)
            .filter(models.QualityIssue.product_model == product_model)
            .order_by(models.QualityIssue.id.desc())
            .all()
        )
        for r in rows:
            quality_issues.append({
                "id": r.id, "issue_no": r.issue_no, "title": r.title,
                "severity": r.severity, "status": r.status, "owner": r.owner,
                "lot_no": r.lot_no,
            })

    # 需求规格：通过 product_id 关联（一并聚合，便于项目追溯需求）
    requirements: list[dict] = []
    if product_id:
        rows = (
            db.query(models.Requirement)
            .filter(models.Requirement.product_id == product_id)
            .order_by(models.Requirement.id.desc())
            .all()
        )
        for r in rows:
            requirements.append({
                "id": r.id, "req_no": r.req_no, "title": r.title,
                "category": r.category, "priority": r.priority, "status": r.status,
                "owner": r.owner,
            })

    return {
        "project_id": project.id,
        "project_no": project.project_no,
        "product_model": product_model,
        "product_id": product_id,
        "product_name": product.name if product else "",
        "product_lifecycle": product.lifecycle if product else "",
        "counts": {
            "boms": len(boms),
            "documents": len(documents),
            "process_routes": len(process_routes),
            "changes": len(changes),
            "quality_issues": len(quality_issues),
            "requirements": len(requirements),
        },
        "boms": boms,
        "documents": documents,
        "process_routes": process_routes,
        "changes": changes,
        "quality_issues": quality_issues,
        "requirements": requirements,
    }


PROJECT_PHASES = ["概念", "设计", "流片", "验证", "试产", "量产导入"]


@router.get("/api/projects/{project_id}/tasks")
def project_tasks(project_id: int, db: Session = Depends(get_db)) -> list[dict]:
    ensure_project_exists(db, project_id)
    rows = db.query(models.ProjectTask).filter(models.ProjectTask.project_id == project_id).order_by(models.ProjectTask.id).all()
    return [{"id": r.id, "name": r.name, "phase": r.phase, "owner": r.owner, "status": r.status, "due_date": r.due_date, "start_date": r.start_date, "parent_id": r.parent_id, "depends_on": r.depends_on} for r in rows]


@router.post("/api/projects/{project_id}/tasks", status_code=201)
def create_project_task(project_id: int, payload: ProjectTaskPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    _ensure_project_editable(db, project_id)
    row = models.ProjectTask(project_id=project_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.put("/api/project-tasks/{task_id}")
def update_project_task(task_id: int, payload: ProjectTaskUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectTask).filter(models.ProjectTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    _ensure_project_editable(db, row.project_id)
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/project-tasks/{task_id}")
def delete_project_task(task_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    row = db.query(models.ProjectTask).filter(models.ProjectTask.id == task_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    _ensure_project_editable(db, row.project_id)
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/api/projects/{project_id}/closure-check")
def project_closure_check(project_id: int, db: Session = Depends(get_db)) -> dict:
    """项目结项齐套校验：检查所有阶段交付物状态完成 + 绑定对象已发布。
    返回每个交付物的校验结果和整体是否齐套，供阶段门推进和结项决策使用。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    deliverables = (
        db.query(models.ProjectDeliverable)
        .filter(models.ProjectDeliverable.project_id == project_id)
        .order_by(models.ProjectDeliverable.phase, models.ProjectDeliverable.id)
        .all()
    )
    items: list[dict] = []
    for d in deliverables:
        obj_brief = _deliverable_object_brief(db, d.object_type, d.object_id)
        status_ok = d.status in {"已完成", "已关闭"}
        # 绑定对象校验：未绑定视为通过（非所有交付物都需绑定对象）；绑定则要求已发布
        object_ok = True
        if d.object_type and d.object_id:
            object_ok = obj_brief.get("object_released", False)
        items.append({
            "id": d.id, "name": d.name, "phase": d.phase, "status": d.status,
            "object_type": d.object_type, "object_id": d.object_id,
            "object_label": obj_brief.get("object_label", ""),
            "object_version": obj_brief.get("object_version", ""),
            "object_status": obj_brief.get("object_status", ""),
            "status_ok": status_ok,
            "object_ok": object_ok,
            "ready": status_ok and object_ok,
            "issue": (
                "交付物状态未完成" if not status_ok
                else f"绑定{d.object_type}未发布（当前：{obj_brief.get('object_status', '未知')}）" if not object_ok
                else ""
            ),
        })
    total = len(items)
    ready_count = sum(1 for it in items if it["ready"])
    pending = [it for it in items if not it["ready"]]
    return {
        "project_id": project.id,
        "project_no": project.project_no,
        "phase": project.phase,
        "progress": project.progress,
        "total": total,
        "ready": ready_count,
        "pending": len(pending),
        "is_complete": len(pending) == 0,
        "items": items,
        "pending_items": pending,
    }


@router.post("/api/projects/{project_id}/advance-phase")
def advance_project_phase(project_id: int, payload: ProjectPhaseGatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("project"))) -> dict:
    project = _ensure_project_editable(db, project_id)
    if project.phase == "量产导入":
        raise HTTPException(status_code=409, detail="Project already at final phase")

    current_phase = project.phase
    deliverables = (
        db.query(models.ProjectDeliverable)
        .filter(models.ProjectDeliverable.project_id == project_id, models.ProjectDeliverable.phase == current_phase)
        .all()
    )
    pending: list[str] = []
    for d in deliverables:
        if d.status not in {"已完成", "已关闭"}:
            pending.append(f"{d.name}(状态:{d.status})")
            continue
        if d.object_type and d.object_id:
            obj_brief = _deliverable_object_brief(db, d.object_type, d.object_id)
            if not obj_brief.get("object_released"):
                pending.append(f"{d.name}(绑定{d.object_type}未发布)")
    if pending:
        detail = "、".join(pending[:3])
        raise HTTPException(status_code=409, detail=f"当前阶段交付物未齐套：{detail}")

    try:
        idx = PROJECT_PHASES.index(current_phase)
    except ValueError:
        idx = 0
    next_phase = PROJECT_PHASES[min(idx + 1, len(PROJECT_PHASES) - 1)]
    old_phase = project.phase
    project.phase = next_phase
    project.progress = min(100, int((idx + 1) / len(PROJECT_PHASES) * 100))
    db.commit()
    db.refresh(project)
    return {
        "ok": True,
        "old_phase": old_phase,
        "new_phase": next_phase,
        "progress": project.progress,
        "message": f"阶段门从「{old_phase}」推进到「{next_phase}」",
    }


@router.post("/api/projects/{project_id}/archive")
def archive_project(project_id: int, payload: ProjectArchivePayload, db: Session = Depends(get_db), user: dict = Depends(current_user_context)) -> dict:
    """项目归档：校验交付物齐套 + 处于最终阶段，冻结为已归档状态。
    归档后项目及关联对象进入只读，形成项目数据包供追溯查询。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.archived_at:
        raise HTTPException(status_code=409, detail="项目已归档，不可重复归档")
    if project.phase != "量产导入":
        raise HTTPException(status_code=409, detail=f"项目未处于最终阶段（当前：{project.phase}），不可归档")

    # 复用结项齐套校验：所有交付物须齐套
    deliverables = (
        db.query(models.ProjectDeliverable)
        .filter(models.ProjectDeliverable.project_id == project_id)
        .all()
    )
    pending: list[str] = []
    for d in deliverables:
        if d.status not in {"已完成", "已关闭"}:
            pending.append(f"{d.name}(状态未完成)")
            continue
        if d.object_type and d.object_id:
            obj_brief = _deliverable_object_brief(db, d.object_type, d.object_id)
            if not obj_brief.get("object_released"):
                pending.append(f"{d.name}(绑定{d.object_type}未发布)")
    if pending:
        detail = "、".join(pending[:5])
        raise HTTPException(status_code=409, detail=f"交付物未齐套，不可归档：{detail}")

    project.archived_at = today_text()
    project.archived_by = payload.archived_by or (user.get("user").username if user.get("user") else "")
    project.archive_summary = payload.summary or ""
    project.progress = 100
    db.commit()
    audit_log(db, "归档", "Project", project.id, project.project_no, f"项目 {project.project_no} 归档", project.archived_by)
    return {
        "ok": True,
        "project_id": project.id,
        "project_no": project.project_no,
        "archived_at": project.archived_at,
        "archived_by": project.archived_by,
        "message": f"项目 {project.project_no} 已归档",
    }


@router.get("/api/projects/{project_id}/archive-package")
def project_archive_package(project_id: int, db: Session = Depends(get_db)) -> dict:
    """项目归档数据包：聚合项目基本信息 + 关联 BOM/文档/工艺/变更/质量报告/流程记录，
    用于归档后追溯查询，一次请求拿到完整数据包。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.archived_at:
        raise HTTPException(status_code=409, detail="项目未归档，暂无数据包")

    product_model = project.product_model or ""
    product = (
        db.query(models.Product).filter(models.Product.model == product_model).first()
    ) if product_model else None
    product_id = product.id if product else None

    # BOM（含明细条数）
    boms: list[dict] = []
    if product_id:
        rows = (
            db.query(models.BomHeader)
            .options(selectinload(models.BomHeader.items))
            .filter(models.BomHeader.product_id == product_id)
            .order_by(models.BomHeader.bom_type, models.BomHeader.version)
            .all()
        )
        for r in rows:
            boms.append({
                "id": r.id, "bom_type": r.bom_type, "version": r.version,
                "status": r.status, "owner": r.owner, "release_date": r.release_date,
                "effective_date": r.effective_date, "items_count": len(r.items),
            })

    # 文档
    documents: list[dict] = []
    if product_id:
        for r in db.query(models.Document).filter(models.Document.product_id == product_id).order_by(models.Document.category, models.Document.doc_no).all():
            documents.append({
                "id": r.id, "doc_no": r.doc_no, "title": r.title, "category": r.category,
                "version": r.version, "status": r.status, "owner": r.owner, "updated_at": r.updated_at,
            })

    # 工艺路线
    process_routes: list[dict] = []
    if product_id:
        for r in db.query(models.ProcessRoute).filter(models.ProcessRoute.product_id == product_id).order_by(models.ProcessRoute.version).all():
            process_routes.append({
                "id": r.id, "route_no": r.route_no, "name": r.name, "version": r.version,
                "status": r.status, "owner": r.owner, "release_date": r.release_date,
            })

    # 工程变更
    changes: list[dict] = []
    if product_id:
        for r in db.query(models.Change).filter(models.Change.product_id == product_id).order_by(models.Change.id.desc()).all():
            changes.append({
                "id": r.id, "change_no": r.change_no, "title": r.title, "change_type": r.change_type,
                "status": r.status, "priority": r.priority, "owner": r.owner, "submitted_at": r.submitted_at,
            })

    # 质量问题
    quality_issues: list[dict] = []
    if product_model:
        for r in db.query(models.QualityIssue).filter(models.QualityIssue.product_model == product_model).order_by(models.QualityIssue.id.desc()).all():
            quality_issues.append({
                "id": r.id, "issue_no": r.issue_no, "title": r.title, "severity": r.severity,
                "status": r.status, "owner": r.owner, "lot_no": r.lot_no,
            })

    # 质量报告
    quality_reports: list[dict] = []
    if product_model:
        for r in db.query(models.QualityReport).filter(models.QualityReport.product_model == product_model).order_by(models.QualityReport.id.desc()).all():
            quality_reports.append({
                "id": r.id, "report_no": r.report_no, "title": r.title, "report_type": r.report_type,
                "status": r.status, "owner": r.owner, "archived_at": r.archived_at,
            })

    # 流程记录：通过 product_model 关联 workflow_instances
    workflow_instances: list[dict] = []
    if product_model:
        for r in db.query(models.WorkflowInstance).filter(models.WorkflowInstance.product_model == product_model).order_by(models.WorkflowInstance.id.desc()).all():
            workflow_instances.append({
                "id": r.id, "object_type": r.object_type, "object_no": r.object_no,
                "title": r.title, "status": r.status, "started_by": r.started_by,
                "started_at": r.started_at, "completed_at": r.completed_at,
            })

    # 交付物
    deliverables = (
        db.query(models.ProjectDeliverable)
        .filter(models.ProjectDeliverable.project_id == project_id)
        .order_by(models.ProjectDeliverable.phase, models.ProjectDeliverable.id)
        .all()
    )
    deliverable_items = [_serialize_deliverable(d, db) for d in deliverables]

    return {
        "project": {
            "id": project.id, "project_no": project.project_no, "name": project.name,
            "product_model": product_model, "phase": project.phase, "progress": project.progress,
            "owner": project.owner, "start_date": project.start_date, "end_date": project.end_date,
            "risk_level": project.risk_level,
            "archived_at": project.archived_at, "archived_by": project.archived_by,
            "archive_summary": project.archive_summary,
        },
        "product": {
            "id": product_id, "name": product.name if product else "",
            "lifecycle": product.lifecycle if product else "",
        } if product else None,
        "counts": {
            "boms": len(boms), "documents": len(documents), "process_routes": len(process_routes),
            "changes": len(changes), "quality_issues": len(quality_issues),
            "quality_reports": len(quality_reports), "workflow_instances": len(workflow_instances),
            "deliverables": len(deliverable_items),
        },
        "deliverables": deliverable_items,
        "boms": boms,
        "documents": documents,
        "process_routes": process_routes,
        "changes": changes,
        "quality_issues": quality_issues,
        "quality_reports": quality_reports,
        "workflow_instances": workflow_instances,
    }


@router.post("/api/projects/{project_id}/unarchive")
def unarchive_project(project_id: int, db: Session = Depends(get_db), user: dict = Depends(current_user_context)) -> dict:
    """撤销归档：仅在特殊情况下使用，恢复项目为可编辑状态。"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.archived_at:
        raise HTTPException(status_code=409, detail="项目未归档，无需撤销")
    project.archived_at = ""
    project.archived_by = ""
    project.archive_summary = ""
    db.commit()
    username = user.get("user").username if user.get("user") else ""
    audit_log(db, "撤销归档", "Project", project.id, project.project_no, f"项目 {project.project_no} 撤销归档", username)
    return {"ok": True, "message": f"项目 {project.project_no} 已撤销归档"}
