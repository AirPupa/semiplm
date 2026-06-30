import { client } from './request'

export async function getWorkbench() {
  const { data } = await client.get('/api/workbench')
  return data
}

export async function getWorkbenchCalendar(month: string) {
  const { data } = await client.get('/api/workbench/calendar', { params: { month } })
  return data
}

export async function getWorkbenchNotifications(params?: { action?: string; limit?: number }) {
  const { data } = await client.get('/api/workbench/notifications', { params })
  return data
}

export async function getClosureCheck() {
  const { data } = await client.get('/api/workbench/closure-check')
  return data
}
