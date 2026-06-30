import { computed, ref } from 'vue'
import { getCurrentSession, updateCurrentProfile } from './api'

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

  function setCurrentUser(username: string) {
    localStorage.setItem('semiplm.currentUser', username)
  }

  async function login(username: string) {
    setCurrentUser(username)
    await refreshSession()
  }

  function logout() {
    localStorage.removeItem('semiplm.currentUser')
    session.value = null
  }

  async function updateProfile(payload: { display_name?: string; avatar_url?: string }) {
    const user = await updateCurrentProfile(payload)
    if (session.value) session.value.user = user
    return user
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
    setCurrentUser,
    updateProfile,
  }
}
