import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const authenticated = ref(false)
  const requireAuth = ref(true) // 是否需要认证（后端可能未设置密码）
  const loading = ref(false)
  
  const isAuthenticated = computed(() => authenticated.value || !requireAuth.value)
  
  /**
   * 检查认证状态
   */
  async function checkAuth() {
    try {
      loading.value = true
      const response = await authApi.checkAuthStatus()
      authenticated.value = response.data.authenticated
      requireAuth.value = response.data.require_auth !== false
    } catch (error) {
      // 如果接口不存在，假设不需要认证
      if (error.response?.status === 404) {
        requireAuth.value = false
        authenticated.value = true
      }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 登录
   */
  async function login(password) {
    loading.value = true
    try {
      const response = await authApi.login(password)
      if (response.data.success) {
        authenticated.value = true
        return { success: true }
      }
      return { success: false, message: response.data.message }
    } catch (error) {
      const message = error.response?.data?.detail || '登录失败'
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 登出
   */
  async function logout() {
    try {
      await authApi.logout()
    } finally {
      authenticated.value = false
    }
  }
  
  return {
    authenticated,
    requireAuth,
    loading,
    isAuthenticated,
    checkAuth,
    login,
    logout
  }
})
