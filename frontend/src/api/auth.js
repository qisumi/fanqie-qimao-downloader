import api from './index'

/**
 * 登录
 * @param {string} password - 密码
 */
export function login(password) {
  return api.post('/auth/login', { password })
}

/**
 * 登出
 */
export function logout() {
  return api.post('/auth/logout')
}

/**
 * 检查认证状态
 */
export function checkAuthStatus() {
  return api.get('/auth/status')
}
