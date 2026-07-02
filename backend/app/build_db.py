"""Build SemiPLM SQLite data products from MES discovery snapshots.

The MES crawler output under ``mes_discovery/`` is the source of truth for
ProductDef, process modeling, BOM, equipment, recipe, and dictionary seed data.
PLM-only demo data is added only for collaboration modules that do not exist in
MES: documents, projects, quality issues, workflow tasks, and integration jobs.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from . import models
from .database import Base
from .services.bootstrap import ensure_admin


ROOT = Path(__file__).resolve().parents[2]
MES_DIR = ROOT / "mes_discovery"


def _read_json(name: str) -> dict[str, Any]:
    path = MES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"MES discovery file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _objects() -> dict[str, Any]:
    return _read_json("mes_full_model_seed.json")["objects"]


def _rows(objects: dict[str, Any], object_name: str) -> list[dict[str, Any]]:
    obj = objects.get(object_name) or {}
    rows = obj.get("rows") or []
    return rows if isinstance(rows, list) else []


def _items(module: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(module, dict):
        return []
    rows = module.get("items") or module.get("rows") or []
    return rows if isinstance(rows, list) else []


def _s(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value)
    return default if text.lower() in {"none", "null", "nan"} else text


def _i(value: Any) -> int | None:
    try:
        return None if value in (None, "") else int(float(value))
    except (TypeError, ValueError):
        return None


def _f(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _yn(value: Any) -> bool:
    return str(value).upper() in {"Y", "YES", "TRUE", "1"}


def build_clean(db: Session) -> None:
    _clear_all(db)
    ensure_admin(db)
    _seed_mes_dictionaries(db)
    _seed_system_parameters(db)
    db.commit()


def build_demo(db: Session) -> None:
    build_clean(db)
    objects = _objects()
    product_detail = _read_json("mes_product_detail_deep_dive.json")
    bom_detail = _read_json("mes_bom_deep_dive.json")

    _seed_demo_users(db)
    _seed_mes_materials_from_bom(db, bom_detail)
    _seed_mes_process_library(db, objects)
    flows = _seed_mes_process_flows(db, objects, product_detail)
    boms = _seed_mes_boms(db, bom_detail)
    products = _seed_mes_products(db, objects, flows, boms)

    changes = _seed_plm_documents_changes(db, products)
    _seed_plm_quality(db, products)
    _seed_plm_requirements(db, products)
    _seed_plm_projects(db, products, boms)
    _seed_plm_workflow(db, products, changes, boms)
    _seed_plm_integration(db, products, changes)
    _seed_plm_problem_reports(db, products)
    db.commit()


def _clear_all(db: Session) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


def _seed_mes_dictionaries(db: Session) -> None:
    seed = _read_json("mes_dictionary_seed.json")
    entries = seed.get("entries") or []
    if not entries:
        # Some snapshots are already grouped by dict code.
        for dict_code, rows in (seed.get("dicts") or {}).items():
            for seq, row in enumerate(rows, start=1):
                db.add(models.DictionaryItem(
                    dict_code=dict_code,
                    dict_name=dict_code,
                    item_value=_s(row.get("item_value") or row.get("value")),
                    item_label=_s(row.get("item_label") or row.get("label") or row.get("value")),
                    object_scope=_s(row.get("object_scope")),
                    sequence=seq,
                    status="启用",
                ))
    else:
        for seq, row in enumerate(entries, start=1):
            db.add(models.DictionaryItem(
                dict_code=_s(row.get("dict_code") or row.get("dictCode")),
                dict_name=_s(row.get("dict_name") or row.get("dictName") or row.get("dict_code") or row.get("dictCode")),
                item_value=_s(row.get("item_value") or row.get("itemValue") or row.get("value")),
                item_label=_s(row.get("item_label") or row.get("itemLabel") or row.get("label") or row.get("value")),
                object_scope=_s(row.get("object_scope") or row.get("objectScope")),
                sequence=_i(row.get("sequence")) or seq,
                status=_s(row.get("status"), "启用"),
            ))

    # UI-specific dictionaries used by PLM screens.
    extras = {
        "DICT_INTEGRATION_SYSTEM": [("ERP", "ERP"), ("MES", "MES"), ("QMS", "QMS")],
        "DICT_INTEGRATION_STATUS": [("等待", "等待"), ("处理中", "处理中"), ("失败", "失败"), ("成功", "成功")],
        "DICT_PRIORITY": [("高", "高"), ("中", "中"), ("低", "低")],
        "DICT_SEVERITY": [("高", "高"), ("中", "中"), ("低", "低")],
        "DICT_PROJECT_PHASE": [("设计", "设计"), ("流片", "流片"), ("验证", "验证"), ("试产", "试产"), ("量产导入", "量产导入")],
    }
    existing = {(r.dict_code, r.item_value) for r in db.query(models.DictionaryItem).all()}
    for dict_code, rows in extras.items():
        for seq, (value, label) in enumerate(rows, start=1):
            if (dict_code, value) not in existing:
                db.add(models.DictionaryItem(dict_code=dict_code, dict_name=dict_code, item_value=value, item_label=label, sequence=seq, status="启用"))


def _seed_system_parameters(db: Session) -> None:
    rows = [
        ("MES_GATEWAY_URL", "http://mes-gateway.local/api", "MES 同步", "模拟 MES 网关地址"),
        ("MES_SYNC_TIMEOUT", "30", "MES 同步", "接口超时时间（秒）"),
        ("MES_SYNC_RETRY", "3", "MES 同步", "失败重试次数"),
    ]
    for key, value, group, desc in rows:
        db.add(models.SystemParameter(param_key=key, param_value=value, param_group=group, description=desc))
    db.add(models.Organization(code="PLM-RD", name="研发制造中心", org_type="部门", manager="caijian.qu", status="启用", description="承接 MES 主数据建模的 PLM 协同组织"))
    for code, name, obj_type in [
        ("WF-DOC-REL", "文档发布流程", "Document"),
        ("WF-BOM-REL", "BOM 发布流程", "BOM"),
        ("WF-ECR-ECN", "变更闭环流程", "Change"),
    ]:
        db.add(models.WorkflowTemplate(code=code, name=name, object_type=obj_type, status="启用", description=f"{name}演示模板"))
    db.add(models.ProjectTemplate(code="TPL-NPI", name="NPI 项目模板", description="半导体芯片 NPI 阶段门模板", stages='["设计","流片","验证","试产","量产导入"]', status="启用"))


def _seed_demo_users(db: Session) -> None:
    for username, display_name, role in [
        ("caijian.qu", "屈才健", "工艺工程师"),
        ("luofusen", "罗富森", "工艺工程师"),
        ("yushuaibing", "于帅兵", "工艺工程师"),
        ("fanglei", "房磊", "项目经理"),
        ("lichao", "李超", "质量工程师"),
    ]:
        db.add(models.User(username=username, display_name=display_name, role=role, department="生产部"))


def _seed_mes_materials_from_bom(db: Session, bom_detail: dict[str, Any]) -> None:
    seen: set[str] = set()
    for bom in bom_detail.get("boms", []):
        for section_name, section in (bom.get("materialSections") or {}).items():
            for item in _items(section):
                name = _s(item.get("materialDefName"))
                if not name or name in seen:
                    continue
                seen.add(name)
                db.add(models.Material(
                    consumable_def_name=name,
                    description=_s(item.get("materialDefDescription"), name),
                    fab_product_name=_s(bom.get("bomName")),
                    consumable_type=_s(item.get("materialType"), section_name),
                    primary_unit_name=_s(item.get("unit"), "EA"),
                    primary_unit_code=_s(item.get("unit"), "EA"),
                    unit_name=_s(item.get("unit"), "EA"),
                    unit=_s(item.get("unit"), "EA"),
                    unit_conversion_rate="1",
                    material_standard_qty=_i(item.get("requireQuantity")) or 1,
                    spec=f"MES BOM material from {_s(bom.get('bomName'))}",
                    supplier="MES",
                    risk_level="中",
                    lifecycle="有效",
                ))


def _seed_mes_process_library(db: Session, objects: dict[str, Any]) -> None:
    for row in _rows(objects, "ProcessCapability"):
        db.add(models.ProcessCapability(
            process_capability_name=_s(row.get("processCapabilityName")),
            description=_s(row.get("description")),
            process_capability_state=_s(row.get("processCapabilityState"), "Valid"),
        ))

    for row in _rows(objects, "Recipe"):
        db.add(models.Recipe(
            process_capability_name=_s(row.get("processCapabilityName")),
            recipe_name=_s(row.get("recipeName")),
            description=_s(row.get("description")),
            object_owner=_s(row.get("objectOwner")),
            recipe_state=_s(row.get("recipeState"), "Valid"),
            effective_time=_i(row.get("effectiveTime")),
            expir_alarm_id=_s(row.get("expirAlarmId")),
        ))

    for row in _rows(objects, "ProcessStage"):
        db.add(models.ProcessStage(
            idx=_i(row.get("idx")),
            process_stage_name=_s(row.get("processStageName")),
            description=_s(row.get("description")),
            process_group1=_s(row.get("processGroup1")),
            process_group2=_s(row.get("processGroup2")),
            key_process=_s(row.get("keyProcess")),
            process_stage_state=_s(row.get("processStageState"), "Valid"),
        ))

    for row in _rows(objects, "ProcessStep"):
        db.add(models.ProcessStep(
            process_step_name=_s(row.get("processStepName")),
            process_step_version=_s(row.get("processStepVersion"), "001"),
            description=_s(row.get("description")),
            process_step_state=_s(row.get("processStepState"), "Active"),
            process_step_type=_s(row.get("processStepType"), "Process"),
            process_stage_name=_s(row.get("processStageName")),
            process_group1=_s(row.get("processGroup1")),
            process_group2=_s(row.get("processGroup2")),
            key_process=_s(row.get("keyProcess")),
            bank_name=_s(row.get("bankName")),
            process_capability_name=_s(row.get("processCapabilityName")),
            recipe_name="",
            is_skip_allowed=_yn(row.get("isSkipAllowed")),
            is_mandatory_step=_yn(row.get("isMandatoryStep")),
            sampling_user_group=_s(row.get("samplingUserGroup")),
            owner_group_name=_s(row.get("ownerGroupName")),
            owner=_s(row.get("owner")),
            cost_center_stage=_s(row.get("costCenterStage")),
            is_deleted=_yn(row.get("isDeleted")),
            is_flip=_yn(row.get("isFlip")),
            detail_process_step_type=_s(row.get("detailProcessStepType"), "Normal"),
        ))

    equipment_types: dict[str, models.EquipmentType] = {}
    for row in _rows(objects, "EquipmentType"):
        name = _s(row.get("equipmentTypeName"))
        et = models.EquipmentType(
            equipment_type_name=name,
            description=_s(row.get("description")),
            process_type1=_s(row.get("processType1"), "Production"),
            process_type2=_s(row.get("processType2"), "Process"),
            construct_type1=_s(row.get("constructType1"), "Main"),
            construct_type2=_s(row.get("constructType2"), "Normal"),
            process_capacity=_i(row.get("processCapacity")),
            process_job_count_min=_i(row.get("processJobCountMin")),
            process_job_count_max=_i(row.get("processJobCountMax")),
            batch_capacity=_i(row.get("batchCapacity")),
            dummy_unmount_flag=_yn(row.get("dummyUnmountFlag")),
            equipment_type_state=_s(row.get("equipmentTypeState"), "Valid"),
        )
        db.add(et)
        db.flush()
        equipment_types[name] = et

    for row in _rows(objects, "EquipmentCapability"):
        cap = _s(row.get("processCapabilityName"))
        # MES row is equipment instance based. PLM maps to equipment type when possible.
        eq_type_name = cap if cap in equipment_types else _s(row.get("equipmentName"))
        if eq_type_name not in equipment_types:
            et = models.EquipmentType(equipment_type_name=eq_type_name, description=_s(row.get("equipmentDescription")), process_type1="Production", process_type2="Process", equipment_type_state="Valid")
            db.add(et)
            db.flush()
            equipment_types[eq_type_name] = et
        db.add(models.EquipmentCapability(
            equipment_type_id=equipment_types[eq_type_name].id,
            equipment_type_name=eq_type_name,
            process_capability_name=cap,
            assign_flag=not (str(row.get("assignFlag")).upper() in {"N", "FALSE", "0"}),
            equipment_capability_state=_s(row.get("equipmentCapabilityState"), "Valid"),
        ))


def _seed_mes_process_flows(db: Session, objects: dict[str, Any], product_detail: dict[str, Any]) -> dict[str, models.ProcessFlow]:
    flow_meta = {row.get("processFlowName"): row for row in _rows(objects, "ProcessFlow")}
    flows: dict[str, models.ProcessFlow] = {}
    seeded_flow_names: set[str] = set()

    for product in product_detail.get("products", []):
        flow_name = _s(product.get("processFlowName"))
        if not flow_name or flow_name in seeded_flow_names:
            continue
        seq_rows = _items((product.get("modules") or {}).get("Seq"))
        actual_version = _s(seq_rows[0].get("processFlowVersion") if seq_rows else product.get("processFlowVersion"), "001")
        meta = flow_meta.get(flow_name, {})
        flow = models.ProcessFlow(
            process_flow_name=flow_name,
            process_flow_version=actual_version,
            description=_s(meta.get("description"), f"MES flow for {flow_name}"),
            process_flow_type1=_s(meta.get("processFlowType1"), "Main"),
            process_flow_type2=_s(meta.get("processFlowType2"), "Production"),
            process_flow_state=_s(meta.get("processFlowState"), "Active"),
            owner_group_name=_s(meta.get("ownerGroupName")),
            owner=_s(meta.get("owner"), _s(product.get("owner"), "caijian.qu")),
            process_group_name=_s(meta.get("processGroupName")),
            is_deleted=_yn(meta.get("isDeleted")),
        )
        db.add(flow)
        db.flush()
        flows[flow_name] = flow
        seeded_flow_names.add(flow_name)

        for row in seq_rows:
            db.add(models.ProcessFlowSeq(
                flow_id=flow.id,
                idx=_i(row.get("idx")),
                step_source=_s(row.get("stepSource"), "Flow"),
                process_flow_seq_name=_s(row.get("processFlowSeqName")),
                process_flow_name=flow_name,
                process_flow_version=actual_version,
                process_name=_s(row.get("processName")),
                process_version=_s(row.get("processVersion")),
                process_flow_seq_type=_s(row.get("processFlowSeqType"), "ProcessStep"),
                process_group1=_s(row.get("processGroup1")),
                process_group2=_s(row.get("processGroup2")),
                process_stage_name=_s(row.get("processStageName")),
                work_layer=_s(row.get("workLayer")),
            ))

        for row in _items((product.get("modules") or {}).get("Content")):
            db.add(models.ProcessFlowContent(
                flow_id=flow.id,
                process_flow_seq_name=_s(row.get("processFlowSeqName")),
                process_flow_name=flow_name,
                process_flow_version=actual_version,
                process_capability_name=_s(row.get("processCapabilityName")),
                recipe_name=_s(row.get("recipeName")),
                recipe_name_description=_s(row.get("recipeNameDescription")),
                dc_spec_name=_s(row.get("dcSpecName")),
                yield_limit=_s(row.get("yieldLimit")),
                reticle_group_name=_s(row.get("reticleGroupName")),
                reticle_name=_s(row.get("reticleName")),
                probe_card_name=_s(row.get("probeCardName")),
                lot_sampling_rule=_s(row.get("lotSamplingRule")),
                is_skip_allowed=_yn(row.get("isSkipAllowed")),
                is_mandatory_step=_yn(row.get("isMandatoryStep")),
                sampling_user_group=_s(row.get("samplingUserGroup")),
                is_flip=_yn(row.get("isFlip")),
                branch_flow_group=_s(row.get("branchFlowGroup")),
                branch_flow_name=_s(row.get("branchFlowName")),
                rework_flow_group=_s(row.get("reworkFlowGroup")),
                rework_flow_name=_s(row.get("reworkFlowName")),
                wafer_selection_rule=_s(row.get("waferSelectionRule")),
                ink_able=_s(row.get("inkAble")),
            ))

        for row in _items((product.get("modules") or {}).get("Measure")):
            db.add(models.ProcessFlowMeasure(
                flow_id=flow.id,
                process_flow_name=flow_name,
                process_flow_version=actual_version,
                process_flow_seq_name=_s(row.get("processFlowSeqName")),
                key_process_flow_seq_name=_s(row.get("keyProcessFlowSeqName")),
                measure_item=_s(row.get("measureItem")),
                target=_f(row.get("target")),
                lower_spec_limit=_f(row.get("lowerSpecLimit")),
                upper_spec_limit=_f(row.get("upperSpecLimit")),
                sample_count=_i(row.get("sampleCount")),
                sample_slots=_s(row.get("sampleSlots")),
                sample_count_type=_s(row.get("sampleCountType")),
            ))

        for row in _items((product.get("modules") or {}).get("Contamination")):
            db.add(models.ProcessFlowContamination(
                flow_id=flow.id,
                process_flow_name=flow_name,
                process_flow_version=actual_version,
                process_flow_seq_name=_s(row.get("processFlowSeqName")),
                require_contamination_levels=_s(row.get("requireContaminationLevels")),
                affect_contamination_level=_s(row.get("affectContaminationLevel")),
            ))

    return flows


def _seed_mes_boms(db: Session, bom_detail: dict[str, Any]) -> dict[str, models.BomHeader]:
    boms: dict[str, models.BomHeader] = {}
    for row in bom_detail.get("boms", []):
        bom = models.BomHeader(
            bom_name=_s(row.get("bomName")),
            bom_version=_s(row.get("bomVersion"), "001"),
            bom_state=_s(row.get("bomState"), "Active"),
            description=_s((row.get("one") or {}).get("description")),
            owner=_s(row.get("owner"), "caijian.qu"),
        )
        db.add(bom)
        db.flush()
        boms[bom.bom_name] = bom
        for section_name, section in (row.get("materialSections") or {}).items():
            for item in _items(section):
                db.add(models.BomItem(
                    bom_id=bom.id,
                    idx=_i(item.get("idx")),
                    bom_name=bom.bom_name,
                    bom_version=bom.bom_version,
                    material_type=_s(item.get("materialType"), section_name),
                    material_def_name=_s(item.get("materialDefName")),
                    material_def_version=_s(item.get("materialDefVersion")),
                    require_quantity=_f(item.get("requireQuantity")),
                    unit=_s(item.get("unit"), "EA"),
                    process_step_name=_s(item.get("processStepName")),
                    process_step_version=_s(item.get("processStepVersion")),
                ))
    return boms


def _seed_mes_products(db: Session, objects: dict[str, Any], flows: dict[str, models.ProcessFlow], boms: dict[str, models.BomHeader]) -> list[models.Product]:
    products: list[models.Product] = []
    for row in _rows(objects, "ProductDef"):
        flow_name = _s(row.get("processFlowName"))
        bom_name = _s(row.get("bomName"))
        flow = flows.get(flow_name)
        bom = boms.get(bom_name)
        product = models.Product(
            product_def_name=_s(row.get("productDefName")),
            product_def_version=_s(row.get("productDefVersion"), "001"),
            description=_s(row.get("description"), _s(row.get("productDefName"))),
            product_def_state=_s(row.get("productDefState"), "Active"),
            product_type=_s(row.get("productType")),
            production_type=_s(row.get("productionType")),
            product_group_name=_s(row.get("productGroupName")),
            process_flow_name=flow_name,
            process_flow_version=flow.process_flow_version if flow else _s(row.get("processFlowVersion"), "001"),
            bom_name=bom_name,
            bom_version=bom.bom_version if bom else _s(row.get("bomVersion"), "001"),
            reticle_set_name=_s(row.get("reticleSetName")),
            gross_die=_i(row.get("grossDie")),
            start_bank_name=_s(row.get("startBankName")),
            end_bank_name=_s(row.get("endBankName")),
            owner=_s(row.get("owner"), "caijian.qu"),
            max_use_count=_i(row.get("maxUseCount")),
            max_recycle_count=_i(row.get("maxRecycleCount")),
            owner_group_name=_s(row.get("ownerGroupName")),
            dummy_max_use_time=_i(row.get("dummyMaxUseTime")),
            dummy_thk_param=_s(row.get("dummyThkParam")),
            dummy_thk_limit=_f(row.get("dummyThkLimit")),
            is_deleted=_yn(row.get("isDeleted")),
            bin_name=_s(row.get("binName")),
            package_qty=_i(row.get("packageQty")),
            product_usage=_s(row.get("productUsage")),
        )
        db.add(product)
        products.append(product)
    db.flush()
    for product in products:
        db.add(models.ProductVersion(product_id=product.id, version=product.product_def_version, lifecycle=product.product_def_state, readiness=product.readiness, released_at="2026-06-01", released_by=product.owner, source_change_no=f"MES-{product.product_def_name}", summary="MES ProductDef 初始化版本"))
    return products


def _seed_plm_documents_changes(db: Session, products: list[models.Product]) -> dict[int, list[models.Change]]:
    changes: dict[int, list[models.Change]] = {}
    for product in products:
        for code, title, status, approval in [
            ("SPEC", "产品规格书", "已发布", "已签核"),
            ("PROC", "工艺流程卡", "审批中", "流转中"),
            ("REL", "可靠性报告", "审批中", "流转中"),
        ]:
            db.add(models.Document(product_id=product.id, doc_no=f"DOC-{product.product_def_name}-{code}", title=f"{product.product_def_name} {title}", category="工艺文件" if code == "PROC" else "产品规格", version=product.product_def_version, status=status, owner=product.owner, approval_status=approval, updated_at="2026-06-20", file_name=f"{code}.pdf", file_path="", file_size=2048, file_type="application/pdf"))

        rows: list[models.Change] = []
        for idx, status in enumerate(["审批中", "执行中", "已关闭"], start=1):
            change = models.Change(product_id=product.id, change_no=f"ECR-{product.product_def_name}-{idx:03d}", title=f"{product.product_def_name} MES 初始化后工艺窗口优化", change_type="工艺", reason="MES 主数据初始化后补齐 PLM 变更闭环演示。", status=status, priority="高" if idx == 1 else "中", owner=product.owner, submitted_at=f"2026-06-{10+idx}", before_desc="MES 当前版本。", after_desc="PLM 受控变更后同步 MES。", implementation_plan="完成影响分析、审批、ECN 发布和同步包生成。", notification_list="PE,QE,PM")
            db.add(change)
            db.flush()
            db.add(models.ChangeImpact(change_id=change.id, impact_type="工艺流程", target=product.process_flow_name, risk="中", action="同步评估"))
            db.add(models.Approval(change_id=change.id, step_name="工艺会签", approver="caijian.qu", status="已通过" if status != "审批中" else "待处理", approved_at="2026-06-15" if status != "审批中" else ""))
            db.add(models.ChangeAction(change_id=change.id, action_no=f"ECA-{product.product_def_name}-{idx:03d}", action_type="同步", target_type="ProcessFlow", target_version=product.process_flow_version, target_object=product.process_flow_name, effectivity_type="日期", effective_date="2026-07-01", department="工艺工程", owner=product.owner, status="已完成" if status == "已关闭" else "进行中", due_date="2026-07-05", result="等待 ECN 闭环后同步"))
            rows.append(change)
        changes[product.id] = rows
    return changes


def _seed_plm_quality(db: Session, products: list[models.Product]) -> None:
    for pidx, product in enumerate(products, start=1):
        for day in range(1, 7):
            db.add(models.QualityLot(product_id=product.id, lot_no=f"LOT-{product.product_def_name}-{day:02d}", wafer_id=f"W{day:02d}", stage="CP", cp_yield=91.5 + day + pidx * 0.2, ft_yield=89.5 + day + pidx * 0.2, bin1_rate=88 + day, issue_count=1 if day % 4 == 0 else 0, status="正常" if day % 4 else "异常跟进", tested_at=f"2026-06-{day+10:02d}"))
        db.add(models.QualityIssue(issue_no=f"QI-{product.product_def_name}-001", product_model=product.product_def_name, lot_no=f"LOT-{product.product_def_name}-04", title=f"{product.product_def_name} 良率波动", severity="高" if pidx == 1 else "中", status="处理中", owner="李超", root_cause="关键工艺窗口偏窄。", corrective_action="调整工艺窗口并增加 SPC 监控。"))
        db.add(models.QualityCAPA(capa_no=f"CAPA-{product.product_def_name}-001", title=f"{product.product_def_name} 良率 CAPA", root_cause="关键工艺窗口偏窄。", corrective_action="更新工艺窗口。", preventive_action="增加阶段门质量复核。", owner="李超", status="执行中", due_date="2026-07-10"))
        db.add(models.QualityReport(report_no=f"QR-{product.product_def_name}-001", title=f"{product.product_def_name} 可靠性归档报告", report_type="可靠性", product_model=product.product_def_name, summary="可靠性阶段性归档。", owner="李超", status="已归档", archived_at="2026-06-28", archived_by="李超"))


def _seed_plm_requirements(db: Session, products: list[models.Product]) -> None:
    for product in products:
        db.add(models.Requirement(product_id=product.id, req_no=f"REQ-{product.product_def_name}-001", source="客户规格", category="性能", title=f"{product.product_def_name} 光电性能指标", priority="高", status="已确认", owner=product.owner, acceptance_criteria="CP/FT 关键指标满足规格书。"))


def _seed_plm_projects(db: Session, products: list[models.Product], boms: dict[str, models.BomHeader]) -> None:
    phases = ["试产", "量产导入", "验证"]
    for idx, product in enumerate(products, start=1):
        project = models.Project(project_no=f"NPI-2026-{60+idx:03d}", name=f"{product.product_def_name} MES 数据导入验证", product_model=product.product_def_name, phase=phases[(idx - 1) % len(phases)], progress=35 + idx * 15, owner="房磊", start_date="2026-05-01", end_date="2026-08-30", risk_level="高" if idx == 1 else "中")
        db.add(project)
        db.flush()
        for tidx, status in enumerate(["已完成", "进行中", "待处理"], start=1):
            db.add(models.ProjectTask(project_id=project.id, name=f"{product.product_def_name} 阶段门任务 {tidx}", phase=project.phase, owner=product.owner if tidx < 3 else "李超", status=status, due_date=f"2026-07-{tidx+idx:02d}", start_date="2026-06-01"))
        db.add(models.ProjectDeliverable(project_id=project.id, name=f"{product.product_def_name} BOM 齐套", deliverable_type="设计文件", phase=project.phase, owner=product.owner, status="进行中", due_date="2026-07-15", object_type="BOM", object_id=boms.get(product.bom_name).id if product.bom_name in boms else None))
        db.add(models.ProjectRisk(project_id=project.id, risk_type="数据风险", description="MES 反向导入后需校验 PLM 字段映射。", impact="中", probability="中", severity=project.risk_level, owner=product.owner, status="跟进中", mitigation="抽样核对产品、流程、BOM 三类对象。"))


def _seed_plm_workflow(db: Session, products: list[models.Product], changes: dict[int, list[models.Change]], boms: dict[str, models.BomHeader]) -> None:
    templates = {tpl.code: tpl for tpl in db.query(models.WorkflowTemplate).all()}
    for idx, product in enumerate(products, start=1):
        tpl = templates["WF-ECR-ECN"] if idx % 2 else templates["WF-BOM-REL"]
        obj_type = "变更" if idx % 2 else "BOM"
        object_id = changes[product.id][0].id if obj_type == "变更" else boms[product.bom_name].id
        object_no = changes[product.id][0].change_no if obj_type == "变更" else product.bom_name
        inst = models.WorkflowInstance(template_id=tpl.id, object_type=obj_type, object_id=object_id, object_no=object_no, title=f"{object_no} 审批", product_model=product.product_def_name, status="运行中", started_by=product.owner, started_at="2026-06-20")
        db.add(inst)
        db.flush()
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=1, node_name="提交", role_name="研发工程师", action_type="提交", status="已完成", assignee=product.owner, acted_by=product.owner, acted_at="2026-06-20", comment="已提交", sla_hours=8))
        db.add(models.WorkflowTask(instance_id=inst.id, sequence=2, node_name="会签", role_name="工艺工程师", action_type="审批", status="待处理", assignee="caijian.qu", sla_hours=24))


def _seed_plm_integration(db: Session, products: list[models.Product], changes: dict[int, list[models.Change]]) -> None:
    status_cycle = ["等待", "处理中", "失败", "成功"]
    for pidx, product in enumerate(products, start=1):
        for idx, system in enumerate(["ERP", "MES", "QMS"], start=1):
            status = status_cycle[(pidx + idx) % len(status_cycle)]
            object_type = "BOM" if system == "ERP" else "ProcessFlow" if system == "MES" else "Document"
            object_no = product.bom_name if system == "ERP" else product.process_flow_name if system == "MES" else f"DOC-{product.product_def_name}-REL"
            db.add(models.IntegrationJob(job_no=f"INT-{product.product_def_name}-{idx:02d}", target_system=system, object_type=object_type, object_no=object_no, product_model=product.product_def_name, direction="下发", status=status, triggered_by=changes[product.id][0].change_no, triggered_at="2026-06-25", message=f"{system} 同步任务由 ECN 闭环触发。", attempt_count=1 if status != "等待" else 0, last_sync_at="2026-06-26" if status != "等待" else "", response_message="同步成功" if status == "成功" else "接口校验失败" if status == "失败" else "", external_id=f"{system}-{pidx:03d}" if status == "成功" else ""))
            if system == "MES":
                pkg = models.MesSyncPackage(package_no=f"MSP-{product.product_def_name}-{idx:02d}", change_no=changes[product.id][0].change_no, target_system="MES", status=status, triggered_by="admin", triggered_at="2026-06-25", response_message="模拟同步包")
                db.add(pkg)
                db.flush()
                db.add(models.MesSyncItem(package_id=pkg.id, object_type="ProcessFlow", object_no=product.process_flow_name, object_version=product.process_flow_version, action="upsert", status=status, request_summary="同步工艺流程主数据"))


def _seed_plm_problem_reports(db: Session, products: list[models.Product]) -> None:
    for idx, product in enumerate(products, start=1):
        db.add(models.ProblemReport(pr_no=f"PR-2026-{idx:03d}", title=f"{product.product_def_name} 工艺异常反馈", problem_type="工艺问题", severity="高" if idx == 1 else "中", source="内部", product_id=product.id, product_model=product.product_def_name, description="试产批次关键指标波动，需要工程分析。", suggested_action="发起 ECR 并追加验证批。", status="评估中" if idx != 2 else "已关闭", reporter="李超", reported_at=f"2026-06-{15+idx:02d}", related_change_no=f"ECR-{product.product_def_name}-001"))


def _build_to_file(target: str, build_fn) -> str:
    db_path = Path.cwd() / target
    if db_path.exists():
        db_path.unlink()
    tmp_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=tmp_engine)
    tmp_session = sessionmaker(autocommit=False, autoflush=False, bind=tmp_engine)
    db = tmp_session()
    try:
        build_fn(db)
    finally:
        db.close()
        tmp_engine.dispose()
    print(f"[OK] {target} built ({os.path.getsize(db_path) // 1024} KB)")
    return str(db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="SemiPLM database builder")
    parser.add_argument("--clean", action="store_true", help="Build semiplm_clean.db")
    parser.add_argument("--demo", action="store_true", help="Build semiplm_demo.db")
    parser.add_argument("--all", action="store_true", help="Build both database files")
    args = parser.parse_args()

    if not (args.clean or args.demo or args.all):
        parser.print_help()
        return

    if args.clean or args.all:
        _build_to_file("semiplm_clean.db", build_clean)
    if args.demo or args.all:
        _build_to_file("semiplm_demo.db", build_demo)


if __name__ == "__main__":
    main()
