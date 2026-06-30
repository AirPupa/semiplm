"""工艺路线校验与 BOM 工序绑定。"""
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models


def ensure_route_editable(route: models.ProcessRoute) -> None:
    if route.status in ("已发布", "审批中"):
        raise HTTPException(status_code=409, detail=f"Process route in {route.status} status cannot be modified")


def validate_process_route_ready(route: models.ProcessRoute) -> None:
    if not route.steps:
        raise HTTPException(status_code=409, detail="Process route has no steps")
    sequences = [step.sequence for step in route.steps]
    if len(sequences) != len(set(sequences)):
        raise HTTPException(status_code=409, detail="Process route has duplicate step sequence")
    for step in route.steps:
        if not step.stage.strip() or not step.operation.strip() or not step.key_params.strip():
            raise HTTPException(status_code=409, detail="Process route step is incomplete")


def apply_bom_item_process_binding(db: Session, payload: BaseModel, product_id: int) -> dict:
    data = payload.model_dump(exclude_unset=True)
    step_id = data.get("process_step_id")
    if step_id:
        step = (
            db.query(models.ProcessStep)
            .join(models.ProcessRoute)
            .filter(models.ProcessStep.id == step_id, models.ProcessRoute.product_id == product_id)
            .first()
        )
        if not step:
            raise HTTPException(status_code=404, detail="Process step not found for this product")
        data["process_step"] = f"{step.sequence}-{step.stage}"
    return data
