"""制造流程校验与 BOM 工序绑定。对齐 MES ProcessFlow（原 ProcessRoute 已重命名）。"""
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models


def ensure_route_editable(flow: models.ProcessFlow) -> None:
    """制造流程状态校验：Frozen/Invalid 状态不可修改。"""
    if flow.process_flow_state in ("Frozen", "Invalid"):
        raise HTTPException(status_code=409, detail=f"Process flow in {flow.process_flow_state} state cannot be modified")


def validate_process_route_ready(flow: models.ProcessFlow) -> None:
    """制造流程就绪校验：必须有工序序列，工序序号不重复。"""
    if not flow.seqs:
        raise HTTPException(status_code=409, detail="Process flow has no sequences")
    idxs = [s.idx for s in flow.seqs if s.idx is not None]
    if len(idxs) != len(set(idxs)):
        raise HTTPException(status_code=409, detail="Process flow has duplicate sequence idx")


def apply_bom_item_process_binding(db: Session, payload: BaseModel, product_id: int) -> dict:
    """BomItem 工步绑定校验：process_step_name 必须在工序库存在。
    产品通过 process_flow_name+version 引用流程，流程的 seqs 引用工序库的 process_step_name。
    """
    data = payload.model_dump(exclude_unset=True)
    step_name = data.get("process_step_name")
    if step_name:
        step = db.query(models.ProcessStep).filter(
            models.ProcessStep.process_step_name == step_name,
            models.ProcessStep.is_deleted == False,
        ).first()
        if not step:
            raise HTTPException(status_code=404, detail="Process step not found in library")
    return data
