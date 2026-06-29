<template>
  <div v-loading="loading">
    <div class="admin-summary">
      <div><span>角色</span><strong>{{ roles.length }}</strong></div>
      <div><span>用户</span><strong>{{ users.length }}</strong></div>
      <div><span>流程模板</span><strong>{{ workflows.length }}</strong></div>
      <div><span>集成端点</span><strong>{{ endpoints.length }}</strong></div>
    </div>

    <el-tabs class="panel">
      <el-tab-pane label="角色与用户">
        <div class="grid-2">
          <div>
            <div class="toolbar">
              <strong>角色权限</strong>
              <el-button type="primary" :icon="Plus" @click="openRoleCreate">新增角色</el-button>
            </div>
            <el-table :data="roles" height="520" size="small">
              <el-table-column prop="code" label="角色编码" width="130" />
              <el-table-column prop="name" label="角色名称" width="130" />
              <el-table-column prop="description" label="说明" min-width="180" />
              <el-table-column prop="status" label="状态" width="80" />
              <el-table-column label="操作" width="130" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="openRoleEdit(row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="removeRole(row)">删</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div>
            <div class="toolbar">
              <strong>用户组织</strong>
              <el-button type="primary" :icon="Plus" @click="openUserCreate">新增用户</el-button>
            </div>
            <el-table :data="users" height="520" size="small">
              <el-table-column prop="username" label="账号" width="110" />
              <el-table-column prop="display_name" label="姓名" width="100" />
              <el-table-column prop="role" label="角色" width="130" />
              <el-table-column prop="department" label="部门" min-width="150" />
              <el-table-column label="操作" width="130" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="openUserEdit(row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="removeUser(row)">删</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="流程模板">
        <div class="grid-main">
          <div>
            <div class="toolbar">
              <strong>流程模板</strong>
              <el-button type="primary" :icon="Plus" @click="openWorkflowCreate">新增模板</el-button>
            </div>
            <el-table :data="workflows" highlight-current-row @current-change="selectedWorkflow = $event" height="560">
              <el-table-column prop="code" label="编码" width="140" />
              <el-table-column prop="name" label="名称" min-width="180" />
              <el-table-column prop="object_type" label="对象" width="90" />
              <el-table-column prop="project_type" label="项目类型" width="110" />
              <el-table-column prop="status" label="状态" width="80" />
              <el-table-column label="操作" width="90">
                <template #default="{ row }"><el-button size="small" @click.stop="openWorkflowEdit(row)">编辑</el-button></template>
              </el-table-column>
            </el-table>
          </div>
          <div>
            <div class="toolbar">
              <strong>{{ selectedWorkflow?.name || '流程节点' }}</strong>
              <el-button :icon="Plus" @click="openNodeCreate" :disabled="!selectedWorkflow">新增节点</el-button>
            </div>
            <div class="workflow-node-list">
              <div v-for="node in selectedWorkflow?.nodes || []" :key="node.id" class="workflow-node">
                <strong>{{ node.sequence }}. {{ node.name }}</strong>
                <span>{{ node.role_name }} · {{ node.action_type }} · SLA {{ node.sla_hours }}h</span>
                <el-button size="small" type="danger" @click="removeNode(node)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="ERP / MES 接口">
        <div class="toolbar">
          <div><strong>集成端点配置</strong><span class="muted"> · 真实接口地址、方向、对象范围，为后续对接 ERP/MES 做准备</span></div>
          <el-button type="primary" :icon="Plus" @click="openEndpointCreate">新增端点</el-button>
        </div>
        <el-table :data="endpoints" stripe height="560">
          <el-table-column prop="code" label="编码" width="120" />
          <el-table-column prop="name" label="名称" width="180" />
          <el-table-column prop="system_type" label="系统" width="90" />
          <el-table-column prop="base_url" label="接口地址" min-width="220" />
          <el-table-column prop="direction" label="方向" width="80" />
          <el-table-column prop="status" label="状态" width="80" />
          <el-table-column prop="object_scope" label="对象范围" min-width="220" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }"><el-button size="small" @click="openEndpointEdit(row)">编辑</el-button></template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="roleDialog" :title="roleId ? '编辑角色' : '新增角色'" width="640px">
      <el-form :model="roleForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="roleForm.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="roleForm.name" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="roleForm.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="权限" class="form-wide"><el-input v-model="roleForm.permissions" /></el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="roleForm.description" type="textarea" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="roleDialog = false">取消</el-button><el-button type="primary" @click="saveRole">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="userDialog" :title="userId ? '编辑用户' : '新增用户'" width="560px">
      <el-form :model="userForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="账号"><el-input v-model="userForm.username" /></el-form-item>
          <el-form-item label="姓名"><el-input v-model="userForm.display_name" /></el-form-item>
          <el-form-item label="角色"><el-select v-model="userForm.role"><el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.name" /></el-select></el-form-item>
          <el-form-item label="部门"><el-input v-model="userForm.department" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="userDialog = false">取消</el-button><el-button type="primary" @click="saveUser">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="workflowDialog" :title="workflowId ? '编辑流程模板' : '新增流程模板'" width="680px">
      <el-form :model="workflowForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="workflowForm.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="workflowForm.name" /></el-form-item>
          <el-form-item label="对象类型"><el-input v-model="workflowForm.object_type" /></el-form-item>
          <el-form-item label="项目类型"><el-input v-model="workflowForm.project_type" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="workflowForm.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="说明" class="form-wide"><el-input v-model="workflowForm.description" type="textarea" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="workflowDialog = false">取消</el-button><el-button type="primary" @click="saveWorkflow">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="nodeDialog" title="新增流程节点" width="560px">
      <el-form :model="nodeForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="序号"><el-input-number v-model="nodeForm.sequence" :min="1" /></el-form-item>
          <el-form-item label="节点"><el-input v-model="nodeForm.name" /></el-form-item>
          <el-form-item label="角色"><el-select v-model="nodeForm.role_name"><el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.name" /></el-select></el-form-item>
          <el-form-item label="动作"><el-input v-model="nodeForm.action_type" /></el-form-item>
          <el-form-item label="SLA小时"><el-input-number v-model="nodeForm.sla_hours" :min="1" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="nodeDialog = false">取消</el-button><el-button type="primary" @click="saveNode">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="endpointDialog" :title="endpointId ? '编辑集成端点' : '新增集成端点'" width="720px">
      <el-form :model="endpointForm" label-width="90px">
        <div class="form-grid">
          <el-form-item label="编码"><el-input v-model="endpointForm.code" /></el-form-item>
          <el-form-item label="名称"><el-input v-model="endpointForm.name" /></el-form-item>
          <el-form-item label="系统"><el-select v-model="endpointForm.system_type"><el-option label="ERP" value="ERP" /><el-option label="MES" value="MES" /><el-option label="QMS" value="QMS" /></el-select></el-form-item>
          <el-form-item label="方向"><el-select v-model="endpointForm.direction"><el-option label="下发" value="下发" /><el-option label="接收" value="接收" /><el-option label="双向" value="双向" /></el-select></el-form-item>
          <el-form-item label="认证"><el-input v-model="endpointForm.auth_type" /></el-form-item>
          <el-form-item label="状态"><el-select v-model="endpointForm.status"><el-option label="启用" value="启用" /><el-option label="停用" value="停用" /></el-select></el-form-item>
          <el-form-item label="负责人"><UserSelect v-model="endpointForm.owner" /></el-form-item>
          <el-form-item label="接口地址" class="form-wide"><el-input v-model="endpointForm.base_url" /></el-form-item>
          <el-form-item label="对象范围" class="form-wide"><el-input v-model="endpointForm.object_scope" type="textarea" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="endpointDialog = false">取消</el-button><el-button type="primary" @click="saveEndpoint">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import {
  createAdminRole,
  createAdminUser,
  createIntegrationEndpoint,
  createWorkflowNode,
  createWorkflowTemplate,
  deleteAdminRole,
  deleteAdminUser,
  deleteWorkflowNode,
  getAdminRoles,
  getAdminUsers,
  getIntegrationEndpoints,
  getWorkflowTemplates,
  updateAdminRole,
  updateAdminUser,
  updateIntegrationEndpoint,
  updateWorkflowTemplate
} from '../api'
import UserSelect from '../components/UserSelect.vue'

const loading = ref(true)
const roles = ref<any[]>([])
const users = ref<any[]>([])
const workflows = ref<any[]>([])
const endpoints = ref<any[]>([])
const selectedWorkflow = ref<any>()

const roleDialog = ref(false)
const userDialog = ref(false)
const workflowDialog = ref(false)
const nodeDialog = ref(false)
const endpointDialog = ref(false)
const roleId = ref<number | null>(null)
const userId = ref<number | null>(null)
const workflowId = ref<number | null>(null)
const endpointId = ref<number | null>(null)

const emptyRole = { code: '', name: '', description: '', permissions: '', status: '启用' }
const emptyUser = { username: '', display_name: '', role: '', department: '' }
const emptyWorkflow = { code: '', name: '', object_type: '', project_type: '', status: '启用', description: '' }
const emptyNode = { sequence: 1, name: '', role_name: '', action_type: '审批', sla_hours: 24 }
const emptyEndpoint = { code: '', name: '', system_type: 'ERP', base_url: '', auth_type: 'Token', direction: '双向', status: '启用', owner: '', object_scope: '' }
const roleForm = ref<any>({ ...emptyRole })
const userForm = ref<any>({ ...emptyUser })
const workflowForm = ref<any>({ ...emptyWorkflow })
const nodeForm = ref<any>({ ...emptyNode })
const endpointForm = ref<any>({ ...emptyEndpoint })

async function loadAll() {
  const [roleRows, userRows, workflowRows, endpointRows] = await Promise.all([getAdminRoles(), getAdminUsers(), getWorkflowTemplates(), getIntegrationEndpoints()])
  roles.value = roleRows
  users.value = userRows
  workflows.value = workflowRows
  endpoints.value = endpointRows
  selectedWorkflow.value = workflows.value.find((item) => item.id === selectedWorkflow.value?.id) || workflows.value[0]
}

function openRoleCreate() { roleId.value = null; roleForm.value = { ...emptyRole }; roleDialog.value = true }
function openRoleEdit(row: any) { roleId.value = row.id; roleForm.value = { ...row }; roleDialog.value = true }
async function saveRole() {
  roleId.value ? await updateAdminRole(roleId.value, roleForm.value) : await createAdminRole(roleForm.value)
  ElMessage.success('角色已保存')
  roleDialog.value = false
  await loadAll()
}
async function removeRole(row: any) {
  await ElMessageBox.confirm(`确认删除角色 ${row.name}？被用户使用的角色会被后端阻止删除。`, '删除确认', { type: 'warning' })
  await deleteAdminRole(row.id)
  ElMessage.success('角色已删除')
  await loadAll()
}

function openUserCreate() { userId.value = null; userForm.value = { ...emptyUser, role: roles.value[0]?.name }; userDialog.value = true }
function openUserEdit(row: any) { userId.value = row.id; userForm.value = { ...row }; userDialog.value = true }
async function saveUser() {
  userId.value ? await updateAdminUser(userId.value, userForm.value) : await createAdminUser(userForm.value)
  ElMessage.success('用户已保存')
  userDialog.value = false
  await loadAll()
}
async function removeUser(row: any) {
  await ElMessageBox.confirm(`确认删除用户 ${row.display_name}？`, '删除确认', { type: 'warning' })
  await deleteAdminUser(row.id)
  ElMessage.success('用户已删除')
  await loadAll()
}

function openWorkflowCreate() { workflowId.value = null; workflowForm.value = { ...emptyWorkflow }; workflowDialog.value = true }
function openWorkflowEdit(row: any) { workflowId.value = row.id; workflowForm.value = { ...row }; workflowDialog.value = true }
async function saveWorkflow() {
  const row = workflowId.value ? await updateWorkflowTemplate(workflowId.value, workflowForm.value) : await createWorkflowTemplate(workflowForm.value)
  selectedWorkflow.value = row
  ElMessage.success('流程模板已保存')
  workflowDialog.value = false
  await loadAll()
}
function openNodeCreate() {
  nodeForm.value = { ...emptyNode, sequence: (selectedWorkflow.value?.nodes?.length || 0) + 1, role_name: roles.value[0]?.name }
  nodeDialog.value = true
}
async function saveNode() {
  await createWorkflowNode(selectedWorkflow.value.id, nodeForm.value)
  ElMessage.success('流程节点已保存')
  nodeDialog.value = false
  await loadAll()
}
async function removeNode(row: any) {
  await deleteWorkflowNode(row.id)
  ElMessage.success('流程节点已删除')
  await loadAll()
}

function openEndpointCreate() { endpointId.value = null; endpointForm.value = { ...emptyEndpoint }; endpointDialog.value = true }
function openEndpointEdit(row: any) { endpointId.value = row.id; endpointForm.value = { ...row }; endpointDialog.value = true }
async function saveEndpoint() {
  endpointId.value ? await updateIntegrationEndpoint(endpointId.value, endpointForm.value) : await createIntegrationEndpoint(endpointForm.value)
  ElMessage.success('集成端点已保存')
  endpointDialog.value = false
  await loadAll()
}

onMounted(async () => {
  await loadAll()
  loading.value = false
})
</script>
