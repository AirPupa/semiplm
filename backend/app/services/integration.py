"""集成队列创建：业务对象发布后写入 ERP/MES/QMS 同步任务。"""
from sqlalchemy.orm import Session

from .. import models
from .helpers import today_text


def create_integration_job(
    db: Session,
    target_system: str,
    object_type: str,
    object_no: str,
    product_model: str,
    triggered_by: str,
    message: str,
) -> None:
    count = db.query(models.IntegrationJob).count() + 1
    db.add(models.IntegrationJob(
        job_no=f"INT-{today_text().replace('-', '')}-{count:04d}",
        target_system=target_system,
        object_type=object_type,
        object_no=object_no,
        product_model=product_model,
        direction="下发",
        status="等待",
        triggered_by=triggered_by,
        triggered_at=today_text(),
        message=message,
    ))
    db.flush()
