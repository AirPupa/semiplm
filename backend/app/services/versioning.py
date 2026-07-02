"""对象升版与版本号生成：BOM / 文档 / 工艺路线下一版号、有效期收尾。"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from .helpers import day_before, today_text


def is_current_effective_bom(row: models.BomHeader) -> bool:
    # BomHeader 已无 status/effective_date/expiry_date 字段，按 bom_state 判断
    return row.bom_state == "Active"


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
    version = next_revision(source.bom_version)
    while db.query(models.BomHeader.id).filter(
        models.BomHeader.bom_name == source.bom_name,
        models.BomHeader.bom_version == version,
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


def next_unique_process_version(db: Session, source: models.ProcessFlow) -> str:
    version = next_revision(source.process_flow_version)
    while db.query(models.ProcessFlow.id).filter(
        models.ProcessFlow.process_flow_name == source.process_flow_name,
        models.ProcessFlow.process_flow_version == version,
    ).first():
        version = next_revision(version)
    return version


def next_unique_route_no(db: Session, source: models.ProcessFlow, version: str) -> str:
    base_no = f"{source.process_flow_name}-R{version}"
    route_no = base_no
    suffix = 1
    while db.query(models.ProcessFlow.id).filter(models.ProcessFlow.process_flow_name == route_no).first():
        suffix += 1
        route_no = f"{base_no}-{suffix}"
    return route_no


def close_previous_effective_boms(db: Session, bom: models.BomHeader) -> list[dict]:
    # BomHeader 已无 effective_date/expiry_date/status 字段，返回空列表
    return []
