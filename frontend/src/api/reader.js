import api from './index'

/**
 * 获取目录
 */
export function getToc(bookId, userId) {
  return api.get(`/books/${bookId}/toc`, {
    params: { user_id: userId }
  })
}

/**
 * 获取章节内容
 */
export function getChapterContent(bookId, chapterId, { userId, format = 'html', range, prefetch = 3 } = {}) {
  return api.get(`/books/${bookId}/chapters/${chapterId}/content`, {
    params: {
      user_id: userId,
      fmt: format,
      range: range || undefined,
      prefetch
    }
  })
}

/**
 * 进度
 */
export function getProgress(bookId, { userId, deviceId }) {
  const params = { user_id: userId }
  if (deviceId) {
    params.device_id = deviceId
  }
  return api.get(`/books/${bookId}/reader/progress`, {
    params
  })
}

export function getAllDeviceProgress(bookId, userId) {
  return api.get(`/books/${bookId}/reader/progress/devices`, {
    params: { user_id: userId }
  })
}

export function saveProgress(bookId, payload, { userId }) {
  return api.post(`/books/${bookId}/reader/progress`, payload, {
    params: { user_id: userId }
  })
}

export function clearProgress(bookId, { userId, deviceId }) {
  const params = { user_id: userId }
  if (deviceId) {
    params.device_id = deviceId
  }
  return api.delete(`/books/${bookId}/reader/progress`, {
    params
  })
}

/**
 * 书签
 */
export function listBookmarks(bookId, userId) {
  return api.get(`/books/${bookId}/reader/bookmarks`, {
    params: { user_id: userId }
  })
}

export function addBookmark(bookId, payload, userId) {
  return api.post(`/books/${bookId}/reader/bookmarks`, payload, {
    params: { user_id: userId }
  })
}

export function deleteBookmark(bookId, bookmarkId, userId) {
  return api.delete(`/books/${bookId}/reader/bookmarks/${bookmarkId}`, {
    params: { user_id: userId }
  })
}

/**
 * 历史
 */
export function listHistory(bookId, userId, limit = 50) {
  return api.get(`/books/${bookId}/reader/history`, {
    params: { user_id: userId, limit }
  })
}

export function clearHistory(bookId, userId) {
  return api.delete(`/books/${bookId}/reader/history`, {
    params: { user_id: userId }
  })
}

/**
 * 缓存与 EPUB
 */
export function getCacheStatus(bookId, userId) {
  return api.get(`/books/${bookId}/cache/status`, {
    params: { user_id: userId }
  })
}

export function cacheEpub(bookId, userId, config = {}) {
  return api.post(`/books/${bookId}/cache/epub`, null, {
    params: { user_id: userId },
    responseType: 'blob',
    ...config
  })
}
