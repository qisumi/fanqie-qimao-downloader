import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import * as userApi from '@/api/users'

export const useUserStore = defineStore('user', () => {
  const authenticated = ref(false)
  const requireAuth = ref(true) // 是否需要认证（后端可能未设置密码）
  const loading = ref(false)
  const userLoading = ref(false)
  const users = ref([])
  const currentUser = ref(null)
  const STORAGE_KEY = 'fanqieqimao-current-user'
  
  const isAuthenticated = computed(() => authenticated.value || !requireAuth.value)
  const currentUsername = computed(() => currentUser.value?.username || '')
  const currentUserId = computed(() => currentUser.value?.id || null)
  
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
      } else {
        // 网络错误或其他错误，假设需要认证但未认证
        requireAuth.value = true
        authenticated.value = false
      }
    } finally {
      loading.value = false
    }
  }

  function persistCurrentUser() {
    if (currentUser.value?.username) {
      localStorage.setItem(STORAGE_KEY, currentUser.value.username)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  async function fetchUsers() {
    userLoading.value = true
    try {
      const response = await userApi.listUsers()
      users.value = response.data.users || []

      const savedName = localStorage.getItem(STORAGE_KEY)
      if (savedName) {
        const savedUser = users.value.find(u => u.username === savedName)
        if (savedUser) {
          currentUser.value = savedUser
        }
      }

      if (!currentUser.value && users.value.length > 0) {
        currentUser.value = users.value[0]
        persistCurrentUser()
      }

      return users.value
    } catch (error) {
      console.error('Failed to fetch users:', error)
      users.value = []
      return []
    } finally {
      userLoading.value = false
    }
  }

  async function switchUser(username) {
    const name = (username || '').trim()
    if (!name) {
      throw new Error('用户名不能为空')
    }

    userLoading.value = true
    try {
      let target = users.value.find(u => u.username === name)
      if (!target) {
        const response = await userApi.createUser(name)
        target = response.data
        users.value.push(target)
      }
      currentUser.value = target
      persistCurrentUser()
      return target
    } catch (error) {
      const message = error.response?.data?.detail || error.message || '切换用户失败'
      throw new Error(message)
    } finally {
      userLoading.value = false
    }
  }

  async function renameUser(userId, username) {
    const name = (username || '').trim()
    if (!name) {
      throw new Error('新用户名不能为空')
    }

    userLoading.value = true
    try {
      const response = await userApi.renameUser(userId, name)
      const updated = response.data
      const index = users.value.findIndex(u => u.id === userId)
      if (index !== -1) {
        users.value[index] = updated
      }
      if (currentUser.value?.id === userId) {
        currentUser.value = updated
        persistCurrentUser()
      }
      return updated
    } catch (error) {
      const message = error.response?.data?.detail || error.message || '重命名失败'
      throw new Error(message)
    } finally {
      userLoading.value = false
    }
  }

  async function deleteUser(userId) {
    userLoading.value = true
    try {
      await userApi.deleteUser(userId)
      const index = users.value.findIndex(u => u.id === userId)
      if (index !== -1) {
        users.value.splice(index, 1)
      }

      if (currentUser.value?.id === userId) {
        currentUser.value = users.value[0] || null
        persistCurrentUser()
      }
    } catch (error) {
      const message = error.response?.data?.detail || '删除用户失败'
      throw new Error(message)
    } finally {
      userLoading.value = false
    }
  }

  async function initUserContext() {
    await fetchUsers()
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
    userLoading,
    users,
    currentUser,
    currentUsername,
    currentUserId,
    isAuthenticated,
    checkAuth,
    initUserContext,
    fetchUsers,
    switchUser,
    renameUser,
    deleteUser,
    login,
    logout
  }
})
