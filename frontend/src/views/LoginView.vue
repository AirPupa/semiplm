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

      <el-form label-position="top" @submit.prevent="doLogin">
        <el-form-item label="账号">
          <el-input v-model="username" placeholder="请输入登录账号" prefix-icon="User" @keyup.enter="doLogin" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password @keyup.enter="doLogin" />
        </el-form-item>
        <el-button type="primary" class="login-button" :loading="loading" @click="doLogin">登录</el-button>
      </el-form>

      <div class="login-hint">默认密码：123456</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../auth'

const router = useRouter()
const { login } = useAuth()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function doLogin() {
  if (!username.value) {
    ElMessage.warning('请输入账号')
    return
  }
  if (!password.value) {
    ElMessage.warning('请输入密码')
    return
  }
  loading.value = true
  try {
    await login(username.value, password.value)
    router.replace('/dashboard')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '登录失败，请检查账号和密码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
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

.login-button {
  width: 100%;
}

.login-hint {
  margin-top: 12px;
  text-align: center;
  color: #999;
  font-size: 12px;
}
</style>
