import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

/**
 * 认证相关组合式函数
 */
export function useAuth() {
  const router = useRouter()
  const userStore = useUserStore()

  const isAuthenticated = computed(() => userStore.isAuthenticated)
  const isLoading = computed(() => userStore.loading)
  const requireAuth = computed(() => userStore.requireAuth)

  /**
   * 登录
   * @param {string} password - 密码
   * @returns {Promise<{success: boolean, message?: string}>}
   */
  async function login(password) {
    return await userStore.login(password)
  }

  /**
   * 登出
   */
  async function logout() {
    await userStore.logout()
    router.push({ name: 'login' })
  }

  /**
   * 检查认证状态
   */
  async function checkAuth() {
    await userStore.checkAuth()
  }

  /**
   * 需要认证时重定向到登录页
   * @param {string} redirect - 登录后重定向的路径
   */
  function requireLogin(redirect = '/') {
    if (!isAuthenticated.value) {
      router.push({ name: 'login', query: { redirect } })
      return false
    }
    return true
  }

  return {
    isAuthenticated,
    isLoading,
    requireAuth,
    login,
    logout,
    checkAuth,
    requireLogin
  }
}

export default useAuth
