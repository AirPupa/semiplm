import { client } from './request'

export async function getAuditLogs(params?: { page?: number; page_size?: number; keyword?: string; object_type?: string; action?: string }) {
  const { data } = await client.get('/api/audit-logs', { params })
  return data
}
