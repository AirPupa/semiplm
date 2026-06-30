import { client } from './request'

export async function getQuality(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/quality', { params })
  return data
}

export async function getQualityCAPAs(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/quality/capas', { params })
  return data
}

export async function createQualityCAPA(payload: any) {
  const { data } = await client.post('/api/quality/capas', payload)
  return data
}

export async function updateQualityCAPA(id: number, payload: any) {
  const { data } = await client.put(`/api/quality/capas/${id}`, payload)
  return data
}

export async function deleteQualityCAPA(id: number) {
  const { data } = await client.delete(`/api/quality/capas/${id}`)
  return data
}

export async function createCAPAFromIssue(issueId: number) {
  const { data } = await client.post(`/api/quality/issues/${issueId}/create-capa`)
  return data
}

export async function createQualityIssue(payload: any) {
  const { data } = await client.post('/api/quality/issues', payload)
  return data
}

export async function updateQualityIssue(id: number, payload: any) {
  const { data } = await client.put(`/api/quality/issues/${id}`, payload)
  return data
}

export async function deleteQualityIssue(id: number) {
  const { data } = await client.delete(`/api/quality/issues/${id}`)
  return data
}

export async function closeQualityIssue(id: number, payload: any) {
  const { data } = await client.post(`/api/quality/issues/${id}/close`, payload)
  return data
}

export async function triggerEcrFromIssue(issueId: number) {
  const { data } = await client.post(`/api/quality/issues/${issueId}/trigger-ecr`)
  return data
}

export async function closeQualityCAPA(id: number, payload: any) {
  const { data } = await client.post(`/api/quality/capas/${id}/close`, payload)
  return data
}

export async function getQualityReports(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/quality/reports', { params })
  return data
}

export async function createQualityReport(payload: any) {
  const { data } = await client.post('/api/quality/reports', payload)
  return data
}

export async function archiveQualityReportFromIssues(payload: any) {
  const { data } = await client.post('/api/quality/reports/archive-from-issues', payload)
  return data
}

export async function updateQualityReport(id: number, payload: any) {
  const { data } = await client.put(`/api/quality/reports/${id}`, payload)
  return data
}

export async function deleteQualityReport(id: number) {
  const { data } = await client.delete(`/api/quality/reports/${id}`)
  return data
}
