from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import require_permission
from ..schemas import (
    AttributeTemplatePayload,
    AttributeTemplateUpdatePayload,
    CategoryTemplatePayload,
    CategoryTemplateUpdatePayload,
    CodingRulePayload,
    CodingRuleUpdatePayload,
    DictionaryItemPayload,
    DictionaryItemUpdatePayload,
    LifecycleStatePayload,
    LifecycleStateUpdatePayload,
    LifecycleTemplatePayload,
    LifecycleTemplateUpdatePayload,
    SystemParameterPayload,
    SystemParameterUpdatePayload,
)
from ..serializers import (
    serialize_category_template,
    serialize_coding_rule,
    serialize_dictionary_item,
    serialize_lifecycle_template,
)
from ..services.helpers import commit_or_409, update_model


router = APIRouter()


@router.get("/api/admin/foundation/coding-rules")
def coding_rules(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.CodingRule)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.CodingRule.code.ilike(kw) | models.CodingRule.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.CodingRule.object_type, models.CodingRule.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_coding_rule(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/admin/foundation/coding-rules", status_code=201)
def create_coding_rule(payload: CodingRulePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = models.CodingRule(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Coding rule code already exists")
    db.refresh(row)
    return serialize_coding_rule(row)


@router.put("/api/admin/foundation/coding-rules/{rule_id}")
def update_coding_rule(rule_id: int, payload: CodingRuleUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.CodingRule).filter(models.CodingRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Coding rule not found")
    update_model(row, payload)
    commit_or_409(db, "Coding rule code already exists")
    db.refresh(row)
    return serialize_coding_rule(row)


@router.delete("/api/admin/foundation/coding-rules/{rule_id}")
def delete_coding_rule(rule_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.CodingRule).filter(models.CodingRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Coding rule not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@router.get("/api/admin/foundation/categories")
def category_templates(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.CategoryTemplate).options(selectinload(models.CategoryTemplate.attributes))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.CategoryTemplate.code.ilike(kw) | models.CategoryTemplate.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.CategoryTemplate.object_type, models.CategoryTemplate.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_category_template(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/admin/foundation/categories", status_code=201)
def create_category_template(payload: CategoryTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = models.CategoryTemplate(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Category code already exists")
    db.refresh(row)
    return serialize_category_template(row)


@router.put("/api/admin/foundation/categories/{category_id}")
def update_category_template(category_id: int, payload: CategoryTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = (
        db.query(models.CategoryTemplate)
        .options(selectinload(models.CategoryTemplate.attributes))
        .filter(models.CategoryTemplate.id == category_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Category not found")
    update_model(row, payload)
    commit_or_409(db, "Category code already exists")
    db.refresh(row)
    return serialize_category_template(row)


@router.delete("/api/admin/foundation/categories/{category_id}")
def delete_category_template(category_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.CategoryTemplate).filter(models.CategoryTemplate.id == category_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@router.post("/api/admin/foundation/categories/{category_id}/attributes", status_code=201)
def create_attribute_template(category_id: int, payload: AttributeTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    if not db.query(models.CategoryTemplate.id).filter(models.CategoryTemplate.id == category_id).first():
        raise HTTPException(status_code=404, detail="Category not found")
    row = models.AttributeTemplate(category_id=category_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "field_key": row.field_key, "data_type": row.data_type, "required": row.required, "dictionary_code": row.dictionary_code, "default_value": row.default_value, "sequence": row.sequence}


@router.put("/api/admin/foundation/attributes/{attribute_id}")
def update_attribute_template(attribute_id: int, payload: AttributeTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.AttributeTemplate).filter(models.AttributeTemplate.id == attribute_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Attribute not found")
    update_model(row, payload)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "field_key": row.field_key, "data_type": row.data_type, "required": row.required, "dictionary_code": row.dictionary_code, "default_value": row.default_value, "sequence": row.sequence}


@router.delete("/api/admin/foundation/attributes/{attribute_id}")
def delete_attribute_template(attribute_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.AttributeTemplate).filter(models.AttributeTemplate.id == attribute_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Attribute not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@router.get("/api/admin/foundation/lifecycles")
def lifecycle_templates(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.LifecycleTemplate).options(selectinload(models.LifecycleTemplate.states))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.LifecycleTemplate.code.ilike(kw) | models.LifecycleTemplate.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.LifecycleTemplate.object_type, models.LifecycleTemplate.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_lifecycle_template(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/admin/foundation/lifecycles", status_code=201)
def create_lifecycle_template(payload: LifecycleTemplatePayload, db: Session = Depends(get_db)) -> dict:
    row = models.LifecycleTemplate(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Lifecycle code already exists")
    db.refresh(row)
    return serialize_lifecycle_template(row)


@router.put("/api/admin/foundation/lifecycles/{template_id}")
def update_lifecycle_template(template_id: int, payload: LifecycleTemplateUpdatePayload, db: Session = Depends(get_db)) -> dict:
    row = (
        db.query(models.LifecycleTemplate)
        .options(selectinload(models.LifecycleTemplate.states))
        .filter(models.LifecycleTemplate.id == template_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle not found")
    update_model(row, payload)
    commit_or_409(db, "Lifecycle code already exists")
    db.refresh(row)
    return serialize_lifecycle_template(row)


@router.delete("/api/admin/foundation/lifecycles/{template_id}")
def delete_lifecycle_template(template_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.LifecycleTemplate).filter(models.LifecycleTemplate.id == template_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@router.post("/api/admin/foundation/lifecycles/{template_id}/states", status_code=201)
def create_lifecycle_state(template_id: int, payload: LifecycleStatePayload, db: Session = Depends(get_db)) -> dict:
    if not db.query(models.LifecycleTemplate.id).filter(models.LifecycleTemplate.id == template_id).first():
        raise HTTPException(status_code=404, detail="Lifecycle not found")
    row = models.LifecycleState(template_id=template_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "sequence": row.sequence, "name": row.name, "state_type": row.state_type, "allow_edit": row.allow_edit, "require_workflow": row.require_workflow, "next_states": row.next_states}


@router.put("/api/admin/foundation/lifecycle-states/{state_id}")
def update_lifecycle_state(state_id: int, payload: LifecycleStateUpdatePayload, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.LifecycleState).filter(models.LifecycleState.id == state_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle state not found")
    update_model(row, payload)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "sequence": row.sequence, "name": row.name, "state_type": row.state_type, "allow_edit": row.allow_edit, "require_workflow": row.require_workflow, "next_states": row.next_states}


@router.delete("/api/admin/foundation/lifecycle-states/{state_id}")
def delete_lifecycle_state(state_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.LifecycleState).filter(models.LifecycleState.id == state_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lifecycle state not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@router.get("/api/admin/foundation/dictionaries")
def dictionary_items(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.DictionaryItem)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            models.DictionaryItem.dict_code.ilike(kw)
            | models.DictionaryItem.dict_name.ilike(kw)
            | models.DictionaryItem.item_value.ilike(kw)
            | models.DictionaryItem.item_label.ilike(kw)
        )
    total = q.count()
    rows = q.order_by(models.DictionaryItem.dict_code, models.DictionaryItem.sequence, models.DictionaryItem.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize_dictionary_item(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/api/admin/foundation/dictionaries", status_code=201)
def create_dictionary_item(payload: DictionaryItemPayload, db: Session = Depends(get_db)) -> dict:
    row = models.DictionaryItem(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return serialize_dictionary_item(row)


@router.put("/api/admin/foundation/dictionaries/{item_id}")
def update_dictionary_item(item_id: int, payload: DictionaryItemUpdatePayload, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.DictionaryItem).filter(models.DictionaryItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Dictionary item not found")
    update_model(row, payload)
    db.commit()
    db.refresh(row)
    return serialize_dictionary_item(row)


@router.delete("/api/admin/foundation/dictionaries/{item_id}")
def delete_dictionary_item(item_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.query(models.DictionaryItem).filter(models.DictionaryItem.id == item_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Dictionary item not found")
    db.delete(row)
    db.commit()
    return {"deleted": True}

@router.get("/api/admin/foundation/system-parameters")
def system_parameters(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.SystemParameter)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            models.SystemParameter.param_key.ilike(kw)
            | models.SystemParameter.param_value.ilike(kw)
            | models.SystemParameter.param_group.ilike(kw)
            | models.SystemParameter.description.ilike(kw)
        )
    total = q.count()
    rows = q.order_by(models.SystemParameter.param_group, models.SystemParameter.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": row.id, "param_key": row.param_key, "param_value": row.param_value, "param_group": row.param_group, "description": row.description}
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/admin/foundation/system-parameters", status_code=201)
def create_system_parameter(payload: SystemParameterPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = models.SystemParameter(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "System parameter key already exists")
    db.refresh(row)
    return {"id": row.id, "param_key": row.param_key, "param_value": row.param_value, "param_group": row.param_group, "description": row.description}


@router.put("/api/admin/foundation/system-parameters/{param_id}")
def update_system_parameter(param_id: int, payload: SystemParameterUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.SystemParameter).filter(models.SystemParameter.id == param_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="System parameter not found")
    update_model(row, payload)
    commit_or_409(db, "System parameter key already exists")
    db.refresh(row)
    return {"id": row.id, "param_key": row.param_key, "param_value": row.param_value, "param_group": row.param_group, "description": row.description}


@router.delete("/api/admin/foundation/system-parameters/{param_id}")
def delete_system_parameter(param_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("system"))) -> dict:
    row = db.query(models.SystemParameter).filter(models.SystemParameter.id == param_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="System parameter not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
