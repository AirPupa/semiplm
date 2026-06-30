import axios from 'axios'

export const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 10000
})

client.interceptors.request.use((config) => {
  const username = localStorage.getItem('semiplm.currentUser')
  if (username) config.headers['X-SemiPLM-User'] = username
  return config
})
