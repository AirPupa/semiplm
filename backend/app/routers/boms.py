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


@router.get("/api/boms")
def boms(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items))
    if keyword:
        kw = f"%{keyword}%"
        q = q.join(models.Product).filter(models.BomHeader.bom_type.ilike(kw) | models.BomHeader.version.ilike(kw) | models.Product.model.ilike(kw))
    total = q.count()
    rows = q.order_by(models.BomHeader.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_bom(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/boms", status_code=201)
def create_bom(payload: BomHeaderPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    ensure_product_exists(db, payload.product_id)
    exists = (
        db.query(models.BomHeader.id)
        .filter(
            models.BomHeader.product_id == payload.product_id,
            models.BomHeader.bom_type == payload.bom_type,
            models.BomHeader.version == payload.version,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="BOM version already exists for this product and type")
    bom = models.BomHeader(**payload.model_dump())
    db.add(bom)
    db.commit()
    db.refresh(bom)
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom.id).first()
    return serialize_bom(bom)


@router.put("/api/boms/{bom_id}")
def update_bom(bom_id: int, payload: BomHeaderUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail=f"BOM in {bom.status} status cannot be edited")
    if payload.product_id is not None:
        ensure_product_exists(db, payload.product_id)
    next_product_id = payload.product_id if payload.product_id is not None else bom.product_id
    next_type = payload.bom_type if payload.bom_type is not None else bom.bom_type
    next_version = payload.version if payload.version is not None else bom.version
    exists = (
        db.query(models.BomHeader.id)
        .filter(
            models.BomHeader.id != bom.id,
            models.BomHeader.product_id == next_product_id,
            models.BomHeader.bom_type == next_type,
            models.BomHeader.version == next_version,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="BOM version already exists for this product and type")
    update_model(bom, payload)
    db.commit()
    db.refresh(bom)
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom.id).first()
    return serialize_bom(bom)


@router.delete("/api/boms/{bom_id}")
def delete_bom(bom_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be deleted")
    if bom.status == "审批中":
        raise HTTPException(status_code=409, detail="BOM in review cannot be deleted")
    db.delete(bom)
    db.commit()
    return {"deleted": True}


@router.post("/api/boms/{bom_id}/items", status_code=201)
def create_bom_item(bom_id: int, payload: BomItemPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail=f"BOM in {bom.status} status cannot be edited")
    data = apply_bom_item_process_binding(db, payload, bom.product_id)
    item = models.BomItem(bom_id=bom_id, parent_id=None, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_bom_item(item)


@router.put("/api/bom-items/{item_id}")
def update_bom_item(item_id: int, payload: BomItemUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    item = db.query(models.BomItem).options(selectinload(models.BomItem.bom)).filter(models.BomItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    if item.bom.status in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail=f"BOM in {item.bom.status} status cannot be edited")
    data = apply_bom_item_process_binding(db, payload, item.bom.product_id)
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return serialize_bom_item(item)


@router.post("/api/boms/{bom_id}/transform", status_code=201)
def transform_bom(bom_id: int, payload: BomTransformPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    source = (
        db.query(models.BomHeader)
        .options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items))
        .filter(models.BomHeader.id == bom_id)
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Source BOM not found")
    if source.bom_type not in ["EBOM", "PBOM"] and payload.target_type in ["PBOM", "MBOM"]:
        raise HTTPException(status_code=409, detail="Only EBOM/PBOM can be transformed to downstream BOM")
    exists = (
        db.query(models.BomHeader.id)
        .filter(
            models.BomHeader.product_id == source.product_id,
            models.BomHeader.bom_type == payload.target_type,
            models.BomHeader.version == payload.version,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Target BOM version already exists for this product and type")
    target = models.BomHeader(
        product_id=source.product_id,
        bom_type=payload.target_type,
        version=payload.version,
        status="编制中",
        owner=payload.owner or source.owner,
        release_date="",
        source_bom_id=source.id,
        effective_date=payload.effective_date,
        expiry_date="",
        effectivity_type=payload.effectivity_type,
        effective_batch=payload.effective_batch or source.effective_batch or "",
    )
    db.add(target)
    db.flush()
    for item in source.items:
        db.add(models.BomItem(
            bom_id=target.id,
            parent_id=None,
            material_code=item.material_code,
            material_name=item.material_name,
            category=item.category,
            specification=item.specification,
            quantity=item.quantity,
            unit=item.unit,
            position=item.position,
            process_step_id=item.process_step_id,
            process_step=item.process_step or "待工艺分配",
            substitute=item.substitute,
            status=item.status,
            effective_date=payload.effective_date or item.effective_date,
            expiry_date=item.expiry_date,
            effectivity_note=f"由 {source.bom_type} {source.version} 转换",
        ))
    db.commit()
    created = (
        db.query(models.BomHeader)
        .options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items))
        .filter(models.BomHeader.id == target.id)
        .first()
    )
    # 计算转换差异摘要（source vs created），避免前端二次调 compare
    source_map = {bom_item_compare_key(item): item for item in source.items}
    created_map = {bom_item_compare_key(item): item for item in created.items}
    added = removed = changed = 0
    for key in set(source_map) | set(created_map):
        src_item = source_map.get(key)
        dst_item = created_map.get(key)
        if src_item and not dst_item:
            removed += 1
        elif dst_item and not src_item:
            added += 1
        elif src_item and dst_item and (
            src_item.quantity != dst_item.quantity
            or src_item.status != dst_item.status
            or src_item.effective_date != dst_item.effective_date
        ):
            changed += 1
    # 顺便统计转换后工序分配完整性
    unassigned_marker = "待工艺分配"
    unassigned = sum(
        1 for it in created.items
        if not (it.process_step or "").strip() or (it.process_step or "").strip() == unassigned_marker
    )
    result = serialize_bom(created)
    result["transform_diff"] = {
        "source": {"id": source.id, "bom_type": source.bom_type, "version": source.version},
        "target": {"id": created.id, "bom_type": created.bom_type, "version": created.version},
        "items_total": len(created.items),
        "items_added": added,
        "items_removed": removed,
        "items_changed": changed,
        "process_unassigned": unassigned,
        "process_is_complete": unassigned == 0,
    }
    return result


@router.get("/api/boms/{bom_id}/compare/{target_bom_id}")
def compare_bom(bom_id: int, target_bom_id: int, db: Session = Depends(get_db)) -> dict:
    base = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom_id).first()
    target = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == target_bom_id).first()
    if not base or not target:
        raise HTTPException(status_code=404, detail="BOM not found")
    base_map = {bom_item_compare_key(item): item for item in base.items}
    target_map = {bom_item_compare_key(item): item for item in target.items}
    changes = []
    for key in sorted(set(base_map) | set(target_map)):
        base_item = base_map.get(key)
        target_item = target_map.get(key)
        if base_item and not target_item:
            changes.append(serialize_bom_compare_item("删除", None, base_item))
        elif target_item and not base_item:
            changes.append(serialize_bom_compare_item("新增", target_item, None))
        elif base_item and target_item and (
            base_item.quantity != target_item.quantity
            or base_item.status != target_item.status
            or base_item.effective_date != target_item.effective_date
            or base_item.expiry_date != target_item.expiry_date
        ):
            changes.append(serialize_bom_compare_item("变更", target_item, base_item))
    return {
        "base": {"id": base.id, "type": base.bom_type, "version": base.version, "product_model": base.product.model},
        "target": {"id": target.id, "type": target.bom_type, "version": target.version, "product_model": target.product.model},
        "summary": {
            "added": len([item for item in changes if item["change_type"] == "新增"]),
            "removed": len([item for item in changes if item["change_type"] == "删除"]),
            "changed": len([item for item in changes if item["change_type"] == "变更"]),
        },
        "changes": changes,
    }


@router.get("/api/boms/{bom_id}/lineage")
def bom_lineage(bom_id: int, db: Session = Depends(get_db)) -> dict:
    """BOM 转换血缘：向上溯源 source_bom 链，向下查所有派生 BOM，用于转换结果可追溯。"""
    current = (
        db.query(models.BomHeader)
        .options(selectinload(models.BomHeader.product))
        .filter(models.BomHeader.id == bom_id)
        .first()
    )
    if not current:
        raise HTTPException(status_code=404, detail="BOM not found")

    def _brief(row: models.BomHeader) -> dict:
        return {
            "id": row.id,
            "bom_type": row.bom_type,
            "version": row.version,
            "status": row.status,
            "product_model": row.product.model if row.product else "",
            "source_bom_id": row.source_bom_id,
            "effective_date": row.effective_date or "",
        }

    # 向上溯源 source_bom 链
    ancestors: list[dict] = []
    seen = {current.id}
    node = current
    while node.source_bom_id and node.source_bom_id not in seen:
        parent = (
            db.query(models.BomHeader)
            .options(selectinload(models.BomHeader.product))
            .filter(models.BomHeader.id == node.source_bom_id)
            .first()
        )
        if not parent:
            break
        seen.add(parent.id)
        ancestors.append(_brief(parent))
        node = parent
    ancestors.reverse()  # 从根到当前

    # 向下递归查派生 BOM（广度优先，按转换层级展开）
    descendants: list[dict] = []
    queue = [current.id]
    visited = {current.id}
    while queue:
        parent_id = queue.pop(0)
        children = (
            db.query(models.BomHeader)
            .options(selectinload(models.BomHeader.product))
            .filter(models.BomHeader.source_bom_id == parent_id)
            .order_by(models.BomHeader.bom_type, models.BomHeader.version)
            .all()
        )
        for child in children:
            if child.id in visited:
                continue
            visited.add(child.id)
            descendants.append(_brief(child))
            queue.append(child.id)

    return {
        "current": _brief(current),
        "ancestors": ancestors,
        "descendants": descendants,
        "has_lineage": bool(ancestors or descendants),
    }


@router.get("/api/boms/{bom_id}/process-coverage")
def bom_process_coverage(bom_id: int, db: Session = Depends(get_db)) -> dict:
    """PBOM/MBOM 工序物料分配完整性校验：统计已分配/未分配工序的明细。"""
    bom = (
        db.query(models.BomHeader)
        .options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items))
        .filter(models.BomHeader.id == bom_id)
        .first()
    )
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    unassigned_marker = "待工艺分配"
    unassigned_items: list[dict] = []
    assigned_count = 0
    for item in sorted(bom.items, key=lambda it: it.id):
        step = (item.process_step or "").strip()
        if not step or step == unassigned_marker:
            unassigned_items.append({
                "item_id": item.id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "position": item.position or "",
                "quantity": item.quantity,
                "unit": item.unit or "",
                "process_step": item.process_step or "",
            })
        else:
            assigned_count += 1
    total = len(bom.items)
    unassigned_count = len(unassigned_items)
    coverage_rate = round(assigned_count / total, 4) if total else 0.0
    return {
        "bom_id": bom.id,
        "bom_type": bom.bom_type,
        "version": bom.version,
        "product_model": bom.product.model if bom.product else "",
        "total_items": total,
        "assigned": assigned_count,
        "unassigned": unassigned_count,
        "coverage_rate": coverage_rate,
        "is_complete": unassigned_count == 0,
        "unassigned_items": unassigned_items,
    }


@router.get("/api/boms/where-used/{material_code}")
def bom_where_used(material_code: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(models.BomItem)
        .join(models.BomHeader)
        .options(selectinload(models.BomItem.bom).selectinload(models.BomHeader.product))
        .filter(models.BomItem.material_code == material_code)
        .order_by(models.BomHeader.product_id, models.BomHeader.bom_type, models.BomHeader.version)
        .all()
    )
    return [
        {
            "bom_id": item.bom_id,
            "product_model": item.bom.product.model,
            "product_name": item.bom.product.name,
            "bom_type": item.bom.bom_type,
            "version": item.bom.version,
            "bom_status": item.bom.status,
            "material_code": item.material_code,
            "material_name": item.material_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "process_step": item.process_step,
            "effective_date": item.effective_date,
            "expiry_date": item.expiry_date,
        }
        for item in rows
    ]


@router.delete("/api/bom-items/{item_id}")
def delete_bom_item(item_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    item = db.query(models.BomItem).options(selectinload(models.BomItem.bom)).filter(models.BomItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    if item.bom.status in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail=f"BOM in {item.bom.status} status cannot be edited")
    db.delete(item)
    db.commit()
    return {"deleted": True}


@router.post("/api/boms/{bom_id}/submit")
def submit_bom(bom_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if not bom.items:
        raise HTTPException(status_code=409, detail="BOM has no items")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be submitted")
    if bom.status == "审批中":
        raise HTTPException(status_code=409, detail="BOM is already in review")
    # ECA 生成对象校验：如果 BOM 有 source_bom_id，说明是 ECA 升版生成的草案
    if bom.source_bom_id:
        generated_no = f"{bom.bom_type}-{bom.product.model}-{bom.version}"
        validate_eca_generated_object_ready(db, "BOM", bom.id, generated_no)
    bom.status = "审批中"
    instance = start_workflow(
        db,
        template_code="WF-BOM-REL",
        object_type="BOM",
        object_id=bom.id,
        object_no=f"{bom.bom_type}-{bom.product.model}-{bom.version}",
        title=f"{bom.product.model} {bom.bom_type} {bom.version} 发布",
        product_model=bom.product.model,
        started_by=bom.owner,
    )
    db.commit()
    return {"id": bom.id, "status": bom.status, "workflow_id": instance.id}


@router.post("/api/boms/{bom_id}/approve")
def approve_bom(bom_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission(["approval", "bom"]))) -> dict:
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if not bom.items:
        raise HTTPException(status_code=409, detail="BOM has no items")
    if bom.status not in ("审批中", "已发布"):
        raise HTTPException(status_code=409, detail="BOM must be submitted for review before approval")
    if bom.source_bom_id:
        generated_no = f"{bom.bom_type}-{bom.product.model}-{bom.version}"
        validate_eca_generated_object_ready(db, "BOM", bom.id, generated_no)
    if bom.status == "已发布" and is_current_effective_bom(bom):
        return {"id": bom.id, "status": bom.status, "release_date": bom.release_date, "effective_date": bom.effective_date, "expiry_date": bom.expiry_date, "closed_versions": []}
    if not bom.effective_date:
        bom.effective_date = today_text()
    bom.status = "已发布"
    bom.release_date = today_text()
    bom.expiry_date = ""
    closed_versions = close_previous_effective_boms(db, bom)
    create_integration_job(
        db,
        target_system="ERP",
        object_type="BOM",
        object_no=f"{bom.bom_type}-{bom.product.model}-{bom.version}",
        product_model=bom.product.model,
        triggered_by=f"BOM-{bom.id}",
        message="BOM 已发布，等待同步 ERP 物料结构和用量。",
    )
    db.commit()
    return {"id": bom.id, "status": bom.status, "release_date": bom.release_date, "effective_date": bom.effective_date, "expiry_date": bom.expiry_date, "closed_versions": closed_versions}


BOM_EXPORT_COLUMNS = [
    "物料编码", "物料名称", "分类", "规格", "数量", "单位", "位号",
    "工序", "替代料", "状态", "生效日期", "失效日期", "有效性备注",
]


def _style_bom_export_ws(ws, bom, include_data: bool = True):
    """Apply consistent styling to a BOM export worksheet."""
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    header_font = Font(bold=True, size=11)
    title_font = Font(bold=True, size=14, color="1F4E79")
    meta_font = Font(size=10, color="666666")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(bold=True, size=10, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    # Title rows
    ws.append(["BOM编号", f"{bom.bom_type}-{bom.product.model}-{bom.version}"])
    ws.append(["产品型号", bom.product.model])
    ws.append(["BOM类型", bom.bom_type])
    ws.append(["版本", bom.version])
    ws.append(["状态", bom.status])
    ws.append(["负责人", bom.owner])
    ws.append(["生效日期", bom.effective_date])
    ws.append(["失效日期", bom.expiry_date])
    ws.append([])

    # Style title rows
    for row_idx in range(1, 9):
        cell_a = ws.cell(row=row_idx, column=1)
        cell_b = ws.cell(row=row_idx, column=2)
        cell_a.font = meta_font
        cell_b.font = Font(bold=True, size=10)
        if row_idx == 1:
            cell_a.font = title_font
            cell_b.font = title_font

    # Column header row (row 10)
    header_row_idx = 10
    ws.append(BOM_EXPORT_COLUMNS)
    for col_idx in range(1, len(BOM_EXPORT_COLUMNS) + 1):
        cell = ws.cell(row=header_row_idx, column=col_idx)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    if include_data:
        for item in bom.items:
            ws.append([
                item.material_code, item.material_name, item.category, item.specification,
                item.quantity, item.unit, item.position, item.process_step,
                item.substitute, item.status, item.effective_date, item.expiry_date, item.effectivity_note,
            ])

        # Style data rows
        data_start = header_row_idx + 1
        data_end = ws.max_row
        for row_idx in range(data_start, data_end + 1):
            for col_idx in range(1, len(BOM_EXPORT_COLUMNS) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
                cell.alignment = left_align if col_idx in (2, 4) else center_align

    # Column widths
    col_widths = [16, 24, 12, 20, 8, 8, 14, 16, 14, 10, 12, 12, 20]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = w
    # Fix: use get_column_letter for proper column references
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Freeze panes below header
    ws.freeze_panes = f"A{header_row_idx + 1}"


@router.get("/api/boms/{bom_id}/export")
def export_bom_excel(bom_id: int, db: Session = Depends(get_db)):
    from openpyxl import Workbook
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product), selectinload(models.BomHeader.items)).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    wb = Workbook()
    ws = wb.active
    ws.title = "BOM"
    _style_bom_export_ws(ws, bom, include_data=True)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    filename = f"{bom.bom_type}-{bom.product.model}-{bom.version}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/boms/template")
def download_bom_template(db: Session = Depends(get_db)):
    """Download a blank BOM Excel template with styled headers and an example row."""
    from openpyxl import Workbook

    class _DummyProduct:
        model = "示例产品型号"

    class _DummyBom:
        bom_type = "EBOM"
        product = _DummyProduct()
        version = "A0"
        status = "编制中"
        owner = ""
        effective_date = ""
        expiry_date = ""

    wb = Workbook()
    ws = wb.active
    ws.title = "BOM模板"
    _style_bom_export_ws(ws, _DummyBom(), include_data=False)
    # Add one example row
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )
    example_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    example_data = ["MAT-001", "示例物料名称", "衬底", "示例规格描述", 1, "件", "U1", "", "", "有效", "", "", ""]
    ws.append(example_data)
    for col_idx in range(1, len(example_data) + 1):
        cell = ws.cell(row=ws.max_row, column=col_idx)
        cell.fill = example_fill
        cell.border = thin_border
        cell.font = Font(italic=True, size=10, color="999999")
    # Add instruction row
    ws.append([])
    ws.append(["说明：请删除示例行后填入真实数据，第一行表头请勿修改。物料编码和物料名称为必填。"])
    ws.cell(row=ws.max_row, column=1).font = Font(size=9, color="999999", italic=True)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="BOM_template.xlsx"'},
    )


@router.post("/api/boms/{bom_id}/import")
async def import_bom_excel(bom_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    from openpyxl import load_workbook
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be modified")
    content = await file.read()
    wb = load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active

    # Pre-load material master data for validation
    material_map: dict[str, dict] = {}
    for m in db.query(models.Material).all():
        material_map[m.code] = {"name": m.name, "category": m.category, "specification": m.specification or ""}

    # Pre-load process steps for this product to auto-bind process_step_id
    step_map: dict[str, int] = {}
    steps = db.query(models.ProcessStep).filter(models.ProcessStep.route_id.in_(
        db.query(models.ProcessRoute.id).filter(models.ProcessRoute.product_id == bom.product_id)
    )).all()
    for s in steps:
        label = f"{s.sequence}-{s.stage}" if s.stage else str(s.sequence)
        step_map[label] = s.id
        step_map[str(s.sequence)] = s.id

    # Pre-load existing material codes in this BOM for duplicate detection
    existing_codes = {item.material_code for item in db.query(models.BomItem).filter(models.BomItem.bom_id == bom_id).all()}
    seen_codes: set[str] = set()

    imported_count = 0
    warnings: list[dict] = []
    errors: list[dict] = []
    skipped_count = 0

    skip_headers = {"物料编码", "BOM编号", "产品型号", "BOM类型", "版本", "状态", "负责人", "生效日期", "失效日期", ""}

    for row_idx, row in enumerate(ws.iter_rows(min_row=1, values_only=True), 1):
        if not row or not row[0]:
            continue
        first_val = str(row[0]).strip()
        if first_val in skip_headers or first_val.startswith("说明"):
            continue
        if len(row) < 6:
            skipped_count += 1
            warnings.append({"row": row_idx, "message": f"列数不足（{len(row)}列），跳过该行"})
            continue

        material_code = first_val
        material_name = str(row[1]).strip() if row[1] else ""
        category = str(row[2]).strip() if row[2] else ""
        specification = str(row[3]).strip() if row[3] else ""
        try:
            quantity = float(row[4]) if row[4] else 0
        except (ValueError, TypeError):
            quantity = 0
            warnings.append({"row": row_idx, "message": f"数量格式错误，已设为0"})
        unit = str(row[5]).strip() if row[5] else ""
        position = str(row[6]).strip() if len(row) > 6 and row[6] else ""
        process_step_text = str(row[7]).strip() if len(row) > 7 and row[7] else ""
        substitute = str(row[8]).strip() if len(row) > 8 and row[8] else ""
        status = str(row[9]).strip() if len(row) > 9 and row[9] else "有效"
        effective_date = str(row[10]).strip() if len(row) > 10 and row[10] else ""
        expiry_date = str(row[11]).strip() if len(row) > 11 and row[11] else ""
        effectivity_note = str(row[12]).strip() if len(row) > 12 and row[12] else ""

        # Validate against material master data
        mat_info = material_map.get(material_code)
        if mat_info:
            # Auto-fill missing fields from master data
            if not material_name:
                material_name = mat_info["name"]
            if not category:
                category = mat_info["category"]
            if not specification:
                specification = mat_info["specification"]
        else:
            warnings.append({"row": row_idx, "message": f"物料编码 {material_code} 不在物料库中，请核实"})

        # Duplicate detection (within file and against existing items)
        if material_code in existing_codes or material_code in seen_codes:
            errors.append({"row": row_idx, "message": f"物料编码 {material_code} 在BOM中已存在，跳过"})
            seen_codes.add(material_code)
            continue
        seen_codes.add(material_code)

        # Auto-bind process_step_id
        process_step_id = None
        if process_step_text:
            process_step_id = step_map.get(process_step_text)
            if process_step_id is None:
                # Try partial match
                for label, sid in step_map.items():
                    if process_step_text in label or label in process_step_text:
                        process_step_id = sid
                        break

        item = models.BomItem(
            bom_id=bom_id, material_code=material_code, material_name=material_name,
            category=category, specification=specification, quantity=quantity, unit=unit,
            position=position, process_step_id=process_step_id, process_step=process_step_text,
            substitute=substitute, status=status, effective_date=effective_date,
            expiry_date=expiry_date, effectivity_note=effectivity_note,
        )
        db.add(item)
        imported_count += 1

    db.commit()
    return {
        "imported": imported_count,
        "bom_id": bom_id,
        "warnings": warnings,
        "errors": errors,
        "skipped": skipped_count,
        "total_processed": imported_count + len(errors) + skipped_count,
    }

@router.post("/api/boms/{bom_id}/batch-replace", status_code=200)
def bom_batch_replace(bom_id: int, payload: BomBatchReplacePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    """Batch replace material code in a BOM — all items matching from_code get updated."""
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be modified")
    items = db.query(models.BomItem).filter(models.BomItem.bom_id == bom_id, models.BomItem.material_code == payload.from_code).all()
    if not items:
        raise HTTPException(status_code=404, detail=f"No items found with material code {payload.from_code}")
    # Check for conflicts — if to_code already exists in this BOM
    existing = db.query(models.BomItem).filter(models.BomItem.bom_id == bom_id, models.BomItem.material_code == payload.to_code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Material code {payload.to_code} already exists in this BOM")
    # Try to fill from material master data
    mat = db.query(models.Material).filter(models.Material.code == payload.to_code).first()
    updated_count = 0
    for item in items:
        item.material_code = payload.to_code
        if payload.to_name:
            item.material_name = payload.to_name
        elif mat:
            item.material_name = mat.name
        if payload.to_category:
            item.category = payload.to_category
        elif mat:
            item.category = mat.category
        if payload.to_specification:
            item.specification = payload.to_specification
        elif mat and mat.specification:
            item.specification = mat.specification
        updated_count += 1
    db.commit()
    return {"updated": updated_count, "bom_id": bom_id, "from_code": payload.from_code, "to_code": payload.to_code}

@router.post("/api/boms/{bom_id}/batch-quantity", status_code=200)
def bom_batch_quantity(bom_id: int, payload: BomBatchQuantityPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    """Batch update quantity for multiple BOM items."""
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be modified")
    if not payload.item_ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")
    if payload.quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity must be non-negative")
    items = db.query(models.BomItem).filter(
        models.BomItem.bom_id == bom_id,
        models.BomItem.id.in_(payload.item_ids),
    ).all()
    for item in items:
        item.quantity = payload.quantity
    db.commit()
    return {"updated": len(items), "bom_id": bom_id, "quantity": payload.quantity}

@router.post("/api/boms/{bom_id}/batch-delete", status_code=200)
def bom_batch_delete(bom_id: int, payload: BomBatchDeletePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("bom"))) -> dict:
    """Batch delete multiple BOM items."""
    bom = db.query(models.BomHeader).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    if bom.status == "已发布":
        raise HTTPException(status_code=409, detail="Released BOM cannot be modified")
    if not payload.item_ids:
        raise HTTPException(status_code=400, detail="No item IDs provided")
    deleted_count = db.query(models.BomItem).filter(
        models.BomItem.bom_id == bom_id,
        models.BomItem.id.in_(payload.item_ids),
    ).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted_count, "bom_id": bom_id}

@router.get("/api/baselines")
def baselines(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = (
        db.query(models.ProductBaseline)
        .options(selectinload(models.ProductBaseline.product), selectinload(models.ProductBaseline.items))
    )
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.ProductBaseline.baseline_no.ilike(kw) | models.ProductBaseline.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.ProductBaseline.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": row.id,
                "baseline_no": row.baseline_no,
                "name": row.name,
                "product_model": row.product.model,
                "version": row.version,
                "status": row.status,
                "created_by": row.created_by,
                "released_at": row.released_at,
                "items": [
                    {
                        "id": item.id,
                        "item_type": item.item_type,
                        "item_no": item.item_no,
                        "title": item.title,
                        "version": item.version,
                        "status": item.status,
                    }
                    for item in row.items
                ],
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@router.get("/api/boms/{bom_id}/version-history")
def bom_version_history(bom_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """追溯 BOM 完整版本链路：来源版本、生成变更单、ECA 动作和发布门状态。"""
    bom = db.query(models.BomHeader).options(selectinload(models.BomHeader.product)).filter(models.BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    chain: list[models.BomHeader] = []
    current = bom
    visited = set()
    while current and current.id not in visited:
        visited.add(current.id)
        chain.append(current)
        if current.source_bom_id:
            current = db.query(models.BomHeader).filter(models.BomHeader.id == current.source_bom_id).first()
        else:
            break
    chain.reverse()

    history = []
    for item in chain:
        eca_action = (
            db.query(models.ChangeAction)
            .filter(
                models.ChangeAction.target_type == "BOM",
                models.ChangeAction.target_id == item.source_bom_id if item.source_bom_id else 0,
            )
            .first() if item.source_bom_id else None
        )
        change_no = ""
        change_status = ""
        action_no = ""
        effectivity_type = ""
        effective_batch = ""
        effective_date = ""
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
            if eca_action.generated_object_no:
                gate = get_eca_generated_object_gate(db, "BOM", eca_action.generated_object_no)
                if gate:
                    release_gate = "可提交" if gate["ready"] else "待变更闭环"
                    gate_message = gate["message"]

        generated_no = f"{item.bom_type}-{item.product.model}-{item.version}" if item.product else ""
        history.append({
            "id": item.id,
            "version": item.version,
            "status": item.status,
            "bom_type": item.bom_type,
            "object_no": generated_no,
            "owner": item.owner,
            "release_date": item.release_date,
            "effective_date": item.effective_date,
            "expiry_date": item.expiry_date,
            "effectivity_type": item.effectivity_type,
            "effective_batch": item.effective_batch,
            "source_bom_id": item.source_bom_id,
            "is_current": item.id == bom.id,
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
