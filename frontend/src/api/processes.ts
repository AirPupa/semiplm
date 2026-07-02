/**
 * 制造流程 + 5 tab + 问题报告 + 工艺参数。
 * 对齐后端 routers/processes.py（MES Template V1.2：ProcessFlow/Seq/Content/Measure/Contamination）。
 * 工艺主数据独立菜单（标准工序/工艺阶段等）见 ./process_lib.ts。
 */
import { client } from './request'

// ===== 制造流程 ProcessFlow =====
export async function getProcessFlows(params?: {
  page?: number
  page_size?: number
  keyword?: string
  state?: string
}) {
  const { data } = await client.get('/api/process-flows', { params })
  return data
}

export async function getProcessFlow(id: number) {
  const { data } = await client.get(`/api/process-flows/${id}`)
  return data
}

export async function createProcessFlow(payload: any) {
  const { data } = await client.post('/api/process-flows', payload)
  return data
}

export async function updateProcessFlow(id: number, payload: any) {
  const { data } = await client.put(`/api/process-flows/${id}`, payload)
  return data
}

export async function deleteProcessFlow(id: number) {
  const { data } = await client.delete(`/api/process-flows/${id}`)
  return data
}

// ===== 工序 tab: ProcessFlowSeq =====
export async function getFlowSeqs(flowId: number) {
  const { data } = await client.get(`/api/process-flows/${flowId}/seqs`)
  return data
}

export async function createFlowSeq(flowId: number, payload: any) {
  const { data } = await client.post(`/api/process-flows/${flowId}/seqs`, payload)
  return data
}

export async function updateFlowSeq(seqId: number, payload: any) {
  const { data } = await client.put(`/api/process-flow-seqs/${seqId}`, payload)
  return data
}

export async function deleteFlowSeq(seqId: number) {
  const { data } = await client.delete(`/api/process-flow-seqs/${seqId}`)
  return data
}

// ===== 制程内容 tab: ProcessFlowContent =====
export async function getFlowContents(flowId: number) {
  const { data } = await client.get(`/api/process-flows/${flowId}/contents`)
  return data
}

export async function createFlowContent(flowId: number, payload: any) {
  const { data } = await client.post(`/api/process-flows/${flowId}/contents`, payload)
  return data
}

export async function updateFlowContent(contentId: number, payload: any) {
  const { data } = await client.put(`/api/process-flow-contents/${contentId}`, payload)
  return data
}

export async function deleteFlowContent(contentId: number) {
  const { data } = await client.delete(`/api/process-flow-contents/${contentId}`)
  return data
}

// ===== 量测 tab: ProcessFlowMeasure =====
export async function getFlowMeasures(flowId: number) {
  const { data } = await client.get(`/api/process-flows/${flowId}/measures`)
  return data
}

export async function createFlowMeasure(flowId: number, payload: any) {
  const { data } = await client.post(`/api/process-flows/${flowId}/measures`, payload)
  return data
}

export async function updateFlowMeasure(measureId: number, payload: any) {
  const { data } = await client.put(`/api/process-flow-measures/${measureId}`, payload)
  return data
}

export async function deleteFlowMeasure(measureId: number) {
  const { data } = await client.delete(`/api/process-flow-measures/${measureId}`)
  return data
}

// ===== 防污染 tab: ProcessFlowContamination =====
export async function getFlowContaminations(flowId: number) {
  const { data } = await client.get(`/api/process-flows/${flowId}/contaminations`)
  return data
}

export async function createFlowContamination(flowId: number, payload: any) {
  const { data } = await client.post(`/api/process-flows/${flowId}/contaminations`, payload)
  return data
}

export async function updateFlowContamination(contaminationId: number, payload: any) {
  const { data } = await client.put(`/api/process-flow-contaminations/${contaminationId}`, payload)
  return data
}

export async function deleteFlowContamination(contaminationId: number) {
  const { data } = await client.delete(`/api/process-flow-contaminations/${contaminationId}`)
  return data
}

// ===== 问题报告（保留一期）=====
export async function getProblemReports(params?: {
  page?: number
  page_size?: number
  keyword?: string
  status?: string
}) {
  const { data } = await client.get('/api/problem-reports', { params })
  return data
}

export async function createProblemReport(payload: any) {
  const { data } = await client.post('/api/problem-reports', payload)
  return data
}

export async function updateProblemReport(id: number, payload: any) {
  const { data } = await client.put(`/api/problem-reports/${id}`, payload)
  return data
}

export async function deleteProblemReport(id: number) {
  const { data } = await client.delete(`/api/problem-reports/${id}`)
  return data
}

// ===== 工艺参数（保留一期）=====
export async function getProcessParameters(params?: {
  page?: number
  page_size?: number
  keyword?: string
  param_type?: string
}) {
  const { data } = await client.get('/api/process-parameters', { params })
  return data
}

export async function createProcessParameter(payload: any) {
  const { data } = await client.post('/api/process-parameters', payload)
  return data
}

export async function updateProcessParameter(id: number, payload: any) {
  const { data } = await client.put(`/api/process-parameters/${id}`, payload)
  return data
}

export async function deleteProcessParameter(id: number) {
  const { data } = await client.delete(`/api/process-parameters/${id}`)
  return data
}
