"""对象升版与版本号生成：BOM / 文档 / 工艺路线下一版号、有效期收尾。"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from .helpers import day_before, today_text


def is_current_effective_bom(row: models.BomHeader) -> bool:
    today = today_text()
    if row.status != "已发布":
        return False
    if row.effective_date and row.effective_date > today:
        return False
    if row.expiry_date and row.expiry_date < today:
        return False
    return True


def next_revision(value: str) -> str:
    text_value = (value or "").strip()
    if not text_value:
        return "A1"
    tail_digits = ""
    for char in reversed(text_value):
        if not char.isdigit():
            break
        tail_digits = char + tail_digits
    if tail_digits:
        prefix = text_value[: len(text_value) - len(tail_digits)]
        width = len(tail_digits)
        return f"{prefix}{int(tail_digits) + 1:0{width}d}"
    if len(text_value) == 1 and "A" <= text_value.upper() <= "Y":
        return chr(ord(text_value.upper()) + 1)
    return f"{text_value}-1"


def next_unique_bom_version(db: Session, source: models.BomHeader) -> str:
    version = next_revision(source.version)
    while db.query(models.BomHeader.id).filter(
        models.BomHeader.product_id == source.product_id,
        models.BomHeader.bom_type == source.bom_type,
        models.BomHeader.version == version,
    ).first():
        version = next_revision(version)
    return version


def next_unique_document_no(db: Session, source: models.Document, version: str) -> str:
    base_no = f"{source.doc_no}-R{version}"
    doc_no = base_no
    suffix = 1
    while db.query(models.Document.id).filter(models.Document.doc_no == doc_no).first():
        suffix += 1
        doc_no = f"{base_no}-{suffix}"
    return doc_no


def next_unique_process_version(db: Session, source: models.ProcessRoute) -> str:
    version = next_revision(source.version)
    while db.query(models.ProcessRoute.id).filter(
        models.ProcessRoute.product_id == source.product_id,
        models.ProcessRoute.version == version,
    ).first():
        version = next_revision(version)
    return version


def next_unique_route_no(db: Session, source: models.ProcessRoute, version: str) -> str:
    base_no = f"{source.route_no}-R{version}"
    route_no = base_no
    suffix = 1
    while db.query(models.ProcessRoute.id).filter(models.ProcessRoute.route_no == route_no).first():
        suffix += 1
        route_no = f"{base_no}-{suffix}"
    return route_no


def close_previous_effective_boms(db: Session, bom: models.BomHeader) -> list[dict]:
    cutoff = day_before(bom.effective_date or today_text())
    rows = (
        db.query(models.BomHeader)
        .filter(
            models.BomHeader.id != bom.id,
            models.BomHeader.product_id == bom.product_id,
            models.BomHeader.bom_type == bom.bom_type,
            models.BomHeader.status == "已发布",
        )
        .all()
    )
    closed = []
    for row in rows:
        if row.effective_date and bom.effective_date and row.effective_date > bom.effective_date:
            continue
        if row.expiry_date and row.expiry_date <= cutoff:
            continue
        row.expiry_date = cutoff
        closed.append({"id": row.id, "type": row.bom_type, "version": row.version, "expiry_date": row.expiry_date})
    return closed
