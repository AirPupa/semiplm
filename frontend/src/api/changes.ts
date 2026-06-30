import { client } from './request'

export async function getChanges(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/changes', { params })
  return data
}

export async function createChange(payload: any) {
  const { data } = await client.post('/api/changes', payload)
  return data
}

export async function updateChange(id: number, payload: any) {
  const { data } = await client.put(`/api/changes/${id}`, payload)
  return data
}

export async function deleteChange(id: number) {
  const { data } = await client.delete(`/api/changes/${id}`)
  return data
}

export async function submitChange(id: number) {
  const { data } = await client.post(`/api/changes/${id}/submit`)
  return data
}

export async function analyzeChange(id: number) {
  const { data } = await client.post(`/api/changes/${id}/analyze`)
  return data
}

export async function createChangeImpact(changeId: number, payload: any) {
  const { data } = await client.post(`/api/changes/${changeId}/impacts`, payload)
  return data
}

export async function updateChangeImpact(id: number, payload: any) {
  const { data } = await client.put(`/api/change-impacts/${id}`, payload)
  return data
}

export async function deleteChangeImpact(id: number) {
  const { data } = await client.delete(`/api/change-impacts/${id}`)
  return data
}

export async function createChangeAction(changeId: number, payload: any) {
  const { data } = await client.post(`/api/changes/${changeId}/actions`, payload)
  return data
}

export async function getChangeRevisionArchive(changeId: number) {
  const { data } = await client.get(`/api/changes/${changeId}/revision-archive`)
  return data
}

export async function updateChangeAction(id: number, payload: any) {
  const { data } = await client.put(`/api/change-actions/${id}`, payload)
  return data
}

export async function closeChangeAction(id: number, payload: any) {
  const { data } = await client.post(`/api/change-actions/${id}/close`, payload)
  return data
}

export async function getChangeActions(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/change-actions', { params })
  return data
}

export async function getProductEffectivityBatches(productId: number) {
  const { data } = await client.get(`/api/products/${productId}/effectivity-batches`)
  return data
}
