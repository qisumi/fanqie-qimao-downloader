import { ref } from 'vue'

const PAGE_ANIMATION_DURATION = 250

/**
 * Page-mode specific behaviors (multi-chapter pagination, edge handling, resize).
 * Keeps ReaderView lean by grouping the heavy paging logic here.
 */
export function useReaderPageMode({
  chapterComposable,
  pageComposable,
  progressComposable,
  readerStore,
  message,
  isPageMode,
  notifyDownloadingIfNeeded,
  onPrevChapter,
  onNextChapter
}) {
  const multiChapterMode = ref(false)
  const prefetchedChapters = ref(new Map())
  const prefetchingChapterIds = ref(new Set())
  let resizeTimer = null

  /**
   * Prefetch chapters around the anchor so page mode can paginate multiple chapters.
   * Returns an ordered array of chapter data with prev/next ids filled.
   */
  async function prefetchChaptersForPageMode(anchorChapterId = null) {
    const currentContent = chapterComposable.chapterContent.value
    const toc = chapterComposable.toc.value || []
    if (!toc.length) return currentContent ? [currentContent] : []

    const anchorId = anchorChapterId || pageComposable.activeChapterId.value || chapterComposable.currentChapter.value?.id
    const anchorIndex = anchorId ? toc.findIndex(c => c.id === anchorId) : -1
    const centerIndex = anchorIndex >= 0 ? anchorIndex : toc.findIndex(c => c.id === chapterComposable.currentChapter.value?.id)
    if (centerIndex < 0) return currentContent ? [currentContent] : []

    const startIdx = Math.max(0, centerIndex - 2)
    const endIdx = Math.min(toc.length - 1, centerIndex + 2)

    const windowChapterIds = new Set()
    for (let i = startIdx; i <= endIdx; i++) {
      windowChapterIds.add(toc[i].id)
    }

    for (const cachedId of prefetchedChapters.value.keys()) {
      if (!windowChapterIds.has(cachedId)) {
        prefetchedChapters.value.delete(cachedId)
      }
    }

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
   * Paginate multiple chapters in page mode while keeping progress in sync.
   */
  async function paginateMultipleChaptersForPageMode(targetPercent = 0, anchorChapterId = null) {
    const anchorId = anchorChapterId || pageComposable.activeChapterId.value || chapterComposable.currentChapter.value?.id
    const chapters = await prefetchChaptersForPageMode(anchorId)
    const currentChapterId = anchorId || chapterComposable.currentChapter.value?.id

    multiChapterMode.value = chapters.length > 1
    pageComposable.setSuppressSave(true)
    try {
      pageComposable.paginateMultipleChapters(chapters, currentChapterId, targetPercent)
      progressComposable.pageChunks.value = pageComposable.pageChunks.value
      progressComposable.currentPageIndex.value = pageComposable.currentPageIndex.value
    } finally {
      pageComposable.setSuppressSave(false)
    }
  }

  function handlePageChanged(event) {
    if (event?.prevIndex === -1) {
      progressComposable.currentPageIndex.value = pageComposable.currentPageIndex.value
      return
    }

    const suppressing = typeof pageComposable.isSuppressSave === 'function' && pageComposable.isSuppressSave()
    const result = pageComposable.handlePageChanged(event)
    progressComposable.currentPageIndex.value = pageComposable.currentPageIndex.value

    if (suppressing) return

    if (multiChapterMode.value && result?.chapterId) {
      if (result.chapterId !== readerStore.currentChapterId) {
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
          progressComposable.queueSaveProgress(0, 0)
        }
      } else {
        const chapterPercent = pageComposable.calculateChapterProgress(result.chapterId)
        progressComposable.scrollPercent.value = chapterPercent
        progressComposable.queueSaveProgress(0, chapterPercent)
      }
    } else {
      progressComposable.updatePageProgress(true)
    }
  }

  async function handleChapterChanged(event) {
    if (!isPageMode.value || !multiChapterMode.value) return
    const { chapterId, boundary } = event
    if (!chapterId || !boundary) return

    readerStore.currentChapterId = chapterId
    readerStore.currentChapter = {
      id: chapterId,
      title: boundary.title,
      index: boundary.index,
      prev_id: boundary.prev_id,
      next_id: boundary.next_id
    }
    progressComposable.queueSaveProgress(0, 0)

    const loadedChapterIds = pageComposable.loadedChapterIds.value
    if (loadedChapterIds.length >= 3) {
      const chapterIndexInWindow = loadedChapterIds.indexOf(chapterId)
      const isNearEnd = chapterIndexInWindow >= loadedChapterIds.length - 1
      const nextChapterNotInWindow = boundary.next_id && !loadedChapterIds.includes(boundary.next_id)
      const isNearStart = chapterIndexInWindow <= 0
      const prevChapterNotInWindow = boundary.prev_id && !loadedChapterIds.includes(boundary.prev_id)
      const shouldMoveWindow = (isNearEnd && nextChapterNotInWindow) || (isNearStart && prevChapterNotInWindow)

      if (shouldMoveWindow) {
        setTimeout(async () => {
          const currentPercent = pageComposable.calculateChapterProgress(chapterId)
          await paginateMultipleChaptersForPageMode(currentPercent, chapterId)
        }, PAGE_ANIMATION_DURATION + 50)
        return
      }
    }

    setTimeout(() => {
      prefetchNextChaptersIfNeeded(chapterId)
    }, PAGE_ANIMATION_DURATION + 50)
  }

  async function handleNeedMoreChapters(event) {
    if (!isPageMode.value || !multiChapterMode.value) return
    if (chapterComposable.isLoadingChapter.value) return
    // placeholder for future dynamic append
  }

  async function handleReachEdge(event) {
    if (!isPageMode.value || chapterComposable.isLoadingChapter.value) return

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

      if (!Number.isFinite(currentPercent)) {
        currentPercent = event?.direction === 'NEXT' ? 100 : 0
      } else if (anchorBoundary) {
        const idx = pageComposable.currentPageIndex.value
        if (event?.direction === 'NEXT' && idx >= anchorBoundary.endPage) currentPercent = 100
        if (event?.direction === 'PREV' && idx <= anchorBoundary.startPage) currentPercent = 0
      }

      if (event?.direction === 'PREV') {
        if (!firstBoundary?.prev_id) {
          message.info('已经是第一章了')
        } else {
          notifyDownloadingIfNeeded(firstBoundary.prev_id)
          await prefetchChapterForPageMode(firstBoundary.prev_id)
          const freshAnchorChapterId = firstBoundary.prev_id
          await paginateMultipleChaptersForPageMode(100, freshAnchorChapterId)
        }
      } else if (event?.direction === 'NEXT') {
        if (!lastBoundary?.next_id) {
          message.info('已经是最后一章了')
        } else {
          notifyDownloadingIfNeeded(lastBoundary.next_id)
          await prefetchChapterForPageMode(lastBoundary.next_id)
          const freshAnchorChapterId = lastBoundary.next_id
          await paginateMultipleChaptersForPageMode(0, freshAnchorChapterId)
        }
      }
      return
    }

    if (event?.direction === 'NEXT' && chapterComposable.currentChapter.value?.next_id) {
      await onNextChapter?.({ auto: true, resetProgress: true })
    } else if (event?.direction === 'PREV' && chapterComposable.currentChapter.value?.prev_id) {
      await onPrevChapter?.({ auto: true, resetProgress: true, startPercent: 100 })
    }
  }

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

  function handlePageResize() {
    if (!isPageMode.value) return
    clearTimeout(resizeTimer)
    resizeTimer = window.setTimeout(async () => {
      const anchorChapterId = pageComposable.activeChapterId.value || chapterComposable.currentChapter.value?.id
      let currentPercent = pageComposable.calculateChapterProgress(anchorChapterId)
      if (!Number.isFinite(currentPercent)) currentPercent = 0
      await paginateMultipleChaptersForPageMode(currentPercent, anchorChapterId)
    }, 200)
  }

  function clearPageResizeTimer() {
    clearTimeout(resizeTimer)
  }

  return {
    multiChapterMode,
    paginateMultipleChaptersForPageMode,
    handlePageChanged,
    handleChapterChanged,
    handleNeedMoreChapters,
    handleReachEdge,
    prefetchNextChaptersIfNeeded,
    prefetchChapterForPageMode,
    handlePageResize,
    clearPageResizeTimer
  }
}
