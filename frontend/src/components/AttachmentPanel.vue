<template>
  <div class="attachment-panel">
    <div class="attachment-toolbar">
      <strong>附件 ({{ items.length }})</strong>
      <el-upload :show-file-list="false" :before-upload="handleUpload" :disabled="!canEdit">
        <el-button size="small" :disabled="!canEdit">上传附件</el-button>
      </el-upload>
    </div>
    <el-table :data="items" size="small" max-height="300" v-loading="loading">
      <el-table-column prop="file_name" label="文件名" min-width="180" show-overflow-tooltip />
      <el-table-column label="大小" width="90">
        <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
      </el-table-column>
      <el-table-column prop="uploaded_by" label="上传人" width="100" />
      <el-table-column prop="uploaded_at" label="上传时间" width="140" />
      <el-table-column prop="description" label="说明" min-width="120" show-overflow-tooltip />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <el-button size="small" @click="handleDownload(row)">下载</el-button>
            <el-button size="small" type="danger" :disabled="!canEdit" @click="handleDelete(row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref, watch } from 'vue'
import { deleteAttachment, downloadAttachment, getAttachments, uploadAttachment } from '../api'

const props = defineProps<{
  objectType: string
  objectId: number
  canEdit?: boolean
}>()

const items = ref<any[]>([])
const loading = ref(false)

async function loadAttachments() {
  if (!props.objectId) return
  loading.value = true
  try {
    items.value = await getAttachments(props.objectType, props.objectId)
  } finally {
    loading.value = false
  }
}

async function handleUpload(file: File) {
  if (!props.objectId) {
    ElMessage.warning('请先保存记录后再上传附件')
    return false
  }
  try {
    await uploadAttachment(props.objectType, props.objectId, file)
    ElMessage.success('附件上传成功')
    await loadAttachments()
  } catch {
    ElMessage.error('上传失败')
  }
  return false
}

async function handleDownload(row: any) {
  await downloadAttachment(row.id)
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除附件 ${row.file_name}？`, '删除确认', { type: 'warning' })
    await deleteAttachment(row.id)
    ElMessage.success('附件已删除')
    await loadAttachments()
  } catch {
    // 用户取消删除时保持静默。
  }
}

function formatSize(bytes?: number | null): string {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

watch(() => [props.objectType, props.objectId], () => loadAttachments())

onMounted(() => loadAttachments())
</script>

<style scoped>
.attachment-panel {
  margin-top: 12px;
}
.attachment-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
</style>
