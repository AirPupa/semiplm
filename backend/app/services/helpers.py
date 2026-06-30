"""通用工具函数：提交、审计日志、用户字典、模型更新、日期、存在性校验。"""
from datetime import date

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models


def commit_or_409(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=message) from exc


def audit_log(db: Session, action: str, object_type: str, object_id: int | None, object_no: str, summary: str, operated_by: str) -> None:
    db.add(models.OperationLog(action=action, object_type=object_type, object_id=object_id, object_no=object_no, summary=summary, operated_by=operated_by, operated_at=today_text()))


def user_dict(user: models.User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role,
        "department": user.department,
        "avatar_url": user.avatar_url or "",
    }


def update_model(instance: object, payload: BaseModel) -> None:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, key, value)


def ensure_product_exists(db: Session, product_id: int) -> None:
    if not db.query(models.Product.id).filter(models.Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")


def ensure_project_exists(db: Session, project_id: int) -> None:
    if not db.query(models.Project.id).filter(models.Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")


def today_text() -> str:
    return date.today().isoformat()


def day_before(value: str) -> str:
    if not value:
        return today_text()
    try:
        return date.fromordinal(date.fromisoformat(value).toordinal() - 1).isoformat()
    except ValueError:
        return today_text()
