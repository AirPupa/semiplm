import { client } from './request'

export async function getBoms(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/boms', { params })
  return data
}

export async function createBom(payload: any) {
  const { data } = await client.post('/api/boms', payload)
  return data
}

export async function updateBom(id: number, payload: any) {
  const { data } = await client.put(`/api/boms/${id}`, payload)
  return data
}

export async function deleteBom(id: number) {
  const { data } = await client.delete(`/api/boms/${id}`)
  return data
}

export async function createBomItem(bomId: number, payload: any) {
  const { data } = await client.post(`/api/boms/${bomId}/items`, payload)
  return data
}

export async function updateBomItem(id: number, payload: any) {
  const { data } = await client.put(`/api/bom-items/${id}`, payload)
  return data
}

export async function deleteBomItem(id: number) {
  const { data } = await client.delete(`/api/bom-items/${id}`)
  return data
}

export async function submitBom(id: number) {
  const { data } = await client.post(`/api/boms/${id}/submit`)
  return data
}

export async function approveBom(id: number) {
  const { data } = await client.post(`/api/boms/${id}/approve`)
  return data
}

export async function transformBom(id: number, payload: any) {
  const { data } = await client.post(`/api/boms/${id}/transform`, payload)
  return data
}

export async function compareBoms(baseId: number, targetId: number) {
  const { data } = await client.get(`/api/boms/${baseId}/compare/${targetId}`)
  return data
}

export async function getBomLineage(bomId: number) {
  const { data } = await client.get(`/api/boms/${bomId}/lineage`)
  return data
}

export async function getBomProcessCoverage(bomId: number) {
  const { data } = await client.get(`/api/boms/${bomId}/process-coverage`)
  return data
}

export async function getBomWhereUsed(materialCode: string) {
  const { data } = await client.get(`/api/boms/where-used/${encodeURIComponent(materialCode)}`)
  return data
}

export async function exportBomExcel(bomId: number) {
  const response = await client.get(`/api/boms/${bomId}/export`, { responseType: 'blob' })
  return response
}

export async function importBomExcel(bomId: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post(`/api/boms/${bomId}/import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

export async function downloadBomTemplate() {
  const response = await client.get('/api/boms/template', { responseType: 'blob' })
  return response
}

export async function batchReplaceBomMaterial(bomId: number, payload: any) {
  const { data } = await client.post(`/api/boms/${bomId}/batch-replace`, payload)
  return data
}

export async function batchUpdateBomQuantity(bomId: number, payload: any) {
  const { data } = await client.post(`/api/boms/${bomId}/batch-quantity`, payload)
  return data
}

export async function batchDeleteBomItems(bomId: number, payload: any) {
  const { data } = await client.post(`/api/boms/${bomId}/batch-delete`, payload)
  return data
}

export async function getBaselines(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/baselines', { params })
  return data
}

export async function getBomVersionHistory(bomId: number) {
  const { data } = await client.get(`/api/boms/${bomId}/version-history`)
  return data
}
