from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import require_permission
from ..schemas import RequirementPayload, RequirementUpdatePayload
from ..services.helpers import commit_or_409, ensure_product_exists, update_model


router = APIRouter()


@router.get("/api/requirements")
def requirements(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Requirement).options(selectinload(models.Requirement.product))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Requirement.req_no.ilike(kw) | models.Requirement.title.ilike(kw) | models.Requirement.category.ilike(kw))
    total = q.count()
    rows = q.order_by(models.Requirement.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": row.id, "req_no": row.req_no, "source": row.source, "category": row.category, "title": row.title, "priority": row.priority, "status": row.status, "owner": row.owner, "acceptance_criteria": row.acceptance_criteria, "product_model": row.product.model, "product_id": row.product_id}
            for row in rows
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/api/requirements", status_code=201)
def create_requirement(payload: RequirementPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("requirement"))) -> dict:
    ensure_product_exists(db, payload.product_id)
    requirement = models.Requirement(**payload.model_dump())
    db.add(requirement)
    commit_or_409(db, "Requirement number already exists")
    db.refresh(requirement)
    return {
        "id": requirement.id,
        "req_no": requirement.req_no,
        "source": requirement.source,
        "category": requirement.category,
        "title": requirement.title,
        "priority": requirement.priority,
        "status": requirement.status,
        "owner": requirement.owner,
        "acceptance_criteria": requirement.acceptance_criteria,
        "product_model": requirement.product.model,
        "product_id": requirement.product_id,
    }


@router.put("/api/requirements/{requirement_id}")
def update_requirement(requirement_id: int, payload: RequirementUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("requirement"))) -> dict:
    requirement = db.query(models.Requirement).options(selectinload(models.Requirement.product)).filter(models.Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if payload.product_id is not None:
        ensure_product_exists(db, payload.product_id)
    update_model(requirement, payload)
    commit_or_409(db, "Requirement number already exists")
    db.refresh(requirement)
    return {
        "id": requirement.id,
        "req_no": requirement.req_no,
        "source": requirement.source,
        "category": requirement.category,
        "title": requirement.title,
        "priority": requirement.priority,
        "status": requirement.status,
        "owner": requirement.owner,
        "acceptance_criteria": requirement.acceptance_criteria,
        "product_model": requirement.product.model,
        "product_id": requirement.product_id,
    }


@router.delete("/api/requirements/{requirement_id}")
def delete_requirement(requirement_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("requirement"))) -> dict:
    requirement = db.query(models.Requirement).filter(models.Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if requirement.status in ["已确认", "已发布"]:
        raise HTTPException(status_code=409, detail="Confirmed requirement cannot be deleted")
    db.delete(requirement)
    db.commit()
    return {"deleted": True}


@router.get("/api/requirements/{requirement_id}/trace")
def requirement_trace(requirement_id: int, db: Session = Depends(get_db)) -> dict:
    """需求追溯链路：需求 -> 产品 -> BOM/变更/项目/文档/工艺"""
    requirement = (
        db.query(models.Requirement)
        .options(selectinload(models.Requirement.product))
        .filter(models.Requirement.id == requirement_id)
        .first()
    )
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    product = requirement.product
    if not product:
        return {"requirement": {"req_no": requirement.req_no, "title": requirement.title}, "product": None, "boms": [], "changes": [], "projects": [], "documents": [], "routes": []}
    # 聚合该产品下游对象
    boms = (
        db.query(models.BomHeader)
        .filter(models.BomHeader.product_id == product.id)
        .order_by(models.BomHeader.id.desc())
        .all()
    )
    changes = (
        db.query(models.Change)
        .filter(models.Change.product_id == product.id)
        .order_by(models.Change.id.desc())
        .limit(20)
        .all()
    )
    documents = (
        db.query(models.Document)
        .filter(models.Document.product_id == product.id)
        .order_by(models.Document.id.desc())
        .limit(20)
        .all()
    )
    routes = (
        db.query(models.ProcessRoute)
        .filter(models.ProcessRoute.product_id == product.id)
        .order_by(models.ProcessRoute.id.desc())
        .all()
    )
    # 项目通过 product_model 字符串关联
    projects = (
        db.query(models.Project)
        .filter(models.Project.product_model == product.model)
        .order_by(models.Project.id.desc())
        .all()
    )
    return {
        "requirement": {
            "id": requirement.id,
            "req_no": requirement.req_no,
            "title": requirement.title,
            "source": requirement.source,
            "category": requirement.category,
            "priority": requirement.priority,
            "status": requirement.status,
            "owner": requirement.owner,
            "acceptance_criteria": requirement.acceptance_criteria,
        },
        "product": {
            "id": product.id,
            "model": product.model,
            "name": product.name,
            "lifecycle": product.lifecycle,
            "version": product.version,
            "readiness": product.readiness,
        },
        "boms": [{"id": b.id, "type": b.bom_type, "version": b.version, "status": b.status, "owner": b.owner, "release_date": b.release_date} for b in boms],
        "changes": [{"id": c.id, "change_no": c.change_no, "title": c.title, "status": c.status, "priority": c.priority} for c in changes],
        "documents": [{"id": d.id, "doc_no": d.doc_no, "title": d.title, "category": d.category, "version": d.version, "status": d.status} for d in documents],
        "routes": [{"id": r.id, "route_no": r.route_no, "name": r.name, "version": r.version, "status": r.status} for r in routes],
        "projects": [{"id": p.id, "project_no": p.project_no, "name": p.name, "phase": p.phase, "progress": p.progress, "owner": p.owner, "risk_level": p.risk_level} for p in projects],
    }
