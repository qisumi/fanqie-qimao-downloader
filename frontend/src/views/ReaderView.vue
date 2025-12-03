<script setup>
/**
 * ReaderView - 阅读器主视图
 * 重构后的版本，通过 composables 和子组件拆分逻辑
 */
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NSpin, NBackTop, useMessage } from 'naive-ui'
import * as readerApi from '@/api/reader'
import { useReaderStore } from '@/stores/reader'
import { useUserStore } from '@/stores/user'
import { useBookStore } from '@/stores/book'
import { getEpubDownloadUrl } from '@/api/books'
import { useThemeStore } from '@/stores/theme'

// Composables
import {
  useReaderProgress,
  useReaderChapter,
  useReaderScroll,
  useReaderPage,
  useReaderEpub,
  useReaderTts
} from '@/composables/reader'

// Components
import {
  ReaderToolbar,
  ReaderTocDrawer,
  ReaderSettingsDrawer,
  ReaderFooter,
  ReaderScrollContent,
  ReaderPageContent,
  ReaderEpubContent
} from '@/components/reader'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// Stores
const readerStore = useReaderStore()
const userStore = useUserStore()
const bookStore = useBookStore()
const themeStore = useThemeStore()

// UI状态
const tocVisible = ref(false)
const settingsVisible = ref(false)
const initializing = ref(true)
const isMobile = ref(false)
const mobileChromeVisible = ref(false)
const isFullscreen = ref(false)
const caching = ref(false)
let resizeTimer = null
let cacheRefreshTimer = null

// 计算属性 - 阅读模式
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

// 计算属性 - 样式
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

// 计算属性 - 书籍信息
const currentBookTitle = computed(() => bookStore.currentBook?.title || '在线阅读')
// 注：API 返回的章节标题已包含"第X章"信息，无需额外拼接
const chapterLabel = computed(() => {
  if (readerStore.currentChapter?.title) return readerStore.currentChapter.title
  return currentBookTitle.value
})

// 翻页模式专用的章节标题（用于分页时插入）
// 注：API 返回的章节标题已包含"第X章"信息，无需额外拼接
const pageChapterTitleText = computed(() => {
  const chapter = chapterComposable.currentChapter.value
  return chapter?.title || null
})

// 多章节模式：是否启用无缝章节切换
const multiChapterMode = ref(false)
// 已预取的章节数据缓存 Map<chapterId, chapterData>
const prefetchedChapters = ref(new Map())
// 正在预取中的章节ID集合
const prefetchingChapterIds = ref(new Set())

// 初始化 Composables
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

// 暴露给模板的引用 - contentRef 需要从子组件获取
const scrollContentRef = ref(null)
const contentRef = computed(() => scrollContentRef.value?.scrollContainerRef)

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
  contentRef // 传入 contentRef
})

const pageComposable = useReaderPage({
  readerSettings,
  textColor,
  chapterContent: chapterComposable.chapterContent,
  textParagraphs: chapterComposable.textParagraphs,
  chapterIndex: computed(() => chapterComposable.currentChapter.value?.index),
  chapterTitle: computed(() => chapterComposable.currentChapter.value?.title)
})

const epubComposable = useReaderEpub({
  getEpubDownloadUrl,
  bookId: computed(() => route.params.bookId)
})

const ttsComposable = useReaderTts({ message })

const pageContainerRef = pageComposable.pageContainerRef
const flickingRef = pageComposable.flickingRef
const epubContainerRef = epubComposable.epubContainerRef

/**
 * 翻页模式：预取前后各2章内容
 * 返回有序的章节数据数组，每个章节都包含 prev_id 和 next_id
 */
async function prefetchChaptersForPageMode(anchorChapterId = null) {
  const currentContent = chapterComposable.chapterContent.value
  const toc = chapterComposable.toc.value || []
  
  if (!toc.length) return currentContent ? [currentContent] : []

  const anchorId = anchorChapterId || pageComposable.activeChapterId.value || chapterComposable.currentChapter.value?.id
  const anchorIndex = anchorId ? toc.findIndex(c => c.id === anchorId) : -1
  const centerIndex = anchorIndex >= 0 ? anchorIndex : toc.findIndex(c => c.id === chapterComposable.currentChapter.value?.id)
  
  if (centerIndex < 0) return currentContent ? [currentContent] : []

  // 固定窗口：当前阅读章节为中心，前后各 2 章
  const startIdx = Math.max(0, centerIndex - 2)
  const endIdx = Math.min(toc.length - 1, centerIndex + 2)

  // 计算当前窗口内的章节ID集合
  const windowChapterIds = new Set()
  for (let i = startIdx; i <= endIdx; i++) {
    windowChapterIds.add(toc[i].id)
  }

  // 清理窗口外的过期缓存，避免内存泄漏
  for (const cachedId of prefetchedChapters.value.keys()) {
    if (!windowChapterIds.has(cachedId)) {
      prefetchedChapters.value.delete(cachedId)
    }
  }

  // 收集需要预取的章节ID（当前章节除外且未缓存）
  const chapterIdsToLoad = []
  for (let i = startIdx; i <= endIdx; i++) {
    const id = toc[i].id
    const hasData = (currentContent?.id === id) || prefetchedChapters.value.has(id)
    if (!hasData) {
      chapterIdsToLoad.push(id)
    }
  }

  const fetchPromises = []
  for (const chapterId of chapterIdsToLoad) {
    if (prefetchingChapterIds.value.has(chapterId)) continue
    prefetchingChapterIds.value.add(chapterId)
    fetchPromises.push(
      chapterComposable.fetchChapterById(chapterId)
        .then(data => {
          if (data) prefetchedChapters.value.set(chapterId, data)
        })
        .finally(() => prefetchingChapterIds.value.delete(chapterId))
    )
  }
  if (fetchPromises.length) await Promise.all(fetchPromises)

  // 组装窗口内的章节，保持目录顺序
  const orderedChapters = []
  for (let i = startIdx; i <= endIdx; i++) {
    const tocEntry = toc[i]
    let chapterData = null
    if (currentContent?.id === tocEntry.id) {
      chapterData = { ...currentContent }
    } else if (prefetchedChapters.value.has(tocEntry.id)) {
      chapterData = { ...prefetchedChapters.value.get(tocEntry.id) }
    }
    if (!chapterData) continue

    if (!chapterData.id) chapterData.id = tocEntry.id
    if (!chapterData.title) chapterData.title = tocEntry.title
    if (chapterData.index === undefined) chapterData.index = tocEntry.index
    chapterData.prev_id = i > 0 ? toc[i - 1].id : null
    chapterData.next_id = i < toc.length - 1 ? toc[i + 1].id : null

    orderedChapters.push(chapterData)
  }

  return orderedChapters
}

/**
 * 翻页模式：执行多章节分页
 */
async function paginateMultipleChaptersForPageMode(targetPercent = 0, anchorChapterId = null) {
  const anchorId = anchorChapterId || pageComposable.activeChapterId.value || chapterComposable.currentChapter.value?.id
  const chapters = await prefetchChaptersForPageMode(anchorId)
  const currentChapterId = anchorId || chapterComposable.currentChapter.value?.id
  
  if (chapters.length > 1) {
    multiChapterMode.value = true
    pageComposable.paginateMultipleChapters(chapters, currentChapterId, targetPercent)
  } else {
    multiChapterMode.value = false
    pageComposable.paginateText(targetPercent, pageChapterTitleText.value)
  }
  
  progressComposable.pageChunks.value = pageComposable.pageChunks.value
  progressComposable.currentPageIndex.value = pageComposable.currentPageIndex.value
}

// 初始化
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
  // 翻页模式需要纯文本内容进行分页，如果当前章节缺少 content_text 则强制以 text 格式重新拉取
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
    // 使用多章节分页实现无缝滑动
    await paginateMultipleChaptersForPageMode(percent)
    return
  }
  if (isScrollMode.value) {
    // 1. 先预加载相邻章节（会触发滚动补偿，但初始化时可能不准确）
    await chapterComposable.prefetchAdjacentChapters(contentRef, isScrollMode)
    
    // 2. 等待 DOM 完全更新
    await nextTick()
    await nextTick()
    
    // 3. 最后精确定位到目标章节的进度位置（基于章节元素的实际偏移量）
    await scrollComposable.scrollToChapterPercent(
      readerStore.currentChapterId,
      percent,
      progressComposable.setSuppressSave
    )
    updateScrollProgress(false)
    return
  }
  
  // 非滚动模式（理论上不会执行到这里，因为 epub 和 page 模式已在上面 return）
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
    updateScrollProgress(true)
    scrollComposable.maybeAutoLoadPrevChapter()
    scrollComposable.maybeAutoLoadNextChapter()
    const chapterChanged = scrollComposable.updateActiveChapterByScroll()
    // 章节切换后裁剪已加载章节，保留当前章节附近的章节，避免内存泄漏
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

// 章节导航
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

// 进度控制
function handleProgressChange(value) {
  if (isScrollMode.value) {
    scrollComposable.scrollToActivePercent(value)
    return
  }
  if (isPageMode.value) {
    pageComposable.moveToPageByPercent(value).then(() => {
      progressComposable.currentPageIndex.value = pageComposable.currentPageIndex.value
      progressComposable.updatePageProgress(true)
    })
    return
  }
  if (isEpubMode.value) {
    epubComposable.jumpToEpubPercent(value)
  }
}

// 翻页模式处理
async function handlePageChanged(event) {
  const suppressing = typeof pageComposable.isSuppressSave === 'function' && pageComposable.isSuppressSave()
  
  const result = pageComposable.handlePageChanged(event)
  progressComposable.currentPageIndex.value = pageComposable.currentPageIndex.value
  
  // 分页过程中（抑制保存阶段）不更新章节状态，避免跳回首章
  if (suppressing) {
    return
  }
  
  // 多章节模式下，只有章节变化时才保存进度
  if (multiChapterMode.value && result?.chapterId) {
    // 章节变化时保存进度到新章节
    if (result.chapterId !== readerStore.currentChapterId) {
      // 静默更新当前章节（不触发重新加载）
      const boundary = pageComposable.getChapterBoundary(result.chapterId)
      if (boundary) {
        readerStore.currentChapterId = result.chapterId
        readerStore.currentChapter = {
          id: result.chapterId,
          title: boundary.title,
          index: boundary.index,
          prev_id: boundary.prev_id,
          next_id: boundary.next_id
        }
        // 保存进度到新章节（进度为0，表示刚进入该章节）
        progressComposable.queueSaveProgress(0, 0)
      }
    } else {
      // 同一章节内，计算章节内进度并保存
      const chapterPercent = pageComposable.calculateChapterProgress(result.chapterId)
      progressComposable.scrollPercent.value = chapterPercent
      progressComposable.queueSaveProgress(0, chapterPercent)
    }
  } else {
    progressComposable.updatePageProgress(true)
  }
}

// 翻页模式章节变化事件处理（由子组件触发）
async function handleChapterChanged(event) {
  if (!isPageMode.value || !multiChapterMode.value) return
  
  const { chapterId, boundary } = event
  if (!chapterId || !boundary) return
  
  // 更新 store 中的当前章节信息
  readerStore.currentChapterId = chapterId
  readerStore.currentChapter = {
    id: chapterId,
    title: boundary.title,
    index: boundary.index,
    prev_id: boundary.prev_id,
    next_id: boundary.next_id
  }
  
  // 保存进度
  progressComposable.queueSaveProgress(0, 0)

  // 新章节到达时，若后续章节未预取则向后预取2章
  await prefetchNextChaptersIfNeeded(chapterId)
}

// 翻页模式需要加载更多章节事件处理
async function handleNeedMoreChapters(event) {
  if (!isPageMode.value || !multiChapterMode.value) return
  if (chapterComposable.isLoadingChapter.value) return
  
  // 这里暂时不做动态追加，因为需要重新分页
  // 未来可以优化为动态追加面板
}

// 翻页模式到达边界时的处理
async function handleReachEdge(event) {
  console.log('[ReaderView] handleReachEdge called:', {
    direction: event?.direction,
    isPageMode: isPageMode.value,
    isLoadingChapter: chapterComposable.isLoadingChapter.value,
    multiChapterMode: multiChapterMode.value
  })
  
  if (!isPageMode.value) return
  if (chapterComposable.isLoadingChapter.value) return
  
  // 多章节模式下，到达边界时检查是否需要加载更多章节
  if (multiChapterMode.value) {
    const loadedChapterIds = pageComposable.loadedChapterIds.value
    if (!loadedChapterIds.length) return
    
    const firstChapterId = loadedChapterIds[0]
    const lastChapterId = loadedChapterIds[loadedChapterIds.length - 1]
    const firstBoundary = pageComposable.getChapterBoundary(firstChapterId)
    const lastBoundary = pageComposable.getChapterBoundary(lastChapterId)
    const anchorChapterId = pageComposable.activeChapterId.value || readerStore.currentChapterId
    const anchorBoundary = anchorChapterId ? pageComposable.getChapterBoundary(anchorChapterId) : null
    let currentPercent = pageComposable.calculateChapterProgress(anchorChapterId)
    
    // 边缘预载时无法计算进度或即将越界时，使用方向性默认值，保持当前页不向前跳
    if (!Number.isFinite(currentPercent)) {
      currentPercent = event?.direction === 'NEXT' ? 100 : 0
    } else if (anchorBoundary) {
      const idx = pageComposable.currentPageIndex.value
      if (event?.direction === 'NEXT' && idx >= anchorBoundary.endPage) {
        currentPercent = 100
      }
      if (event?.direction === 'PREV' && idx <= anchorBoundary.startPage) {
        currentPercent = 0
      }
    }

    if (event?.direction === 'PREV') {
      if (!firstBoundary?.prev_id) {
        message.info('已经是第一章了')
      } else {
        notifyDownloadingIfNeeded(firstBoundary.prev_id)
        // 预取上一章内容
        await prefetchChapterForPageMode(firstBoundary.prev_id)
        
        // 预取完成后，使用第一个加载的章节作为锚点（而不是当前阅读章节）
        // 这样可以确保新预取的章节被包含在分页窗口内
        const freshAnchorChapterId = firstChapterId
        const freshPosition = pageComposable.getChapterRelativePosition(freshAnchorChapterId)
        
        // 使用当前最新位置计算进度
        let finalPercent = 0
        if (freshPosition) {
          const { relativeIndex, totalPages } = freshPosition
          finalPercent = totalPages > 1 ? (relativeIndex / (totalPages - 1)) * 100 : 0
        }
        await paginateMultipleChaptersForPageMode(finalPercent, freshAnchorChapterId)
      }
    } else if (event?.direction === 'NEXT') {
      if (!lastBoundary?.next_id) {
        message.info('已经是最后一章了')
      } else {
        notifyDownloadingIfNeeded(lastBoundary.next_id)
        // 预取下一章内容
        await prefetchChapterForPageMode(lastBoundary.next_id)
        
        // 预取完成后，使用最后加载的章节作为锚点（而不是当前阅读章节）
        // 这样可以确保新预取的章节被包含在分页窗口内
        const freshAnchorChapterId = lastChapterId
        const freshPosition = pageComposable.getChapterRelativePosition(freshAnchorChapterId)
        
        // 使用当前最新位置计算进度
        let finalPercent = 100
        if (freshPosition) {
          const { relativeIndex, totalPages } = freshPosition
          finalPercent = totalPages > 1 ? (relativeIndex / (totalPages - 1)) * 100 : 100
        }
        await paginateMultipleChaptersForPageMode(finalPercent, freshAnchorChapterId)
      }
    }
    return
  }
  
  // 单章节模式下，保持原有的自动切章逻辑
  if (event?.direction === 'NEXT' && chapterComposable.currentChapter.value?.next_id) {
    await handleNext({ auto: true, resetProgress: true })
  } else if (event?.direction === 'PREV' && chapterComposable.currentChapter.value?.prev_id) {
    await handlePrev({ auto: true, resetProgress: true, startPercent: 100 })
  }
}

/**
 * 加载指定章节并重新分页（用于多章节模式下达到边界时）
 */
async function loadChapterAndRepaginate(chapterId, startPercent = 0) {
  if (chapterComposable.isLoadingChapter.value) return
  
  try {
    // 清理预取缓存
    prefetchedChapters.value.clear()
    
    // 加载新章节
    await readerStore.loadChapter(chapterId, { format: 'text' })
    
    // 重新分页
    await paginateMultipleChaptersForPageMode(startPercent)
  } catch (error) {
    console.error('Failed to load chapter and repaginate:', error)
    message.error('加载章节失败')
  }
}

/**
 * 预取指定章节但不切换当前章节，适用于翻页模式追加内容
 */
async function prefetchChapterForPageMode(chapterId) {
  if (!chapterId || prefetchedChapters.value.has(chapterId)) return
  const data = await chapterComposable.fetchChapterById(chapterId)
  if (data) {
    prefetchedChapters.value.set(chapterId, data)
  }
}

async function prefetchNextChaptersIfNeeded(currentChapterId) {
  const toc = chapterComposable.toc.value || []
  const currentIdx = toc.findIndex(c => c.id === currentChapterId)
  if (currentIdx < 0) return

  const idsToPrefetch = []
  for (let i = 1; i <= 2; i++) {
    const nextEntry = toc[currentIdx + i]
    if (nextEntry?.id) idsToPrefetch.push(nextEntry.id)
  }

  const tasks = []
  for (const id of idsToPrefetch) {
    if (!id) continue
    const alreadyLoaded = chapterComposable.findInLoaded(id) || prefetchedChapters.value.has(id)
    if (alreadyLoaded) continue
    tasks.push(prefetchChapterForPageMode(id))
  }

  if (tasks.length) {
    await Promise.all(tasks)
  }
}

// 模式切换
function changeMode(mode) {
  if (mode === 'page' && !isMobile.value) {
    message.warning('PC 端暂不支持翻页模式')
    return
  }
  if (activeMode.value === mode) return
  readerStore.updateSetting('readingMode', mode)
}

// 设置更新
function handleUpdateSetting(key, value) {
  readerStore.updateSetting(key, value)
}

// 全屏控制
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

// 书签
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

// EPUB缓存
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

// TTS
function handleToggleTts() {
  ttsComposable.toggleTts(chapterComposable.chapterContent.value)
}

// 响应式处理
function handleResize() {
  const wasMobile = isMobile.value
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value && activeMode.value === 'page') {
    // PC 不支持翻页模式，自动回退为滚动
    readerStore.updateSetting('readingMode', 'scroll')
  }
  mobileChromeVisible.value = isMobile.value ? mobileChromeVisible.value && wasMobile : true

  // 更新滚动监听
  if (isMobile.value) {
    window.addEventListener('scroll', handleScroll)
  } else {
    window.removeEventListener('scroll', handleScroll)
  }
}

function handlePageResize({ width, height }) {
  if (!isPageMode.value) return
  
  pageComposable.updateDimensions(width, height)
  
  clearTimeout(resizeTimer)
  resizeTimer = window.setTimeout(async () => {
    const anchorChapterId = pageComposable.activeChapterId.value || chapterComposable.currentChapter.value?.id
    let currentPercent = pageComposable.calculateChapterProgress(anchorChapterId)
    if (!Number.isFinite(currentPercent)) currentPercent = 0
    await paginateMultipleChaptersForPageMode(currentPercent, anchorChapterId)
  }, 200)
}

function goBack() {
  router.push({ name: 'book-detail', params: { id: route.params.bookId } })
}

// 生命周期
onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  document.addEventListener('fullscreenchange', onFullscreenChange)
  initPage()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  progressComposable.cleanup()
  clearTimeout(resizeTimer)
  clearTimeout(cacheRefreshTimer)
  epubComposable.disposeEpub()
  ttsComposable.stopTts()
})

// Watchers
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
      // 设置变化时重新分页（使用多章节模式）
      const currentPercent = pageComposable.calculateChapterProgress()
      await paginateMultipleChaptersForPageMode(currentPercent)
    }
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
      // 确保翻页模式有文本内容
      if (!chapterComposable.chapterContent.value?.content_text && readerStore.currentChapterId) {
        await readerStore.loadChapter(readerStore.currentChapterId, { format: 'text' })
      }
      await nextTick()
      // 切换到翻页模式时，使用多章节分页
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
</script>

<template>
  <div class="reader-view" :style="backgroundStyle" :class="{ 'is-mobile': isMobile }">
    <!-- 工具栏 -->
    <ReaderToolbar
      :is-mobile="isMobile"
      :show-chrome="showChrome"
      :is-scroll-mode="isScrollMode"
      :is-page-mode="isPageMode"
      :is-epub-mode="isEpubMode"
      :is-fullscreen="isFullscreen"
      :is-loading-chapter="chapterComposable.isLoadingChapter.value"
      :current-book-title="currentBookTitle"
      :chapter-label="chapterLabel"
      :display-percent="progressComposable.displayPercent.value"
      :has-prev="!!chapterComposable.currentChapter.value?.prev_id"
      :has-next="!!chapterComposable.currentChapter.value?.next_id"
      :tts-state="ttsComposable.ttsState.value"
      :caching="caching"
      :epub-cached="cacheStatus.epub_cached"
      @back="goBack"
      @open-toc="tocVisible = true"
      @open-settings="settingsVisible = true"
      @reload="reloadChapter"
      @prev="handlePrev"
      @next="handleNext"
      @change-mode="changeMode"
      @toggle-fullscreen="toggleFullscreen"
      @add-bookmark="addBookmarkAtCurrent"
      @cache-epub="handleCacheEpub"
      @toggle-tts="handleToggleTts"
      @progress-change="handleProgressChange"
    />

    <div class="reader-body">
      <!-- 目录抽屉 -->
      <ReaderTocDrawer
        v-model:visible="tocVisible"
        :is-mobile="isMobile"
        :toc="chapterComposable.toc.value"
        :current-chapter-id="readerStore.currentChapterId"
        :current-book-title="currentBookTitle"
        :cached-chapters="cacheStatus.cached_chapters"
        @select-chapter="handleSelectChapter"
      />

      <!-- 设置抽屉 -->
      <ReaderSettingsDrawer
        v-model:visible="settingsVisible"
        :is-mobile="isMobile"
        :settings="readerSettings"
        :is-scroll-mode="isScrollMode"
        :is-page-mode="isPageMode"
        :is-epub-mode="isEpubMode"
        :is-fullscreen="isFullscreen"
        :background-color="backgroundColor"
        :text-color="textColor"
        @update-setting="handleUpdateSetting"
        @change-mode="changeMode"
        @toggle-fullscreen="toggleFullscreen"
        @reset-settings="readerStore.resetSettings()"
      />

      <!-- 内容区域 -->
      <div class="reader-content" :class="{ 'mobile-content': isMobile }" @click="handleContentTap">
        <n-spin :show="initializing || chapterComposable.isLoadingChapter.value || (isEpubMode && epubComposable.epubLoading.value)">
          <!-- EPUB模式 -->
          <template v-if="isEpubMode">
            <ReaderEpubContent
              v-model:epub-container-ref="epubContainerRef"
              :error="epubComposable.epubError.value"
            />
          </template>

          <!-- 翻页模式 -->
          <template v-else-if="isPageMode">
            <ReaderPageContent
              v-model:flicking-ref="flickingRef"
              :is-mobile="isMobile"
              :page-chunks="pageComposable.pageChunks.value"
              :page-panel-style="pagePanelStyle"
              :reader-content-style="readerContentStyle"
              :paragraph-style="paragraphStyle"
              :chapter-title="chapterComposable.currentChapter.value?.title || ''"
              :chapter-boundaries="pageComposable.chapterBoundaries.value"
              :multi-chapter-mode="multiChapterMode"
              :has-next-chapter="!!chapterComposable.currentChapter.value?.next_id"
              :has-prev-chapter="!!chapterComposable.currentChapter.value?.prev_id"
              @page-changed="handlePageChanged"
              @chapter-changed="handleChapterChanged"
              @need-more-chapters="handleNeedMoreChapters"
              @reach-edge="handleReachEdge"
              @resize="handlePageResize"
            />
          </template>

          <!-- 滚动模式 -->
          <template v-else>
            <ReaderScrollContent
              ref="scrollContentRef"
              :is-mobile="isMobile"
              :display-chapters="chapterComposable.displayChapters.value"
              :has-content="chapterComposable.hasContent.value"
              :is-fetching="chapterComposable.isFetching.value"
              :error="readerStore.error"
              :initializing="initializing"
              :is-loading-chapter="chapterComposable.isLoadingChapter.value"
              :current-book-title="currentBookTitle"
              :current-chapter-id="readerStore.currentChapterId"
              :reader-content-style="readerContentStyle"
              :paragraph-style="paragraphStyle"
              @scroll="handleScroll"
              @reload="reloadChapter"
              @register-ref="chapterComposable.registerChapterRef"
            />
          </template>
        </n-spin>
      </div>
    </div>

    <!-- 移动端底部控制栏 -->
    <ReaderFooter
      :visible="showChrome"
      :is-mobile="isMobile"
      :current-chapter="chapterComposable.currentChapter.value"
      :display-percent="progressComposable.displayPercent.value"
      :is-loading-chapter="chapterComposable.isLoadingChapter.value"
      :tts-state="ttsComposable.ttsState.value"
      :caching="caching"
      :epub-cached="cacheStatus.epub_cached"
      @prev="handlePrev"
      @next="handleNext"
      @add-bookmark="addBookmarkAtCurrent"
      @cache-epub="handleCacheEpub"
      @toggle-tts="handleToggleTts"
      @stop-tts="ttsComposable.stopTts"
      @progress-change="handleProgressChange"
    />

    <n-back-top
      v-if="isScrollMode"
      :right="24"
      :bottom="isMobile ? 96 : 32"
      listen-to=".chapter-scroll"
    />
  </div>
</template>

<style scoped>
.reader-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 12px 12px 24px;
  box-sizing: border-box;
}

.reader-view:not(.is-mobile) {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 24px;
  padding: 0 12px 0 0;
  height: 100vh;
  min-height: unset;
}

.reader-view.is-mobile {
  padding: 0;
  overflow: hidden;
  height: 100vh;
  min-height: unset;
}

.reader-body {
  display: flex;
  gap: 12px;
  margin-top: 0;
  flex: 1;
  min-height: 0; /* 允许 flex 子元素收缩，确保内部滚动正常 */
  justify-content: center;
}

.reader-view.is-mobile .reader-body {
  margin-top: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.reader-content {
  flex: 1;
  width: 100%;
  max-width: 960px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  /* 桌面端需要明确高度以支持内部滚动 */
  height: calc(100vh - 24px);
  min-height: 0; /* 允许 flex 子元素收缩 */
  overflow: hidden;
  overflow-anchor: none;
  display: flex;
  flex-direction: column;
}

/* n-spin 需要撑满父容器以传递高度 */
.reader-content :deep(.n-spin-container),
.reader-content :deep(.n-spin-content) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.reader-view.is-mobile .reader-content {
  height: 100%;
  max-width: none;
  overflow: hidden;
  padding: 0;
}

.reader-content.mobile-content {
  background: transparent;
  box-shadow: none;
  padding: 0;
}

@media (max-width: 768px) {
  .reader-view {
    padding: 0;
  }

  .reader-content {
    height: 100%;
  }
}
</style>

<style>
/* 工具栏响应式样式 - 需要全局以覆盖子组件 */
.reader-view.is-mobile .reader-toolbar {
  padding: 10px 12px;
  top: 0;
  position: fixed;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  transition: transform 0.3s ease;
}

.reader-view:not(.is-mobile) .reader-toolbar {
  flex-direction: column;
  width: 80px;
  padding: 16px 10px;
  height: calc(100vh - 24px);
  position: sticky;
  top: 12px;
  align-self: flex-start;
  gap: 16px;
  justify-content: flex-start;
}

.reader-view:not(.is-mobile) .toolbar-group {
  flex-direction: column;
  width: 100%;
}

.reader-view:not(.is-mobile) .toolbar-group.center {
  flex: 1;
  justify-content: center;
  gap: 16px;
}

.reader-view:not(.is-mobile) .toolbar-group.bottom {
  margin-top: auto;
  gap: 16px;
}

.reader-view:not(.is-mobile) .mode-switch {
  flex-direction: column;
  width: 100%;
  padding: 8px 6px;
}

.reader-view.is-mobile .toolbar-group.top {
  justify-content: space-between;
  width: 100%;
}

.reader-view.is-mobile .toolbar-group.center {
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.reader-view.is-mobile .toolbar-group.bottom {
  display: none;
}

.reader-view.is-mobile .mode-switch {
  width: 100%;
  justify-content: center;
  padding: 6px 8px;
}

.reader-view.is-mobile .chapter-title {
  max-width: 60vw;
}
</style>
