import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as readerApi from '@/api/reader'
import { useUserStore } from './user'

const SETTINGS_KEY = 'reader-settings'
const DEVICE_ID_KEY = 'reader-device-id'
const LAST_BOOK_KEY = 'reader-last-book'
const READING_MODE_KEY = 'reader-reading-mode'
const DEFAULT_TOC_PAGE_SIZE = 50

function loadFromStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch (error) {
    console.warn(`Failed to parse localStorage for ${key}`, error)
    return fallback
  }
}

function persistToStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.warn(`Failed to persist ${key}`, error)
  }
}

function loadReadingModePreference() {
  const saved = loadFromStorage(READING_MODE_KEY, null)
  return ['scroll', 'page'].includes(saved) ? saved : null
}

function persistReadingMode(mode) {
  if (!mode) return
  persistToStorage(READING_MODE_KEY, mode)
}

function ensureDeviceId() {
  let id = localStorage.getItem(DEVICE_ID_KEY)
  if (!id) {
    id = `device-${crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)}`
    localStorage.setItem(DEVICE_ID_KEY, id)
  }
  return id
}

const defaultSettings = () => ({
  fontFamily: '"LXGW WenKai Screen", "LXGW WenKai", serif',
  fontWeight: 400,
  fontSize: 18,
  lineHeight: 1.8,
  paragraphSpacing: 12,
  firstLineIndent: true,
  background: 'paper',
  textColor: '#333333',
  readingMode: 'scroll', // scroll | page
  pageTransition: 'slide',
})

export const useReaderStore = defineStore('reader', () => {
  const userStore = useUserStore()

  const bookId = ref(null)
  const toc = ref([])
  const tocTotal = ref(0)
  const tocPages = ref(0)
  const tocLimit = ref(DEFAULT_TOC_PAGE_SIZE)
  const tocMinPage = ref(null)
  const tocMaxPage = ref(null)
  const tocHasMoreNext = ref(false)
  const tocHasMorePrev = ref(false)
  const tocLoading = ref(false)
  const tocLoadedPages = ref(new Set())
  const currentChapterId = ref(null)
  const currentChapter = ref(null)
  const chapterContent = ref({ status: 'idle' })
  const loading = ref(false)
  const bookmarks = ref([])
  const history = ref([])
  const cacheStatus = ref({ cached_chapters: [] })
  const error = ref(null)

  // 先加载默认设置，再用 localStorage 中的值覆盖
  const savedSettings = loadFromStorage(SETTINGS_KEY, {})
  const savedReadingMode = loadReadingModePreference()
  const settings = ref({
    ...defaultSettings(),
    ...savedSettings,
    ...(savedReadingMode ? { readingMode: savedReadingMode } : {}),
  })

  const deviceId = ref(ensureDeviceId())

  const isReady = computed(() => !!bookId.value && !!currentChapterId.value && !loading.value)
  const currentUserId = computed(() => userStore.currentUserId)

  function persistSettings() {
    persistToStorage(SETTINGS_KEY, settings.value)
    persistReadingMode(settings.value.readingMode)
  }

  function resetTocState() {
    toc.value = []
    tocTotal.value = 0
    tocPages.value = 0
    tocLimit.value = DEFAULT_TOC_PAGE_SIZE
    tocMinPage.value = null
    tocMaxPage.value = null
    tocHasMoreNext.value = false
    tocHasMorePrev.value = false
    tocLoadedPages.value = new Set()
  }

  function mergeToc(chapters = []) {
    if (!Array.isArray(chapters) || !chapters.length) return
    const cache = new Map(toc.value.map(ch => [ch.id, ch]))
    chapters.forEach(ch => {
      const prev = cache.get(ch.id) || {}
      cache.set(ch.id, { ...prev, ...ch })
    })
    toc.value = Array.from(cache.values()).sort((a, b) => (a.index ?? 0) - (b.index ?? 0))
  }

  function setBookContext(id) {
    bookId.value = id
    resetTocState()
    localStorage.setItem(LAST_BOOK_KEY, id || '')
  }

  async function fetchToc(
    targetBookId = bookId.value,
    { page, anchorChapterId, limit, force } = {}
  ) {
    if (!targetBookId || !currentUserId.value) return
    const pageSet = tocLoadedPages.value
    const requestPage = page
      || (pageSet.size ? Math.max(...pageSet) + 1 : 1)
    if (tocLoading.value) return
    if (!force && page && pageSet.has(page)) return
    tocLoading.value = true
    try {
      const response = await readerApi.getToc(targetBookId, currentUserId.value, {
        page: requestPage,
        limit: limit || tocLimit.value,
        anchorId: anchorChapterId
      })
      const data = response.data || {}
      mergeToc(data.chapters || [])

      const currentPage = data.page || requestPage
      tocLimit.value = data.limit || tocLimit.value || DEFAULT_TOC_PAGE_SIZE
      tocTotal.value = data.total ?? tocTotal.value ?? toc.value.length
      const pages = data.pages
        || (tocTotal.value && tocLimit.value ? Math.ceil(tocTotal.value / tocLimit.value) : tocPages.value)
      tocPages.value = pages

      // 更新已加载页范围
      pageSet.add(currentPage)
      tocMinPage.value = tocMinPage.value === null ? currentPage : Math.min(tocMinPage.value, currentPage)
      tocMaxPage.value = tocMaxPage.value === null ? currentPage : Math.max(tocMaxPage.value, currentPage)

      tocHasMoreNext.value = pages ? (tocMaxPage.value < pages) : Boolean(data.has_more)
      tocHasMorePrev.value = tocMinPage.value > 1
    } catch (error) {
      console.warn('Failed to fetch TOC', error)
    } finally {
      tocLoading.value = false
    }
  }

  async function loadMoreTocDown() {
    if (tocLoading.value) return
    if (!tocHasMoreNext.value && tocPages.value && tocMaxPage.value === tocPages.value) return
    const nextPage = tocPages.value ? Math.min(tocPages.value, (tocMaxPage.value || 0) + 1) : (tocMaxPage.value || 1) + 1
    await fetchToc(bookId.value, { page: nextPage })
  }

  async function loadMoreTocUp() {
    if (tocLoading.value) return
    if (!tocHasMorePrev.value || tocMinPage.value === 1) return
    const prevPage = Math.max(1, (tocMinPage.value || 2) - 1)
    await fetchToc(bookId.value, { page: prevPage })
  }

  async function ensureChapterInToc(chapterId) {
    if (!chapterId || toc.value.some(ch => ch.id === chapterId)) return
    await fetchToc(bookId.value, { anchorChapterId: chapterId, force: true })
  }

  async function fetchProgress() {
    if (!bookId.value || !currentUserId.value) return null
    try {
      // 默认获取跨设备同步进度（不传device_id）
      const response = await readerApi.getProgress(bookId.value, {
        userId: currentUserId.value,
      })
      return response.data
    } catch (error) {
      // 204 无内容直接跳过
      if (error.response?.status === 204) return null
      throw error
    }
  }

  async function fetchAllDeviceProgress() {
    if (!bookId.value || !currentUserId.value) return []
    try {
      const response = await readerApi.getAllDeviceProgress(bookId.value, currentUserId.value)
      return response.data || []
    } catch (error) {
      console.warn('Failed to fetch all device progress', error)
      return []
    }
  }

  async function loadChapter(chapterId, { range, prefetch = 5, format = 'html' } = {}) {
    if (!bookId.value || !currentUserId.value) return
    loading.value = true
    error.value = null
    try {
      const response = await readerApi.getChapterContent(bookId.value, chapterId, {
        userId: currentUserId.value,
        range,
        prefetch,
        format,
      })
      chapterContent.value = response.data
      currentChapterId.value = response.data.prev_id && range === 'prev'
        ? response.data.prev_id
        : response.data.next_id && range === 'next'
          ? response.data.next_id
          : chapterId

      currentChapter.value = {
        id: currentChapterId.value,
        title: response.data.title,
        index: response.data.index,
        prev_id: response.data.prev_id,
        next_id: response.data.next_id,
      }
      // 目录异步补齐，避免阻塞阅读
      ensureChapterInToc(currentChapterId.value)?.catch((err) => console.warn('ensure toc failed', err))
      return response.data
    } catch (err) {
      console.error('Load chapter failed', err)
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  async function initReader(targetBookId, opts = {}) {
    setBookContext(targetBookId)
    const saved = await fetchProgress()
    const anchorChapterId = opts.chapterId || saved?.chapter_id

    // 若没有锚点，先拉取最小目录页以获取首章ID
    if (!anchorChapterId && !toc.value.length) {
      // 使用默认分页大小加载首章，避免后续分页基于 limit=1 导致只拿到少量章节
      await fetchToc(targetBookId)
    }
    const startChapterId = anchorChapterId || toc.value[0]?.id
    if (startChapterId) {
      await loadChapter(startChapterId, { format: opts.format || 'html' })
    }
    if (saved) {
      // 前端渲染时可用的进度
      chapterContent.value.offset_px = saved.offset_px
      chapterContent.value.percent = saved.percent
    }
    // 目录后台拉取（不阻塞阅读）
    fetchToc(targetBookId)?.catch((err) => console.warn('background toc fetch failed', err))
    await refreshCacheStatus()
    await fetchBookmarks()
    await fetchHistory()
  }

  async function saveProgress(progress) {
    if (!bookId.value || !currentUserId.value || !currentChapterId.value) return
    const payload = {
      chapter_id: currentChapterId.value,
      offset_px: progress?.offset_px || 0,
      percent: progress?.percent || 0,
      device_id: deviceId.value,
    }
    chapterContent.value.offset_px = payload.offset_px
    chapterContent.value.percent = payload.percent
    await readerApi.saveProgress(bookId.value, payload, { userId: currentUserId.value })
  }

  async function fetchBookmarks() {
    if (!bookId.value || !currentUserId.value) return
    const response = await readerApi.listBookmarks(bookId.value, currentUserId.value)
    bookmarks.value = response.data || []
  }

  async function addBookmark(offsetPx, percent, note = '') {
    if (!bookId.value || !currentUserId.value || !currentChapterId.value) return
    const payload = {
      chapter_id: currentChapterId.value,
      offset_px: offsetPx,
      percent,
      note,
    }
    const response = await readerApi.addBookmark(bookId.value, payload, currentUserId.value)
    bookmarks.value.unshift(response.data)
    return response.data
  }

  async function removeBookmark(bookmarkId) {
    if (!bookId.value || !currentUserId.value) return
    await readerApi.deleteBookmark(bookId.value, bookmarkId, currentUserId.value)
    const index = bookmarks.value.findIndex(b => b.id === bookmarkId)
    if (index !== -1) bookmarks.value.splice(index, 1)
  }

  async function fetchHistory(limit = 1) {
    if (!bookId.value || !currentUserId.value) return
    const response = await readerApi.listHistory(bookId.value, currentUserId.value, limit)
    history.value = response.data || []
  }

  async function clearHistory() {
    if (!bookId.value || !currentUserId.value) return
    await readerApi.clearHistory(bookId.value, currentUserId.value)
    history.value = []
  }

  async function refreshCacheStatus() {
    if (!bookId.value || !currentUserId.value) return
    const response = await readerApi.getCacheStatus(bookId.value, currentUserId.value)
    cacheStatus.value = response.data || { cached_chapters: [] }
  }

  function updateSetting(key, value) {
    settings.value = { ...settings.value, [key]: value }
    persistSettings()
    if (key === 'readingMode') {
      persistReadingMode(value)
    }
  }

  function resetSettings() {
    settings.value = defaultSettings()
    persistSettings()
  }

  return {
    bookId,
    toc,
    tocTotal,
    tocPages,
    tocLimit,
    tocHasMore: tocHasMoreNext,
    tocHasMoreNext,
    tocHasMorePrev,
    tocLoading,
    currentChapterId,
    currentChapter,
    chapterContent,
    bookmarks,
    history,
    cacheStatus,
    settings,
    loading,
    error,
    deviceId,
    isReady,
    currentUserId,
    initReader,
    fetchToc,
    loadMoreToc: loadMoreTocDown,
    loadMoreTocDown,
    loadMoreTocUp,
    loadChapter,
    saveProgress,
    fetchBookmarks,
    addBookmark,
    removeBookmark,
    fetchHistory,
    clearHistory,
    refreshCacheStatus,
    updateSetting,
    resetSettings,
  }
})
