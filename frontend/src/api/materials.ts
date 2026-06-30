import { client } from './request'

export async function getMaterials(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/materials', { params })
  return data
}

export async function createMaterial(payload: any) {
  const { data } = await client.post('/api/materials', payload)
  return data
}

export async function updateMaterial(id: number, payload: any) {
  const { data } = await client.put(`/api/materials/${id}`, payload)
  return data
}

export async function deleteMaterial(id: number) {
  const { data } = await client.delete(`/api/materials/${id}`)
  return data
}

export async function getSubstituteMaterials(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/substitute-materials', { params })
  return data
}

export async function createSubstituteMaterial(payload: any) {
  const { data } = await client.post('/api/substitute-materials', payload)
  return data
}

export async function updateSubstituteMaterial(id: number, payload: any) {
  const { data } = await client.put(`/api/substitute-materials/${id}`, payload)
  return data
}

export async function deleteSubstituteMaterial(id: number) {
  const { data } = await client.delete(`/api/substitute-materials/${id}`)
  return data
}

export async function getSuppliers(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/suppliers', { params })
  return data
}

export async function createSupplier(payload: any) {
  const { data } = await client.post('/api/suppliers', payload)
  return data
}

export async function updateSupplier(id: number, payload: any) {
  const { data } = await client.put(`/api/suppliers/${id}`, payload)
  return data
}

export async function deleteSupplier(id: number) {
  const { data } = await client.delete(`/api/suppliers/${id}`)
  return data
}
