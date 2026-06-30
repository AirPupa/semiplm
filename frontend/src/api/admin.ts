import { client } from './request'

export async function getAdminRoles(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/roles', { params })
  return data
}

export async function getOrganizations(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/organizations', { params })
  return data
}

export async function createOrganization(payload: any) {
  const { data } = await client.post('/api/admin/organizations', payload)
  return data
}

export async function updateOrganization(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/organizations/${id}`, payload)
  return data
}

export async function deleteOrganization(id: number) {
  const { data } = await client.delete(`/api/admin/organizations/${id}`)
  return data
}

export async function createAdminRole(payload: any) {
  const { data } = await client.post('/api/admin/roles', payload)
  return data
}

export async function updateAdminRole(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/roles/${id}`, payload)
  return data
}

export async function deleteAdminRole(id: number) {
  const { data } = await client.delete(`/api/admin/roles/${id}`)
  return data
}

export async function getAdminUsers(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/users', { params })
  return data
}

export async function createAdminUser(payload: any) {
  const { data } = await client.post('/api/admin/users', payload)
  return data
}

export async function updateAdminUser(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/users/${id}`, payload)
  return data
}

export async function deleteAdminUser(id: number) {
  const { data } = await client.delete(`/api/admin/users/${id}`)
  return data
}

export async function getWorkflowTemplates(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/admin/workflows', { params })
  return data
}

export async function createWorkflowTemplate(payload: any) {
  const { data } = await client.post('/api/admin/workflows', payload)
  return data
}

export async function updateWorkflowTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/workflows/${id}`, payload)
  return data
}

export async function deleteWorkflowTemplate(id: number) {
  const { data } = await client.delete(`/api/admin/workflows/${id}`)
  return data
}

export async function createWorkflowNode(templateId: number, payload: any) {
  const { data } = await client.post(`/api/admin/workflows/${templateId}/nodes`, payload)
  return data
}

export async function updateWorkflowNode(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/workflow-nodes/${id}`, payload)
  return data
}

export async function deleteWorkflowNode(id: number) {
  const { data } = await client.delete(`/api/admin/workflow-nodes/${id}`)
  return data
}
