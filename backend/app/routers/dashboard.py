from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db


router = APIRouter()


@router.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    product_count = db.query(models.Product).count()
    active_projects = db.query(models.Project).filter(models.Project.phase != "量产导入").count()
    pending_changes = db.query(models.Change).filter(models.Change.status.in_(["审批中", "执行中"])).count()
    docs = db.query(models.Document).count()
    signed_docs = db.query(models.Document).filter(models.Document.approval_status == "已签核").count()
    bom_total = db.query(models.BomHeader).count()
    bom_ready = db.query(models.BomHeader).filter(models.BomHeader.bom_state == "Active").count()

    lifecycle_rows = db.query(models.Product.product_def_state, func.count(models.Product.id)).group_by(models.Product.product_def_state).all()
    changes_rows = db.query(models.Change.change_type, func.count(models.Change.id)).group_by(models.Change.change_type).all()
    quality_rows = db.query(models.QualityLot.tested_at, func.avg(models.QualityLot.cp_yield), func.avg(models.QualityLot.ft_yield)).group_by(models.QualityLot.tested_at).order_by(models.QualityLot.tested_at).all()

    # 新增聚合指标
    integration_pending = db.query(models.IntegrationJob).filter(models.IntegrationJob.status.in_(["待处理", "处理中", "失败"])).count()
    integration_failed = db.query(models.IntegrationJob).filter(models.IntegrationJob.status == "失败").count()
    quality_open_issues = db.query(models.QualityIssue).filter(models.QualityIssue.status != "已关闭").count()
    capa_open = db.query(models.QualityCAPA).filter(models.QualityCAPA.status != "已关闭").count()
    deliverable_pending = db.query(models.ProjectDeliverable).filter(models.ProjectDeliverable.status.notin_(["已完成", "已关闭"])).count()
    recent_reports = db.query(models.QualityReport).count()

    project_rows = db.query(models.Project.phase, func.count(models.Project.id)).group_by(models.Project.phase).all()
    integration_status_rows = db.query(models.IntegrationJob.status, func.count(models.IntegrationJob.id)).group_by(models.IntegrationJob.status).all()
    change_status_rows = db.query(models.Change.status, func.count(models.Change.id)).group_by(models.Change.status).all()

    return {
        "metrics": {
            "products": product_count,
            "active_projects": active_projects,
            "pending_changes": pending_changes,
            "document_readiness": round((signed_docs / docs) * 100) if docs else 0,
            "bom_readiness": round((bom_ready / bom_total) * 100) if bom_total else 0,
            "integration_pending": integration_pending,
            "integration_failed": integration_failed,
            "quality_open_issues": quality_open_issues,
            "capa_open": capa_open,
            "deliverable_pending": deliverable_pending,
            "quality_reports": recent_reports,
        },
        "lifecycle": [{"name": name, "value": value} for name, value in lifecycle_rows],
        "changes": [{"name": name, "value": value} for name, value in changes_rows],
        "quality_trend": [{"date": date, "cp": round(cp or 0, 1), "ft": round(ft or 0, 1)} for date, cp, ft in quality_rows],
        "project_phases": [{"name": name, "value": value} for name, value in project_rows],
        "integration_status": [{"name": name, "value": value} for name, value in integration_status_rows],
        "change_status": [{"name": name, "value": value} for name, value in change_status_rows],
        "recent_tasks": [
            {
                "name": task.name,
                "phase": task.phase,
                "owner": task.owner,
                "status": task.status,
                "due_date": task.due_date,
            }
            for task in db.query(models.ProjectTask).order_by(models.ProjectTask.due_date).limit(6)
        ],
    }
