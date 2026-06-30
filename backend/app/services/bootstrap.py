"""启动引导：建表补列、确保 admin 账号存在。

仅在应用启动时执行，由 main.py 的 startup 事件调用。
不灌入任何业务/主数据——数据由 build_db.py 构建制品提供。
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import models


def ensure_lightweight_schema() -> None:
    """对已有表追加新列（SQLite ALTER TABLE ADD COLUMN）。"""
    columns = {
        "bom_headers": {
            "source_bom_id": "INTEGER",
            "effective_date": "VARCHAR(30) DEFAULT ''",
            "expiry_date": "VARCHAR(30) DEFAULT ''",
            "effectivity_type": "VARCHAR(30) DEFAULT '日期'",
            "effective_batch": "VARCHAR(80) DEFAULT ''",
        },
        "bom_items": {
            "process_step_id": "INTEGER",
            "effective_date": "VARCHAR(30) DEFAULT ''",
            "expiry_date": "VARCHAR(30) DEFAULT ''",
            "effectivity_note": "VARCHAR(160) DEFAULT ''",
        },
        "process_routes": {
            "release_date": "VARCHAR(30) DEFAULT ''",
            "source_route_id": "INTEGER",
            "effective_batch": "VARCHAR(80) DEFAULT ''",
        },
        "integration_jobs": {
            "attempt_count": "INTEGER DEFAULT 0",
            "last_sync_at": "VARCHAR(30) DEFAULT ''",
            "response_message": "TEXT DEFAULT ''",
            "external_id": "VARCHAR(120) DEFAULT ''",
        },
        "change_actions": {
            "target_type": "VARCHAR(40) DEFAULT ''",
            "target_id": "INTEGER",
            "target_version": "VARCHAR(30) DEFAULT ''",
            "effectivity_type": "VARCHAR(30) DEFAULT '日期'",
            "effectivity_scope": "VARCHAR(80) DEFAULT ''",
            "effective_date": "VARCHAR(30) DEFAULT ''",
            "effective_batch": "VARCHAR(80) DEFAULT ''",
            "generated_object_no": "VARCHAR(160) DEFAULT ''",
        },
        "operation_logs": {
            "object_id": "INTEGER",
        },
        "project_deliverables": {
            "object_type": "VARCHAR(40) DEFAULT ''",
            "object_id": "INTEGER",
        },
        "documents": {
            "file_name": "VARCHAR(255) DEFAULT ''",
            "file_path": "VARCHAR(500) DEFAULT ''",
            "file_size": "INTEGER",
            "file_type": "VARCHAR(100) DEFAULT ''",
        },
        "project_tasks": {
            "start_date": "VARCHAR(30) DEFAULT ''",
            "parent_id": "INTEGER",
            "depends_on": "VARCHAR(200) DEFAULT ''",
        },
        "materials": {
            "supplier_id": "INTEGER",
        },
        "substitute_materials": {
            "material_id": "INTEGER",
            "substitute_material_id": "INTEGER",
        },
        "users": {
            "avatar_url": "VARCHAR(500) DEFAULT ''",
            "password_hash": "VARCHAR(128) DEFAULT ''",
        },
        "changes": {
            "implementation_plan": "TEXT DEFAULT ''",
            "notification_list": "TEXT DEFAULT ''",
        },
        "projects": {
            "archived_at": "VARCHAR(30) DEFAULT ''",
            "archived_by": "VARCHAR(80) DEFAULT ''",
            "archive_summary": "TEXT DEFAULT ''",
        },
    }
    from ..database import engine
    with engine.begin() as conn:
        for table, table_columns in columns.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}
            for column, definition in table_columns.items():
                if column not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def ensure_admin(db: Session) -> None:
    """确保 admin 账号存在（upsert，单条）。首次部署空库时兜底。"""
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        db.add(models.User(username="admin", display_name="系统管理员", role="管理员", department="生产部"))
        db.commit()
