import { client } from './request'
import { triggerDownload } from './download'

export async function getReportCompleteness() {
  const { data } = await client.get('/api/reports/completeness')
  return data
}

export async function getReportChangeCycle() {
  const { data } = await client.get('/api/reports/change-cycle')
  return data
}

export async function getReportProjectProgress() {
  const { data } = await client.get('/api/reports/project-progress')
  return data
}

export async function getReportQualityClosure() {
  const { data } = await client.get('/api/reports/quality-closure')
  return data
}

export async function exportReportCompleteness() {
  const res = await client.get('/api/reports/completeness/export', { responseType: 'blob' })
  triggerDownload(res, 'report_completeness.xlsx')
}

export async function exportReportChangeCycle() {
  const res = await client.get('/api/reports/change-cycle/export', { responseType: 'blob' })
  triggerDownload(res, 'report_change_cycle.xlsx')
}

export async function exportReportProjectProgress() {
  const res = await client.get('/api/reports/project-progress/export', { responseType: 'blob' })
  triggerDownload(res, 'report_project_progress.xlsx')
}

export async function exportReportQualityClosure() {
  const res = await client.get('/api/reports/quality-closure/export', { responseType: 'blob' })
  triggerDownload(res, 'report_quality_closure.xlsx')
}

export async function getReportSnapshots(params?: { page?: number; page_size?: number; report_type?: string }) {
  const { data } = await client.get('/api/reports/snapshots', { params })
  return data
}

export async function createReportSnapshot(payload: { report_type: string; generated_by?: string; schedule_key?: string }) {
  const { data } = await client.post('/api/reports/snapshots', payload)
  return data
}
