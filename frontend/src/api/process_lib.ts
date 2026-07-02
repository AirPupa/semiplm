/**
 * 工艺主数据独立菜单 API：标准工序/工艺阶段/工艺能力/工艺配方/设备类型/设备能力。
 * 对齐后端 routers/process_lib.py（MES Template V1.2）。
 */
import { client } from './request'

// ===== 标准工序 ProcessStep（21 字段，分页）=====
export async function getProcessSteps(params?: {
  page?: number
  page_size?: number
  keyword?: string
  state?: string
}) {
  const { data } = await client.get('/api/process-steps', { params })
  return data
}

export async function createProcessStep(payload: any) {
  const { data } = await client.post('/api/process-steps', payload)
  return data
}

export async function updateProcessStep(id: number, payload: any) {
  const { data } = await client.put(`/api/process-steps/${id}`, payload)
  return data
}

export async function deleteProcessStep(id: number) {
  const { data } = await client.delete(`/api/process-steps/${id}`)
  return data
}

// ===== 工艺阶段 ProcessStage（7 字段，不分页）=====
export async function getProcessStages(params?: { keyword?: string; state?: string }) {
  const { data } = await client.get('/api/process-stages', { params })
  return data
}

export async function createProcessStage(payload: any) {
  const { data } = await client.post('/api/process-stages', payload)
  return data
}

export async function updateProcessStage(id: number, payload: any) {
  const { data } = await client.put(`/api/process-stages/${id}`, payload)
  return data
}

export async function deleteProcessStage(id: number) {
  const { data } = await client.delete(`/api/process-stages/${id}`)
  return data
}

// ===== 工艺能力 ProcessCapability（3 字段，不分页）=====
export async function getProcessCapabilities(params?: { keyword?: string; state?: string }) {
  const { data } = await client.get('/api/process-capabilities', { params })
  return data
}

export async function createProcessCapability(payload: any) {
  const { data } = await client.post('/api/process-capabilities', payload)
  return data
}

export async function updateProcessCapability(id: number, payload: any) {
  const { data } = await client.put(`/api/process-capabilities/${id}`, payload)
  return data
}

export async function deleteProcessCapability(id: number) {
  const { data } = await client.delete(`/api/process-capabilities/${id}`)
  return data
}

// ===== 工艺配方 Recipe（7 字段，分页）=====
export async function getRecipes(params?: {
  page?: number
  page_size?: number
  keyword?: string
  state?: string
  capability?: string
}) {
  const { data } = await client.get('/api/recipes', { params })
  return data
}

export async function createRecipe(payload: any) {
  const { data } = await client.post('/api/recipes', payload)
  return data
}

export async function updateRecipe(id: number, payload: any) {
  const { data } = await client.put(`/api/recipes/${id}`, payload)
  return data
}

export async function deleteRecipe(id: number) {
  const { data } = await client.delete(`/api/recipes/${id}`)
  return data
}

// ===== 设备类型 EquipmentType（12 字段，不分页）=====
export async function getEquipmentTypes(params?: { keyword?: string; state?: string }) {
  const { data } = await client.get('/api/equipment-types', { params })
  return data
}

export async function createEquipmentType(payload: any) {
  const { data } = await client.post('/api/equipment-types', payload)
  return data
}

export async function updateEquipmentType(id: number, payload: any) {
  const { data } = await client.put(`/api/equipment-types/${id}`, payload)
  return data
}

export async function deleteEquipmentType(id: number) {
  const { data } = await client.delete(`/api/equipment-types/${id}`)
  return data
}

// ===== 设备能力 EquipmentCapability（4 字段，不分页）=====
export async function getEquipmentCapabilities(params?: { eqtype?: string; capability?: string }) {
  const { data } = await client.get('/api/equipment-capabilities', { params })
  return data
}

export async function createEquipmentCapability(payload: any) {
  const { data } = await client.post('/api/equipment-capabilities', payload)
  return data
}

export async function updateEquipmentCapability(id: number, payload: any) {
  const { data } = await client.put(`/api/equipment-capabilities/${id}`, payload)
  return data
}

export async function deleteEquipmentCapability(id: number) {
  const { data } = await client.delete(`/api/equipment-capabilities/${id}`)
  return data
}
