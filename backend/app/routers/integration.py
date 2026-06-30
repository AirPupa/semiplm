from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import require_permission
from ..schemas import IntegrationJobActionPayload
from ..serializers import serialize_integration_job
from ..services.helpers import today_text


router = APIRouter()


@router.get("/api/integration-jobs")
def integration_jobs(
    status: str = "",
    target_system: str = "",
    object_type: str = "",
    keyword: str = "",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(models.IntegrationJob)
    if status:
        query = query.filter(models.IntegrationJob.status == status)
    if target_system:
        query = query.filter(models.IntegrationJob.target_system == target_system)
    if object_type:
        query = query.filter(models.IntegrationJob.object_type == object_type)
    if keyword:
        like_value = f"%{keyword}%"
        query = query.filter(
            (models.IntegrationJob.object_no.like(like_value))
            | (models.IntegrationJob.product_model.like(like_value))
            | (models.IntegrationJob.job_no.like(like_value))
        )
    total = query.count()
    rows = query.order_by(models.IntegrationJob.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_integration_job(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/api/integration-jobs/summary")
def integration_jobs_summary(db: Session = Depends(get_db)) -> dict:
    rows = db.query(models.IntegrationJob.status, func.count(models.IntegrationJob.id)).group_by(models.IntegrationJob.status).all()
    status_counts = {status: count for status, count in rows}
    target_rows = db.query(models.IntegrationJob.target_system, func.count(models.IntegrationJob.id)).group_by(models.IntegrationJob.target_system).all()
    return {
        "total": sum(status_counts.values()),
        "waiting": status_counts.get("等待", 0),
        "processing": status_counts.get("处理中", 0),
        "failed": status_counts.get("失败", 0),
        "success": status_counts.get("成功", 0),
        "target_systems": [{"target_system": target, "count": count} for target, count in target_rows],
    }


@router.post("/api/integration-jobs/{job_id}/start")
def start_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    if job.status == "成功":
        raise HTTPException(status_code=409, detail="Successful integration job cannot be restarted")
    job.status = "处理中"
    job.attempt_count += 1
    job.last_sync_at = today_text()
    job.response_message = payload.response_message or f"{payload.acted_by} 已开始同步"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)


@router.post("/api/integration-jobs/{job_id}/success")
def complete_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    job.status = "成功"
    job.last_sync_at = today_text()
    job.external_id = payload.external_id or job.external_id
    job.response_message = payload.response_message or "下游系统已确认接收"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)


@router.post("/api/integration-jobs/{job_id}/fail")
def fail_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    job.status = "失败"
    job.last_sync_at = today_text()
    job.response_message = payload.response_message or "下游系统返回失败"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)


@router.post("/api/integration-jobs/{job_id}/retry")
def retry_integration_job(job_id: int, payload: IntegrationJobActionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    job = db.query(models.IntegrationJob).filter(models.IntegrationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Integration job not found")
    if job.status == "成功":
        raise HTTPException(status_code=409, detail="Successful integration job cannot be retried")
    job.status = "等待"
    job.response_message = payload.response_message or f"{payload.acted_by} 已加入重试队列"
    db.commit()
    db.refresh(job)
    return serialize_integration_job(job)
