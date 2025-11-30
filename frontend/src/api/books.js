import api from './index'

/**
 * 搜索书籍
 * @param {string} platform - fanqie | qimao
 * @param {string} keyword - 搜索关键词
 * @param {number} page - 页码
 */
export function searchBooks(platform, keyword, page = 0) {
  return api.get('/books/search', {
    params: { platform, q: keyword, page }
  })
}

/**
 * 添加书籍到书库
 * @param {string} platform - fanqie | qimao
 * @param {string} bookId - 平台书籍ID
 */
export function addBook(platform, bookId) {
  return api.post(`/books/add/${platform}/${bookId}`)
}

/**
 * 获取书籍列表
 * @param {Object} params - 查询参数
 */
export function listBooks(params = {}) {
  return api.get('/books/', { params })
}

/**
 * 获取书籍详情
 * @param {string} id - 书籍UUID
 */
export function getBook(id) {
  return api.get(`/books/${id}`)
}

/**
 * 刷新书籍信息
 * @param {string} id - 书籍UUID
 */
export function refreshBook(id) {
  return api.post(`/books/${id}/refresh`)
}

/**
 * 获取书籍状态（轻量级，用于轮询）
 * @param {string} id - 书籍UUID
 */
export async function getBookStatus(id) {
  const response = await api.get(`/books/${id}/status`)
  return response.data
}

/**
 * 获取章节状态摘要（热力图数据）
 * @param {string} id - 书籍UUID
 * @param {number} segmentSize - 每段章节数量
 */
export async function getChapterSummary(id, segmentSize = 50) {
  const response = await api.get(`/books/${id}/chapters/summary`, {
    params: { segment_size: segmentSize }
  })
  return response.data
}

/**
 * 删除书籍
 * @param {string} id - 书籍UUID
 */
export function deleteBook(id) {
  return api.delete(`/books/${id}`, { params: { delete_files: true } })
}

/**
 * 生成EPUB
 * @param {string} id - 书籍UUID
 */
export function generateEpub(id) {
  return api.post(`/books/${id}/epub`)
}

/**
 * 下载EPUB
 * @param {string} id - 书籍UUID
 */
export function getEpubDownloadUrl(id) {
  return `/api/books/${id}/epub/download`
}

