import { client } from './request'

export async function getDashboard() {
  const { data } = await client.get('/api/dashboard')
  return data
}
