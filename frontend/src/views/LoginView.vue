<template>
  <div class="login-page">
    <section class="login-panel">
      <div class="login-brand">
        <div class="brand-mark">S</div>
        <div>
          <h1>SemiPLM</h1>
          <p>光电芯片制造 PLM</p>
        </div>
      </div>

      <el-form label-position="top">
        <el-form-item label="登录账号">
          <el-select v-model="username" filterable placeholder="选择用户" class="login-select">
            <el-option v-for="user in users" :key="user.username" :label="`${user.display_name} / ${user.role}`" :value="user.username">
              <div class="user-option">
                <img v-if="user.avatar_url" :src="user.avatar_url" alt="" />
                <span v-else>{{ initials(user.display_name) }}</span>
                <div>
                  <strong>{{ user.display_name }}</strong>
                  <small>{{ user.username }} · {{ user.role }}</small>
                </div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-button type="primary" class="login-button" :loading="loading" @click="doLogin">登录</el-button>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getLoginUsers } from '../api'
import { useAuth } from '../auth'

const router = useRouter()
const { login } = useAuth()
const users = ref<any[]>([])
const username = ref('')
const loading = ref(false)

function initials(name: string) {
  return (name || 'U').slice(0, 1)
}

async function doLogin() {
  if (!username.value) {
    ElMessage.warning('请选择登录账号')
    return
  }
  loading.value = true
  try {
    await login(username.value)
    router.replace('/dashboard')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  users.value = await getLoginUsers()
  username.value = localStorage.getItem('semiplm.currentUser') || users.value[0]?.username || ''
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #eef3f8 0%, #f8fafc 55%, #edf7f5 100%);
}

.login-panel {
  width: min(420px, calc(100vw - 32px));
  background: #fff;
  border: 1px solid #e5e8ef;
  border-radius: 8px;
  box-shadow: 0 18px 45px rgba(24, 39, 75, 0.12);
  padding: 32px;
}

.login-brand {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 28px;
}

.brand-mark {
  width: 46px;
  height: 46px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: #1f6f8b;
  color: #fff;
  font-weight: 700;
  font-size: 22px;
}

.login-brand h1 {
  margin: 0;
  font-size: 24px;
  color: #1f2937;
}

.login-brand p {
  margin: 4px 0 0;
  color: #667085;
}

.login-select,
.login-button {
  width: 100%;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-option img,
.user-option > span {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  display: grid;
  place-items: center;
  background: #e8f4f8;
  color: #1f6f8b;
  font-weight: 600;
}

.user-option small {
  display: block;
  color: #667085;
  line-height: 1.2;
}
</style>
