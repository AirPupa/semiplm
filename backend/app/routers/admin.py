from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import require_permission
from ..schemas import (
    IntegrationEndpointPayload,
    IntegrationEndpointUpdatePayload,
    OrganizationPayload,
    OrganizationUpdatePayload,
    RolePayload,
    RoleUpdatePayload,
    UserPayload,
    UserUpdatePayload,
    WorkflowNodePayload,
    WorkflowNodeUpdatePayload,
    WorkflowTemplatePayload,
    WorkflowTemplateUpdatePayload,
)
from ..services.helpers import commit_or_409, update_model, user_dict


router = APIRouter()


@router.get("/api/admin/roles")
def roles(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Role)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Role.code.ilike(kw) | models.Role.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.Role.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": row.id, "code": row.code, "name": row.name, "description": row.description, "permissions": row.permissions, "status": row.status}
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/api/admin/organizations")
def organizations(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.Organization)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.Organization.code.ilike(kw) | models.Organization.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.Organization.org_type, models.Organization.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {"id": row.id, "code": row.code, "name": row.name, "org_type": row.org_type, "parent_code": row.parent_code, "manager": row.manager, "status": row.status, "description": row.description}
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/admin/organizations", status_code=201)
def create_organization(payload: OrganizationPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("organization"))) -> dict:
    row = models.Organization(**payload.model_dump())
    db.add(row)
    commit_or_409(db, "Organization code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code, "name": row.name, "org_type": row.org_type, "parent_code": row.parent_code, "manager": row.manager, "status": row.status, "description": row.description}


@router.put("/api/admin/organizations/{org_id}")
def update_organization(org_id: int, payload: OrganizationUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("organization"))) -> dict:
    row = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    update_model(row, payload)
    commit_or_409(db, "Organization code already exists")
    db.refresh(row)
    return {"id": row.id, "code": row.code, "name": row.name, "org_type": row.org_type, "parent_code": row.parent_code, "manager": row.manager, "status": row.status, "description": row.description}


@router.delete("/api/admin/organizations/{org_id}")
def delete_organization(org_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("organization"))) -> dict:
    row = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Organization not found")
    if row.code in {"NZGD", "PROD"}:
        raise HTTPException(status_code=409, detail="Built-in single organization cannot be deleted")
    db.delete(row)
    db.commit()
    return {"deleted": True}


@router.post("/api/admin/roles", status_code=201)
def create_role(payload: RolePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("role"))) -> dict:
    role = models.Role(**payload.model_dump())
    db.add(role)
    commit_or_409(db, "Role code already exists")
    db.refresh(role)
    return {"id": role.id, "code": role.code, "name": role.name, "description": role.description, "permissions": role.permissions, "status": role.status}


@router.put("/api/admin/roles/{role_id}")
def update_role(role_id: int, payload: RoleUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("role"))) -> dict:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    update_model(role, payload)
    commit_or_409(db, "Role code already exists")
    db.refresh(role)
    return {"id": role.id, "code": role.code, "name": role.name, "description": role.description, "permissions": role.permissions, "status": role.status}


@router.delete("/api/admin/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("role"))) -> dict:
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if db.query(models.User).filter(models.User.role == role.name).count():
        raise HTTPException(status_code=409, detail="Role is used by users")
    db.delete(role)
    db.commit()
    return {"deleted": True}

@router.get("/api/admin/users")
def users(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.User)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            models.User.username.ilike(kw)
            | models.User.display_name.ilike(kw)
            | models.User.role.ilike(kw)
        )
    total = q.count()
    rows = q.order_by(models.User.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            user_dict(row)
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/admin/users", status_code=201)
def create_user(payload: UserPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("user"))) -> dict:
    user = models.User(**payload.model_dump())
    db.add(user)
    commit_or_409(db, "Username already exists")
    db.refresh(user)
    return user_dict(user)


@router.put("/api/admin/users/{user_id}")
def update_user(user_id: int, payload: UserUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("user"))) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_model(user, payload)
    commit_or_409(db, "Username already exists")
    db.refresh(user)
    return user_dict(user)


@router.delete("/api/admin/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("user"))) -> dict:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.username == "admin":
        raise HTTPException(status_code=409, detail="Built-in admin cannot be deleted")
    db.delete(user)
    db.commit()
    return {"deleted": True}


@router.get("/api/admin/workflows")
def workflow_templates(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.WorkflowTemplate).options(selectinload(models.WorkflowTemplate.nodes))
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.WorkflowTemplate.code.ilike(kw) | models.WorkflowTemplate.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.WorkflowTemplate.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "object_type": row.object_type,
                "project_type": row.project_type,
                "status": row.status,
                "description": row.description,
                "nodes": [
                    {"id": node.id, "sequence": node.sequence, "name": node.name, "role_name": node.role_name, "action_type": node.action_type, "sla_hours": node.sla_hours}
                    for node in sorted(row.nodes, key=lambda item: item.sequence)
                ],
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/admin/workflows", status_code=201)
def create_workflow_template(payload: WorkflowTemplatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    template = models.WorkflowTemplate(**payload.model_dump())
    db.add(template)
    commit_or_409(db, "Workflow code already exists")
    db.refresh(template)
    return {"id": template.id, "code": template.code, "name": template.name, "object_type": template.object_type, "project_type": template.project_type, "status": template.status, "description": template.description, "nodes": []}


@router.put("/api/admin/workflows/{workflow_id}")
def update_workflow_template(workflow_id: int, payload: WorkflowTemplateUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    template = db.query(models.WorkflowTemplate).filter(models.WorkflowTemplate.id == workflow_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Workflow not found")
    update_model(template, payload)
    commit_or_409(db, "Workflow code already exists")
    db.refresh(template)
    return {"id": template.id, "code": template.code, "name": template.name, "object_type": template.object_type, "project_type": template.project_type, "status": template.status, "description": template.description}


@router.delete("/api/admin/workflows/{workflow_id}")
def delete_workflow_template(workflow_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    template = db.query(models.WorkflowTemplate).filter(models.WorkflowTemplate.id == workflow_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db.delete(template)
    db.commit()
    return {"deleted": True}


@router.post("/api/admin/workflows/{workflow_id}/nodes", status_code=201)
def create_workflow_node(workflow_id: int, payload: WorkflowNodePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    if not db.query(models.WorkflowTemplate.id).filter(models.WorkflowTemplate.id == workflow_id).first():
        raise HTTPException(status_code=404, detail="Workflow not found")
    node = models.WorkflowNode(template_id=workflow_id, **payload.model_dump())
    db.add(node)
    db.commit()
    db.refresh(node)
    return {"id": node.id, "sequence": node.sequence, "name": node.name, "role_name": node.role_name, "action_type": node.action_type, "sla_hours": node.sla_hours}


@router.put("/api/admin/workflow-nodes/{node_id}")
def update_workflow_node(node_id: int, payload: WorkflowNodeUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    node = db.query(models.WorkflowNode).filter(models.WorkflowNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Workflow node not found")
    update_model(node, payload)
    db.commit()
    db.refresh(node)
    return {"id": node.id, "sequence": node.sequence, "name": node.name, "role_name": node.role_name, "action_type": node.action_type, "sla_hours": node.sla_hours}


@router.delete("/api/admin/workflow-nodes/{node_id}")
def delete_workflow_node(node_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("workflow"))) -> dict:
    node = db.query(models.WorkflowNode).filter(models.WorkflowNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Workflow node not found")
    db.delete(node)
    db.commit()
    return {"deleted": True}


@router.get("/api/admin/integration-endpoints")
def integration_endpoints(page: int = 1, page_size: int = 20, keyword: str = "", db: Session = Depends(get_db)) -> dict:
    q = db.query(models.IntegrationEndpoint)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.IntegrationEndpoint.code.ilike(kw) | models.IntegrationEndpoint.name.ilike(kw))
    total = q.count()
    rows = q.order_by(models.IntegrationEndpoint.id).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "system_type": row.system_type,
                "base_url": row.base_url,
                "auth_type": row.auth_type,
                "direction": row.direction,
                "status": row.status,
                "owner": row.owner,
                "object_scope": row.object_scope,
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/admin/integration-endpoints", status_code=201)
def create_integration_endpoint(payload: IntegrationEndpointPayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    endpoint = models.IntegrationEndpoint(**payload.model_dump())
    db.add(endpoint)
    commit_or_409(db, "Endpoint code already exists")
    db.refresh(endpoint)
    return {"id": endpoint.id, "code": endpoint.code, "name": endpoint.name, "system_type": endpoint.system_type, "base_url": endpoint.base_url, "auth_type": endpoint.auth_type, "direction": endpoint.direction, "status": endpoint.status, "owner": endpoint.owner, "object_scope": endpoint.object_scope}


@router.put("/api/admin/integration-endpoints/{endpoint_id}")
def update_integration_endpoint(endpoint_id: int, payload: IntegrationEndpointUpdatePayload, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    endpoint = db.query(models.IntegrationEndpoint).filter(models.IntegrationEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    update_model(endpoint, payload)
    commit_or_409(db, "Endpoint code already exists")
    db.refresh(endpoint)
    return {"id": endpoint.id, "code": endpoint.code, "name": endpoint.name, "system_type": endpoint.system_type, "base_url": endpoint.base_url, "auth_type": endpoint.auth_type, "direction": endpoint.direction, "status": endpoint.status, "owner": endpoint.owner, "object_scope": endpoint.object_scope}


@router.delete("/api/admin/integration-endpoints/{endpoint_id}")
def delete_integration_endpoint(endpoint_id: int, db: Session = Depends(get_db), _: dict = Depends(require_permission("integration"))) -> dict:
    endpoint = db.query(models.IntegrationEndpoint).filter(models.IntegrationEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    db.delete(endpoint)
    db.commit()
    return {"deleted": True}
