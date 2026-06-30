import { computed, ref } from 'vue'
import { getCurrentSession, loginWithPassword } from './api'

const session = ref<any>(null)
const loadingSession = ref(false)

export function useAuth() {
  const permissions = computed(() => new Set(session.value?.permissions || []))
  const currentUser = computed(() => session.value?.user)

  function can(permission: string | string[]) {
    if (permissions.value.has('all')) return true
    const required = Array.isArray(permission) ? permission : [permission]
    return required.some((item) => permissions.value.has(item))
  }

  async function refreshSession() {
    loadingSession.value = true
    try {
      session.value = await getCurrentSession()
    } finally {
      loadingSession.value = false
    }
  }

  async function login(username: string, password: string) {
    const data = await loginWithPassword(username, password)
    localStorage.setItem('semiplm.currentUser', username)
    session.value = data
  }

  function logout() {
    localStorage.removeItem('semiplm.currentUser')
    session.value = null
  }

  return {
    can,
    currentUser,
    login,
    loadingSession,
    logout,
    permissions,
    refreshSession,
    session,
  }
}
