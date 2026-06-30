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


@router.get("/api/changes")
def changes(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Change.change_no.ilike(kw) | models.Change.title.ilike(kw))
    total = q.count()
    rows = q.order_by(models.Change.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_change(row, db) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/changes", status_code=201)
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


@router.put("/api/changes/{change_id}")
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


@router.delete("/api/changes/{change_id}")
def delete_change(change_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    change = db.query(models.Change).filter(models.Change.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    if change.status != "草稿":
        raise HTTPException(status_code=409, detail="Only draft changes can be deleted")
    db.delete(change)
    db.commit()
    return {"ok": True}


@router.post("/api/changes/{change_id}/submit")
def submit_change(change_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    if change.status not in ("草稿", "已驳回"):
        raise HTTPException(status_code=409, detail=f"Change in {change.status} status cannot be submitted")
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


@router.post("/api/changes/{change_id}/analyze")
def analyze_change(change_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change_id).first()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    analyze_change_impacts(db, change)
    db.commit()
    change = db.query(models.Change).options(selectinload(models.Change.product), selectinload(models.Change.impacts), selectinload(models.Change.approvals)).filter(models.Change.id == change_id).first()
    return serialize_change(change, db)


@router.post("/api/changes/{change_id}/impacts", status_code=201)
def create_change_impact(change_id: int, payload: ChangeImpactPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    if not db.query(models.Change.id).filter(models.Change.id == change_id).first():
        raise HTTPException(status_code=404, detail="Change not found")
    impact = models.ChangeImpact(change_id=change_id, **payload.model_dump())
    db.add(impact)
    db.commit()
    db.refresh(impact)
    return {"id": impact.id, "type": impact.impact_type, "impact_type": impact.impact_type, "target": impact.target, "risk": impact.risk, "action": impact.action}


@router.put("/api/change-impacts/{impact_id}")
def update_change_impact(impact_id: int, payload: ChangeImpactUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    impact = db.query(models.ChangeImpact).filter(models.ChangeImpact.id == impact_id).first()
    if not impact:
        raise HTTPException(status_code=404, detail="Change impact not found")
    update_model(impact, payload)
    db.commit()
    db.refresh(impact)
    return {"id": impact.id, "type": impact.impact_type, "impact_type": impact.impact_type, "target": impact.target, "risk": impact.risk, "action": impact.action}


@router.delete("/api/change-impacts/{impact_id}")
def delete_change_impact(impact_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    impact = db.query(models.ChangeImpact).filter(models.ChangeImpact.id == impact_id).first()
    if not impact:
        raise HTTPException(status_code=404, detail="Change impact not found")
    db.delete(impact)
    db.commit()
    return {"ok": True}


@router.post("/api/changes/{change_id}/actions", status_code=201)
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


@router.get("/api/changes/{change_id}/revision-archive")
def change_revision_archive(change_id: int, db: Session = Depends(get_db)) -> list[dict]:
    if not db.query(models.Change.id).filter(models.Change.id == change_id).first():
        raise HTTPException(status_code=404, detail="Change not found")
    rows = (
        db.query(models.ChangeAction)
        .filter(models.ChangeAction.change_id == change_id, models.ChangeAction.generated_object_no != "")
        .order_by(models.ChangeAction.id)
        .all()
    )
    archive_rows = []
    for row in rows:
        gate = get_eca_generated_object_gate(db, row.target_type, row.generated_object_no) or {
            "ready": True,
            "action_no": row.action_no,
            "action_status": row.status,
            "change_no": "",
            "change_status": "",
            "message": "生成对象已满足提交发布条件。",
        }
        archive_rows.append({
            "action_no": row.action_no,
            "action_type": row.action_type,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "source_object": row.target_object,
            "source_version": row.target_version,
            "effectivity_type": row.effectivity_type,
            "effectivity_scope": row.effectivity_scope,
            "effective_date": row.effective_date,
            "effective_batch": row.effective_batch,
            "generated_object_no": row.generated_object_no,
            "owner": row.owner,
            "status": row.status,
            "change_no": gate["change_no"],
            "change_status": gate["change_status"],
            "release_gate_status": "可提交" if gate["ready"] else "待变更闭环",
            "release_gate_message": gate["message"],
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
        })
    return archive_rows


@router.put("/api/change-actions/{action_id}")
def update_change_action(action_id: int, payload: ChangeActionUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    action = db.query(models.ChangeAction).filter(models.ChangeAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Change action not found")
    if action.status == "已完成":
        raise HTTPException(status_code=409, detail="Completed action cannot be edited")
    update_model(action, payload)
    validate_change_action_target(db, action)
    commit_or_409(db, "Change action number already exists")
    db.refresh(action)
    return serialize_change_action(action)


@router.post("/api/change-actions/{action_id}/close")
def close_change_action(action_id: int, payload: ChangeActionClosePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("change"))) -> dict:
    action = db.query(models.ChangeAction).filter(models.ChangeAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Change action not found")
    if action.status == "已完成":
        raise HTTPException(status_code=409, detail="ECA action is already closed")

    change = db.query(models.Change).filter(models.Change.id == action.change_id).first()
    if change and change.status != "执行中":
        raise HTTPException(status_code=409, detail=f"Change is in {change.status} status, actions can only be closed when change is executing")

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


@router.get("/api/change-actions")
def change_actions(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.ChangeAction).join(models.Change).join(models.Product)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.ChangeAction.action_no.ilike(kw) | models.ChangeAction.target_object.ilike(kw))
    total = q.count()
    rows = q.order_by(models.ChangeAction.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
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
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/api/products/{product_id}/effectivity-batches")
def product_effectivity_batches(product_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """按产品聚合所有 ECA 动作的生效批次，用于批次控制总览。"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    actions = (
        db.query(models.ChangeAction)
        .join(models.Change)
        .filter(models.Change.product_id == product_id)
        .order_by(models.ChangeAction.id)
        .all()
    )

    batch_map: dict[str, dict] = {}
    no_batch_rows: list[dict] = []
    for action in actions:
        change = db.query(models.Change).filter(models.Change.id == action.change_id).first()
        change_no = change.change_no if change else ""
        change_status = change.status if change else ""
        gate = get_eca_generated_object_gate(db, action.target_type, action.generated_object_no) if action.generated_object_no else None
        row = {
            "action_no": action.action_no,
            "action_type": action.action_type,
            "target_type": action.target_type,
            "target_object": action.target_object,
            "target_version": action.target_version,
            "generated_object_no": action.generated_object_no,
            "effectivity_type": action.effectivity_type,
            "effectivity_scope": action.effectivity_scope,
            "effective_date": action.effective_date,
            "effective_batch": action.effective_batch,
            "owner": action.owner,
            "status": action.status,
            "due_date": action.due_date,
            "change_no": change_no,
            "change_status": change_status,
            "release_gate_status": (gate["ready"] if gate else True),
            "release_gate_message": (gate["message"] if gate else ""),
        }
        batch_key = action.effective_batch or ""
        if "批次" in (action.effectivity_type or "") and batch_key:
            if batch_key not in batch_map:
                batch_map[batch_key] = {
                    "effective_batch": batch_key,
                    "effectivity_type": action.effectivity_type,
                    "effective_date": action.effective_date,
                    "actions": [],
                    "change_nos": set(),
                    "pending_count": 0,
                    "done_count": 0,
                }
            batch_map[batch_key]["actions"].append(row)
            batch_map[batch_key]["change_nos"].add(change_no)
            if action.status == "已完成":
                batch_map[batch_key]["done_count"] += 1
            else:
                batch_map[batch_key]["pending_count"] += 1
            if not batch_map[batch_key]["effective_date"] and action.effective_date:
                batch_map[batch_key]["effective_date"] = action.effective_date
        else:
            no_batch_rows.append(row)

    batches = []
    for batch_key, info in batch_map.items():
        all_done = info["pending_count"] == 0 and info["done_count"] > 0
        batches.append({
            "effective_batch": info["effective_batch"],
            "effectivity_type": info["effectivity_type"],
            "effective_date": info["effective_date"],
            "change_nos": sorted(info["change_nos"]),
            "action_count": len(info["actions"]),
            "pending_count": info["pending_count"],
            "done_count": info["done_count"],
            "batch_status": "已生效" if all_done else "执行中" if info["done_count"] > 0 else "待执行",
            "actions": info["actions"],
        })
    batches.sort(key=lambda b: b["effective_batch"])

    return {
        "product_id": product_id,
        "product_model": product.model,
        "batches": batches,
        "no_batch_actions": no_batch_rows,
    }
