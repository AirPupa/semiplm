<template>
  <el-select v-model="value" filterable clearable :placeholder="placeholder">
    <el-option
      v-for="user in users"
      :key="user.id || user.username"
      :label="`${user.display_name} / ${user.role}`"
      :value="user.display_name"
    />
  </el-select>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getAdminUsers } from '../api'

const props = withDefaults(defineProps<{ modelValue: string; placeholder?: string }>(), {
  placeholder: '请选择人员',
})
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const users = ref<any[]>([])
const value = computed({
  get: () => props.modelValue,
  set: (next: string) => emit('update:modelValue', next),
})

onMounted(async () => {
  users.value = await getAdminUsers()
})
</script>
