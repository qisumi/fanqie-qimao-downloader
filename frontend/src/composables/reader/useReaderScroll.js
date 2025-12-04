/**
 * 滚动模式 composable
 * 负责滚动事件处理、进度计算、自动加载等
 */
import { nextTick } from 'vue'

export function useReaderScroll(options = {}) {
  const {
    isMobile,
    chapterRefs,
    readerStore,
    currentChapter,
    loadedChapters,
    prevChapterContent,
    nextChapterContent,
    autoLoadingNext,
    autoLoadingPrev,
    fetchChapterById,
    activateChapter,
    addLoadedChapter,
    contentRef  // 外部传入的滚动容器 ref
  } = options

  // 应用保存的滚动位置
  async function applySavedScroll(chapterContent, targetPercent = null, setSuppressSave) {
    const container = contentRef?.value
    if (!container && !isMobile?.value) return
    await nextTick()
    setSuppressSave?.(true)

    const savedPx = chapterContent?.offset_px
    const savedPercent = targetPercent ?? chapterContent?.percent

    if (container) {
      const maxScroll = Math.max(container.scrollHeight - container.clientHeight, 0)
      if (Number.isFinite(targetPercent)) {
        container.scrollTop = (Math.max(0, Math.min(100, targetPercent)) / 100) * maxScroll
      } else if (Number.isFinite(savedPx) && savedPx > 0) {
        container.scrollTop = Math.min(savedPx, maxScroll)
      } else if (Number.isFinite(savedPercent) && savedPercent > 0 && maxScroll > 0) {
        container.scrollTop = (savedPercent / 100) * maxScroll
      } else {
        container.scrollTop = 0
      }
    } else {
      const maxScroll = Math.max(document.documentElement.scrollHeight - window.innerHeight, 0)
      if (Number.isFinite(targetPercent)) {
        window.scrollTo(0, (Math.max(0, Math.min(100, targetPercent)) / 100) * maxScroll)
      } else if (Number.isFinite(savedPx) && savedPx > 0) {
        window.scrollTo(0, Math.min(savedPx, maxScroll))
      } else if (Number.isFinite(savedPercent) && savedPercent > 0 && maxScroll > 0) {
        window.scrollTo(0, (savedPercent / 100) * maxScroll)
      } else {
        window.scrollTo(0, 0)
      }
    }
    setSuppressSave?.(false)
  }

  // 计算滚动进度
  function calculateScrollProgress() {
    const container = contentRef?.value
    if (!container && !isMobile?.value) return { percent: 0, offsetPx: 0 }

    let scrollTop = 0
    let scrollHeight = 0
    let clientHeight = 0

    if (container) {
      scrollTop = container.scrollTop
      scrollHeight = container.scrollHeight
      clientHeight = container.clientHeight
    } else {
      scrollTop = window.scrollY || document.documentElement.scrollTop
      scrollHeight = document.documentElement.scrollHeight
      clientHeight = window.innerHeight
    }

    // 计算当前章节的进度
    const currentChapterId = readerStore?.currentChapterId
    const activeEl = chapterRefs?.get(currentChapterId)
    if (activeEl) {
      const offset = Math.max(0, scrollTop - activeEl.offsetTop)
      const maxScroll = Math.max(activeEl.scrollHeight - clientHeight, 1)
      const percent = Math.min(100, Math.max(0, (offset / maxScroll) * 100))
      return { percent, offsetPx: offset }
    }

    const maxScroll = Math.max(scrollHeight - clientHeight, 1)
    const percent = Math.min(100, Math.max(0, (scrollTop / maxScroll) * 100))
    return { percent, offsetPx: scrollTop }
  }

  // 滚动到指定章节的指定进度
  function scrollToActivePercent(value) {
    const container = contentRef?.value
    if (!container && !isMobile?.value) return

    const currentChapterId = readerStore?.currentChapterId
    const activeEl = chapterRefs?.get(currentChapterId)
    if (!activeEl) return

    if (container) {
      const maxScroll = Math.max(activeEl.scrollHeight - container.clientHeight, 0)
      container.scrollTo({
        top: activeEl.offsetTop + (value / 100) * maxScroll,
        behavior: 'smooth'
      })
    } else {
      const maxScroll = Math.max(activeEl.scrollHeight - window.innerHeight, 0)
      window.scrollTo({
        top: activeEl.offsetTop + (value / 100) * maxScroll,
        behavior: 'smooth'
      })
    }
  }

  // 滚动到指定章节
  function scrollIntoChapter(chapterId) {
    const container = contentRef?.value
    const el = chapterRefs?.get(chapterId)
    if ((!container && !isMobile?.value) || !el) return

    let viewTop = 0
    let viewBottom = 0

    if (container) {
      viewTop = container.scrollTop
      viewBottom = viewTop + container.clientHeight
    } else {
      viewTop = window.scrollY || document.documentElement.scrollTop
      viewBottom = viewTop + window.innerHeight
    }

    const top = el.offsetTop
    const bottom = top + el.offsetHeight
    const inside = viewTop <= top && viewBottom >= bottom
    if (!inside) {
      if (container) {
        container.scrollTo({ top, behavior: 'auto' })
      } else {
        window.scrollTo({ top, behavior: 'auto' })
      }
    }
  }

  // 滚动到指定章节的指定进度位置（用于预加载后精确定位）
  async function scrollToChapterPercent(chapterId, percent, setSuppressSave) {
    const container = contentRef?.value
    const chapterEl = chapterRefs?.get(chapterId)
    
    if (!chapterEl) {
      console.warn('scrollToChapterPercent: chapter element not found', chapterId)
      return
    }
    
    // 移动端和桌面端都使用容器滚动（因为移动端 CSS 也是在 .chapter-scroll 容器内滚动）
    if (!container) {
      console.warn('scrollToChapterPercent: container not found')
      return
    }

    await nextTick()
    setSuppressSave?.(true)

    const clientHeight = container.clientHeight
    const maxScroll = Math.max(chapterEl.scrollHeight - clientHeight, 0)
    // offsetTop 是相对于容器的，直接使用
    const targetScroll = chapterEl.offsetTop + (percent / 100) * maxScroll

    container.scrollTop = targetScroll

    setSuppressSave?.(false)
  }

  // 根据滚动位置更新当前章节，返回是否发生章节切换
  function updateActiveChapterByScroll() {
    const currentChapterId = readerStore?.currentChapterId
    const container = contentRef?.value
    if (!container || !chapterRefs?.size) return false

    // 移动端和桌面端都使用容器滚动
    const center = container.scrollTop + container.clientHeight / 2

    let closestId = null
    let minDist = Number.POSITIVE_INFINITY
    chapterRefs.forEach((el, id) => {
      if (!el) return
      const top = el.offsetTop
      const height = el.offsetHeight
      const blockCenter = top + height / 2
      const dist = Math.abs(blockCenter - center)
      if (dist < minDist) {
        minDist = dist
        closestId = id
      }
    })

    if (closestId && closestId !== currentChapterId) {
      activateChapter?.(closestId, { scroll: false })
      return true // 章节切换了
    }
    return false
  }

  // 自动加载下一章
  async function maybeAutoLoadNextChapter() {
    if (autoLoadingNext?.value) return
    if (!currentChapter?.value?.next_id || nextChapterContent?.value) return

    const container = contentRef?.value
    if (!container) return

    // 移动端和桌面端都使用容器滚动
    const distanceToBottom = container.scrollHeight - (container.scrollTop + container.clientHeight)

    if (distanceToBottom > 120) return

    if (autoLoadingNext) autoLoadingNext.value = true
    const nextData = await fetchChapterById?.(currentChapter.value.next_id)
    if (nextData && nextChapterContent) {
      nextChapterContent.value = nextData
      addLoadedChapter?.(nextData, 'end')
    }
    if (autoLoadingNext) autoLoadingNext.value = false
  }

  // 自动加载上一章
  async function maybeAutoLoadPrevChapter() {
    if (autoLoadingPrev?.value) return
    if (!currentChapter?.value?.prev_id || prevChapterContent?.value) return

    const container = contentRef?.value
    if (!container) return

    // 移动端和桌面端都使用容器滚动
    const distanceToTop = container.scrollTop

    if (distanceToTop > 120) return

    if (autoLoadingPrev) autoLoadingPrev.value = true
    const prevData = await fetchChapterById?.(currentChapter.value.prev_id)
    if (prevData) {
      const beforeHeight = container.scrollHeight
      const beforeScroll = container.scrollTop
        
      if (prevChapterContent) prevChapterContent.value = prevData
      addLoadedChapter?.(prevData, 'start')
      
      // 等待 DOM 更新
      await nextTick()
      await nextTick() // 双重 nextTick 确保 DOM 完全渲染
      
      const afterHeight = container.scrollHeight
      const diff = afterHeight - beforeHeight
      
      if (diff > 0) {
        container.scrollTop = beforeScroll + diff
      }
    }
    if (autoLoadingPrev) autoLoadingPrev.value = false
  }

  return {
    applySavedScroll,
    calculateScrollProgress,
    scrollToActivePercent,
    scrollIntoChapter,
    scrollToChapterPercent,
    updateActiveChapterByScroll,
    maybeAutoLoadNextChapter,
    maybeAutoLoadPrevChapter
  }
}
