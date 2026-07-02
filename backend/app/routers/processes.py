"""制造流程 + 5 tab + 工艺参数 + 问题报告。
对齐 MES Template V1.2：ProcessFlow/ProcessFlowSeq/ProcessFlowContent/ProcessFlowMeasure/ProcessFlowContamination/ProcessStep(独立)/ProcessStage/ProcessCapability/Recipe/EquipmentType/EquipmentCapability。
本文件只放制造流程主菜单 + 5 tab。工艺库独立菜单放 routers/process_lib.py。问题报告/工艺参数保留。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..deps import current_user_context, require_permission
from ..schemas import (
    ProcessFlowContentPayload,
    ProcessFlowContentUpdatePayload,
    ProcessFlowContaminationPayload,
    ProcessFlowContaminationUpdatePayload,
    ProcessFlowMeasurePayload,
    ProcessFlowMeasureUpdatePayload,
    ProcessFlowPayload,
    ProcessFlowSeqPayload,
    ProcessFlowSeqUpdatePayload,
    ProcessFlowUpdatePayload,
    ProcessParameterPayload,
    ProcessParameterUpdatePayload,
    ProblemReportPayload,
    ProblemReportUpdatePayload,
)
from ..services.helpers import audit_log, commit_or_409, today_text, update_model

router = APIRouter()


# ===== 制造流程 ProcessFlow =====
@router.get("/api/process-flows")
def list_process_flows(
    keyword: str = "",
    state: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    q = db.query(models.ProcessFlow).filter(models.ProcessFlow.is_deleted == False)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.ProcessFlow.process_flow_name.like(like))
            | (models.ProcessFlow.description.like(like))
        )
    if state:
        q = q.filter(models.ProcessFlow.process_flow_state == state)
    total = q.count()
    items = (
        q.order_by(models.ProcessFlow.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [_flow_dict(f) for f in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/api/process-flows", status_code=201)
def create_process_flow(
    payload: ProcessFlowPayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    flow = models.ProcessFlow(**payload.model_dump())
    db.add(flow)
    try:
        commit_or_409(db, "操作冲突")
    except IntegrityError:
        raise HTTPException(409, "流程名称+版本已存在")
    audit_log(db, "create", "ProcessFlow", flow.id, flow.process_flow_name, "创建制造流程", ctx["user"])
    return _flow_dict(flow)


@router.get("/api/process-flows/{flow_id}")
def get_process_flow(
    flow_id: int,
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    flow = (
        db.query(models.ProcessFlow)
        .options(
            selectinload(models.ProcessFlow.seqs),
            selectinload(models.ProcessFlow.contents),
            selectinload(models.ProcessFlow.measures),
            selectinload(models.ProcessFlow.contaminations),
        )
        .filter(models.ProcessFlow.id == flow_id)
        .first()
    )
    if not flow:
        raise HTTPException(404, "流程不存在")
    return _flow_detail_dict(flow)


@router.put("/api/process-flows/{flow_id}")
def update_process_flow(
    flow_id: int,
    payload: ProcessFlowUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(404, "流程不存在")
    update_model(flow, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessFlow", flow.id, flow.process_flow_name, "更新制造流程", ctx["user"])
    return _flow_dict(flow)


@router.delete("/api/process-flows/{flow_id}")
def delete_process_flow(
    flow_id: int,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(404, "流程不存在")
    flow.is_deleted = True
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessFlow", flow.id, flow.process_flow_name, "删除制造流程", ctx["user"])
    return {"ok": True}


# ===== 工序 tab: ProcessFlowSeq =====
@router.get("/api/process-flows/{flow_id}/seqs")
def list_flow_seqs(
    flow_id: int,
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    seqs = (
        db.query(models.ProcessFlowSeq)
        .filter(models.ProcessFlowSeq.flow_id == flow_id)
        .order_by(models.ProcessFlowSeq.idx)
        .all()
    )
    return {"items": [_seq_dict(s) for s in seqs]}


@router.post("/api/process-flows/{flow_id}/seqs", status_code=201)
def create_flow_seq(
    flow_id: int,
    payload: ProcessFlowSeqPayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(404, "流程不存在")
    data = payload.model_dump()
    data["flow_id"] = flow_id
    data["process_flow_name"] = flow.process_flow_name
    data["process_flow_version"] = flow.process_flow_version
    seq = models.ProcessFlowSeq(**data)
    db.add(seq)
    commit_or_409(db, "操作冲突")
    audit_log(db, "create", "ProcessFlowSeq", seq.id, seq.process_flow_seq_name, "新增流程工序", ctx["user"])
    return _seq_dict(seq)


@router.put("/api/process-flow-seqs/{seq_id}")
def update_flow_seq(
    seq_id: int,
    payload: ProcessFlowSeqUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    seq = db.query(models.ProcessFlowSeq).filter(models.ProcessFlowSeq.id == seq_id).first()
    if not seq:
        raise HTTPException(404, "工序不存在")
    update_model(seq, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessFlowSeq", seq.id, seq.process_flow_seq_name, "更新流程工序", ctx["user"])
    return _seq_dict(seq)


@router.delete("/api/process-flow-seqs/{seq_id}")
def delete_flow_seq(
    seq_id: int,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    seq = db.query(models.ProcessFlowSeq).filter(models.ProcessFlowSeq.id == seq_id).first()
    if not seq:
        raise HTTPException(404, "工序不存在")
    db.delete(seq)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessFlowSeq", seq_id, seq.process_flow_seq_name, "删除流程工序", ctx["user"])
    return {"ok": True}


# ===== 制程内容 tab: ProcessFlowContent（含分支/返工字段）=====
@router.get("/api/process-flows/{flow_id}/contents")
def list_flow_contents(
    flow_id: int,
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    items = (
        db.query(models.ProcessFlowContent)
        .filter(models.ProcessFlowContent.flow_id == flow_id)
        .all()
    )
    return {"items": [_content_dict(c) for c in items]}


@router.post("/api/process-flows/{flow_id}/contents", status_code=201)
def create_flow_content(
    flow_id: int,
    payload: ProcessFlowContentPayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(404, "流程不存在")
    data = payload.model_dump()
    data["flow_id"] = flow_id
    data["process_flow_name"] = flow.process_flow_name
    data["process_flow_version"] = flow.process_flow_version
    c = models.ProcessFlowContent(**data)
    db.add(c)
    commit_or_409(db, "操作冲突")
    audit_log(db, "create", "ProcessFlowContent", c.id, c.process_flow_seq_name, "新增制程内容", ctx["user"])
    return _content_dict(c)


@router.put("/api/process-flow-contents/{content_id}")
def update_flow_content(
    content_id: int,
    payload: ProcessFlowContentUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    c = db.query(models.ProcessFlowContent).filter(models.ProcessFlowContent.id == content_id).first()
    if not c:
        raise HTTPException(404, "制程内容不存在")
    update_model(c, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessFlowContent", c.id, c.process_flow_seq_name, "更新制程内容", ctx["user"])
    return _content_dict(c)


@router.delete("/api/process-flow-contents/{content_id}")
def delete_flow_content(
    content_id: int,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    c = db.query(models.ProcessFlowContent).filter(models.ProcessFlowContent.id == content_id).first()
    if not c:
        raise HTTPException(404, "制程内容不存在")
    db.delete(c)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessFlowContent", content_id, c.process_flow_seq_name, "删除制程内容", ctx["user"])
    return {"ok": True}


# ===== 量测 tab: ProcessFlowMeasure =====
@router.get("/api/process-flows/{flow_id}/measures")
def list_flow_measures(
    flow_id: int,
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    items = (
        db.query(models.ProcessFlowMeasure)
        .filter(models.ProcessFlowMeasure.flow_id == flow_id)
        .all()
    )
    return {"items": [_measure_dict(m) for m in items]}


@router.post("/api/process-flows/{flow_id}/measures", status_code=201)
def create_flow_measure(
    flow_id: int,
    payload: ProcessFlowMeasurePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(404, "流程不存在")
    data = payload.model_dump()
    data["flow_id"] = flow_id
    data["process_flow_name"] = flow.process_flow_name
    data["process_flow_version"] = flow.process_flow_version
    m = models.ProcessFlowMeasure(**data)
    db.add(m)
    commit_or_409(db, "操作冲突")
    audit_log(db, "create", "ProcessFlowMeasure", m.id, m.measure_item, "新增量测项", ctx["user"])
    return _measure_dict(m)


@router.put("/api/process-flow-measures/{measure_id}")
def update_flow_measure(
    measure_id: int,
    payload: ProcessFlowMeasureUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    m = db.query(models.ProcessFlowMeasure).filter(models.ProcessFlowMeasure.id == measure_id).first()
    if not m:
        raise HTTPException(404, "量测项不存在")
    update_model(m, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessFlowMeasure", m.id, m.measure_item, "更新量测项", ctx["user"])
    return _measure_dict(m)


@router.delete("/api/process-flow-measures/{measure_id}")
def delete_flow_measure(
    measure_id: int,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    m = db.query(models.ProcessFlowMeasure).filter(models.ProcessFlowMeasure.id == measure_id).first()
    if not m:
        raise HTTPException(404, "量测项不存在")
    db.delete(m)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessFlowMeasure", measure_id, m.measure_item, "删除量测项", ctx["user"])
    return {"ok": True}


# ===== 防污染 tab: ProcessFlowContamination =====
@router.get("/api/process-flows/{flow_id}/contaminations")
def list_flow_contaminations(
    flow_id: int,
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    items = (
        db.query(models.ProcessFlowContamination)
        .filter(models.ProcessFlowContamination.flow_id == flow_id)
        .all()
    )
    return {"items": [_contamination_dict(c) for c in items]}


@router.post("/api/process-flows/{flow_id}/contaminations", status_code=201)
def create_flow_contamination(
    flow_id: int,
    payload: ProcessFlowContaminationPayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    flow = db.query(models.ProcessFlow).filter(models.ProcessFlow.id == flow_id).first()
    if not flow:
        raise HTTPException(404, "流程不存在")
    data = payload.model_dump()
    data["flow_id"] = flow_id
    data["process_flow_name"] = flow.process_flow_name
    data["process_flow_version"] = flow.process_flow_version
    c = models.ProcessFlowContamination(**data)
    db.add(c)
    commit_or_409(db, "操作冲突")
    audit_log(db, "create", "ProcessFlowContamination", c.id, c.process_flow_seq_name, "新增防污染", ctx["user"])
    return _contamination_dict(c)


@router.put("/api/process-flow-contaminations/{contamination_id}")
def update_flow_contamination(
    contamination_id: int,
    payload: ProcessFlowContaminationUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    c = db.query(models.ProcessFlowContamination).filter(models.ProcessFlowContamination.id == contamination_id).first()
    if not c:
        raise HTTPException(404, "防污染记录不存在")
    update_model(c, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessFlowContamination", c.id, c.process_flow_seq_name, "更新防污染", ctx["user"])
    return _contamination_dict(c)


@router.delete("/api/process-flow-contaminations/{contamination_id}")
def delete_flow_contamination(
    contamination_id: int,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    c = db.query(models.ProcessFlowContamination).filter(models.ProcessFlowContamination.id == contamination_id).first()
    if not c:
        raise HTTPException(404, "防污染记录不存在")
    db.delete(c)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessFlowContamination", contamination_id, c.process_flow_seq_name, "删除防污染", ctx["user"])
    return {"ok": True}


# ===== 问题报告（保留一期）=====
@router.get("/api/problem-reports")
def list_problem_reports(
    keyword: str = "",
    status: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    q = db.query(models.ProblemReport)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.ProblemReport.pr_no.like(like))
            | (models.ProblemReport.title.like(like))
        )
    if status:
        q = q.filter(models.ProblemReport.status == status)
    total = q.count()
    items = q.order_by(models.ProblemReport.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_pr_dict(p) for p in items], "total": total, "page": page, "page_size": page_size}


@router.post("/api/problem-reports", status_code=201)
def create_problem_report(
    payload: ProblemReportPayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    pr = models.ProblemReport(**payload.model_dump())
    pr.pr_no = "PR-" + datetime.now().strftime("%Y%m%d%H%M%S")
    pr.reporter = ctx["user"]
    pr.reported_at = today_text()
    db.add(pr)
    commit_or_409(db, "操作冲突")
    audit_log(db, "create", "ProblemReport", pr.id, pr.pr_no, "创建问题报告", ctx["user"])
    return _pr_dict(pr)


@router.put("/api/problem-reports/{report_id}")
def update_problem_report(
    report_id: int,
    payload: ProblemReportUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    pr = db.query(models.ProblemReport).filter(models.ProblemReport.id == report_id).first()
    if not pr:
        raise HTTPException(404, "问题报告不存在")
    update_model(pr, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProblemReport", pr.id, pr.pr_no, "更新问题报告", ctx["user"])
    return _pr_dict(pr)


@router.delete("/api/problem-reports/{report_id}")
def delete_problem_report(
    report_id: int,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    pr = db.query(models.ProblemReport).filter(models.ProblemReport.id == report_id).first()
    if not pr:
        raise HTTPException(404, "问题报告不存在")
    db.delete(pr)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProblemReport", report_id, pr.pr_no, "删除问题报告", ctx["user"])
    return {"ok": True}


# ===== 工艺参数库（保留一期）=====
@router.get("/api/process-parameters")
def list_process_parameters(
    keyword: str = "",
    param_type: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    _ctx: dict = Depends(current_user_context),
):
    q = db.query(models.ProcessParameter)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (models.ProcessParameter.param_code.like(like))
            | (models.ProcessParameter.param_name.like(like))
        )
    if param_type:
        q = q.filter(models.ProcessParameter.param_type == param_type)
    total = q.count()
    items = q.order_by(models.ProcessParameter.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_param_dict(p) for p in items], "total": total, "page": page, "page_size": page_size}


@router.post("/api/process-parameters", status_code=201)
def create_process_parameter(
    payload: ProcessParameterPayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    p = models.ProcessParameter(**payload.model_dump())
    if not p.param_code:
        p.param_code = "PP-" + datetime.now().strftime("%Y%m%d%H%M%S")
    db.add(p)
    commit_or_409(db, "操作冲突")
    audit_log(db, "create", "ProcessParameter", p.id, p.param_code, "创建工艺参数", ctx["user"])
    return _param_dict(p)


@router.put("/api/process-parameters/{param_id}")
def update_process_parameter(
    param_id: int,
    payload: ProcessParameterUpdatePayload,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    p = db.query(models.ProcessParameter).filter(models.ProcessParameter.id == param_id).first()
    if not p:
        raise HTTPException(404, "工艺参数不存在")
    update_model(p, payload)
    commit_or_409(db, "操作冲突")
    audit_log(db, "update", "ProcessParameter", p.id, p.param_code, "更新工艺参数", ctx["user"])
    return _param_dict(p)


@router.delete("/api/process-parameters/{param_id}")
def delete_process_parameter(
    param_id: int,
    db: Session = Depends(get_db),
    ctx: dict = Depends(current_user_context),
):
    p = db.query(models.ProcessParameter).filter(models.ProcessParameter.id == param_id).first()
    if not p:
        raise HTTPException(404, "工艺参数不存在")
    db.delete(p)
    commit_or_409(db, "操作冲突")
    audit_log(db, "delete", "ProcessParameter", param_id, p.param_code, "删除工艺参数", ctx["user"])
    return {"ok": True}


# ===== 序列化 =====
def _flow_dict(f: models.ProcessFlow) -> dict:
    return {
        "id": f.id,
        "process_flow_name": f.process_flow_name,
        "process_flow_version": f.process_flow_version,
        "description": f.description,
        "process_flow_type1": f.process_flow_type1,
        "process_flow_type2": f.process_flow_type2,
        "process_flow_state": f.process_flow_state,
        "owner_group_name": f.owner_group_name,
        "owner": f.owner,
        "process_group_name": f.process_group_name,
        "is_deleted": f.is_deleted,
        "created_at": f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else "",
    }


def _flow_detail_dict(f: models.ProcessFlow) -> dict:
    d = _flow_dict(f)
    d["seqs"] = [_seq_dict(s) for s in f.seqs]
    d["contents"] = [_content_dict(c) for c in f.contents]
    d["measures"] = [_measure_dict(m) for m in f.measures]
    d["contaminations"] = [_contamination_dict(c) for c in f.contaminations]
    return d


def _seq_dict(s: models.ProcessFlowSeq) -> dict:
    return {
        "id": s.id,
        "idx": s.idx,
        "step_source": s.step_source,
        "process_flow_seq_name": s.process_flow_seq_name,
        "process_flow_name": s.process_flow_name,
        "process_flow_version": s.process_flow_version,
        "process_name": s.process_name,
        "process_version": s.process_version,
        "process_flow_seq_type": s.process_flow_seq_type,
        "process_group1": s.process_group1,
        "process_group2": s.process_group2,
        "process_stage_name": s.process_stage_name,
        "work_layer": s.work_layer,
    }


def _content_dict(c: models.ProcessFlowContent) -> dict:
    return {
        "id": c.id,
        "process_flow_seq_name": c.process_flow_seq_name,
        "process_flow_name": c.process_flow_name,
        "process_flow_version": c.process_flow_version,
        "process_capability_name": c.process_capability_name,
        "recipe_name": c.recipe_name,
        "recipe_name_description": c.recipe_name_description,
        "dc_spec_name": c.dc_spec_name,
        "yield_limit": c.yield_limit,
        "reticle_group_name": c.reticle_group_name,
        "reticle_name": c.reticle_name,
        "probe_card_name": c.probe_card_name,
        "lot_sampling_rule": c.lot_sampling_rule,
        "is_skip_allowed": c.is_skip_allowed,
        "is_mandatory_step": c.is_mandatory_step,
        "sampling_user_group": c.sampling_user_group,
        "is_flip": c.is_flip,
        "branch_flow_group": c.branch_flow_group,
        "branch_flow_name": c.branch_flow_name,
        "rework_flow_group": c.rework_flow_group,
        "rework_flow_name": c.rework_flow_name,
        "wafer_selection_rule": c.wafer_selection_rule,
        "ink_able": c.ink_able,
    }


def _measure_dict(m: models.ProcessFlowMeasure) -> dict:
    return {
        "id": m.id,
        "process_flow_name": m.process_flow_name,
        "process_flow_version": m.process_flow_version,
        "process_flow_seq_name": m.process_flow_seq_name,
        "key_process_flow_seq_name": m.key_process_flow_seq_name,
        "measure_item": m.measure_item,
        "target": m.target,
        "lower_spec_limit": m.lower_spec_limit,
        "upper_spec_limit": m.upper_spec_limit,
        "sample_count": m.sample_count,
        "sample_slots": m.sample_slots,
        "sample_count_type": m.sample_count_type,
    }


def _contamination_dict(c: models.ProcessFlowContamination) -> dict:
    return {
        "id": c.id,
        "process_flow_name": c.process_flow_name,
        "process_flow_version": c.process_flow_version,
        "process_flow_seq_name": c.process_flow_seq_name,
        "require_contamination_levels": c.require_contamination_levels,
        "affect_contamination_level": c.affect_contamination_level,
    }


def _pr_dict(p: models.ProblemReport) -> dict:
    return {
        "id": p.id,
        "pr_no": p.pr_no,
        "title": p.title,
        "problem_type": p.problem_type,
        "severity": p.severity,
        "source": p.source,
        "product_id": p.product_id,
        "product_model": p.product_model,
        "description": p.description,
        "suggested_action": p.suggested_action,
        "status": p.status,
        "reporter": p.reporter,
        "reported_at": p.reported_at,
        "related_change_no": p.related_change_no,
        "remark": p.remark,
    }


def _param_dict(p: models.ProcessParameter) -> dict:
    return {
        "id": p.id,
        "param_code": p.param_code,
        "param_name": p.param_name,
        "param_type": p.param_type,
        "unit": p.unit,
        "category": p.category,
        "default_value": p.default_value,
        "min_value": p.min_value,
        "max_value": p.max_value,
        "description": p.description,
        "status": p.status,
    }
