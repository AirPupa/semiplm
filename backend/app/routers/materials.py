from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import require_permission
from ..schemas import (
    MaterialPayload,
    MaterialUpdatePayload,
    SubstituteMaterialPayload,
    SubstituteMaterialUpdatePayload,
    SupplierPayload,
    SupplierUpdatePayload,
)
from ..services.helpers import commit_or_409, update_model


router = APIRouter()


@router.get("/api/materials")
def materials(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Material)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Material.code.ilike(kw) | models.Material.name.ilike(kw) | models.Material.category.ilike(kw))
    total = q.count()
    rows = q.order_by(models.Material.category, models.Material.code).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": row.id, "code": row.code, "name": row.name, "category": row.category, "specification": row.specification, "supplier": row.supplier, "supplier_id": row.supplier_id, "risk_level": row.risk_level, "lifecycle": row.lifecycle}
            for row in rows
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/api/materials", status_code=201)
def create_material(payload: MaterialPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    material = models.Material(**payload.model_dump())
    db.add(material)
    commit_or_409(db, "Material code already exists")
    db.refresh(material)
    return {
        "id": material.id,
        "code": material.code,
        "name": material.name,
        "category": material.category,
        "specification": material.specification,
        "supplier": material.supplier,
        "supplier_id": material.supplier_id,
        "risk_level": material.risk_level,
        "lifecycle": material.lifecycle,
    }


@router.put("/api/materials/{material_id}")
def update_material(material_id: int, payload: MaterialUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    update_model(material, payload)
    commit_or_409(db, "Material code already exists")
    db.refresh(material)
    return {
        "id": material.id,
        "code": material.code,
        "name": material.name,
        "category": material.category,
        "specification": material.specification,
        "supplier": material.supplier,
        "supplier_id": material.supplier_id,
        "risk_level": material.risk_level,
        "lifecycle": material.lifecycle,
    }


@router.delete("/api/materials/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    bom_refs = db.query(models.BomItem).filter(models.BomItem.material_code == material.code).count()
    if bom_refs:
        raise HTTPException(status_code=409, detail="Material is used by BOM and cannot be deleted")
    db.delete(material)
    db.commit()
    return {"deleted": True}

@router.get("/api/substitute-materials")
def substitute_materials(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.SubstituteMaterial)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            models.SubstituteMaterial.material_code.ilike(kw)
            | models.SubstituteMaterial.material_name.ilike(kw)
            | models.SubstituteMaterial.substitute_code.ilike(kw)
            | models.SubstituteMaterial.substitute_name.ilike(kw)
        )
    total = q.count()
    rows = q.order_by(models.SubstituteMaterial.material_code).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": r.id, "material_code": r.material_code, "material_name": r.material_name, "substitute_code": r.substitute_code, "substitute_name": r.substitute_name, "material_id": r.material_id, "substitute_material_id": r.substitute_material_id, "substitute_type": r.substitute_type, "strategy": r.strategy, "risk_level": r.risk_level, "status": r.status, "effective_date": r.effective_date, "expiry_date": r.expiry_date, "description": r.description} for r in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/substitute-materials", status_code=201)
def create_substitute_material(payload: SubstituteMaterialPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = models.SubstituteMaterial(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "material_id": row.material_id, "substitute_material_id": row.substitute_material_id}


@router.put("/api/substitute-materials/{row_id}")
def update_substitute_material(row_id: int, payload: SubstituteMaterialUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.SubstituteMaterial).filter(models.SubstituteMaterial.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Substitute material not found")
    update_model(row, payload)
    db.commit()
    return {"ok": True}


@router.delete("/api/substitute-materials/{row_id}")
def delete_substitute_material(row_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.SubstituteMaterial).filter(models.SubstituteMaterial.id == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Substitute material not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/api/suppliers")
def suppliers(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Supplier)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Supplier.code.ilike(kw) | models.Supplier.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.Supplier.code).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": r.id, "code": r.code, "name": r.name, "supplier_type": r.supplier_type, "contact": r.contact, "phone": r.phone, "email": r.email, "address": r.address, "certification": r.certification, "risk_level": r.risk_level, "status": r.status, "description": r.description} for r in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/suppliers", status_code=201)
def create_supplier(payload: SupplierPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = models.Supplier(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Supplier code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code, "name": row.name}


@router.put("/api/suppliers/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")
    update_model(row, payload)
    commit_or_409(db, "Supplier code already exists")
    return {"ok": True}


@router.delete("/api/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("material"))) -> dict:
    row = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
