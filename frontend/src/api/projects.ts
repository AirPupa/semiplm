import { client } from './request'

export async function getProjects(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/projects', { params })
  return data
}

export async function createProject(payload: any) {
  const { data } = await client.post('/api/projects', payload)
  return data
}

export async function updateProject(id: number, payload: any) {
  const { data } = await client.put(`/api/projects/${id}`, payload)
  return data
}

export async function deleteProject(id: number) {
  const { data } = await client.delete(`/api/projects/${id}`)
  return data
}

export async function createProjectFromTemplate(payload: any) {
  const { data } = await client.post('/api/projects/from-template', payload)
  return data
}

export async function getProjectTemplates(params?: { page?: number; page_size?: number; keyword?: string }) {
  const { data } = await client.get('/api/project-templates', { params })
  return data
}

export async function createProjectTemplate(payload: any) {
  const { data } = await client.post('/api/project-templates', payload)
  return data
}

export async function updateProjectTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/project-templates/${id}`, payload)
  return data
}

export async function deleteProjectTemplate(id: number) {
  const { data } = await client.delete(`/api/project-templates/${id}`)
  return data
}

export async function getProjectDeliverables(projectId: number) {
  const { data } = await client.get(`/api/projects/${projectId}/deliverables`)
  return data
}

export async function createProjectDeliverable(projectId: number, payload: any) {
  const { data } = await client.post(`/api/projects/${projectId}/deliverables`, payload)
  return data
}

export async function updateProjectDeliverable(id: number, payload: any) {
  const { data } = await client.put(`/api/project-deliverables/${id}`, payload)
  return data
}

export async function deleteProjectDeliverable(id: number) {
  const { data } = await client.delete(`/api/project-deliverables/${id}`)
  return data
}

export async function getProjectRisks(projectId: number) {
  const { data } = await client.get(`/api/projects/${projectId}/risks`)
  return data
}

export async function createProjectRisk(projectId: number, payload: any) {
  const { data } = await client.post(`/api/projects/${projectId}/risks`, payload)
  return data
}

export async function updateProjectRisk(id: number, payload: any) {
  const { data } = await client.put(`/api/project-risks/${id}`, payload)
  return data
}

export async function deleteProjectRisk(id: number) {
  const { data } = await client.delete(`/api/project-risks/${id}`)
  return data
}

export async function getProjectTasks(projectId: number) {
  const { data } = await client.get(`/api/projects/${projectId}/tasks`)
  return data
}

export async function createProjectTask(projectId: number, payload: any) {
  const { data } = await client.post(`/api/projects/${projectId}/tasks`, payload)
  return data
}

export async function updateProjectTask(id: number, payload: any) {
  const { data } = await client.put(`/api/project-tasks/${id}`, payload)
  return data
}

export async function deleteProjectTask(id: number) {
  const { data } = await client.delete(`/api/project-tasks/${id}`)
  return data
}

export async function advanceProjectPhase(projectId: number, payload: any) {
  const { data } = await client.post(`/api/projects/${projectId}/advance-phase`, payload)
  return data
}

export async function getProjectCrossModules(projectId: number) {
  const { data } = await client.get(`/api/projects/${projectId}/cross-modules`)
  return data
}

export async function getProjectClosureCheck(projectId: number) {
  const { data } = await client.get(`/api/projects/${projectId}/closure-check`)
  return data
}

export async function archiveProject(projectId: number, payload: { archived_by?: string; summary?: string }) {
  const { data } = await client.post(`/api/projects/${projectId}/archive`, payload)
  return data
}

export async function unarchiveProject(projectId: number) {
  const { data } = await client.post(`/api/projects/${projectId}/unarchive`, {})
  return data
}

export async function getProjectArchivePackage(projectId: number) {
  const { data } = await client.get(`/api/projects/${projectId}/archive-package`)
  return data
}
