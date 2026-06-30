import { client } from './request'

export async function getWorkflowTasks(params?: { page?: number; page_size?: number; keyword?: string; status?: string; mine?: boolean }) {
  const { data } = await client.get('/api/workflow-tasks', { params })
  return data
}

export async function approveWorkflowTask(id: number, payload: any) {
  const { data } = await client.post(`/api/workflow-tasks/${id}/approve`, payload)
  return data
}

export async function rejectWorkflowTask(id: number, payload: any) {
  const { data } = await client.post(`/api/workflow-tasks/${id}/reject`, payload)
  return data
}

export async function transferWorkflowTask(id: number, payload: any) {
  const { data } = await client.post(`/api/workflow-tasks/${id}/transfer`, payload)
  return data
}

export async function withdrawWorkflowInstance(id: number, payload: any) {
  const { data } = await client.post(`/api/workflow-instances/${id}/withdraw`, payload)
  return data
}
