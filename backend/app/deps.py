"""权限与请求上下文公共依赖。

从 main.py 抽出，供所有 router 共享。包含权限标签常量、用户角色回退表、
权限拆分、当前用户上下文解析、权限校验依赖工厂。
"""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from . import models
from .database import get_db


PERMISSION_LABELS = {
    "all": "全部权限",
    "system": "系统设置",
    "organization": "组织管理",
    "user": "用户管理",
    "role": "角色权限",
    "workflow": "流程配置",
    "integration": "集成配置",
    "product": "产品主数据",
    "requirement": "需求规格",
    "material": "研发物料",
    "bom": "设计 BOM",
    "document": "文档管理",
    "process": "工艺路线",
    "change": "工程变更",
    "project": "项目管理",
    "quality": "质量闭环",
    "approval": "审批处理",
    "erp": "ERP 接口",
    "mes": "MES 接口",
}

USER_ROLE_FALLBACKS = {
    "admin": "ADMIN",
    "luofusen": "PE_ENGINEER",
    "yushuaibing": "PE_ENGINEER",
    "zhanghao": "PE_ENGINEER",
    "fanglei": "PM_MANAGER",
    "liangweiwei": "IT_ENGINEER",
}


def split_permissions(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]


def current_user_context(
    db: Session = Depends(get_db),
    username: str = Header("admin", alias="X-SemiPLM-User"),
) -> dict:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        user = db.query(models.User).filter(models.User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=401, detail="No active user")
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
    return {"user": user, "role": role, "permissions": permissions}


def has_permission(context: dict, required: str | list[str] | tuple[str, ...]) -> bool:
    permissions = set(context.get("permissions", []))
    if "all" in permissions:
        return True
    required_items = [required] if isinstance(required, str) else list(required)
    return any(item in permissions for item in required_items)


def require_permission(required: str | list[str] | tuple[str, ...]):
    def dependency(context: dict = Depends(current_user_context)) -> dict:
        if not has_permission(context, required):
            raise HTTPException(status_code=403, detail="Permission denied")
        return context

    return dependency


def hash_password(password: str) -> str:
    """SHA256 密码哈希。首次登录时用默认密码 123456 的哈希填充。"""
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()
