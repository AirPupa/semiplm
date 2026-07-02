import { client } from './request'

export async function getProducts(params?: { page?: number; page_size?: number; keyword?: string; state?: string; product_type?: string }) {
  const { data } = await client.get('/api/products', { params })
  return data
}

export async function createProduct(payload: any) {
  const { data } = await client.post('/api/products', payload)
  return data
}

export async function updateProduct(id: number, payload: any) {
  const { data } = await client.put(`/api/products/${id}`, payload)
  return data
}

export async function deleteProduct(id: number) {
  const { data } = await client.delete(`/api/products/${id}`)
  return data
}

export async function getProduct(id: string | number) {
  const { data } = await client.get(`/api/products/${id}`)
  return data
}

export async function getProductVersions(productId: string | number) {
  const { data } = await client.get(`/api/products/${productId}/versions`)
  return data
}

export async function createProductVersion(productId: string | number, payload: any) {
  const { data } = await client.post(`/api/products/${productId}/versions`, payload)
  return data
}
