"""产品中心 - ProductDef（对齐 MES Template V1.2，26 字段）。

架构独立化：Product 不再绑定 process_routes 外键关系，通过 processFlowName+Version
字符串引用制造流程。详情接口返回引用对象的轻量信息（不内嵌所有业务模块）。
"""
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
def products(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    state: str = "",
    product_type: str = "",
    db: Session = Depends(get_db),
) -> dict:
    """产品列表 - 对齐 ProductDef 字段过滤。"""
    q = db.query(models.Product)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            models.Product.product_def_name.ilike(kw)
            | models.Product.description.ilike(kw)
            | models.Product.product_type.ilike(kw)
            | models.Product.product_group_name.ilike(kw)
            | models.Product.owner.ilike(kw)
        )
    if state:
        q = q.filter(models.Product.product_def_state == state)
    if product_type:
        q = q.filter(models.Product.product_type == product_type)
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
    commit_or_409(db, "ProductDef name already exists")
    db.refresh(product)
    return serialize_product(product)


@router.get("/api/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)) -> dict:
    """产品详情 - 展示自身 26 字段 + 引用对象（ProcessFlow/Bom）的轻量信息。

    不再内嵌全部业务模块（需求/文档/BOM/工艺/变更/项目/质量）。
    PLM 是源头，详情聚焦 ProductDef 自身规格和引用关系；
    各业务对象在自己的菜单维护，避免详情页变成 8 模块大杂烩。
    """
    product = (
        db.query(models.Product)
        .options(
            selectinload(models.Product.documents),
            selectinload(models.Product.changes),
            selectinload(models.Product.quality_lots),
            selectinload(models.Product.requirements),
        )
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = serialize_product(product)

    # 引用对象 - ProcessFlow（通过 process_flow_name+version 字符串引用）
    referenced_flow = None
    if product.process_flow_name:
        flow = (
            db.query(models.ProcessFlow)
            .filter(
                models.ProcessFlow.process_flow_name == product.process_flow_name,
                models.ProcessFlow.process_flow_version == (product.process_flow_version or "001"),
                models.ProcessFlow.is_deleted == False,
            )
            .first()
        )
        if flow:
            referenced_flow = {
                "id": flow.id,
                "process_flow_name": flow.process_flow_name,
                "process_flow_version": flow.process_flow_version,
                "process_flow_state": flow.process_flow_state,
                "process_flow_type1": flow.process_flow_type1,
                "process_flow_type2": flow.process_flow_type2,
                "owner": flow.owner,
                "description": flow.description,
            }

    # 引用对象 - Bom（通过 bom_name+version 字符串引用）
    referenced_bom = None
    if product.bom_name:
        bom = (
            db.query(models.BomHeader)
            .filter(
                models.BomHeader.bom_name == product.bom_name,
                models.BomHeader.bom_version == (product.bom_version or "001"),
            )
            .first()
        )
        if bom:
            referenced_bom = {
                "id": bom.id,
                "bom_name": bom.bom_name,
                "bom_version": bom.bom_version,
                "bom_state": bom.bom_state,
                "owner": bom.owner,
                "description": bom.description,
            }

    # 轻量关联：按字符串 product_model 关联的项目
    linked_projects = (
        db.query(models.Project)
        .filter(models.Project.product_model == product.product_def_name)
        .order_by(models.Project.id.desc())
        .all()
    )

    data.update(
        {
            "referenced_flow": referenced_flow,
            "referenced_bom": referenced_bom,
            "documents_count": len(product.documents),
            "changes_count": len(product.changes),
            "quality_lots_count": len(product.quality_lots),
            "requirements_count": len(product.requirements),
            "projects": [
                {
                    "id": proj.id,
                    "project_no": proj.project_no,
                    "name": proj.name,
                    "phase": proj.phase,
                    "progress": proj.progress,
                    "owner": proj.owner,
                    "risk_level": proj.risk_level,
                }
                for proj in linked_projects
            ],
        }
    )
    return data


@router.put("/api/products/{product_id}")
def update_product(product_id: int, payload: ProductUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_model(product, payload)
    commit_or_409(db, "ProductDef name already exists")
    db.refresh(product)
    return serialize_product(product)


@router.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("product"))) -> dict:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # 架构独立化后：ProcessFlow 不再外键绑定，但 Document/Change/QualityLot/Requirement 仍可能引用
    linked_count = (
        db.query(models.Document).filter(models.Document.product_id == product_id).count()
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
