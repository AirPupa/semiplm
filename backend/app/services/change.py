"""工程变更影响分析与 ECA 执行动作：影响分析、版本升版、动作校验、关闭联动。"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import selectinload, Session

from .. import models
from .helpers import today_text
from .integration import create_integration_job
from .process import validate_process_route_ready
from .versioning import (
    next_revision,
    next_unique_bom_version,
    next_unique_document_no,
    next_unique_process_version,
    next_unique_route_no,
)


def analyze_change_impacts(db: Session, change: models.Change) -> None:
    """对新建变更自动生成影响条目与 ECA 执行动作草稿。"""
    existing_impacts = db.query(models.ChangeImpact).filter(models.ChangeImpact.change_id == change.id).count()
    existing_actions = db.query(models.ChangeAction).filter(models.ChangeAction.change_id == change.id).count()
    if existing_impacts or existing_actions:
        return

    product = change.product or db.query(models.Product).filter(models.Product.id == change.product_id).first()
    product_model = product.model if product else ""
    boms = (
        db.query(models.BomHeader)
        .filter(models.BomHeader.product_id == change.product_id)
        .order_by(models.BomHeader.bom_type, models.BomHeader.version.desc())
        .all()
    )
    routes = (
        db.query(models.ProcessRoute)
        .filter(models.ProcessRoute.product_id == change.product_id)
        .order_by(models.ProcessRoute.version.desc())
        .all()
    )
    documents = (
        db.query(models.Document)
        .filter(models.Document.product_id == change.product_id)
        .order_by(models.Document.category, models.Document.version.desc())
        .all()
    )

    impacts: list[tuple[str, str, str, str]] = [("产品", product_model, "中", "确认型号主数据、生命周期和版本基线是否需要更新。")]
    impacts.extend((f"{bom.bom_type} BOM", f"{bom.bom_type}-{product_model}-{bom.version}", "高", "评估物料结构、用量、替代料和有效期。") for bom in boms[:4])
    impacts.extend(("工艺路线", route.route_no, "高", "评估工序、工艺参数、站点控制和 MES 下发内容。") for route in routes[:3])
    impacts.extend(("文档", f"{doc.doc_no} / {doc.title}", "中", "评估规格书、流程卡、检验规范和文控发布。") for doc in documents[:4])
    for impact_type, target, risk, action in impacts:
        db.add(models.ChangeImpact(change_id=change.id, impact_type=impact_type, target=target, risk=risk, action=action))

    action_defs: list[dict] = []
    if boms:
        bom = boms[0]
        action_defs.append({
            "action_type": "BOM升版",
            "target_type": "BOM",
            "target_id": bom.id,
            "target_version": bom.version,
            "target_object": f"{bom.bom_type}-{product_model}-{bom.version}",
            "effectivity_type": "日期+批次",
            "effectivity_scope": "版本升版",
            "effective_date": today_text(),
            "effective_batch": f"LOT-{product_model}-2606",
            "department": "生产部",
            "owner": change.owner or "罗富森",
            "result": "根据影响分析生成下一版 BOM 草稿并维护有效期。",
        })
    if routes:
        route = routes[0]
        action_defs.append({
            "action_type": "工艺更新",
            "target_type": "工艺路线",
            "target_id": route.id,
            "target_version": route.version,
            "target_object": route.route_no,
            "effectivity_type": "日期+批次",
            "effectivity_scope": "工艺切换",
            "effective_date": today_text(),
            "effective_batch": f"LOT-{product_model}-2606",
            "department": "生产部",
            "owner": "罗富森",
            "result": "更新工艺路线、工序参数和站点控制。",
        })
    if documents:
        document = documents[0]
        action_defs.append({
            "action_type": "文档发布",
            "target_type": "文档",
            "target_id": document.id,
            "target_version": document.version,
            "target_object": f"{document.doc_no} / {document.title}",
            "effectivity_type": "日期",
            "effectivity_scope": "文档升版",
            "effective_date": today_text(),
            "effective_batch": "",
            "department": "生产部",
            "owner": "于帅兵",
            "result": "生成受影响文档下一版草稿并完成文控发布准备。",
        })
    action_defs.append({
        "action_type": "ECN通知",
        "target_type": "通知",
        "target_id": None,
        "target_version": "",
        "target_object": f"{change.change_no} 变更通知",
        "effectivity_type": "批次",
        "effectivity_scope": "签收跟踪",
        "effective_date": "",
        "effective_batch": f"LOT-{product_model}-2606",
        "department": "生产部",
        "owner": change.owner or "房磊",
        "result": "通知受影响部门并跟踪签收结果。",
    })
    for index, action_data in enumerate(action_defs, start=1):
        db.add(models.ChangeAction(
            change_id=change.id,
            action_no=f"ECA-{change.change_no}-{index:02d}",
            action_type=action_data["action_type"],
            target_type=action_data["target_type"],
            target_id=action_data["target_id"],
            target_version=action_data["target_version"],
            target_object=action_data["target_object"],
            effectivity_type=action_data["effectivity_type"],
            effectivity_scope=action_data["effectivity_scope"],
            effective_date=action_data["effective_date"],
            effective_batch=action_data["effective_batch"],
            department=action_data["department"],
            owner=action_data["owner"],
            status="待处理",
            due_date=today_text(),
            result=action_data["result"],
        ))


def create_change_release_jobs(db: Session, change: models.Change) -> None:
    """变更关闭时向 ERP/MES 写入 ECN 同步任务，并联动回收受影响文档。"""
    existing_targets = {
        row.target_system
        for row in db.query(models.IntegrationJob)
        .filter(models.IntegrationJob.object_type == "ECN", models.IntegrationJob.object_no == change.change_no)
        .all()
    }
    if "ERP" not in existing_targets:
        create_integration_job(db, "ERP", "ECN", change.change_no, change.product.model, change.change_no, "工程变更执行完成，等待同步 ERP 物料/BOM 变更通知。")
    if "MES" not in existing_targets:
        create_integration_job(db, "MES", "ECN", change.change_no, change.product.model, change.change_no, "工程变更执行完成，等待同步 MES 工艺和制造切换要求。")
    # 联动文档：对已升版的源文档（旧版已发布）创建回收发放记录
    trigger_document_recall_for_change(db, change)


def trigger_document_recall_for_change(db: Session, change: models.Change) -> list[dict]:
    """变更关闭时，遍历所有 target_type=文档 的 ECA 动作，对源文档（被升版的旧版）
    自动创建"回收"发放记录，使旧版文档按变更生效规则回收。返回创建的回收记录摘要。"""
    recalled: list[dict] = []
    actions = (
        db.query(models.ChangeAction)
        .filter(
            models.ChangeAction.change_id == change.id,
            models.ChangeAction.target_type == "文档",
            models.ChangeAction.target_id.isnot(None),
        )
        .all()
    )
    for action in actions:
        source_doc = db.query(models.Document).filter(models.Document.id == action.target_id).first()
        if not source_doc or source_doc.status != "已发布":
            continue
        # 检查是否已为该文档创建过该变更的回收记录，避免重复
        existing = (
            db.query(models.DocumentDistribution)
            .filter(
                models.DocumentDistribution.document_id == source_doc.id,
                models.DocumentDistribution.status == "已回收",
                models.DocumentDistribution.recall_reason.like(f"%{change.change_no}%"),
            )
            .first()
        )
        if existing:
            continue
        dist = models.DocumentDistribution(
            document_id=source_doc.id,
            doc_no=source_doc.doc_no,
            title=source_doc.title,
            version=source_doc.version,
            recipient_type="角色",
            recipient="文控/生产/质量",
            status="已回收",
            distributed_by="系统",
            distributed_at=source_doc.updated_at or source_doc.release_date or today_text(),
            recalled_by=action.owner or change.owner or "系统",
            recalled_at=today_text(),
            recall_reason=f"{change.change_no} 变更升版回收，新版本 {action.generated_object_no or '待发布'} 生效后旧版回收",
        )
        db.add(dist)
        recalled.append({
            "document_id": source_doc.id,
            "doc_no": source_doc.doc_no,
            "version": source_doc.version,
            "new_version_no": action.generated_object_no or "",
        })
    return recalled


def trigger_document_distribution_on_publish(db: Session, document: models.Document) -> list[str]:
    """文档发布时，若该文档由 ECA 变更动作生成，按变更通知单的接收人列表
    自动创建"已发放"记录。返回已发放的接收人列表。"""
    action = (
        db.query(models.ChangeAction)
        .filter(
            models.ChangeAction.target_type == "文档",
            models.ChangeAction.generated_object_no == document.doc_no,
        )
        .first()
    )
    if not action:
        return []
    change = db.query(models.Change).filter(models.Change.id == action.change_id).first()
    if not change:
        return []
    # 解析变更通知单的接收人列表（逗号分隔）
    notification_list = (change.notification_list or "").strip()
    if not notification_list:
        return []
    recipients = [r.strip() for r in notification_list.replace("，", ",").split(",") if r.strip()]
    distributed: list[str] = []
    for recipient in recipients:
        existing = (
            db.query(models.DocumentDistribution)
            .filter(
                models.DocumentDistribution.document_id == document.id,
                models.DocumentDistribution.recipient == recipient,
                models.DocumentDistribution.status == "已发放",
            )
            .first()
        )
        if existing:
            continue
        db.add(models.DocumentDistribution(
            document_id=document.id,
            doc_no=document.doc_no,
            title=document.title,
            version=document.version,
            recipient_type="人员",
            recipient=recipient,
            status="已发放",
            distributed_by=f"系统({change.change_no})",
            distributed_at=today_text(),
        ))
        distributed.append(recipient)
    return distributed


def validate_action_effectivity(action: models.ChangeAction) -> None:
    effectivity_type = action.effectivity_type or "日期"
    if "日期" in effectivity_type and not action.effective_date:
        raise HTTPException(status_code=409, detail="Date-based ECA action requires effective date")
    if "批次" in effectivity_type and not action.effective_batch:
        raise HTTPException(status_code=409, detail="Batch-based ECA action requires effective batch")
    if action.effective_date:
        try:
            date.fromisoformat(action.effective_date)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail="Effective date must use YYYY-MM-DD") from exc


def validate_change_action_target(db: Session, action: models.ChangeAction) -> None:
    validate_action_effectivity(action)
    if action.target_type in {"BOM", "文档", "工艺路线"} and not action.target_id:
        raise HTTPException(status_code=409, detail="Revision ECA action requires target object")

    if action.target_type == "BOM" and action.target_id:
        source = (
            db.query(models.BomHeader)
            .options(selectinload(models.BomHeader.items))
            .filter(models.BomHeader.id == action.target_id)
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="Target BOM not found")
        if action.target_version and action.target_version != source.version:
            raise HTTPException(status_code=409, detail="ECA target version does not match current BOM version")
        if source.status != "已发布":
            raise HTTPException(status_code=409, detail="Only released BOM can be revised by ECA")
        if not source.items:
            raise HTTPException(status_code=409, detail="Target BOM has no items")
        return

    if action.target_type == "文档" and action.target_id:
        source = db.query(models.Document).filter(models.Document.id == action.target_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Target document not found")
        if action.target_version and action.target_version != source.version:
            raise HTTPException(status_code=409, detail="ECA target version does not match current document version")
        if source.status == "已废止":
            raise HTTPException(status_code=409, detail="Obsolete document cannot be revised by ECA")
        return

    if action.target_type == "工艺路线" and action.target_id:
        source = (
            db.query(models.ProcessRoute)
            .options(selectinload(models.ProcessRoute.steps))
            .filter(models.ProcessRoute.id == action.target_id)
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="Target process route not found")
        if action.target_version and action.target_version != source.version:
            raise HTTPException(status_code=409, detail="ECA target version does not match current process route version")
        if source.status not in {"已发布", "有效"}:
            raise HTTPException(status_code=409, detail="Only released process route can be revised by ECA")
        validate_process_route_ready(source)


def get_eca_generated_object_gate(db: Session, object_type: str, generated_object_no: str) -> dict | None:
    """查询 ECA 生成对象的提交发布门禁状态。"""
    action = (
        db.query(models.ChangeAction)
        .filter(
            models.ChangeAction.target_type == object_type,
            models.ChangeAction.generated_object_no == generated_object_no,
        )
        .first()
    )
    if not action:
        return None
    change = db.query(models.Change).filter(models.Change.id == action.change_id).first()
    if action.status != "已完成":
        return {
            "ready": False,
            "action_no": action.action_no,
            "action_status": action.status,
            "change_no": change.change_no if change else "",
            "change_status": change.status if change else "",
            "message": f"ECA 动作 {action.action_no} 尚未关闭，生成对象不能提交发布。",
        }
    if change and change.status != "已关闭":
        return {
            "ready": False,
            "action_no": action.action_no,
            "action_status": action.status,
            "change_no": change.change_no,
            "change_status": change.status,
            "message": f"变更单 {change.change_no} 尚未关闭，需等待全部 ECA 动作完成后再提交发布生成对象。",
        }
    return {
        "ready": True,
        "action_no": action.action_no,
        "action_status": action.status,
        "change_no": change.change_no if change else "",
        "change_status": change.status if change else "",
        "message": "生成对象已满足提交发布条件。",
    }


def validate_eca_generated_object_ready(db: Session, object_type: str, object_id: int, generated_object_no: str) -> None:
    """校验 ECA 生成的对象草稿在提交/发布前已完成整张变更闭环。"""
    gate = get_eca_generated_object_gate(db, object_type, generated_object_no)
    if gate and not gate["ready"]:
        raise HTTPException(
            status_code=409,
            detail=gate["message"],
        )


def apply_change_action_revision(db: Session, action: models.ChangeAction) -> str:
    """执行 ECA 动作：为目标 BOM/文档/工艺路线生成下一版草稿。"""
    if action.generated_object_no:
        return action.generated_object_no

    validate_change_action_target(db, action)
    effective_date = action.effective_date or today_text()
    if action.target_type == "BOM" and action.target_id:
        source = db.query(models.BomHeader).options(selectinload(models.BomHeader.items), selectinload(models.BomHeader.product)).filter(models.BomHeader.id == action.target_id).first()
        if not source:
            return ""
        new_version = next_unique_bom_version(db, source)
        new_bom = models.BomHeader(
            product_id=source.product_id,
            bom_type=source.bom_type,
            version=new_version,
            status="编制中",
            owner=action.owner or source.owner,
            release_date="",
            source_bom_id=source.id,
            effective_date=effective_date,
            expiry_date="",
            effectivity_type=action.effectivity_type or "变更生效",
            effective_batch=action.effective_batch or "",
        )
        db.add(new_bom)
        db.flush()
        item_id_map: dict[int, int] = {}
        for source_item in sorted(source.items, key=lambda item: item.id):
            new_item = models.BomItem(
                bom_id=new_bom.id,
                parent_id=item_id_map.get(source_item.parent_id),
                material_code=source_item.material_code,
                material_name=source_item.material_name,
                category=source_item.category,
                specification=source_item.specification,
                quantity=source_item.quantity,
                unit=source_item.unit,
                position=source_item.position,
                process_step_id=source_item.process_step_id,
                process_step=source_item.process_step,
                substitute=source_item.substitute,
                status=source_item.status,
                effective_date=source_item.effective_date or effective_date,
                expiry_date=source_item.expiry_date,
                effectivity_note=source_item.effectivity_note or action.effective_batch,
            )
            db.add(new_item)
            db.flush()
            item_id_map[source_item.id] = new_item.id
        product_model = source.product.model if source.product else str(source.product_id)
        action.generated_object_no = f"{source.bom_type}-{product_model}-{new_version}"
        action.target_version = source.version
        return action.generated_object_no

    if action.target_type == "文档" and action.target_id:
        source = db.query(models.Document).filter(models.Document.id == action.target_id).first()
        if not source:
            return ""
        new_version = next_revision(source.version)
        new_doc_no = next_unique_document_no(db, source, new_version)
        db.add(models.Document(
            product_id=source.product_id,
            doc_no=new_doc_no,
            title=source.title,
            category=source.category,
            version=new_version,
            status="编制中",
            owner=action.owner or source.owner,
            approval_status="未提交",
            updated_at=effective_date,
        ))
        db.flush()
        action.generated_object_no = new_doc_no
        action.target_version = source.version
        return action.generated_object_no

    if action.target_type == "工艺路线" and action.target_id:
        source = (
            db.query(models.ProcessRoute)
            .options(selectinload(models.ProcessRoute.steps), selectinload(models.ProcessRoute.product))
            .filter(models.ProcessRoute.id == action.target_id)
            .first()
        )
        if not source:
            return ""
        new_version = next_unique_process_version(db, source)
        new_route_no = next_unique_route_no(db, source, new_version)
        new_route = models.ProcessRoute(
            product_id=source.product_id,
            route_no=new_route_no,
            name=source.name,
            version=new_version,
            status="编制中",
            owner=action.owner or source.owner,
            release_date="",
            source_route_id=source.id,
            effective_batch=action.effective_batch or "",
        )
        db.add(new_route)
        db.flush()
        for source_step in sorted(source.steps, key=lambda item: item.sequence):
            db.add(models.ProcessStep(
                route_id=new_route.id,
                sequence=source_step.sequence,
                stage=source_step.stage,
                operation=source_step.operation,
                key_params=source_step.key_params,
                owner=action.owner or source_step.owner,
                status=source_step.status,
            ))
        db.flush()
        action.generated_object_no = new_route_no
        action.target_version = source.version
        return action.generated_object_no

    return ""


def close_change_when_actions_done(db: Session, change_id: int, acted_by: str) -> bool:
    """所有 ECA 动作完成后关闭变更，写入 ERP/MES 同步任务并补流程日志。"""
    # 延迟导入避免与 services.workflow 形成循环依赖
    from .workflow import add_workflow_log

    change = db.query(models.Change).options(selectinload(models.Change.product)).filter(models.Change.id == change_id).first()
    if not change or change.status == "已关闭":
        return False
    actions = db.query(models.ChangeAction).filter(models.ChangeAction.change_id == change_id).all()
    if not actions or any(action.status != "已完成" for action in actions):
        return False
    change.status = "已关闭"
    create_change_release_jobs(db, change)
    instance = (
        db.query(models.WorkflowInstance)
        .filter(models.WorkflowInstance.object_type == "变更", models.WorkflowInstance.object_id == change_id)
        .order_by(models.WorkflowInstance.id.desc())
        .first()
    )
    if instance:
        add_workflow_log(db, instance.id, None, "变更关闭", acted_by, "全部 ECA 执行动作已关闭", "执行中", "已关闭")
    return True
