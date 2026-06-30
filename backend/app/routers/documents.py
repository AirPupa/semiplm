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
    trigger_document_distribution_on_publish,
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


@router.get("/api/documents")
def documents(page: int = 1, page_size: int = 20, keyword: str = "", sort_by: str = "", sort_order: str = "desc", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Document).options(selectinload(models.Document.product))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Document.doc_no.ilike(kw) | models.Document.title.ilike(kw) | models.Document.category.ilike(kw))
    total = q.count()
    # 服务端排序：支持 version/status/approval_status/updated_at/doc_no，默认 id desc（新增在最前）
    sort_column_map = {
        "version": models.Document.version,
        "status": models.Document.status,
        "approval_status": models.Document.approval_status,
        "updated_at": models.Document.updated_at,
        "doc_no": models.Document.doc_no,
    }
    if sort_by in sort_column_map and sort_order in ("asc", "desc"):
        col = sort_column_map[sort_by]
        q = q.order_by(col.asc() if sort_order == "asc" else col.desc())
    else:
        q = q.order_by(models.Document.id.desc())
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": row.id, "doc_no": row.doc_no, "title": row.title, "category": row.category, "version": row.version, "status": row.status, "approval_status": row.approval_status, "owner": row.owner, "updated_at": row.updated_at, "product_model": row.product.model, "product_id": row.product_id, "file_name": row.file_name, "file_size": row.file_size, "file_type": row.file_type}
            for row in rows
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/api/documents", status_code=201)
def create_document(payload: DocumentPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    ensure_product_exists(db, payload.product_id)
    document = models.Document(**payload.model_dump())
    db.add(document)
    commit_or_409(db, "Document number already exists")
    db.refresh(document)
    return {
        "id": document.id,
        "doc_no": document.doc_no,
        "title": document.title,
        "category": document.category,
        "version": document.version,
        "status": document.status,
        "approval_status": document.approval_status,
        "owner": document.owner,
        "updated_at": document.updated_at,
        "product_model": document.product.model,
        "product_id": document.product_id,
        "file_name": document.file_name,
        "file_size": document.file_size,
        "file_type": document.file_type,
    }


@router.put("/api/documents/{document_id}")
def update_document(document_id: int, payload: DocumentUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail=f"Document in {document.status} status cannot be edited")
    if payload.product_id is not None:
        ensure_product_exists(db, payload.product_id)
    update_model(document, payload)
    commit_or_409(db, "Document number already exists")
    db.refresh(document)
    return {
        "id": document.id,
        "doc_no": document.doc_no,
        "title": document.title,
        "category": document.category,
        "version": document.version,
        "status": document.status,
        "approval_status": document.approval_status,
        "owner": document.owner,
        "updated_at": document.updated_at,
        "product_model": document.product.model,
        "product_id": document.product_id,
        "file_name": document.file_name,
        "file_size": document.file_size,
        "file_type": document.file_type,
    }


@router.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status == "已发布":
        raise HTTPException(status_code=409, detail="Released document cannot be deleted")
    if document.status == "审批中":
        raise HTTPException(status_code=409, detail="Document in review cannot be deleted")
    db.delete(document)
    db.commit()
    return {"deleted": True}


@router.get("/api/documents/{document_id}/relations")
def document_relations(document_id: int, db: Session = Depends(get_db)) -> dict:
    """文档与对象关联聚合：通过 document.product_id 反查产品，再聚合 BOM/工艺路线/项目/工程变更。
    用于文档详情页「关联对象」面板，一次请求拿到全部关联对象。"""
    document = (
        db.query(models.Document)
        .options(selectinload(models.Document.product))
        .filter(models.Document.id == document_id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    product_id = document.product_id
    product_model = document.product.model if document.product else ""

    # BOM：同产品下的所有 BOM
    boms: list[dict] = []
    if product_id:
        rows = (
            db.query(models.BomHeader)
            .options(selectinload(models.BomHeader.product))
            .filter(models.BomHeader.product_id == product_id)
            .order_by(models.BomHeader.bom_type, models.BomHeader.version)
            .all()
        )
        for r in rows:
            boms.append({
                "id": r.id, "bom_type": r.bom_type, "version": r.version,
                "status": r.status, "owner": r.owner, "release_date": r.release_date,
                "effective_date": r.effective_date, "is_current": is_current_effective_bom(r),
            })

    # 工艺路线：同产品下的所有工艺路线
    process_routes: list[dict] = []
    if product_id:
        rows = (
            db.query(models.ProcessRoute)
            .filter(models.ProcessRoute.product_id == product_id)
            .order_by(models.ProcessRoute.version)
            .all()
        )
        for r in rows:
            process_routes.append({
                "id": r.id, "route_no": r.route_no, "name": r.name,
                "version": r.version, "status": r.status, "owner": r.owner,
                "release_date": r.release_date,
            })

    # 项目：通过 product_model 关联
    projects: list[dict] = []
    if product_model:
        rows = (
            db.query(models.Project)
            .filter(models.Project.product_model == product_model)
            .order_by(models.Project.id.desc())
            .all()
        )
        for r in rows:
            projects.append({
                "id": r.id, "project_no": r.project_no, "name": r.name,
                "phase": r.phase, "progress": r.progress, "owner": r.owner,
                "is_archived": bool(r.archived_at),
            })

    # 工程变更：同产品下的所有变更
    changes: list[dict] = []
    if product_id:
        rows = (
            db.query(models.Change)
            .filter(models.Change.product_id == product_id)
            .order_by(models.Change.id.desc())
            .all()
        )
        for r in rows:
            changes.append({
                "id": r.id, "change_no": r.change_no, "title": r.title,
                "change_type": r.change_type, "status": r.status, "priority": r.priority,
                "owner": r.owner, "submitted_at": r.submitted_at,
            })

    # 同产品的其他文档（同源文档，便于切换版本/类别参考）
    related_documents: list[dict] = []
    if product_id:
        rows = (
            db.query(models.Document)
            .filter(models.Document.product_id == product_id, models.Document.id != document.id)
            .order_by(models.Document.category, models.Document.doc_no)
            .all()
        )
        for r in rows:
            related_documents.append({
                "id": r.id, "doc_no": r.doc_no, "title": r.title, "category": r.category,
                "version": r.version, "status": r.status, "owner": r.owner,
            })

    return {
        "document_id": document.id,
        "doc_no": document.doc_no,
        "title": document.title,
        "product_id": product_id,
        "product_model": product_model,
        "product_name": document.product.name if document.product else "",
        "product_lifecycle": document.product.lifecycle if document.product else "",
        "counts": {
            "boms": len(boms),
            "process_routes": len(process_routes),
            "projects": len(projects),
            "changes": len(changes),
            "related_documents": len(related_documents),
        },
        "boms": boms,
        "process_routes": process_routes,
        "projects": projects,
        "changes": changes,
        "related_documents": related_documents,
    }


@router.post("/api/documents/{document_id}/submit")
def submit_document(document_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status == "已发布":
        raise HTTPException(status_code=409, detail="Released document cannot be submitted")
    if document.status == "审批中":
        raise HTTPException(status_code=409, detail="Document is already in review")
    # ECA 生成对象校验：检查文档是否由 ECA 动作生成
    validate_eca_generated_object_ready(db, "文档", document.id, document.doc_no)
    document.status = "审批中"
    document.approval_status = "流转中"
    document.updated_at = today_text()
    instance = start_workflow(
        db,
        template_code="WF-DOC-STD",
        object_type="文档",
        object_id=document.id,
        object_no=document.doc_no,
        title=document.title,
        product_model=document.product.model,
        started_by=document.owner,
    )
    db.commit()
    return {"id": document.id, "status": document.status, "approval_status": document.approval_status, "workflow_id": instance.id}


@router.post("/api/documents/{document_id}/approve")
def approve_document(document_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission(["approval", "document"]))) -> dict:
    document = db.query(models.Document).options(selectinload(models.Document.product)).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status not in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail="Document must be submitted for review before approval")
    validate_eca_generated_object_ready(db, "文档", document.id, document.doc_no)
    document.status = "已发布"
    document.approval_status = "已签核"
    document.updated_at = today_text()
    create_integration_job(
        db,
        target_system="QMS",
        object_type="文档",
        object_no=document.doc_no,
        product_model=document.product.model,
        triggered_by=document.doc_no,
        message="文档已签核发布，等待同步 QMS/文控归档。",
    )
    # ECO 联动：若文档由 ECA 变更动作生成，按变更通知单接收人列表自动发放
    distributed_recipients = trigger_document_distribution_on_publish(db, document)
    db.commit()
    result = {"id": document.id, "status": document.status, "approval_status": document.approval_status, "updated_at": document.updated_at}
    if distributed_recipients:
        result["auto_distributed_to"] = distributed_recipients
        result["auto_distribution_count"] = len(distributed_recipients)
    return result


FILE_UPLOAD_DIR = os.path.join(os.getcwd(), "data", "files")


@router.post("/api/documents/{document_id}/upload")
async def upload_document_file(document_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status == "已发布":
        raise HTTPException(status_code=409, detail="Released document cannot be modified")
    if document.status == "审批中":
        raise HTTPException(status_code=409, detail="Document in review cannot be modified")
    os.makedirs(FILE_UPLOAD_DIR, exist_ok=True)
    file_content = await file.read()
    file_size = len(file_content)
    safe_name = f"{document_id}_{file.filename}"
    file_path = os.path.join(FILE_UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_content)
    document.file_name = file.filename
    document.file_path = safe_name  # 只存文件名，运行时拼接绝对路径，保证 Windows/Linux 可移植
    document.file_size = file_size
    document.file_type = file.content_type or ""
    document.updated_at = today_text()
    db.commit()
    return {"id": document.id, "file_name": document.file_name, "file_size": document.file_size, "file_type": document.file_type}


@router.get("/api/documents/{document_id}/download")
def download_document_file(document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    abs_path = os.path.join(FILE_UPLOAD_DIR, os.path.basename(document.file_path)) if document.file_path else ""
    if not abs_path or not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(abs_path, "rb") as f:
        content = f.read()
    return Response(
        content=content,
        media_type=document.file_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{document.file_name}"'},
    )


PREVIEWABLE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}
PREVIEWABLE_MIME_PREFIXES = ("application/pdf", "image/")


@router.get("/api/documents/{document_id}/preview")
def preview_document_file(document_id: int, db: Session = Depends(get_db)):
    """Return file content inline for browser preview. Supports PDF and images only."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    abs_path = os.path.join(FILE_UPLOAD_DIR, os.path.basename(document.file_path)) if document.file_path else ""
    if not abs_path or not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    # Determine if file is previewable
    file_ext = os.path.splitext(document.file_name or document.file_path)[1].lower()
    file_mime = document.file_type or ""
    is_previewable = file_ext in PREVIEWABLE_EXTENSIONS or any(file_mime.startswith(p) for p in PREVIEWABLE_MIME_PREFIXES)
    if not is_previewable:
        raise HTTPException(status_code=415, detail=f"File type {file_ext or file_mime} is not previewable. Only PDF and images are supported.")
    with open(abs_path, "rb") as f:
        content = f.read()
    # Use inline disposition so browser renders instead of downloading
    return Response(
        content=content,
        media_type=file_mime or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{document.file_name}"',
            "Cache-Control": "no-cache",
        },
    )
@router.get("/api/documents/{document_id}/distributions")
def list_document_distributions(document_id: int, db: Session = Depends(get_db)) -> dict:
    """List all distribution records for a document."""
    rows = db.query(models.DocumentDistribution).filter(
        models.DocumentDistribution.document_id == document_id
    ).order_by(models.DocumentDistribution.id.desc()).all()
    return {
        "items": [
            {
                "id": r.id,
                "document_id": r.document_id,
                "doc_no": r.doc_no,
                "title": r.title,
                "version": r.version,
                "recipient_type": r.recipient_type,
                "recipient": r.recipient,
                "status": r.status,
                "distributed_by": r.distributed_by,
                "distributed_at": r.distributed_at,
                "recalled_by": r.recalled_by,
                "recalled_at": r.recalled_at,
                "recall_reason": r.recall_reason,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/api/documents/{document_id}/distribute", status_code=201)
def distribute_document(document_id: int, payload: DocumentDistributionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    """Distribute a published document to specified recipients."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status != "已发布":
        raise HTTPException(status_code=409, detail="Only published documents can be distributed")
    if not payload.recipient:
        raise HTTPException(status_code=400, detail="Recipient is required")
    # Support multiple recipients separated by comma
    recipients = [r.strip() for r in payload.recipient.split(",") if r.strip()]
    created = []
    for recipient in recipients:
        # Check if already distributed to this recipient and still active
        existing = db.query(models.DocumentDistribution).filter(
            models.DocumentDistribution.document_id == document_id,
            models.DocumentDistribution.recipient == recipient,
            models.DocumentDistribution.status == "已发放",
        ).first()
        if existing:
            continue  # Skip duplicate active distribution
        dist = models.DocumentDistribution(
            document_id=document_id,
            doc_no=document.doc_no,
            title=document.title,
            version=document.version,
            recipient_type=payload.recipient_type,
            recipient=recipient,
            status="已发放",
            distributed_by=payload.distributed_by or "系统",
            distributed_at=today_text(),
        )
        db.add(dist)
        created.append(recipient)
    db.commit()
    return {"distributed_to": created, "count": len(created), "document_id": document_id}


@router.post("/api/document-distributions/{dist_id}/recall")
def recall_distribution(dist_id: int, payload: DocumentDistributionRecallPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("document"))) -> dict:
    """Recall a distributed document."""
    dist = db.query(models.DocumentDistribution).filter(models.DocumentDistribution.id == dist_id).first()
    if not dist:
        raise HTTPException(status_code=404, detail="Distribution record not found")
    if dist.status == "已回收":
        raise HTTPException(status_code=409, detail="Distribution already recalled")
    dist.status = "已回收"
    dist.recalled_by = payload.recalled_by or "系统"
    dist.recalled_at = today_text()
    dist.recall_reason = payload.recall_reason
    db.commit()
    return {"id": dist.id, "status": dist.status, "recalled_at": dist.recalled_at}

@router.get("/api/documents/{document_id}/version-history")
def document_version_history(document_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """追溯文档版本链路：同一产品同标题的版本序列及关联变更。"""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    siblings = (
        db.query(models.Document)
        .filter(
            models.Document.product_id == doc.product_id,
            models.Document.title == doc.title,
            models.Document.category == doc.category,
        )
        .order_by(models.Document.id)
        .all()
    )

    history = []
    for item in siblings:
        eca_action = (
            db.query(models.ChangeAction)
            .filter(
                models.ChangeAction.target_type == "文档",
                models.ChangeAction.generated_object_no == item.doc_no,
            )
            .first()
        )
        change_no = ""
        change_status = ""
        action_no = ""
        effectivity_type = ""
        effective_batch = ""
        effective_date = ""
        source_version = ""
        release_gate = ""
        gate_message = ""
        if eca_action:
            change = db.query(models.Change).filter(models.Change.id == eca_action.change_id).first()
            change_no = change.change_no if change else ""
            change_status = change.status if change else ""
            action_no = eca_action.action_no
            effectivity_type = eca_action.effectivity_type
            effective_batch = eca_action.effective_batch
            effective_date = eca_action.effective_date
            source_version = eca_action.target_version
            gate = get_eca_generated_object_gate(db, "文档", item.doc_no)
            if gate:
                release_gate = "可提交" if gate["ready"] else "待变更闭环"
                gate_message = gate["message"]

        history.append({
            "id": item.id,
            "doc_no": item.doc_no,
            "version": item.version,
            "status": item.status,
            "category": item.category,
            "owner": item.owner,
            "approval_status": item.approval_status,
            "updated_at": item.updated_at,
            "source_version": source_version,
            "is_current": item.id == doc.id,
            "change_no": change_no,
            "change_status": change_status,
            "eca_action_no": action_no,
            "eca_effectivity_type": effectivity_type,
            "eca_effective_batch": effective_batch,
            "eca_effective_date": effective_date,
            "release_gate_status": release_gate,
            "release_gate_message": gate_message,
        })
    return history

@router.get("/api/attachments")
def list_attachments(object_type: str = "", object_id: int = 0, db: Session = Depends(get_db), context: dict = Depends(current_user_context)) -> list[dict]:
    if not object_type:
        raise HTTPException(status_code=400, detail="object_type is required")
    _require_attachment_permission(object_type, context)
    q = db.query(models.Attachment)
    q = q.filter(models.Attachment.object_type == object_type)
    if object_id:
        q = q.filter(models.Attachment.object_id == object_id)
    rows = q.order_by(models.Attachment.id.desc()).all()
    return [_attachment_dict(r) for r in rows]


@router.post("/api/attachments/upload", status_code=201)
async def upload_attachment(object_type: str = Form(...), object_id: int = Form(...), description: str = Form(""), file: UploadFile = File(...), db: Session = Depends(get_db), context: dict = Depends(current_user_context)):
    from datetime import datetime
    from uuid import uuid4

    _require_attachment_permission(object_type, context)
    user_name = context["user"].display_name
    os.makedirs(FILE_UPLOAD_DIR, exist_ok=True)
    original_name = os.path.basename(file.filename or "attachment")
    safe_name = f"{object_type}_{object_id}_{uuid4().hex}_{original_name}"
    file_path = os.path.join(FILE_UPLOAD_DIR, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    att = models.Attachment(
        object_type=object_type,
        object_id=object_id,
        file_name=original_name,
        file_path=safe_name,  # 只存文件名，运行时拼接绝对路径
        file_size=len(content),
        file_type=file.content_type or "",
        description=description,
        uploaded_by=user_name,
        uploaded_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    db.add(att)
    audit_log(db, "附件上传", object_type, object_id, f"{object_type}#{object_id}", f"上传附件 {original_name}", user_name)
    db.commit()
    db.refresh(att)
    return _attachment_dict(att)


@router.get("/api/attachments/{attachment_id}/download")
def download_attachment(attachment_id: int, db: Session = Depends(get_db), context: dict = Depends(current_user_context)):
    att = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    _require_attachment_permission(att.object_type, context)
    abs_path = os.path.join(FILE_UPLOAD_DIR, os.path.basename(att.file_path)) if att.file_path else ""
    if not abs_path or not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    with open(abs_path, "rb") as f:
        content = f.read()
    audit_log(db, "附件下载", att.object_type, att.object_id, f"{att.object_type}#{att.object_id}", f"下载附件 {att.file_name}", context["user"].display_name)
    db.commit()
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{att.file_name}"'},
    )


@router.delete("/api/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, db: Session = Depends(get_db), context: dict = Depends(current_user_context)):
    att = db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attachment not found")
    _require_attachment_permission(att.object_type, context)
    object_type = att.object_type
    object_id = att.object_id
    file_name = att.file_name
    abs_path = os.path.join(FILE_UPLOAD_DIR, os.path.basename(att.file_path)) if att.file_path else ""
    if abs_path and os.path.exists(abs_path):
        os.remove(abs_path)
    db.delete(att)
    audit_log(db, "附件删除", object_type, object_id, f"{object_type}#{object_id}", f"删除附件 {file_name}", context["user"].display_name)
    db.commit()
    return {"ok": True}


def _attachment_dict(r: models.Attachment) -> dict:
    return {
        "id": r.id,
        "object_type": r.object_type,
        "object_id": r.object_id,
        "file_name": r.file_name,
        "file_size": r.file_size,
        "file_type": r.file_type,
        "description": r.description,
        "uploaded_by": r.uploaded_by,
        "uploaded_at": r.uploaded_at,
    }
