from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import (
    PERMISSION_LABELS,
    USER_ROLE_FALLBACKS,
    current_user_context,
    hash_password,
    split_permissions,
)
from ..schemas import LoginPayload, ProfileUpdatePayload
from ..services.helpers import audit_log, user_dict


router = APIRouter()


@router.post("/api/session/login")
def session_login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict:
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="账号不存在")
    if not user.password_hash:
        user.password_hash = hash_password("123456")
        db.commit()
    if user.password_hash != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="密码错误")
    role = db.query(models.Role).filter(models.Role.name == user.role, models.Role.status == "启用").first()
    if not role:
        fallback_code = USER_ROLE_FALLBACKS.get(user.username)
        if fallback_code:
            role = db.query(models.Role).filter(models.Role.code == fallback_code, models.Role.status == "启用").first()
    if not role:
        role_keyword = user.role.replace("整合", "")
        role = (
            db.query(models.Role)
            .filter(models.Role.name.like(f"%{role_keyword}%"), models.Role.status == "启用")
            .first()
        )
    permissions = split_permissions(role.permissions if role else "")
    return {
        "user": user_dict(user),
        "role": {
            "id": role.id if role else None,
            "code": role.code if role else "",
            "name": role.name if role else user.role,
            "description": role.description if role else "",
            "status": role.status if role else "未配置",
        },
        "permissions": permissions,
    }


@router.get("/api/session/current")
def session_current(context: dict = Depends(current_user_context)) -> dict:
    user = context["user"]
    role = context["role"]
    permissions = context["permissions"]
    return {
        "user": user_dict(user),
        "role": {
            "id": role.id if role else None,
            "code": role.code if role else "",
            "name": role.name if role else user.role,
            "description": role.description if role else "",
            "status": role.status if role else "未配置",
        },
        "permissions": permissions,
        "permission_labels": {key: PERMISSION_LABELS.get(key, key) for key in permissions},
    }


@router.get("/api/session/login-users")
def login_users(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.User).order_by(models.User.id).all()
    return [user_dict(row) for row in rows]


@router.put("/api/session/profile")
def update_current_profile(
    payload: ProfileUpdatePayload,
    db: Session = Depends(get_db),
    context: dict = Depends(current_user_context),
) -> dict:
    user = context["user"]
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url
    audit_log(db, "更新个人资料", "User", user.id, user.username, "更新个人头像/姓名", user.display_name)
    db.commit()
    db.refresh(user)
    return user_dict(user)
