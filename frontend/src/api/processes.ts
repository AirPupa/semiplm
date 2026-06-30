import { client } from './request'

export async function getRoutes(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/process-routes', { params })
  return data
}

export async function createProcessRoute(payload: any) {
  const { data } = await client.post('/api/process-routes', payload)
  return data
}

export async function updateProcessRoute(id: number, payload: any) {
  const { data } = await client.put(`/api/process-routes/${id}`, payload)
  return data
}

export async function deleteProcessRoute(id: number) {
  const { data } = await client.delete(`/api/process-routes/${id}`)
  return data
}

export async function createProcessStep(routeId: number, payload: any) {
  const { data } = await client.post(`/api/process-routes/${routeId}/steps`, payload)
  return data
}

export async function updateProcessStep(id: number, payload: any) {
  const { data } = await client.put(`/api/process-steps/${id}`, payload)
  return data
}

export async function deleteProcessStep(id: number) {
  const { data } = await client.delete(`/api/process-steps/${id}`)
  return data
}

export async function submitProcessRoute(id: number, payload: any) {
  const { data } = await client.post(`/api/process-routes/${id}/submit`, payload)
  return data
}

export async function approveProcessRoute(id: number, payload: any) {
  const { data } = await client.post(`/api/process-routes/${id}/approve`, payload)
  return data
}

export async function getProductProcessSteps(productId: number) {
  const { data } = await client.get(`/api/products/${productId}/process-steps`)
  return data
}

export async function getProcessRouteVersionHistory(routeId: number) {
  const { data } = await client.get(`/api/process-routes/${routeId}/version-history`)
  return data
}

export async function getProblemReports(params?: { page?: number; page_size?: number; keyword?: string }) {
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

export async function getProcessParameters(params?: { page?: number; page_size?: number; keyword?: string }) {
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
