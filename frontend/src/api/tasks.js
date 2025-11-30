import api from './index'

/**
 * 获取任务列表
 * @param {Object} params - 查询参数
 */
export function listTasks(params = {}) {
  return api.get('/tasks/', { params })
}

/**
 * 获取任务详情
 * @param {string} taskId - 任务ID
 */
export function getTask(taskId) {
  return api.get(`/tasks/${taskId}`)
}

/**
 * 启动书籍下载任务
 * @param {string} bookId - 书籍UUID
 * @param {number} startChapter - 起始章节索引（可选，0-indexed）
 * @param {number} endChapter - 结束章节索引（可选，0-indexed）
 */
export function startDownload(bookId, startChapter, endChapter) {
  const params = {}
  if (startChapter !== undefined) params.start_chapter = startChapter
  if (endChapter !== undefined) params.end_chapter = endChapter
  return api.post(`/tasks/${bookId}/download`, null, { params })
}

/**
 * 取消任务
 * @param {string} taskId - 任务ID
 */
export function cancelTask(taskId) {
  return api.post(`/tasks/${taskId}/cancel`)
}
