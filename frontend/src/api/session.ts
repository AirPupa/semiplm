import { client } from './request'

export async function loginWithPassword(username: string, password: string) {
  const { data } = await client.post('/api/session/login', { username, password })
  return data
}

export async function getCurrentSession() {
  const { data } = await client.get('/api/session/current')
  return data
}

export async function updateCurrentProfile(payload: { display_name?: string; avatar_url?: string }) {
  const { data } = await client.put('/api/session/profile', payload)
  return data
}
