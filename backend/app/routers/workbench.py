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


@router.get("/api/workbench")
def workbench(db: Session = Depends(get_db), context: dict = Depends(current_user_context)) -> dict:
    user = context["user"]
    user_display = user.display_name

    approvals = (
        db.query(models.Approval)
        .join(models.Change)
        .join(models.Product)
        .filter(models.Approval.status.in_(["处理中", "待处理", "流转中"]))
        .order_by(models.Approval.id)
        .limit(12)
        .all()
    )
    gate_rows = db.query(models.Product).order_by(models.Product.id.desc()).limit(8).all()

    my_changes = (
        db.query(models.Change)
        .join(models.Product)
        .filter(models.Change.owner == user_display)
        .order_by(models.Change.id.desc())
        .limit(10)
        .all()
    )

    my_projects = (
        db.query(models.Project)
        .filter(models.Project.owner == user_display)
        .order_by(models.Project.id.desc())
        .limit(10)
        .all()
    )

    my_tasks = (
        db.query(models.ProjectTask)
        .join(models.Project)
        .filter(models.ProjectTask.owner == user_display, models.ProjectTask.status != "已完成")
        .order_by(models.ProjectTask.due_date)
        .limit(10)
        .all()
    )

    my_quality_issues = (
        db.query(models.QualityIssue)
        .filter(models.QualityIssue.owner == user_display, models.QualityIssue.status != "已关闭")
        .order_by(models.QualityIssue.id.desc())
        .limit(10)
        .all()
    )

    recent_changes = (
        db.query(models.Change)
        .join(models.Product)
        .filter(models.Change.status.in_(["审批中", "执行中", "已关闭"]))
        .order_by(models.Change.id.desc())
        .limit(8)
        .all()
    )

    pending_workflow_tasks = (
        db.query(models.WorkflowTask)
        .join(models.WorkflowInstance)
        .filter(models.WorkflowTask.status == "待处理")
        .order_by(models.WorkflowTask.id.desc())
        .limit(8)
        .all()
    )

    return {
        "todo_approvals": [
            {
                "id": row.id,
                "change_no": row.change.change_no,
                "product_model": row.change.product.model,
                "step_name": row.step_name,
                "approver": row.approver,
                "status": row.status,
                "priority": row.change.priority,
                "submitted_at": row.change.submitted_at,
            }
            for row in approvals
        ],
        "stage_gates": [
            {
                "id": product.id,
                "model": product.model,
                "lifecycle": product.lifecycle,
                "owner": product.owner,
                "readiness": product.readiness,
                "next_gate": "量产发布" if product.readiness >= 80 else "资料齐套评审",
                "blocker": "可靠性报告/变更签核未闭环" if product.readiness < 80 else "客户承认书归档",
            }
            for product in gate_rows
        ],
        "my_changes": [
            {
                "id": c.id,
                "change_no": c.change_no,
                "title": c.title,
                "product_model": c.product.model,
                "status": c.status,
                "priority": c.priority,
                "submitted_at": c.submitted_at,
            }
            for c in my_changes
        ],
        "my_projects": [
            {
                "id": p.id,
                "project_no": p.project_no,
                "name": p.name,
                "product_model": p.product_model,
                "phase": p.phase,
                "progress": p.progress,
                "end_date": p.end_date,
                "risk_level": p.risk_level,
            }
            for p in my_projects
        ],
        "my_tasks": [
            {
                "id": t.id,
                "name": t.name,
                "phase": t.phase,
                "status": t.status,
                "due_date": t.due_date,
                "project_no": t.project.project_no if t.project else "",
            }
            for t in my_tasks
        ],
        "my_quality_issues": [
            {
                "id": i.id,
                "issue_no": i.issue_no,
                "title": i.title,
                "product_model": i.product_model,
                "severity": i.severity,
                "status": i.status,
            }
            for i in my_quality_issues
        ],
        "recent_changes": [
            {
                "id": c.id,
                "change_no": c.change_no,
                "title": c.title,
                "product_model": c.product.model,
                "status": c.status,
                "priority": c.priority,
                "submitted_at": c.submitted_at,
            }
            for c in recent_changes
        ],
        "pending_workflow_tasks": [
            {
                "id": t.id,
                "instance_id": t.instance_id,
                "node_name": t.node_name,
                "role_name": t.role_name,
                "status": t.status,
                "object_type": t.instance.object_type if t.instance else "",
                "object_no": t.instance.object_no if t.instance else "",
                "title": t.instance.title if t.instance else "",
            }
            for t in pending_workflow_tasks
        ],
    }


@router.get("/api/workbench/calendar")
def workbench_calendar(month: str, db: Session = Depends(get_db), context: dict = Depends(current_user_context)) -> dict:
    """工作台任务日历：聚合当前用户在该月内截止的项目任务/ECA动作/项目交付物"""
    user = context["user"]
    user_display = user.display_name
    # month 格式 YYYY-MM，构造当月起止
    try:
        year, mon = month.split("-")
        year_i, mon_i = int(year), int(mon)
        start = f"{year_i:04d}-{mon_i:02d}-01"
        if mon_i == 12:
            end = f"{year_i + 1:04d}-01-01"
        else:
            end = f"{year_i:04d}-{mon_i + 1:02d}-01"
    except Exception:
        raise HTTPException(status_code=400, detail="month must be YYYY-MM")

    items: list[dict] = []

    # 项目任务
    tasks = (
        db.query(models.ProjectTask, models.Project)
        .join(models.Project, models.ProjectTask.project_id == models.Project.id)
        .filter(
            models.ProjectTask.owner == user_display,
            models.ProjectTask.due_date >= start,
            models.ProjectTask.due_date < end,
        )
        .order_by(models.ProjectTask.due_date)
        .all()
    )
    for t, proj in tasks:
        items.append({
            "type": "项目任务",
            "no": t.name,
            "title": t.name,
            "owner": t.owner,
            "status": t.status,
            "due_date": t.due_date,
            "source_no": proj.project_no if proj else "",
            "source_name": proj.name if proj else "",
        })

    # ECA 动作
    actions = (
        db.query(models.ChangeAction)
        .filter(
            models.ChangeAction.owner == user_display,
            models.ChangeAction.due_date >= start,
            models.ChangeAction.due_date < end,
            models.ChangeAction.due_date != "",
        )
        .order_by(models.ChangeAction.due_date)
        .all()
    )
    for a in actions:
        change = db.query(models.Change).filter(models.Change.id == a.change_id).first()
        items.append({
            "type": "ECA动作",
            "no": a.action_no,
            "title": a.target_object or a.action_no,
            "owner": a.owner,
            "status": a.status,
            "due_date": a.due_date,
            "source_no": change.change_no if change else "",
            "source_name": change.title if change else "",
        })

    # 项目交付物
    deliverables = (
        db.query(models.ProjectDeliverable, models.Project)
        .join(models.Project, models.ProjectDeliverable.project_id == models.Project.id)
        .filter(
            models.ProjectDeliverable.owner == user_display,
            models.ProjectDeliverable.due_date >= start,
            models.ProjectDeliverable.due_date < end,
            models.ProjectDeliverable.due_date != "",
        )
        .order_by(models.ProjectDeliverable.due_date)
        .all()
    )
    for d, proj in deliverables:
        items.append({
            "type": "项目交付物",
            "no": d.name,
            "title": d.name,
            "owner": d.owner,
            "status": d.status,
            "due_date": d.due_date,
            "source_no": proj.project_no if proj else "",
            "source_name": proj.name if proj else "",
        })

    # 统计
    by_type = {}
    by_status = {}
    overdue = 0
    today_str = datetime.now().strftime("%Y-%m-%d")
    for it in items:
        by_type[it["type"]] = by_type.get(it["type"], 0) + 1
        by_status[it["status"]] = by_status.get(it["status"], 0) + 1
        if it["due_date"] < today_str and it["status"] not in ["已完成", "已关闭"]:
            overdue += 1

    return {
        "month": month,
        "items": items,
        "summary": {
            "total": len(items),
            "overdue": overdue,
            "by_type": [{"name": k, "value": v} for k, v in by_type.items()],
            "by_status": [{"name": k, "value": v} for k, v in by_status.items()],
        },
    }


@router.get("/api/workbench/notifications")
def workbench_notifications(action: str | None = None, limit: int = 50, db: Session = Depends(get_db)) -> dict:
    """工作台消息通知：基于操作日志聚合关键事件（发布/关闭/驳回/提交/删除/失败）"""
    # 关键动作白名单
    key_actions = ["发布", "关闭", "驳回", "提交", "删除", "新增", "编辑"]
    q = db.query(models.OperationLog).filter(models.OperationLog.action.in_(key_actions))
    if action:
        q = q.filter(models.OperationLog.action == action)
    rows = q.order_by(models.OperationLog.id.desc()).limit(min(limit, 200)).all()
    items = [
        {
            "id": row.id,
            "action": row.action,
            "object_type": row.object_type,
            "object_no": row.object_no,
            "summary": row.summary,
            "operated_by": row.operated_by,
            "operated_at": row.operated_at,
            "level": _notify_level(row.action),
        }
        for row in rows
    ]
    # 按动作统计
    by_action = {}
    for it in items:
        by_action[it["action"]] = by_action.get(it["action"], 0) + 1
    return {
        "items": items,
        "total": len(items),
        "by_action": [{"name": k, "value": v} for k, v in by_action.items()],
    }


def _notify_level(action: str) -> str:
    """通知级别：danger/warning/info/success"""
    if action in ["删除", "驳回"]:
        return "danger"
    if action in ["关闭", "发布"]:
        return "success"
    if action in ["提交"]:
        return "warning"
    return "info"


@router.get("/api/workbench/closure-check")
def workbench_closure_check(db: Session = Depends(get_db)) -> dict:
    """业务闭环验证：按产品检查 9 个环节的数据完整性，定位断点"""
    products = db.query(models.Product).order_by(models.Product.id).all()
    # 环节定义：(key, label)
    stages = [
        ("requirement", "需求规格"),
        ("product_version", "产品版本"),
        ("bom", "BOM"),
        ("process_route", "工艺路线"),
        ("document", "文档"),
        ("change", "工程变更"),
        ("project", "项目"),
        ("quality", "质量追溯"),
        ("integration", "下游同步"),
    ]

    product_rows = []
    full_closed = 0
    total_breakpoints = 0

    for p in products:
        req_count = db.query(models.Requirement).filter(models.Requirement.product_id == p.id).count()
        version_count = db.query(models.ProductVersion).filter(models.ProductVersion.product_id == p.id).count()
        bom_count = 0
        if p.bom_name:
            bom_count = db.query(models.BomHeader).filter(
                models.BomHeader.bom_name == p.bom_name,
                models.BomHeader.bom_version == p.bom_version,
            ).count()
        route_count = 0
        if p.process_flow_name:
            route_count = db.query(models.ProcessFlow).filter(
                models.ProcessFlow.process_flow_name == p.process_flow_name,
                models.ProcessFlow.process_flow_version == p.process_flow_version,
            ).count()
        doc_count = db.query(models.Document).filter(models.Document.product_id == p.id).count()
        change_count = db.query(models.Change).filter(models.Change.product_id == p.id).count()
        # 项目通过 product_model 关联
        project_count = db.query(models.Project).filter(models.Project.product_model == p.product_def_name).count()
        quality_count = db.query(models.QualityLot).filter(models.QualityLot.product_id == p.id).count()
        # 集成：该产品相关对象产生的集成任务
        integration_count = db.query(models.IntegrationJob).filter(models.IntegrationJob.product_model == p.product_def_name).count()

        counts = {
            "requirement": req_count,
            "product_version": version_count,
            "bom": bom_count,
            "process_route": route_count,
            "document": doc_count,
            "change": change_count,
            "project": project_count,
            "quality": quality_count,
            "integration": integration_count,
        }
        # 状态：有数据=ok，无数据=gap，有数据但发布率低=warn
        stage_status = {}
        breakpoints = 0
        for key, _label in stages:
            cnt = counts[key]
            if cnt > 0:
                stage_status[key] = "ok"
            else:
                stage_status[key] = "gap"
                breakpoints += 1

        if breakpoints == 0:
            full_closed += 1
        total_breakpoints += breakpoints

        product_rows.append({
            "id": p.id,
            "model": p.model,
            "name": p.name,
            "lifecycle": p.lifecycle,
            "owner": p.owner,
            "readiness": p.readiness,
            "counts": counts,
            "stage_status": stage_status,
            "breakpoints": breakpoints,
            "closed": breakpoints == 0,
        })

    # 环节维度的覆盖率
    stage_coverage = []
    for key, label in stages:
        ok_count = sum(1 for r in product_rows if r["stage_status"][key] == "ok")
        stage_coverage.append({
            "key": key,
            "label": label,
            "ok_count": ok_count,
            "total": len(products),
            "rate": round((ok_count / len(products)) * 100) if products else 0,
        })

    return {
        "summary": {
            "product_total": len(products),
            "full_closed": full_closed,
            "closure_rate": round((full_closed / len(products)) * 100) if products else 0,
            "total_breakpoints": total_breakpoints,
        },
        "stages": [{"key": k, "label": l} for k, l in stages],
        "stage_coverage": stage_coverage,
        "products": product_rows,
    }
