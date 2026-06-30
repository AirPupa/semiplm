<template>
  <div class="login-page">
    <div class="login-left">
      <div class="login-left-content">
        <div class="login-brand">
          <div class="brand-mark">S</div>
          <div>
            <h1>SemiPLM</h1>
            <p>光电芯片制造产品生命周期管理</p>
          </div>
        </div>
        <div class="login-features">
          <div class="feature-item">
            <div class="feature-icon">01</div>
            <div>
              <div class="feature-title">单一产品数据源</div>
              <div class="feature-desc">需求、产品、BOM、工艺、变更、项目全链路追溯</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">02</div>
            <div>
              <div class="feature-title">工程变更闭环</div>
              <div class="feature-desc">PR → ECR → ECO → ECN → ECA 全链路管控</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">03</div>
            <div>
              <div class="feature-title">研产数据同步</div>
              <div class="feature-desc">ERP / MES / QMS 集成队列，发布即下发</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="login-right">
      <div class="login-form-wrap">
        <h2 class="login-title">欢迎登录</h2>
        <p class="login-subtitle">请输入账号和密码登录系统</p>

        <el-form ref="formRef" :model="loginForm" :rules="rules" label-position="top" @submit.prevent="doLogin">
          <el-form-item label="账号" prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入登录账号"
              prefix-icon="User"
              size="large"
              clearable
              @keyup.enter="doLogin"
            />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              size="large"
              @keyup.enter="doLogin"
            />
          </el-form-item>
          <div class="login-options">
            <el-checkbox v-model="rememberMe">记住账号</el-checkbox>
          </div>
          <el-button type="primary" size="large" class="login-button" :loading="loading" @click="doLogin">
            登 录
          </el-button>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../auth'

const router = useRouter()
const { login } = useAuth()
const formRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function doLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await login(loginForm.username, loginForm.password)
      if (rememberMe.value) {
        localStorage.setItem('semiplm.rememberUser', loginForm.username)
      } else {
        localStorage.removeItem('semiplm.rememberUser')
      }
      router.replace('/dashboard')
    } catch (e: any) {
      const msg = e?.response?.data?.detail || '登录失败，请检查账号和密码'
      ElMessage.error(msg)
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  const saved = localStorage.getItem('semiplm.rememberUser')
  if (saved) {
    loginForm.username = saved
    rememberMe.value = true
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
}

/* Left brand panel */
.login-left {
  flex: 1;
  background: linear-gradient(160deg, #1a4d6e 0%, #1f6f8b 45%, #2a8aa5 100%);
  display: flex;
  align-items: center;
  padding: 48px;
  position: relative;
  overflow: hidden;
}
.login-left::before {
  content: '';
  position: absolute;
  top: -120px;
  right: -120px;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}
.login-left::after {
  content: '';
  position: absolute;
  bottom: -80px;
  left: -80px;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
}

.login-left-content {
  position: relative;
  z-index: 1;
  max-width: 480px;
}

.login-brand {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 56px;
}
.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  font-weight: 700;
  font-size: 24px;
  backdrop-filter: blur(8px);
}
.login-brand h1 {
  margin: 0;
  font-size: 26px;
  color: #fff;
}
.login-brand p {
  margin: 4px 0 0;
  color: rgba(255, 255, 255, 0.75);
  font-size: 14px;
}

.login-features {
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.feature-item {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.feature-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}
.feature-title {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}
.feature-desc {
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  line-height: 1.5;
}

/* Right form panel */
.login-right {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: #fff;
}
.login-form-wrap {
  width: 100%;
  max-width: 360px;
}
.login-title {
  margin: 0 0 8px;
  font-size: 24px;
  color: #1f2937;
}
.login-subtitle {
  margin: 0 0 32px;
  color: #6b7280;
  font-size: 14px;
}
.login-options {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}
.login-button {
  width: 100%;
  letter-spacing: 4px;
}

@media (max-width: 900px) {
  .login-left {
    display: none;
  }
  .login-right {
    width: 100%;
  }
}
</style>
