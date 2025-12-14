import api from './index'

/**
 * 搜索书籍
 * @param {string} platform - fanqie | qimao | biquge
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
 * @param {string} platform - fanqie | qimao | biquge
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
 * 下载EPUB
 * @param {string} id - 书籍UUID
 */
export function getEpubDownloadUrl(id) {
  return `/api/books/${id}/epub/download`
}

/**
/**
 * 下载TXT
 * @param {string} id - 书籍UUID
 */
export function getTxtDownloadUrl(id) {
  return `/api/books/${id}/txt/download`
}
// TXT 生成已从前端UI移除，保留下载接口

/**
 * 发起 EPUB 下载请求（返回 blob 或 202 状态）
 * @param {string} id
 */
export function downloadEpub(id) {
  return api.get(`/books/${id}/epub/download`, { responseType: 'blob' })
}

/**
 * 查询 EPUB 生成状态
 * @param {string} id
 */
export async function getEpubStatus(id) {
  const resp = await api.get(`/books/${id}/epub/status`)
  return resp.data
}

/**
 * 发起 TXT 下载请求（返回 blob 或 202 状态）
 * @param {string} id
 */
export function downloadTxt(id) {
  return api.get(`/books/${id}/txt/download`, { responseType: 'blob' })
}

/**
 * 查询 TXT 生成状态
 * @param {string} id
 */
export async function getTxtStatus(id) {
  const resp = await api.get(`/books/${id}/txt/status`)
  return resp.data
}
