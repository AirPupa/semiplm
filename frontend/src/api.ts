import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 10000
})

client.interceptors.request.use((config) => {
  const username = localStorage.getItem('semiplm.currentUser') || 'admin'
  config.headers['X-SemiPLM-User'] = username
  return config
})

export async function getCurrentSession() {
  const { data } = await client.get('/api/session/current')
  return data
}

export async function getDashboard() {
  const { data } = await client.get('/api/dashboard')
  return data
}

export async function getProducts() {
  const { data } = await client.get('/api/products')
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

export async function getBoms() {
  const { data } = await client.get('/api/boms')
  return data
}

export async function createBom(payload: any) {
  const { data } = await client.post('/api/boms', payload)
  return data
}

export async function updateBom(id: number, payload: any) {
  const { data } = await client.put(`/api/boms/${id}`, payload)
  return data
}

export async function deleteBom(id: number) {
  const { data } = await client.delete(`/api/boms/${id}`)
  return data
}

export async function createBomItem(bomId: number, payload: any) {
  const { data } = await client.post(`/api/boms/${bomId}/items`, payload)
  return data
}

export async function updateBomItem(id: number, payload: any) {
  const { data } = await client.put(`/api/bom-items/${id}`, payload)
  return data
}

export async function deleteBomItem(id: number) {
  const { data } = await client.delete(`/api/bom-items/${id}`)
  return data
}

export async function submitBom(id: number) {
  const { data } = await client.post(`/api/boms/${id}/submit`)
  return data
}

export async function approveBom(id: number) {
  const { data } = await client.post(`/api/boms/${id}/approve`)
  return data
}

export async function transformBom(id: number, payload: any) {
  const { data } = await client.post(`/api/boms/${id}/transform`, payload)
  return data
}

export async function compareBoms(baseId: number, targetId: number) {
  const { data } = await client.get(`/api/boms/${baseId}/compare/${targetId}`)
  return data
}

export async function getBomWhereUsed(materialCode: string) {
  const { data } = await client.get(`/api/boms/where-used/${encodeURIComponent(materialCode)}`)
  return data
}

export async function getMaterials() {
  const { data } = await client.get('/api/materials')
  return data
}

export async function createMaterial(payload: any) {
  const { data } = await client.post('/api/materials', payload)
  return data
}

export async function updateMaterial(id: number, payload: any) {
  const { data } = await client.put(`/api/materials/${id}`, payload)
  return data
}

export async function deleteMaterial(id: number) {
  const { data } = await client.delete(`/api/materials/${id}`)
  return data
}

export async function getDocuments() {
  const { data } = await client.get('/api/documents')
  return data
}

export async function createDocument(payload: any) {
  const { data } = await client.post('/api/documents', payload)
  return data
}

export async function updateDocument(id: number, payload: any) {
  const { data } = await client.put(`/api/documents/${id}`, payload)
  return data
}

export async function deleteDocument(id: number) {
  const { data } = await client.delete(`/api/documents/${id}`)
  return data
}

export async function submitDocument(id: number) {
  const { data } = await client.post(`/api/documents/${id}/submit`)
  return data
}

export async function approveDocument(id: number) {
  const { data } = await client.post(`/api/documents/${id}/approve`)
  return data
}

export async function getRequirements() {
  const { data } = await client.get('/api/requirements')
  return data
}

export async function createRequirement(payload: any) {
  const { data } = await client.post('/api/requirements', payload)
  return data
}

export async function updateRequirement(id: number, payload: any) {
  const { data } = await client.put(`/api/requirements/${id}`, payload)
  return data
}

export async function deleteRequirement(id: number) {
  const { data } = await client.delete(`/api/requirements/${id}`)
  return data
}

export async function getBaselines() {
  const { data } = await client.get('/api/baselines')
  return data
}

export async function getWorkbench() {
  const { data } = await client.get('/api/workbench')
  return data
}

export async function getWorkflowTasks() {
  const { data } = await client.get('/api/workflow-tasks')
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

export async function getRoutes() {
  const { data } = await client.get('/api/process-routes')
  return data
}

export async function createProcessRoute(payload: any) {
  const { data } = await client.post('/api/process-routes', payload)
  return data
}

export async function updateProcessRoute(id: number, payload: any) {
  const { data } = await client.put(`/api/process-routes/${id}`, payload)
  return data
}

export async function deleteProcessRoute(id: number) {
  const { data } = await client.delete(`/api/process-routes/${id}`)
  return data
}

export async function createProcessStep(routeId: number, payload: any) {
  const { data } = await client.post(`/api/process-routes/${routeId}/steps`, payload)
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

export async function submitProcessRoute(id: number, payload: any) {
  const { data } = await client.post(`/api/process-routes/${id}/submit`, payload)
  return data
}

export async function approveProcessRoute(id: number, payload: any) {
  const { data } = await client.post(`/api/process-routes/${id}/approve`, payload)
  return data
}

export async function getProductProcessSteps(productId: number) {
  const { data } = await client.get(`/api/products/${productId}/process-steps`)
  return data
}

export async function getChanges() {
  const { data } = await client.get('/api/changes')
  return data
}

export async function createChange(payload: any) {
  const { data } = await client.post('/api/changes', payload)
  return data
}

export async function updateChange(id: number, payload: any) {
  const { data } = await client.put(`/api/changes/${id}`, payload)
  return data
}

export async function deleteChange(id: number) {
  const { data } = await client.delete(`/api/changes/${id}`)
  return data
}

export async function submitChange(id: number) {
  const { data } = await client.post(`/api/changes/${id}/submit`)
  return data
}

export async function analyzeChange(id: number) {
  const { data } = await client.post(`/api/changes/${id}/analyze`)
  return data
}

export async function createChangeImpact(changeId: number, payload: any) {
  const { data } = await client.post(`/api/changes/${changeId}/impacts`, payload)
  return data
}

export async function updateChangeImpact(id: number, payload: any) {
  const { data } = await client.put(`/api/change-impacts/${id}`, payload)
  return data
}

export async function deleteChangeImpact(id: number) {
  const { data } = await client.delete(`/api/change-impacts/${id}`)
  return data
}

export async function createChangeAction(changeId: number, payload: any) {
  const { data } = await client.post(`/api/changes/${changeId}/actions`, payload)
  return data
}

export async function getChangeRevisionArchive(changeId: number) {
  const { data } = await client.get(`/api/changes/${changeId}/revision-archive`)
  return data
}

export async function updateChangeAction(id: number, payload: any) {
  const { data } = await client.put(`/api/change-actions/${id}`, payload)
  return data
}

export async function closeChangeAction(id: number, payload: any) {
  const { data } = await client.post(`/api/change-actions/${id}/close`, payload)
  return data
}

export async function getChangeActions() {
  const { data } = await client.get('/api/change-actions')
  return data
}

export async function getIntegrationJobs(params: any = {}) {
  const { data } = await client.get('/api/integration-jobs', { params })
  return data
}

export async function getIntegrationSummary() {
  const { data } = await client.get('/api/integration-jobs/summary')
  return data
}

export async function startIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/start`, payload)
  return data
}

export async function completeIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/success`, payload)
  return data
}

export async function failIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/fail`, payload)
  return data
}

export async function retryIntegrationJob(id: number, payload: any) {
  const { data } = await client.post(`/api/integration-jobs/${id}/retry`, payload)
  return data
}

export async function getProjects() {
  const { data } = await client.get('/api/projects')
  return data
}

export async function getQuality() {
  const { data } = await client.get('/api/quality')
  return data
}

export async function getAdminRoles() {
  const { data } = await client.get('/api/admin/roles')
  return data
}

export async function getOrganizations() {
  const { data } = await client.get('/api/admin/organizations')
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

export async function getCodingRules() {
  const { data } = await client.get('/api/admin/foundation/coding-rules')
  return data
}

export async function createCodingRule(payload: any) {
  const { data } = await client.post('/api/admin/foundation/coding-rules', payload)
  return data
}

export async function updateCodingRule(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/coding-rules/${id}`, payload)
  return data
}

export async function deleteCodingRule(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/coding-rules/${id}`)
  return data
}

export async function getCategoryTemplates() {
  const { data } = await client.get('/api/admin/foundation/categories')
  return data
}

export async function createCategoryTemplate(payload: any) {
  const { data } = await client.post('/api/admin/foundation/categories', payload)
  return data
}

export async function updateCategoryTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/categories/${id}`, payload)
  return data
}

export async function deleteCategoryTemplate(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/categories/${id}`)
  return data
}

export async function createAttributeTemplate(categoryId: number, payload: any) {
  const { data } = await client.post(`/api/admin/foundation/categories/${categoryId}/attributes`, payload)
  return data
}

export async function updateAttributeTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/attributes/${id}`, payload)
  return data
}

export async function deleteAttributeTemplate(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/attributes/${id}`)
  return data
}

export async function getLifecycleTemplates() {
  const { data } = await client.get('/api/admin/foundation/lifecycles')
  return data
}

export async function createLifecycleTemplate(payload: any) {
  const { data } = await client.post('/api/admin/foundation/lifecycles', payload)
  return data
}

export async function updateLifecycleTemplate(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/lifecycles/${id}`, payload)
  return data
}

export async function deleteLifecycleTemplate(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/lifecycles/${id}`)
  return data
}

export async function createLifecycleState(templateId: number, payload: any) {
  const { data } = await client.post(`/api/admin/foundation/lifecycles/${templateId}/states`, payload)
  return data
}

export async function updateLifecycleState(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/lifecycle-states/${id}`, payload)
  return data
}

export async function deleteLifecycleState(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/lifecycle-states/${id}`)
  return data
}

export async function getDictionaryItems() {
  const { data } = await client.get('/api/admin/foundation/dictionaries')
  return data
}

export async function createDictionaryItem(payload: any) {
  const { data } = await client.post('/api/admin/foundation/dictionaries', payload)
  return data
}

export async function updateDictionaryItem(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/dictionaries/${id}`, payload)
  return data
}

export async function deleteDictionaryItem(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/dictionaries/${id}`)
  return data
}

export async function getAdminUsers() {
  const { data } = await client.get('/api/admin/users')
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

export async function getWorkflowTemplates() {
  const { data } = await client.get('/api/admin/workflows')
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

export async function getIntegrationEndpoints() {
  const { data } = await client.get('/api/admin/integration-endpoints')
  return data
}

export async function createIntegrationEndpoint(payload: any) {
  const { data } = await client.post('/api/admin/integration-endpoints', payload)
  return data
}

export async function updateIntegrationEndpoint(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/integration-endpoints/${id}`, payload)
  return data
}

export async function getSystemParameters() {
  const { data } = await client.get('/api/admin/foundation/system-parameters')
  return data
}

export async function createSystemParameter(payload: any) {
  const { data } = await client.post('/api/admin/foundation/system-parameters', payload)
  return data
}

export async function updateSystemParameter(id: number, payload: any) {
  const { data } = await client.put(`/api/admin/foundation/system-parameters/${id}`, payload)
  return data
}

export async function deleteSystemParameter(id: number) {
  const { data } = await client.delete(`/api/admin/foundation/system-parameters/${id}`)
  return data
}

export async function getAuditLogs(params?: { object_type?: string; action?: string; limit?: number }) {
  const { data } = await client.get('/api/audit-logs', { params })
  return data
}

export async function getSubstituteMaterials() {
  const { data } = await client.get('/api/substitute-materials')
  return data
}

export async function createSubstituteMaterial(payload: any) {
  const { data } = await client.post('/api/substitute-materials', payload)
  return data
}

export async function updateSubstituteMaterial(id: number, payload: any) {
  const { data } = await client.put(`/api/substitute-materials/${id}`, payload)
  return data
}

export async function deleteSubstituteMaterial(id: number) {
  const { data } = await client.delete(`/api/substitute-materials/${id}`)
  return data
}

export async function getSuppliers() {
  const { data } = await client.get('/api/suppliers')
  return data
}

export async function createSupplier(payload: any) {
  const { data } = await client.post('/api/suppliers', payload)
  return data
}

export async function updateSupplier(id: number, payload: any) {
  const { data } = await client.put(`/api/suppliers/${id}`, payload)
  return data
}

export async function deleteSupplier(id: number) {
  const { data } = await client.delete(`/api/suppliers/${id}`)
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

export async function getProjectTemplates() {
  const { data } = await client.get('/api/project-templates')
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

export async function getQualityCAPAs() {
  const { data } = await client.get('/api/quality/capas')
  return data
}

export async function createQualityCAPA(payload: any) {
  const { data } = await client.post('/api/quality/capas', payload)
  return data
}

export async function updateQualityCAPA(id: number, payload: any) {
  const { data } = await client.put(`/api/quality/capas/${id}`, payload)
  return data
}

export async function deleteQualityCAPA(id: number) {
  const { data } = await client.delete(`/api/quality/capas/${id}`)
  return data
}

export async function createCAPAFromIssue(issueId: number) {
  const { data } = await client.post(`/api/quality/issues/${issueId}/create-capa`)
  return data
}

export async function getProblemReports() {
  const { data } = await client.get('/api/problem-reports')
  return data
}

export async function createProblemReport(payload: any) {
  const { data } = await client.post('/api/problem-reports', payload)
  return data
}

export async function updateProblemReport(id: number, payload: any) {
  const { data } = await client.put(`/api/problem-reports/${id}`, payload)
  return data
}

export async function deleteProblemReport(id: number) {
  const { data } = await client.delete(`/api/problem-reports/${id}`)
  return data
}

export async function getProcessParameters() {
  const { data } = await client.get('/api/process-parameters')
  return data
}

export async function createProcessParameter(payload: any) {
  const { data } = await client.post('/api/process-parameters', payload)
  return data
}

export async function updateProcessParameter(id: number, payload: any) {
  const { data } = await client.put(`/api/process-parameters/${id}`, payload)
  return data
}

export async function deleteProcessParameter(id: number) {
  const { data } = await client.delete(`/api/process-parameters/${id}`)
  return data
}
