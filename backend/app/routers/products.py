from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import require_permission
from ..schemas import ProductPayload, ProductUpdatePayload, ProductVersionPayload
from ..serializers import serialize_product
from ..services.helpers import commit_or_409, ensure_product_exists, update_model


router = APIRouter()


@router.get("/api/products")
def products(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Product)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            models.Product.code.ilike(kw)
            | models.Product.model.ilike(kw)
            | models.Product.name.ilike(kw)
            | models.Product.product_type.ilike(kw)
        )
    total = q.count()
    rows = q.order_by(models.Product.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [serialize_product(p) for p in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/products", status_code=201)
def create_product(payload: ProductPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = models.Product(**payload.model_dump())
    db.add(product)
    commit_or_409(db, "Product code or model already exists")
    db.refresh(product)
    return serialize_product(product)


@router.get("/api/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)) -> dict:
    product = (
        db.query(models.Product)
        .options(
            selectinload(models.Product.bom_headers),
            selectinload(models.Product.documents),
            selectinload(models.Product.process_routes).selectinload(models.ProcessRoute.steps),
            selectinload(models.Product.changes).selectinload(models.Change.impacts),
            selectinload(models.Product.quality_lots),
            selectinload(models.Product.requirements),
        )
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    data = serialize_product(product)
    # 项目通过 product_model 字符串关联，非外键，单独查询
    linked_projects = (
        db.query(models.Project)
        .filter(models.Project.product_model == product.model)
        .order_by(models.Project.id.desc())
        .all()
    )
    data.update(
        {
            "boms": [{"id": bom.id, "type": bom.bom_type, "version": bom.version, "status": bom.status, "owner": bom.owner, "release_date": bom.release_date} for bom in product.bom_headers],
            "documents": [{"id": doc.id, "doc_no": doc.doc_no, "title": doc.title, "category": doc.category, "version": doc.version, "status": doc.status, "approval_status": doc.approval_status} for doc in product.documents],
            "routes": [{"id": route.id, "route_no": route.route_no, "name": route.name, "version": route.version, "status": route.status, "steps": len(route.steps)} for route in product.process_routes],
            "changes": [{"id": change.id, "change_no": change.change_no, "title": change.title, "status": change.status, "priority": change.priority} for change in product.changes],
            "quality": [{"lot_no": lot.lot_no, "stage": lot.stage, "cp_yield": lot.cp_yield, "ft_yield": lot.ft_yield, "status": lot.status} for lot in product.quality_lots],
            "requirements": [{"id": req.id, "req_no": req.req_no, "title": req.title, "source": req.source, "category": req.category, "priority": req.priority, "status": req.status, "owner": req.owner} for req in product.requirements],
            "projects": [{"id": proj.id, "project_no": proj.project_no, "name": proj.name, "phase": proj.phase, "progress": proj.progress, "owner": proj.owner, "risk_level": proj.risk_level} for proj in linked_projects],
        }
    )
    return data


@router.put("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_model(product, payload)
    commit_or_409(db, "Product code or model already exists")
    db.refresh(product)
    return serialize_product(product)


@router.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    linked_count = (
        db.query(models.BomHeader).filter(models.BomHeader.product_id == product_id).count()
        + db.query(models.Document).filter(models.Document.product_id == product_id).count()
        + db.query(models.ProcessRoute).filter(models.ProcessRoute.product_id == product_id).count()
        + db.query(models.Change).filter(models.Change.product_id == product_id).count()
        + db.query(models.QualityLot).filter(models.QualityLot.product_id == product_id).count()
        + db.query(models.Requirement).filter(models.Requirement.product_id == product_id).count()
        + db.query(models.ProductBaseline).filter(models.ProductBaseline.product_id == product_id).count()
    )
    if linked_count:
        raise HTTPException(status_code=409, detail="Product has linked PLM data and cannot be deleted")
    db.delete(product)
    db.commit()
    return {"deleted": True}


@router.get("/api/products/{product_id}/versions")
def product_versions(product_id: int, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.ProductVersion).filter(models.ProductVersion.product_id == product_id).order_by(models.ProductVersion.id.desc()).all()
    return [
        {"id": r.id, "version": r.version, "lifecycle": r.lifecycle, "readiness": r.readiness, "released_at": r.released_at, "released_by": r.released_by, "source_change_no": r.source_change_no, "summary": r.summary}
        for r in rows
    ]


@router.post("/api/products/{product_id}/versions", status_code=201)
def create_product_version(product_id: int, payload: ProductVersionPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    ensure_product_exists(db, product_id)
    row = models.ProductVersion(product_id=product_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "version": row.version}
