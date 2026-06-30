import { client } from './request'

export async function getIntegrationJobs(params: any = {}) {
  const { data } = await client.get('/api/integration-jobs', { params })
  return data
}

export async function getIntegrationSummary() {
  const { data } = await client.get('/api/integration-jobs/summary')
  return data
}

export async function startIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/start`, payload)
  return data
}

export async function completeIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/success`, payload)
  return data
}

export async function failIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/fail`, payload)
  return data
}

export async function retryIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/retry`, payload)
  return data
}

export async function getIntegrationEndpoints(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/integration-endpoints', { params })
  return data
}

export async function createIntegrationEndpoint(payload: any) {
  const { data } = await client.post('/api/admin/integration-endpoints', payload)
  return data
}

export async function updateIntegrationEndpoint(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/integration-endpoints/${id}`, payload)
  return data
}
