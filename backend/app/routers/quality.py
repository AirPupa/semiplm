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


@router.get("/api/quality")
def quality(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    lots_q = db.query(models.QualityLot).options(selectinload(models.QualityLot.product))
    issues_q = db.query(models.QualityIssue)
    if keyword:
        kw = f"%{keyword}%"
        lots_q = lots_q.filter(models.QualityLot.lot_no.ilike(kw) | models.QualityLot.wafer_id.ilike(kw))
        issues_q = issues_q.filter(models.QualityIssue.issue_no.ilike(kw) | models.QualityIssue.title.ilike(kw))
    lots_total = lots_q.count()
    issues_total = issues_q.count()
    lots = lots_q.order_by(models.QualityLot.id).offset((page - 1) * page_size).limit(page_size).all()
    issues = issues_q.order_by(models.QualityIssue.id).offset((page - 1) * page_size).limit(page_size).all()
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
        "lots_total": lots_total,
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
        "issues_total": issues_total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/api/quality/capas")
def quality_capas(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.QualityCAPA)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.QualityCAPA.capa_no.ilike(kw) | models.QualityCAPA.title.ilike(kw))
    total = q.count()
    rows = q.order_by(models.QualityCAPA.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": r.id, "capa_no": r.capa_no, "issue_id": r.issue_id, "title": r.title, "source": r.source, "root_cause": r.root_cause, "corrective_action": r.corrective_action, "preventive_action": r.preventive_action, "owner": r.owner, "status": r.status, "due_date": r.due_date, "closed_at": r.closed_at, "result": r.result}
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/quality/capas", status_code=201)
def create_quality_capa(payload: QualityCAPAPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    if not payload.capa_no:
        count = db.query(models.QualityCAPA).count() + 1
        payload.capa_no = f"CAPA-{count:04d}"
    row = models.QualityCAPA(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "capa_no": row.capa_no}


@router.put("/api/quality/capas/{capa_id}")
def update_quality_capa(capa_id: int, payload: QualityCAPAUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityCAPA).filter(models.QualityCAPA.id == capa_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="CAPA not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/quality/capas/{capa_id}")
def delete_quality_capa(capa_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityCAPA).filter(models.QualityCAPA.id == capa_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="CAPA not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/api/quality/issues/{issue_id}/create-capa", status_code=201)
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


@router.post("/api/quality/issues", status_code=201)
def create_quality_issue(payload: QualityIssuePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    if not payload.issue_no:
        count = db.query(models.QualityIssue).count() + 1
        payload.issue_no = f"QI-{count:04d}"
    row = models.QualityIssue(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Issue number already exists")
    db.refresh(row)
    return {"id": row.id, "issue_no": row.issue_no}


@router.put("/api/quality/issues/{issue_id}")
def update_quality_issue(issue_id: int, payload: QualityIssueUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quality issue not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/quality/issues/{issue_id}")
def delete_quality_issue(issue_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quality issue not found")
    if row.status in {"CAPA 执行中", "已关闭"}:
        raise HTTPException(status_code=409, detail="Cannot delete issue with CAPA in progress or closed")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/api/quality/issues/{issue_id}/close")
def close_quality_issue(issue_id: int, payload: WorkflowTaskActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Quality issue not found")
    if issue.status == "已关闭":
        raise HTTPException(status_code=409, detail="Issue already closed")
    issue.status = "已关闭"
    issue.corrective_action = f"{issue.corrective_action}\n[关闭人：{payload.acted_by}，日期：{today_text()}，备注：{payload.comment}]".strip()
    db.commit()
    return {"ok": True}


@router.post("/api/quality/issues/{issue_id}/trigger-ecr", status_code=201)
def trigger_ecr_from_issue(issue_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    """质量问题触发 ECR：自动创建关联产品的变更单草稿。"""
    issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Quality issue not found")
    if issue.status == "已关闭":
        raise HTTPException(status_code=409, detail="Cannot trigger ECR from closed issue")

    product = (
        db.query(models.Product)
        .filter(models.Product.model == issue.product_model)
        .first()
        if issue.product_model else None
    )
    if not product:
        raise HTTPException(status_code=409, detail=f"Product model '{issue.product_model}' not found, cannot trigger ECR")

    existing = (
        db.query(models.Change)
        .filter(models.Change.title.like(f"%{issue.issue_no}%"))
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"ECR already exists for {issue.issue_no}: {existing.change_no}")

    count = db.query(models.Change).count() + 1
    change_no = f"ECR-{product.model}-QI{count:03d}"
    change = models.Change(
        product_id=product.id,
        change_no=change_no,
        title=f"质量问题 {issue.issue_no} 触发变更：{issue.title}",
        change_type="ECR",
        reason=f"质量问题 {issue.issue_no} 触发。\n问题描述：{issue.title}\n根因：{issue.root_cause}\n纠正措施：{issue.corrective_action}",
        status="草稿",
        priority="高" if issue.severity == "高" else "中",
        owner=issue.owner or product.owner,
        submitted_at="",
        before_desc=f"Lot {issue.lot_no} 出现质量问题：{issue.title}",
        after_desc="待影响分析后确定",
    )
    db.add(change)
    issue.status = "已触发 ECR"
    db.commit()
    db.refresh(change)
    return {"id": change.id, "change_no": change.change_no, "product_id": product.id}


@router.post("/api/quality/capas/{capa_id}/close")
def close_quality_capa(capa_id: int, payload: WorkflowTaskActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    """关闭 CAPA 并联动关闭关联的质量问题。"""
    capa = db.query(models.QualityCAPA).filter(models.QualityCAPA.id == capa_id).first()
    if not capa:
        raise HTTPException(status_code=404, detail="CAPA not found")
    if capa.status == "已关闭":
        raise HTTPException(status_code=409, detail="CAPA already closed")
    capa.status = "已关闭"
    capa.closed_at = today_text()
    capa.result = f"{capa.result}\n[关闭人：{payload.acted_by}，日期：{capa.closed_at}，备注：{payload.comment}]".strip()

    issue_closed = False
    if capa.issue_id:
        issue = db.query(models.QualityIssue).filter(models.QualityIssue.id == capa.issue_id).first()
        if issue and issue.status != "已关闭":
            issue.status = "已关闭"
            issue_closed = True
    db.commit()
    return {"ok": True, "issue_closed": issue_closed}


@router.get("/api/quality/reports")
def quality_reports(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.QualityReport)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.QualityReport.report_no.ilike(kw) | models.QualityReport.title.ilike(kw) | models.QualityReport.product_model.ilike(kw))
    total = q.count()
    rows = q.order_by(models.QualityReport.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": r.id, "report_no": r.report_no, "title": r.title, "report_type": r.report_type, "product_model": r.product_model, "issue_nos": r.issue_nos, "capa_nos": r.capa_nos, "summary": r.summary, "root_cause": r.root_cause, "corrective_action": r.corrective_action, "preventive_action": r.preventive_action, "owner": r.owner, "status": r.status, "archived_at": r.archived_at, "archived_by": r.archived_by}
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/quality/reports", status_code=201)
def create_quality_report(payload: QualityReportPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    if not payload.report_no:
        count = db.query(models.QualityReport).count() + 1
        payload.report_no = f"QR-{count:04d}"
    row = models.QualityReport(**payload.model_dump(), archived_at=today_text())
    db.add(row)
    commit_or_409(db, "Report number already exists")
    db.refresh(row)
    return {"id": row.id, "report_no": row.report_no}


@router.post("/api/quality/reports/archive-from-issues", status_code=201)
def archive_quality_report_from_issues(payload: QualityReportArchiveFromIssuePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    """从已关闭的质量问题+CAPA 批量生成质量归档报告。"""
    if not payload.issue_ids:
        raise HTTPException(status_code=409, detail="No issues selected")
    issues = db.query(models.QualityIssue).filter(models.QualityIssue.id.in_(payload.issue_ids)).all()
    if not issues:
        raise HTTPException(status_code=404, detail="Issues not found")
    not_closed = [i for i in issues if i.status != "已关闭"]
    if not_closed:
        raise HTTPException(status_code=409, detail=f"Cannot archive: issues {[i.issue_no for i in not_closed]} are not closed")

    issue_ids = [i.id for i in issues]
    capas = db.query(models.QualityCAPA).filter(models.QualityCAPA.issue_id.in_(issue_ids)).all()
    issue_nos = "、".join(i.issue_no for i in issues)
    capa_nos = "、".join(c.capa_no for c in capas)
    product_models = list({i.product_model for i in issues if i.product_model})
    product_model = "、".join(product_models)
    root_causes = "\n".join(f"[{i.issue_no}] {i.root_cause}" for i in issues if i.root_cause)
    corrective = "\n".join(f"[{i.issue_no}] {i.corrective_action}" for i in issues if i.corrective_action)
    preventive = "\n".join(f"[{c.capa_no}] {c.preventive_action}" for c in capas if c.preventive_action)
    summary = f"本报告归档 {len(issues)} 个质量问题、{len(capas)} 个 CAPA。"

    count = db.query(models.QualityReport).count() + 1
    report_no = f"QR-{count:04d}"
    title = payload.title or f"质量归档报告 {report_no}"
    report = models.QualityReport(
        report_no=report_no,
        title=title,
        report_type="质量问题归档",
        product_model=product_model,
        issue_nos=issue_nos,
        capa_nos=capa_nos,
        summary=summary,
        root_cause=root_causes,
        corrective_action=corrective,
        preventive_action=preventive,
        owner=payload.owner or (issues[0].owner if issues else ""),
        status="已归档",
        archived_at=today_text(),
        archived_by=payload.owner or "系统",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "report_no": report.report_no}


@router.put("/api/quality/reports/{report_id}")
def update_quality_report(report_id: int, payload: QualityReportUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityReport).filter(models.QualityReport.id == report_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/quality/reports/{report_id}")
def delete_quality_report(report_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("quality"))) -> dict:
    row = db.query(models.QualityReport).filter(models.QualityReport.id == report_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
