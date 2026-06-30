from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db


router = APIRouter()


@router.get("/api/audit-logs")
def audit_logs(page: int = 1, page_size: int = 20, keyword: str = "", object_type: str | None = None, action: str | None = None, db: Session = Depends(get_db)) -> dict:
    query = db.query(models.OperationLog)
    if object_type:
        query = query.filter(models.OperationLog.object_type == object_type)
    if action:
        query = query.filter(models.OperationLog.action == action)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(models.OperationLog.object_no.ilike(kw) | models.OperationLog.summary.ilike(kw) | models.OperationLog.operated_by.ilike(kw))
    total = query.count()
    rows = query.order_by(models.OperationLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": row.id, "action": row.action, "object_type": row.object_type, "object_id": row.object_id, "object_no": row.object_no, "summary": row.summary, "operated_by": row.operated_by, "operated_at": row.operated_at}
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
