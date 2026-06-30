"""所有对象序列化函数：ORM 模型 -> API 响应字典。

供 routers/ 在返回响应时调用。BOM/工艺路线/变更等复杂对象
的序列化依赖关联关系加载。
"""
from sqlalchemy.orm import Session

from . import models
from .services.versioning import is_current_effective_bom


def serialize_product(product: models.Product) -> dict:
    return {
        "id": product.id,
        "code": product.code,
        "model": product.model,
        "name": product.name,
        "product_type": product.product_type,
        "process_platform": product.process_platform,
        "wafer_size": product.wafer_size,
        "package_type": product.package_type,
        "temperature_grade": product.temperature_grade,
        "quality_grade": product.quality_grade,
        "application": product.application,
        "lifecycle": product.lifecycle,
        "owner": product.owner,
        "customer_part_no": product.customer_part_no,
        "internal_part_no": product.internal_part_no,
        "version": product.version,
        "readiness": product.readiness,
        "latest_release": product.latest_release,
    }


def serialize_bom_item(item: models.BomItem) -> dict:
    return {
        "id": item.id,
        "parent_id": item.parent_id,
        "material_code": item.material_code,
        "material_name": item.material_name,
        "category": item.category,
        "specification": item.specification,
        "quantity": item.quantity,
        "unit": item.unit,
        "position": item.position,
        "process_step_id": item.process_step_id,
        "process_step": item.process_step,
        "substitute": item.substitute,
        "status": item.status,
        "effective_date": item.effective_date,
        "expiry_date": item.expiry_date,
        "effectivity_note": item.effectivity_note,
    }


def serialize_bom(row: models.BomHeader) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "product_model": row.product.model,
        "product_name": row.product.name,
        "bom_type": row.bom_type,
        "type": row.bom_type,
        "version": row.version,
        "status": row.status,
        "owner": row.owner,
        "release_date": row.release_date,
        "source_bom_id": row.source_bom_id,
        "effective_date": row.effective_date,
        "expiry_date": row.expiry_date,
        "effectivity_type": row.effectivity_type,
        "is_current": is_current_effective_bom(row),
        "effective_batch": row.effective_batch,
        "items": [serialize_bom_item(item) for item in sorted(row.items, key=lambda item: item.id)],
    }


def bom_item_compare_key(item: models.BomItem) -> tuple[str, str, str]:
    return (item.material_code, item.process_step or "", item.position or "")


def serialize_bom_compare_item(kind: str, item: models.BomItem | None, base: models.BomItem | None = None) -> dict:
    active = item or base
    assert active is not None
    return {
        "change_type": kind,
        "material_code": active.material_code,
        "material_name": active.material_name,
        "process_step": active.process_step,
        "from_quantity": base.quantity if base else None,
        "to_quantity": item.quantity if item else None,
        "from_status": base.status if base else "",
        "to_status": item.status if item else "",
        "from_effective_date": base.effective_date if base else "",
        "to_effective_date": item.effective_date if item else "",
    }


def serialize_process_route(row: models.ProcessRoute) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "route_no": row.route_no,
        "name": row.name,
        "product_model": row.product.model,
        "version": row.version,
        "status": row.status,
        "owner": row.owner,
        "release_date": row.release_date,
        "source_route_id": row.source_route_id,
        "effective_batch": row.effective_batch,
        "steps": [
            {
                "id": step.id,
                "sequence": step.sequence,
                "stage": step.stage,
                "operation": step.operation,
                "key_params": step.key_params,
                "owner": step.owner,
                "status": step.status,
            }
            for step in sorted(row.steps, key=lambda item: item.sequence)
        ],
    }


def serialize_integration_job(row: models.IntegrationJob) -> dict:
    return {
        "id": row.id,
        "job_no": row.job_no,
        "target_system": row.target_system,
        "object_type": row.object_type,
        "object_no": row.object_no,
        "product_model": row.product_model,
        "direction": row.direction,
        "status": row.status,
        "triggered_by": row.triggered_by,
        "triggered_at": row.triggered_at,
        "message": row.message,
        "attempt_count": row.attempt_count,
        "last_sync_at": row.last_sync_at,
        "response_message": row.response_message,
        "external_id": row.external_id,
    }


def serialize_change_action(row: models.ChangeAction) -> dict:
    return {
        "id": row.id,
        "action_no": row.action_no,
        "action_type": row.action_type,
        "target_type": row.target_type,
        "target_id": row.target_id,
        "target_version": row.target_version,
        "target_object": row.target_object,
        "effectivity_type": row.effectivity_type,
        "effectivity_scope": row.effectivity_scope,
        "effective_date": row.effective_date,
        "effective_batch": row.effective_batch,
        "generated_object_no": row.generated_object_no,
        "department": row.department,
        "owner": row.owner,
        "status": row.status,
        "due_date": row.due_date,
        "result": row.result,
    }


def serialize_change(row: models.Change, db: Session) -> dict:
    return {
        "id": row.id,
        "product_id": row.product_id,
        "change_no": row.change_no,
        "product_model": row.product.model if row.product else "",
        "change_type": row.change_type,
        "reason": row.reason,
        "status": row.status,
        "priority": row.priority,
        "owner": row.owner,
        "submitted_at": row.submitted_at,
        "before_desc": row.before_desc,
        "after_desc": row.after_desc,
        "implementation_plan": row.implementation_plan,
        "notification_list": row.notification_list,
        "impacts": [{"id": impact.id, "type": impact.impact_type, "impact_type": impact.impact_type, "target": impact.target, "risk": impact.risk, "action": impact.action} for impact in row.impacts],
        "approvals": [{"step": approval.step_name, "approver": approval.approver, "status": approval.status, "comment": approval.comment, "approved_at": approval.approved_at} for approval in row.approvals],
        "actions": [
            serialize_change_action(action)
            for action in db.query(models.ChangeAction).filter(models.ChangeAction.change_id == row.id).order_by(models.ChangeAction.id).all()
        ],
    }


def serialize_workflow_instance(row: models.WorkflowInstance) -> dict:
    return {
        "id": row.id,
        "template_id": row.template_id,
        "template_name": row.template.name if row.template else "",
        "object_type": row.object_type,
        "object_id": row.object_id,
        "object_no": row.object_no,
        "title": row.title,
        "product_model": row.product_model,
        "status": row.status,
        "started_by": row.started_by,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "tasks": [
            {
                "id": task.id,
                "sequence": task.sequence,
                "node_name": task.node_name,
                "role_name": task.role_name,
                "action_type": task.action_type,
                "status": task.status,
                "assignee": task.assignee,
                "acted_by": task.acted_by,
                "acted_at": task.acted_at,
                "comment": task.comment,
                "sla_hours": task.sla_hours,
            }
            for task in sorted(row.tasks, key=lambda item: item.sequence)
        ],
        "logs": [
            {
                "id": log.id,
                "task_id": log.task_id,
                "action": log.action,
                "actor": log.actor,
                "acted_at": log.acted_at,
                "comment": log.comment,
                "from_status": log.from_status,
                "to_status": log.to_status,
            }
            for log in sorted(getattr(row, "logs", []), key=lambda item: item.id)
        ],
    }


def serialize_coding_rule(row: models.CodingRule) -> dict:
    return {
        "id": row.id,
        "object_type": row.object_type,
        "code": row.code,
        "name": row.name,
        "prefix": row.prefix,
        "pattern": row.pattern,
        "current_no": row.current_no,
        "sample": row.sample,
        "status": row.status,
        "owner": row.owner,
    }


def serialize_category_template(row: models.CategoryTemplate) -> dict:
    return {
        "id": row.id,
        "object_type": row.object_type,
        "code": row.code,
        "name": row.name,
        "parent_code": row.parent_code,
        "lifecycle_template": row.lifecycle_template,
        "coding_rule": row.coding_rule,
        "status": row.status,
        "description": row.description,
        "attributes": [
            {
                "id": item.id,
                "name": item.name,
                "field_key": item.field_key,
                "data_type": item.data_type,
                "required": item.required,
                "dictionary_code": item.dictionary_code,
                "default_value": item.default_value,
                "sequence": item.sequence,
            }
            for item in sorted(row.attributes, key=lambda attr: attr.sequence)
        ],
    }


def serialize_lifecycle_template(row: models.LifecycleTemplate) -> dict:
    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "object_type": row.object_type,
        "status": row.status,
        "description": row.description,
        "states": [
            {
                "id": item.id,
                "sequence": item.sequence,
                "name": item.name,
                "state_type": item.state_type,
                "allow_edit": item.allow_edit,
                "require_workflow": item.require_workflow,
                "next_states": item.next_states,
            }
            for item in sorted(row.states, key=lambda state: state.sequence)
        ],
    }


def serialize_dictionary_item(row: models.DictionaryItem) -> dict:
    return {
        "id": row.id,
        "dict_code": row.dict_code,
        "dict_name": row.dict_name,
        "item_value": row.item_value,
        "item_label": row.item_label,
        "object_scope": row.object_scope,
        "sequence": row.sequence,
        "status": row.status,
    }
