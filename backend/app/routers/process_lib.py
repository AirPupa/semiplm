"""工艺库独立菜单：工序库(ProcessStep)/制程阶段库(ProcessStage)/制程能力库(ProcessCapability)/制程配方库(Recipe)/设备类型库(EquipmentType)/设备能力库(EquipmentCapability)。
对齐 MES Template V1.2，6 个 PLM 主控独立菜单。
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import current_user_context
from ..schemas import (
    EquipmentCapabilityPayload,
    EquipmentCapabilityUpdatePayload,
    EquipmentTypePayload,
    EquipmentTypeUpdatePayload,
    ProcessCapabilityPayload,
    ProcessCapabilityUpdatePayload,
    ProcessStagePayload,
    ProcessStageUpdatePayload,
    ProcessStepPayload,
    ProcessStepUpdatePayload,
    RecipePayload,
    RecipeUpdatePayload,
)
from ..services.helpers import audit_log, commit_or_409, update_model

router = APIRouter()


# ===== 工序库 ProcessStep（独立菜单，21 字段）=====
@router.get("/api/process-steps")
def list_process_steps(
    keyword: str = "",
    state: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    q = db.query(models.ProcessStep).filter(models.ProcessStep.is_deleted == False)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.ProcessStep.process_step_name.like(like))
            | (models.ProcessStep.description.like(like))
        )
    if state:
        q = q.filter(models.ProcessStep.process_step_state == state)
    total = q.count()
    items = q.order_by(models.ProcessStep.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_step_dict(s) for s in items], "total": total, "page": page, "page_size": page_size}


@router.post("/api/process-steps", status_code=201)
def create_process_step(
    payload: ProcessStepPayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    step = models.ProcessStep(**payload.model_dump())
    db.add(step)
    try:
        commit_or_409(db, "操作冲突")
    except IntegrityError:
        raise HTTPException(409, "工步名称+版本已存在")
    audit_log(db, "create", "ProcessStep", step.id, step.process_step_name, "创建工序", ctx["user"])
    return _step_dict(step)


@router.get("/api/process-steps/{step_id}")
def get_process_step(step_id: int, db: Session = Depends(get_db), _ctx: dict = Depends(current_user_context)):
    step = db.query(models.ProcessStep).filter(models.ProcessStep.id == step_id).first()
    if not step:
        raise HTTPException(404, "工序不存在")
    return _step_dict(step)


@router.put("/api/process-steps/{step_id}")
def update_process_step(
    step_id: int,
    payload: ProcessStepUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    step = db.query(models.ProcessStep).filter(models.ProcessStep.id == step_id).first()
    if not step:
        raise HTTPException(404, "工序不存在")
    update_model(step, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessStep", step.id, step.process_step_name, "更新工序", ctx["user"])
    return _step_dict(step)


@router.delete("/api/process-steps/{step_id}")
def delete_process_step(step_id: int, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    step = db.query(models.ProcessStep).filter(models.ProcessStep.id == step_id).first()
    if not step:
        raise HTTPException(404, "工序不存在")
    step.is_deleted = True
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessStep", step_id, step.process_step_name, "删除工序", ctx["user"])
    return {"ok": True}


# ===== 制程阶段库 ProcessStage（7 字段）=====
@router.get("/api/process-stages")
def list_process_stages(
    keyword: str = "",
    state: str = "",
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    q = db.query(models.ProcessStage)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.ProcessStage.process_stage_name.like(like))
            | (models.ProcessStage.description.like(like))
        )
    if state:
        q = q.filter(models.ProcessStage.process_stage_state == state)
    items = q.order_by(models.ProcessStage.idx).all()
    return {"items": [_stage_dict(s) for s in items], "total": len(items)}


@router.post("/api/process-stages", status_code=201)
def create_process_stage(payload: ProcessStagePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    stage = models.ProcessStage(**payload.model_dump())
    db.add(stage)
    try:
        commit_or_409(db, "操作冲突")
    except IntegrityError:
        raise HTTPException(409, "制程阶段名称已存在")
    audit_log(db, "create", "ProcessStage", stage.id, stage.process_stage_name, "创建制程阶段", ctx["user"])
    return _stage_dict(stage)


@router.put("/api/process-stages/{stage_id}")
def update_process_stage(stage_id: int, payload: ProcessStageUpdatePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    stage = db.query(models.ProcessStage).filter(models.ProcessStage.id == stage_id).first()
    if not stage:
        raise HTTPException(404, "制程阶段不存在")
    update_model(stage, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessStage", stage.id, stage.process_stage_name, "更新制程阶段", ctx["user"])
    return _stage_dict(stage)


@router.delete("/api/process-stages/{stage_id}")
def delete_process_stage(stage_id: int, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    stage = db.query(models.ProcessStage).filter(models.ProcessStage.id == stage_id).first()
    if not stage:
        raise HTTPException(404, "制程阶段不存在")
    db.delete(stage)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessStage", stage_id, stage.process_stage_name, "删除制程阶段", ctx["user"])
    return {"ok": True}


# ===== 制程能力库 ProcessCapability（3 字段）=====
@router.get("/api/process-capabilities")
def list_process_capabilities(keyword: str = "", state: str = "", db: Session = Depends(get_db), _ctx: dict = Depends(current_user_context)):
    q = db.query(models.ProcessCapability)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.ProcessCapability.process_capability_name.like(like))
            | (models.ProcessCapability.description.like(like))
        )
    if state:
        q = q.filter(models.ProcessCapability.process_capability_state == state)
    items = q.order_by(models.ProcessCapability.id).all()
    return {"items": [_cap_dict(c) for c in items], "total": len(items)}


@router.post("/api/process-capabilities", status_code=201)
def create_process_capability(payload: ProcessCapabilityPayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    cap = models.ProcessCapability(**payload.model_dump())
    db.add(cap)
    try:
        commit_or_409(db, "操作冲突")
    except IntegrityError:
        raise HTTPException(409, "制程能力名称已存在")
    audit_log(db, "create", "ProcessCapability", cap.id, cap.process_capability_name, "创建制程能力", ctx["user"])
    return _cap_dict(cap)


@router.put("/api/process-capabilities/{cap_id}")
def update_process_capability(cap_id: int, payload: ProcessCapabilityUpdatePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    cap = db.query(models.ProcessCapability).filter(models.ProcessCapability.id == cap_id).first()
    if not cap:
        raise HTTPException(404, "制程能力不存在")
    update_model(cap, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessCapability", cap.id, cap.process_capability_name, "更新制程能力", ctx["user"])
    return _cap_dict(cap)


@router.delete("/api/process-capabilities/{cap_id}")
def delete_process_capability(cap_id: int, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    cap = db.query(models.ProcessCapability).filter(models.ProcessCapability.id == cap_id).first()
    if not cap:
        raise HTTPException(404, "制程能力不存在")
    db.delete(cap)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessCapability", cap_id, cap.process_capability_name, "删除制程能力", ctx["user"])
    return {"ok": True}


# ===== 制程配方库 Recipe（7 字段，不含物理参数）=====
@router.get("/api/recipes")
def list_recipes(keyword: str = "", state: str = "", capability: str = "", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=1000), db: Session = Depends(get_db), _ctx: dict = Depends(current_user_context)):
    q = db.query(models.Recipe)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.Recipe.recipe_name.like(like))
            | (models.Recipe.description.like(like))
        )
    if state:
        q = q.filter(models.Recipe.recipe_state == state)
    if capability:
        q = q.filter(models.Recipe.process_capability_name == capability)
    total = q.count()
    items = q.order_by(models.Recipe.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_recipe_dict(r) for r in items], "total": total, "page": page, "page_size": page_size}


@router.post("/api/recipes", status_code=201)
def create_recipe(payload: RecipePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    r = models.Recipe(**payload.model_dump())
    db.add(r)
    try:
        commit_or_409(db, "操作冲突")
    except IntegrityError:
        raise HTTPException(409, "配方名称已存在")
    audit_log(db, "create", "Recipe", r.id, r.recipe_name, "创建制程配方", ctx["user"])
    return _recipe_dict(r)


@router.put("/api/recipes/{recipe_id}")
def update_recipe(recipe_id: int, payload: RecipeUpdatePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    r = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not r:
        raise HTTPException(404, "制程配方不存在")
    update_model(r, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "Recipe", r.id, r.recipe_name, "更新制程配方", ctx["user"])
    return _recipe_dict(r)


@router.delete("/api/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    r = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not r:
        raise HTTPException(404, "制程配方不存在")
    db.delete(r)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "Recipe", recipe_id, r.recipe_name, "删除制程配方", ctx["user"])
    return {"ok": True}


# ===== 设备类型库 EquipmentType（12 字段）=====
@router.get("/api/equipment-types")
def list_equipment_types(keyword: str = "", state: str = "", db: Session = Depends(get_db), _ctx: dict = Depends(current_user_context)):
    q = db.query(models.EquipmentType)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.EquipmentType.equipment_type_name.like(like))
            | (models.EquipmentType.description.like(like))
        )
    if state:
        q = q.filter(models.EquipmentType.equipment_type_state == state)
    items = q.order_by(models.EquipmentType.id).all()
    return {"items": [_eqtype_dict(e) for e in items], "total": len(items)}


@router.post("/api/equipment-types", status_code=201)
def create_equipment_type(payload: EquipmentTypePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    e = models.EquipmentType(**payload.model_dump())
    db.add(e)
    try:
        commit_or_409(db, "操作冲突")
    except IntegrityError:
        raise HTTPException(409, "设备类型名称已存在")
    audit_log(db, "create", "EquipmentType", e.id, e.equipment_type_name, "创建设备类型", ctx["user"])
    return _eqtype_dict(e)


@router.put("/api/equipment-types/{eqtype_id}")
def update_equipment_type(eqtype_id: int, payload: EquipmentTypeUpdatePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    e = db.query(models.EquipmentType).filter(models.EquipmentType.id == eqtype_id).first()
    if not e:
        raise HTTPException(404, "设备类型不存在")
    update_model(e, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "EquipmentType", e.id, e.equipment_type_name, "更新设备类型", ctx["user"])
    return _eqtype_dict(e)


@router.delete("/api/equipment-types/{eqtype_id}")
def delete_equipment_type(eqtype_id: int, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    e = db.query(models.EquipmentType).filter(models.EquipmentType.id == eqtype_id).first()
    if not e:
        raise HTTPException(404, "设备类型不存在")
    db.delete(e)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "EquipmentType", eqtype_id, e.equipment_type_name, "删除设备类型", ctx["user"])
    return {"ok": True}


# ===== 设备能力库 EquipmentCapability（4 字段，equipmentName→equipment_type_name 改造）=====
@router.get("/api/equipment-capabilities")
def list_equipment_capabilities(eqtype: str = "", capability: str = "", db: Session = Depends(get_db), _ctx: dict = Depends(current_user_context)):
    q = db.query(models.EquipmentCapability)
    if eqtype:
        q = q.filter(models.EquipmentCapability.equipment_type_name == eqtype)
    if capability:
        q = q.filter(models.EquipmentCapability.process_capability_name == capability)
    items = q.all()
    return {"items": [_eqcap_dict(c) for c in items], "total": len(items)}


@router.post("/api/equipment-capabilities", status_code=201)
def create_equipment_capability(payload: EquipmentCapabilityPayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    c = models.EquipmentCapability(**payload.model_dump())
    db.add(c)
    commit_or_409(db, "操作冲突")
    audit_log(db, "create", "EquipmentCapability", c.id, f"{c.equipment_type_name}-{c.process_capability_name}", "创建设备能力", ctx["user"])
    return _eqcap_dict(c)


@router.put("/api/equipment-capabilities/{cap_id}")
def update_equipment_capability(cap_id: int, payload: EquipmentCapabilityUpdatePayload, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    c = db.query(models.EquipmentCapability).filter(models.EquipmentCapability.id == cap_id).first()
    if not c:
        raise HTTPException(404, "设备能力不存在")
    update_model(c, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "EquipmentCapability", c.id, f"{c.equipment_type_name}-{c.process_capability_name}", "更新设备能力", ctx["user"])
    return _eqcap_dict(c)


@router.delete("/api/equipment-capabilities/{cap_id}")
def delete_equipment_capability(cap_id: int, db: Session = Depends(get_db), ctx: dict = Depends(current_user_context)):
    c = db.query(models.EquipmentCapability).filter(models.EquipmentCapability.id == cap_id).first()
    if not c:
        raise HTTPException(404, "设备能力不存在")
    db.delete(c)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "EquipmentCapability", cap_id, f"{c.equipment_type_name}-{c.process_capability_name}", "删除设备能力", ctx["user"])
    return {"ok": True}


# ===== 序列化 =====
def _step_dict(s: models.ProcessStep) -> dict:
    return {
        "id": s.id,
        "process_step_name": s.process_step_name,
        "process_step_version": s.process_step_version,
        "description": s.description,
        "process_step_state": s.process_step_state,
        "process_step_type": s.process_step_type,
        "process_stage_name": s.process_stage_name,
        "process_group1": s.process_group1,
        "process_group2": s.process_group2,
        "key_process": s.key_process,
        "bank_name": s.bank_name,
        "process_capability_name": s.process_capability_name,
        "recipe_name": s.recipe_name,
        "is_skip_allowed": s.is_skip_allowed,
        "is_mandatory_step": s.is_mandatory_step,
        "sampling_user_group": s.sampling_user_group,
        "owner_group_name": s.owner_group_name,
        "owner": s.owner,
        "cost_center_stage": s.cost_center_stage,
        "is_deleted": s.is_deleted,
        "is_flip": s.is_flip,
        "detail_process_step_type": s.detail_process_step_type,
    }


def _stage_dict(s: models.ProcessStage) -> dict:
    return {
        "id": s.id,
        "idx": s.idx,
        "process_stage_name": s.process_stage_name,
        "description": s.description,
        "process_group1": s.process_group1,
        "process_group2": s.process_group2,
        "key_process": s.key_process,
        "process_stage_state": s.process_stage_state,
    }


def _cap_dict(c: models.ProcessCapability) -> dict:
    return {
        "id": c.id,
        "process_capability_name": c.process_capability_name,
        "description": c.description,
        "process_capability_state": c.process_capability_state,
    }


def _recipe_dict(r: models.Recipe) -> dict:
    return {
        "id": r.id,
        "process_capability_name": r.process_capability_name,
        "recipe_name": r.recipe_name,
        "description": r.description,
        "object_owner": r.object_owner,
        "recipe_state": r.recipe_state,
        "effective_time": r.effective_time,
        "expir_alarm_id": r.expir_alarm_id,
    }


def _eqtype_dict(e: models.EquipmentType) -> dict:
    return {
        "id": e.id,
        "equipment_type_name": e.equipment_type_name,
        "description": e.description,
        "process_type1": e.process_type1,
        "process_type2": e.process_type2,
        "construct_type1": e.construct_type1,
        "construct_type2": e.construct_type2,
        "process_capacity": e.process_capacity,
        "process_job_count_min": e.process_job_count_min,
        "process_job_count_max": e.process_job_count_max,
        "batch_capacity": e.batch_capacity,
        "dummy_unmount_flag": e.dummy_unmount_flag,
        "equipment_type_state": e.equipment_type_state,
    }


def _eqcap_dict(c: models.EquipmentCapability) -> dict:
    return {
        "id": c.id,
        "equipment_type_name": c.equipment_type_name,
        "process_capability_name": c.process_capability_name,
        "assign_flag": c.assign_flag,
        "equipment_capability_state": c.equipment_capability_state,
    }
