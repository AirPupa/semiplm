import { client } from './request'
import { triggerDownload } from './download'

export async function getDocuments(params?: { page?: number; page_size?: number; keyword?: string; sort_by?: string; sort_order?: 'asc' | 'desc' }) {
  const { data } = await client.get('/api/documents', { params })
  return data
}

export async function createDocument(payload: any) {
  const { data } = await client.post('/api/documents', payload)
  return data
}

export async function updateDocument(id: number, payload: any) {
  const { data } = await client.put(`/api/documents/${id}`, payload)
  return data
}

export async function deleteDocument(id: number) {
  const { data } = await client.delete(`/api/documents/${id}`)
  return data
}

export async function submitDocument(id: number) {
  const { data } = await client.post(`/api/documents/${id}/submit`)
  return data
}

export async function approveDocument(id: number) {
  const { data } = await client.post(`/api/documents/${id}/approve`)
  return data
}

export async function uploadDocumentFile(id: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post(`/api/documents/${id}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

export async function downloadDocumentFile(id: number) {
  const response = await client.get(`/api/documents/${id}/download`, { responseType: 'blob' })
  return response
}

export async function previewDocumentFile(id: number) {
  const response = await client.get(`/api/documents/${id}/preview`, { responseType: 'blob' })
  return response
}

export async function getDocumentDistributions(documentId: number) {
  const { data } = await client.get(`/api/documents/${documentId}/distributions`)
  return data
}

export async function distributeDocument(documentId: number, payload: any) {
  const { data } = await client.post(`/api/documents/${documentId}/distribute`, payload)
  return data
}

export async function recallDistribution(distId: number, payload: any) {
  const { data } = await client.post(`/api/document-distributions/${distId}/recall`, payload)
  return data
}

export async function getDocumentVersionHistory(documentId: number) {
  const { data } = await client.get(`/api/documents/${documentId}/version-history`)
  return data
}

export async function getAttachments(objectType: string, objectId: number) {
  const { data } = await client.get('/api/attachments', { params: { object_type: objectType, object_id: objectId } })
  return data
}

export async function uploadAttachment(objectType: string, objectId: number, file: File, description?: string) {
  const form = new FormData()
  form.append('object_type', objectType)
  form.append('object_id', String(objectId))
  form.append('file', file)
  if (description) form.append('description', description)
  const { data } = await client.post('/api/attachments/upload', form)
  return data
}

export async function downloadAttachment(attachmentId: number) {
  const res = await client.get(`/api/attachments/${attachmentId}/download`, { responseType: 'blob' })
  triggerDownload(res, `attachment_${attachmentId}`)
}

export async function deleteAttachment(attachmentId: number) {
  await client.delete(`/api/attachments/${attachmentId}`)
}

export async function getDocumentRelations(documentId: number) {
  const { data } = await client.get(`/api/documents/${documentId}/relations`)
  return data
}
