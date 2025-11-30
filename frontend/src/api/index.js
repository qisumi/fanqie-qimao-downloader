import axios from 'axios'
import router from '@/router'

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true, // 携带 Cookie
})

// Request interceptor
api.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 未认证，跳转到登录页
      router.push({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
    }
    return Promise.reject(error)
  }
)

export default api
