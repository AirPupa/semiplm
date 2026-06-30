import { client } from './request'

export async function getCodingRules(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/foundation/coding-rules', { params })
  return data
}

export async function createCodingRule(payload: any) {
  const { data } = await client.post('/api/admin/foundation/coding-rules', payload)
  return data
}

export async function updateCodingRule(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/coding-rules/${id}`, payload)
  return data
}

export async function deleteCodingRule(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/coding-rules/${id}`)
  return data
}

export async function getCategoryTemplates(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/foundation/categories', { params })
  return data
}

export async function createCategoryTemplate(payload: any) {
  const { data } = await client.post('/api/admin/foundation/categories', payload)
  return data
}

export async function updateCategoryTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/categories/${id}`, payload)
  return data
}

export async function deleteCategoryTemplate(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/categories/${id}`)
  return data
}

export async function createAttributeTemplate(categoryId: number, payload: any) {
  const { data } = await client.post(`/api/admin/foundation/categories/${categoryId}/attributes`, payload)
  return data
}

export async function updateAttributeTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/attributes/${id}`, payload)
  return data
}

export async function deleteAttributeTemplate(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/attributes/${id}`)
  return data
}

export async function getLifecycleTemplates(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/foundation/lifecycles', { params })
  return data
}

export async function createLifecycleTemplate(payload: any) {
  const { data } = await client.post('/api/admin/foundation/lifecycles', payload)
  return data
}

export async function updateLifecycleTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/lifecycles/${id}`, payload)
  return data
}

export async function deleteLifecycleTemplate(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/lifecycles/${id}`)
  return data
}

export async function createLifecycleState(templateId: number, payload: any) {
  const { data } = await client.post(`/api/admin/foundation/lifecycles/${templateId}/states`, payload)
  return data
}

export async function updateLifecycleState(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/lifecycle-states/${id}`, payload)
  return data
}

export async function deleteLifecycleState(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/lifecycle-states/${id}`)
  return data
}

export async function getDictionaryItems(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/foundation/dictionaries', { params })
  return data
}

export async function createDictionaryItem(payload: any) {
  const { data } = await client.post('/api/admin/foundation/dictionaries', payload)
  return data
}

export async function updateDictionaryItem(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/dictionaries/${id}`, payload)
  return data
}

export async function deleteDictionaryItem(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/dictionaries/${id}`)
  return data
}

export async function getSystemParameters(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/foundation/system-parameters', { params })
  return data
}

export async function createSystemParameter(payload: any) {
  const { data } = await client.post('/api/admin/foundation/system-parameters', payload)
  return data
}

export async function updateSystemParameter(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/system-parameters/${id}`, payload)
  return data
}

export async function deleteSystemParameter(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/system-parameters/${id}`)
  return data
}
