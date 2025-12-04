import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import * as readerApi from '@/api/reader'
import { getEpubDownloadUrl } from '@/api/books'
import { useReaderStore } from '@/stores/reader'
import { useUserStore } from '@/stores/user'
import { useBookStore } from '@/stores/book'
import { useThemeStore } from '@/stores/theme'
import themeColorManager from '@/utils/themeColorManager'
import {
  useReaderProgress,
  useReaderChapter,
  useReaderScroll,
  useReaderPage,
  useReaderEpub,
  useReaderTts
} from '@/composables/reader'
import { useReaderPageMode } from './useReaderPageMode'

export function useReaderView() {
  const route = useRoute()
  const router = useRouter()
  const message = useMessage()

  const readerStore = useReaderStore()
  const userStore = useUserStore()
  const bookStore = useBookStore()
  const themeStore = useThemeStore()

  const tocVisible = ref(false)
  const settingsVisible = ref(false)
  const initializing = ref(true)
  const isMobile = ref(false)
  const mobileChromeVisible = ref(false)
  const isFullscreen = ref(false)
  const caching = ref(false)
  let cacheRefreshTimer = null

  const readerSettings = computed(() => readerStore.settings || {})
  const activeMode = computed(() => readerSettings.value.readingMode || 'scroll')
  const isScrollMode = computed(() => activeMode.value === 'scroll')
  const isPageMode = computed(() => activeMode.value === 'page')
  const isEpubMode = computed(() => activeMode.value === 'epub')
  const showChrome = computed(() => !isMobile.value || mobileChromeVisible.value)
  const cacheStatus = computed(() => readerStore.cacheStatus || {})
  const cachedChapterSet = computed(() => new Set(cacheStatus.value.cached_chapters || []))

  function refreshCacheStatusDebounced(delay = 400) {
    if (cacheRefreshTimer) return
    cacheRefreshTimer = window.setTimeout(async () => {
      cacheRefreshTimer = null
      try {
        await readerStore.refreshCacheStatus()
      } catch (error) {
        console.warn('refreshCacheStatus failed', error)
      }
    }, delay)
  }

  function isChapterCached(chapterId) {
    return !!chapterId && cachedChapterSet.value.has(chapterId)
  }

  function notifyDownloadingIfNeeded(chapterId) {
    if (!chapterId || isChapterCached(chapterId)) return
    message.info('后端正在下载新章节，请稍等', { duration: 3000 })
    refreshCacheStatusDebounced(0)
  }

  const textColor = computed(() =>
    readerSettings.value.textColor || (themeStore.isDark ? '#e6e6e6' : '#333333')
  )

  const backgroundColor = computed(() => {
    const bg = readerSettings.value.background
    const map = { paper: '#f7f3e8', green: '#e9f5ec', dark: '#0f0f11' }
    if (!bg) return themeStore.isDark ? '#0f0f11' : '#f7f3e8'
    return map[bg] || bg
  })

  const backgroundStyle = computed(() => ({
    background: `radial-gradient(circle at 12% 20%, rgba(255,255,255,0.12), transparent 24%), radial-gradient(circle at 82% 8%, rgba(255,255,255,0.1), transparent 18%), ${backgroundColor.value}`,
    color: textColor.value
  }))

  const readerContentStyle = computed(() => ({
    fontSize: `${readerSettings.value.fontSize || 18}px`,
    fontWeight: readerSettings.value.fontWeight || 400,
    lineHeight: readerSettings.value.lineHeight || 1.8,
    color: textColor.value,
    fontFamily: readerSettings.value.fontFamily || 'serif'
  }))

  const paragraphStyle = computed(() => ({
    marginBottom: `${readerSettings.value.paragraphSpacing || 12}px`,
    textIndent: readerSettings.value.firstLineIndent === false ? '0' : '2em'
  }))

  const pagePanelStyle = computed(() => ({
    background: backgroundColor.value,
    color: textColor.value
  }))

  const currentBookTitle = computed(() => bookStore.currentBook?.title || '在线阅读')
  const chapterLabel = computed(() => {
    if (readerStore.currentChapter?.title) return readerStore.currentChapter.title
    return currentBookTitle.value
  })

  const scrollContentRef = ref(null)
  const contentRef = computed(() => scrollContentRef.value?.scrollContainerRef)

  const progressComposable = useReaderProgress({
    readerStore,
    isScrollMode,
    isPageMode,
    isEpubMode
  })

  const chapterComposable = useReaderChapter({
    readerStore,
    bookStore,
    userStore,
    readerApi,
    isMobile
  })

  const scrollComposable = useReaderScroll({
    isMobile,
    chapterRefs: chapterComposable.chapterRefs,
    readerStore,
    currentChapter: chapterComposable.currentChapter,
    loadedChapters: chapterComposable.loadedChapters,
    prevChapterContent: chapterComposable.prevChapterContent,
    nextChapterContent: chapterComposable.nextChapterContent,
    autoLoadingNext: chapterComposable.autoLoadingNext,
    autoLoadingPrev: chapterComposable.autoLoadingPrev,
    fetchChapterById: chapterComposable.fetchChapterById,
    activateChapter: chapterComposable.activateChapter,
    addLoadedChapter: chapterComposable.addLoadedChapter,
    contentRef
  })

  const pageComposable = useReaderPage({
    readerSettings,
    textColor
  })

  const epubComposable = useReaderEpub({
    getEpubDownloadUrl,
    bookId: computed(() => route.params.bookId)
  })

  const ttsComposable = useReaderTts({ message })
  const epubContainerRef = epubComposable.epubContainerRef

  const {
    multiChapterMode,
    paginateMultipleChaptersForPageMode,
    handlePageChanged,
    handleChapterChanged,
    handleNeedMoreChapters,
    handleReachEdge,
    handlePageResize,
    clearPageResizeTimer
  } = useReaderPageMode({
    chapterComposable,
    pageComposable,
    progressComposable,
    readerStore,
    message,
    isPageMode,
    notifyDownloadingIfNeeded,
    onPrevChapter: handlePrev,
    onNextChapter: handleNext
  })

  async function initPage() {
    const bookId = route.params.bookId
    if (!bookId) return
    initializing.value = true
    try {
      if (!userStore.currentUserId) {
        await userStore.initUserContext()
      }
      await bookStore.fetchBook(bookId)
      await readerStore.initReader(bookId, {
        chapterId: route.query.chapterId,
        format: 'text'
      })
      await onContentReady()
    } catch (error) {
      console.error('Failed to init reader', error)
      message.error(error?.response?.data?.detail || '加载阅读器失败')
      router.push({ name: 'books' })
    } finally {
      initializing.value = false
    }
  }

  async function onContentReady() {
    if (readerStore.currentChapterId && !readerStore.chapterContent?.id) {
      readerStore.chapterContent = { ...(readerStore.chapterContent || {}), id: readerStore.currentChapterId }
    }
    if (isPageMode.value && !chapterComposable.chapterContent.value?.content_text && readerStore.currentChapterId) {
      await readerStore.loadChapter(readerStore.currentChapterId, { format: 'text' })
    }
    const rawPercent = typeof chapterComposable.chapterContent.value.percent === 'number'
      ? chapterComposable.chapterContent.value.percent
      : 0
    const percent = progressComposable.consumeStartPercent(rawPercent)
    progressComposable.scrollPercent.value = Math.max(0, Math.min(100, percent))

    chapterComposable.initCurrentChapter()
    chapterComposable.pruneLoadedAroundCurrent(contentRef)

    if (isEpubMode.value) {
      await nextTick()
      await epubComposable.loadEpub(percent, (p) => progressComposable.updateEpubPercent(p))
      return
    }
    if (isPageMode.value) {
      await nextTick()
      await paginateMultipleChaptersForPageMode(percent)
      return
    }
    if (isScrollMode.value) {
      await chapterComposable.prefetchAdjacentChapters(contentRef, isScrollMode)
      await nextTick()
      await nextTick()
      await scrollComposable.scrollToChapterPercent(
        readerStore.currentChapterId,
        percent,
        progressComposable.setSuppressSave
      )
      updateScrollProgress(false)
      return
    }

    await nextTick()
    scrollComposable.applySavedScroll(
      chapterComposable.chapterContent.value,
      percent,
      progressComposable.setSuppressSave
    )
    updateScrollProgress(false)
  }

  function updateScrollProgress(shouldSave = true) {
    const { percent, offsetPx } = scrollComposable.calculateScrollProgress()
    progressComposable.scrollPercent.value = Number(percent.toFixed(2))
    if (shouldSave) {
      progressComposable.queueSaveProgress(offsetPx, percent)
    }
  }

  function handleScroll() {
    if (initializing.value || chapterComposable.isLoadingChapter.value) return
    if (isScrollMode.value) {
      const chapterChanged = scrollComposable.updateActiveChapterByScroll()
      updateScrollProgress(true)
      scrollComposable.maybeAutoLoadPrevChapter()
      scrollComposable.maybeAutoLoadNextChapter()
      if (chapterChanged) {
        chapterComposable.pruneLoadedAroundCurrent(contentRef)
      }
    }
  }

  function handleContentTap(event) {
    if (!isMobile.value) return
    if (event.target.closest('.reader-toolbar') ||
        event.target.closest('.reader-footer') ||
        event.target.closest('.n-drawer')) {
      return
    }
    const selection = window.getSelection?.()
    if (selection && selection.toString()) return
    mobileChromeVisible.value = !mobileChromeVisible.value
  }

  async function reloadChapter() {
    if (!readerStore.currentChapterId) return
    await readerStore.loadChapter(readerStore.currentChapterId, { format: 'text' })
    await onContentReady()
  }

  async function handleSelectChapter(chapter) {
    if (!chapter?.id || chapter.id === readerStore.currentChapterId) {
      tocVisible.value = false
      return
    }
    try {
      notifyDownloadingIfNeeded(chapter.id)
      chapterComposable.resetAdjacentCaches()
      chapterComposable.clearLoadedChapters()
      await readerStore.loadChapter(chapter.id, { format: 'text' })
      tocVisible.value = false
      await onContentReady()
    } catch (error) {
      message.error('切换章节失败')
    }
  }

  async function handlePrev(options = {}) {
    if (!chapterComposable.currentChapter.value?.prev_id || chapterComposable.isLoadingChapter.value) return
    if (options.auto && chapterComposable.autoLoadingPrev.value) return
    notifyDownloadingIfNeeded(chapterComposable.currentChapter.value.prev_id)
    if (options.resetProgress !== false) {
      progressComposable.setForcedStartPercent(options.startPercent ?? 0)
    } else if (options.startPercent !== undefined) {
      progressComposable.setForcedStartPercent(options.startPercent)
    }
    if (options.auto) chapterComposable.autoLoadingPrev.value = true
    try {
      chapterComposable.resetAdjacentCaches()
      chapterComposable.clearLoadedChapters()
      await readerStore.loadChapter(chapterComposable.currentChapter.value.prev_id, { format: 'text' })
      await onContentReady()
    } finally {
      if (options.auto) chapterComposable.autoLoadingPrev.value = false
    }
  }

  async function handleNext(options = {}) {
    if (!chapterComposable.currentChapter.value?.next_id || chapterComposable.isLoadingChapter.value) return
    if (options.auto && chapterComposable.autoLoadingNext.value) return
    notifyDownloadingIfNeeded(chapterComposable.currentChapter.value.next_id)
    if (options.resetProgress !== false) {
      progressComposable.setForcedStartPercent(options.startPercent ?? 0)
    } else if (options.startPercent !== undefined) {
      progressComposable.setForcedStartPercent(options.startPercent)
    }
    if (options.auto) chapterComposable.autoLoadingNext.value = true
    try {
      chapterComposable.resetAdjacentCaches()
      chapterComposable.clearLoadedChapters()
      await readerStore.loadChapter(chapterComposable.currentChapter.value.next_id, { format: 'text' })
      await onContentReady()
    } finally {
      if (options.auto) chapterComposable.autoLoadingNext.value = false
    }
  }

  function handleProgressChange(value) {
    if (isScrollMode.value) {
      scrollComposable.scrollToActivePercent(value)
      return
    }
    if (isPageMode.value) {
      const chapterId = pageComposable.activeChapterId.value
      if (chapterId) {
        const targetIndex = pageComposable.getChapterPageIndex(chapterId, value)
        if (targetIndex !== null) {
          pageComposable.currentPageIndex.value = targetIndex
          progressComposable.currentPageIndex.value = targetIndex
          progressComposable.updatePageProgress(true)
        }
      }
      return
    }
    if (isEpubMode.value) {
      epubComposable.jumpToEpubPercent(value)
    }
  }

  function changeMode(mode) {
    if (mode === 'page' && !isMobile.value) {
      message.warning('PC 端暂不支持翻页模式')
      return
    }
    if (activeMode.value === mode) return
    readerStore.updateSetting('readingMode', mode)
  }

  function handleUpdateSetting(key, value) {
    readerStore.updateSetting(key, value)
  }

  async function toggleFullscreen() {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen()
        isFullscreen.value = true
      } else {
        await document.exitFullscreen()
        isFullscreen.value = false
      }
    } catch (error) {
      console.warn('Fullscreen failed', error)
    }
  }

  function onFullscreenChange() {
    isFullscreen.value = !!document.fullscreenElement
  }

  async function addBookmarkAtCurrent() {
    try {
      const { offsetPx, percent } = progressComposable.getCurrentProgress(
        contentRef,
        chapterComposable.chapterRefs,
        readerStore.currentChapterId
      )
      await readerStore.addBookmark(offsetPx, percent, '')
      message.success('书签已保存')
    } catch (error) {
      message.error(error?.response?.data?.detail || '保存书签失败')
    }
  }

  async function handleCacheEpub() {
    if (caching.value) return
    caching.value = true
    try {
      await readerStore.cacheEpub()
      await readerStore.refreshCacheStatus()
      message.success('EPUB 已缓存')
    } catch (error) {
      message.error(error?.response?.data?.detail || '缓存失败')
    } finally {
      caching.value = false
    }
  }

  function handleToggleTts() {
    ttsComposable.toggleTts(chapterComposable.chapterContent.value)
  }

  function handleResize() {
    const wasMobile = isMobile.value
    isMobile.value = window.innerWidth < 768
    if (!isMobile.value && activeMode.value === 'page') {
      readerStore.updateSetting('readingMode', 'scroll')
    }
    mobileChromeVisible.value = isMobile.value ? mobileChromeVisible.value && wasMobile : true

    if (isMobile.value) {
      window.addEventListener('scroll', handleScroll)
    } else {
      window.removeEventListener('scroll', handleScroll)
    }
  }

  function goBack() {
    router.push({ name: 'book-detail', params: { id: route.params.bookId } })
  }

  function updateThemeColorForReading() {
    const isDark = themeStore.isDark || readerSettings.value.background === 'dark'
    const bg = readerSettings.value.background
    const map = { paper: '#f7f3e8', green: '#e9f5ec', dark: '#0f0f11' }
    const backgroundColorValue = map[bg] || (isDark ? '#0f0f11' : '#f7f3e8')

    themeColorManager.setReaderThemeColor({
      backgroundColor: backgroundColorValue,
      isDark
    })
  }

  onMounted(() => {
    handleResize()
    window.addEventListener('resize', handleResize)
    document.addEventListener('fullscreenchange', onFullscreenChange)
    updateThemeColorForReading()
    initPage()
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize)
    window.removeEventListener('scroll', handleScroll)
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    progressComposable.cleanup()
    clearPageResizeTimer()
    clearTimeout(cacheRefreshTimer)
    epubComposable.disposeEpub()
    ttsComposable.stopTts()
    themeColorManager.restoreDefaultThemeColor()
  })

  watch(
    () => readerStore.currentChapterId,
    (id) => {
      if (id) refreshCacheStatusDebounced()
    }
  )

  watch(
    () => tocVisible.value,
    (visible) => {
      if (visible) refreshCacheStatusDebounced(0)
    }
  )

  watch(() => route.params.bookId, (id, prev) => {
    if (id && id !== prev) {
      ttsComposable.stopTts()
      initPage()
    }
  })

  watch(
    () => chapterComposable.chapterContent.value.status,
    () => {
      ttsComposable.stopTts()
      onContentReady()
    }
  )

  watch(
    () => [
      readerSettings.value.fontSize,
      readerSettings.value.lineHeight,
      readerSettings.value.paragraphSpacing,
      readerSettings.value.firstLineIndent
    ],
    async () => {
      if (isPageMode.value) {
        const currentPercent = pageComposable.calculateChapterProgress()
        await paginateMultipleChaptersForPageMode(currentPercent)
      }
    }
  )

  watch(
    () => readerSettings.value.background,
    () => {
      updateThemeColorForReading()
    }
  )

  watch(
    () => themeStore.isDark,
    () => {
      updateThemeColorForReading()
    }
  )

  watch(
    () => activeMode.value,
    async (mode, prev) => {
      if (mode === prev) return
      ttsComposable.stopTts()
      if (mode === 'epub') {
        await epubComposable.loadEpub(
          chapterComposable.chapterContent.value.percent || 0,
          (p) => progressComposable.updateEpubPercent(p)
        )
        return
      }
      epubComposable.disposeEpub()
      if (mode === 'page') {
        if (!chapterComposable.chapterContent.value?.content_text && readerStore.currentChapterId) {
          await readerStore.loadChapter(readerStore.currentChapterId, { format: 'text' })
        }
        await nextTick()
        await paginateMultipleChaptersForPageMode(0)
        return
      }
      await nextTick()
      scrollComposable.applySavedScroll(
        chapterComposable.chapterContent.value,
        null,
        progressComposable.setSuppressSave
      )
      updateScrollProgress(false)
    }
  )

  return {
    tocVisible,
    settingsVisible,
    initializing,
    isMobile,
    showChrome,
    isScrollMode,
    isPageMode,
    isEpubMode,
    isFullscreen,
    caching,
    readerSettings,
    textColor,
    backgroundColor,
    backgroundStyle,
    readerContentStyle,
    paragraphStyle,
    pagePanelStyle,
    currentBookTitle,
    chapterLabel,
    cacheStatus,
    scrollContentRef,
    epubContainerRef,
    multiChapterMode,
    readerStore,
    chapterComposable,
    progressComposable,
    pageComposable,
    epubComposable,
    ttsComposable,
    handleContentTap,
    handleSelectChapter,
    reloadChapter,
    handlePrev,
    handleNext,
    changeMode,
    handleUpdateSetting,
    toggleFullscreen,
    addBookmarkAtCurrent,
    handleCacheEpub,
    handleToggleTts,
    handleProgressChange,
    handleScroll,
    handlePageChanged,
    handleChapterChanged,
    handleNeedMoreChapters,
    handleReachEdge,
    handlePageResize,
    goBack
  }
}
