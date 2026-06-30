import { client } from './request'

export async function getRequirements(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/requirements', { params })
  return data
}

export async function createRequirement(payload: any) {
  const { data } = await client.post('/api/requirements', payload)
  return data
}

export async function updateRequirement(id: number, payload: any) {
  const { data } = await client.put(`/api/requirements/${id}`, payload)
  return data
}

export async function deleteRequirement(id: number) {
  const { data } = await client.delete(`/api/requirements/${id}`)
  return data
}

export async function getRequirementTrace(id: number) {
  const { data } = await client.get(`/api/requirements/${id}/trace`)
  return data
}
