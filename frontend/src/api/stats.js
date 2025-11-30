import api from './index'

/**
 * 获取系统统计信息
 */
export function getStats() {
  return api.get('/stats/')
}
