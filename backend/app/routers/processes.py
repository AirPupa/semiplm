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


@router.get("/api/process-routes")
def process_routes(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.ProcessRoute).options(selectinload(models.ProcessRoute.product), selectinload(models.ProcessRoute.steps))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.ProcessRoute.route_no.ilike(kw) | models.ProcessRoute.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.ProcessRoute.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_process_route(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/process-routes", status_code=201)
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


@router.put("/api/process-routes/{route_id}")
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


@router.delete("/api/process-routes/{route_id}")
def delete_process_route(route_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    route = db.query(models.ProcessRoute).filter(models.ProcessRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Process route not found")
    ensure_route_editable(route)
    db.delete(route)
    db.commit()
    return {"ok": True}


@router.post("/api/process-routes/{route_id}/steps", status_code=201)
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


@router.put("/api/process-steps/{step_id}")
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


@router.delete("/api/process-steps/{step_id}")
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


@router.post("/api/process-routes/{route_id}/submit")
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
    if route.status == "审批中":
        raise HTTPException(status_code=409, detail="Process route is already in review")
    # ECA 生成对象校验：如果工艺路线有 source_route_id，说明是 ECA 升版生成的草案
    if route.source_route_id:
        validate_eca_generated_object_ready(db, "工艺路线", route.id, route.route_no)
    route.status = "审批中"
    db.commit()
    db.refresh(route)
    return serialize_process_route(route)


@router.post("/api/process-routes/{route_id}/approve")
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
    if route.status not in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail="Process route must be submitted for review before approval")
    if route.source_route_id:
        validate_eca_generated_object_ready(db, "工艺路线", route.id, route.route_no)
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


@router.get("/api/products/{product_id}/process-steps")
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

@router.get("/api/process-routes/{route_id}/version-history")
def process_route_version_history(route_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """追溯工艺路线版本链路：来源路线、生成变更单和发布门状态。"""
    route = db.query(models.ProcessRoute).options(selectinload(models.ProcessRoute.product)).filter(models.ProcessRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Process route not found")

    chain: list[models.ProcessRoute] = []
    current = route
    visited = set()
    while current and current.id not in visited:
        visited.add(current.id)
        chain.append(current)
        if current.source_route_id:
            current = db.query(models.ProcessRoute).filter(models.ProcessRoute.id == current.source_route_id).first()
        else:
            break
    chain.reverse()

    history = []
    for item in chain:
        eca_action = (
            db.query(models.ChangeAction)
            .filter(
                models.ChangeAction.target_type == "工艺路线",
                models.ChangeAction.target_id == item.source_route_id if item.source_route_id else 0,
            )
            .first() if item.source_route_id else None
        )
        change_no = ""
        change_status = ""
        action_no = ""
        effectivity_type = ""
        effective_batch = ""
        effective_date = ""
        release_gate = ""
        gate_message = ""
        if eca_action:
            change = db.query(models.Change).filter(models.Change.id == eca_action.change_id).first()
            change_no = change.change_no if change else ""
            change_status = change.status if change else ""
            action_no = eca_action.action_no
            effectivity_type = eca_action.effectivity_type
            effective_batch = eca_action.effective_batch
            effective_date = eca_action.effective_date
            if eca_action.generated_object_no:
                gate = get_eca_generated_object_gate(db, "工艺路线", eca_action.generated_object_no)
                if gate:
                    release_gate = "可提交" if gate["ready"] else "待变更闭环"
                    gate_message = gate["message"]

        history.append({
            "id": item.id,
            "route_no": item.route_no,
            "version": item.version,
            "status": item.status,
            "name": item.name,
            "owner": item.owner,
            "release_date": item.release_date,
            "effective_batch": item.effective_batch,
            "source_route_id": item.source_route_id,
            "is_current": item.id == route.id,
            "change_no": change_no,
            "change_status": change_status,
            "eca_action_no": action_no,
            "eca_effectivity_type": effectivity_type,
            "eca_effective_batch": effective_batch,
            "eca_effective_date": effective_date,
            "release_gate_status": release_gate,
            "release_gate_message": gate_message,
        })
    return history

@router.get("/api/problem-reports")
def problem_reports(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.ProblemReport)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.ProblemReport.pr_no.ilike(kw) | models.ProblemReport.title.ilike(kw))
    total = q.count()
    rows = q.order_by(models.ProblemReport.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": r.id,
                "pr_no": r.pr_no,
                "title": r.title,
                "problem_type": r.problem_type,
                "severity": r.severity,
                "source": r.source,
                "product_id": r.product_id,
                "product_model": r.product_model,
                "description": r.description,
                "suggested_action": r.suggested_action,
                "status": r.status,
                "reporter": r.reporter,
                "reported_at": r.reported_at,
                "related_change_no": r.related_change_no,
                "remark": r.remark,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/problem-reports", status_code=201)
def create_problem_report(payload: ProblemReportPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    count = db.query(models.ProblemReport).count() + 1
    pr_no = payload.pr_no or f"PR-{count:04d}"
    row = models.ProblemReport(**{**payload.model_dump(), "pr_no": pr_no})
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "pr_no": row.pr_no}


@router.put("/api/problem-reports/{report_id}")
def update_problem_report(report_id: int, payload: ProblemReportUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    row = db.query(models.ProblemReport).filter(models.ProblemReport.id == report_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Problem report not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/problem-reports/{report_id}")
def delete_problem_report(report_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    row = db.query(models.ProblemReport).filter(models.ProblemReport.id == report_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Problem report not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/api/process-parameters")
def process_parameters(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.ProcessParameter)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.ProcessParameter.param_code.ilike(kw) | models.ProcessParameter.param_name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.ProcessParameter.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": r.id,
                "param_code": r.param_code,
                "param_name": r.param_name,
                "param_type": r.param_type,
                "unit": r.unit,
                "category": r.category,
                "default_value": r.default_value,
                "min_value": r.min_value,
                "max_value": r.max_value,
                "description": r.description,
                "status": r.status,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/process-parameters", status_code=201)
def create_process_parameter(payload: ProcessParameterPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    count = db.query(models.ProcessParameter).count() + 1
    param_code = payload.param_code or f"PARAM-{count:04d}"
    row = models.ProcessParameter(**{**payload.model_dump(), "param_code": param_code})
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "param_code": row.param_code}


@router.put("/api/process-parameters/{param_id}")
def update_process_parameter(param_id: int, payload: ProcessParameterUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    row = db.query(models.ProcessParameter).filter(models.ProcessParameter.id == param_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Process parameter not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/process-parameters/{param_id}")
def delete_process_parameter(param_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("process"))) -> dict:
    row = db.query(models.ProcessParameter).filter(models.ProcessParameter.id == param_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Process parameter not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
