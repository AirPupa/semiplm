import { computed, ref } from 'vue'
import { getCurrentSession } from './api'

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

  return {
    can,
    currentUser,
    loadingSession,
    permissions,
    refreshSession,
    session,
    setCurrentUser,
  }
}
