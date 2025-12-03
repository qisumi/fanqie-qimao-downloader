/**
 * 阅读进度管理 composable
 * 负责进度计算、保存、恢复
 */
import { ref, computed } from 'vue'

export function useReaderProgress(options = {}) {
  const { readerStore, isScrollMode, isPageMode, isEpubMode } = options

  // 进度状态
  const scrollPercent = ref(0)
  const epubPercent = ref(0)
  const currentPageIndex = ref(0)
  const pageChunks = ref([])

  // 内部状态
  let saveTimer = null
  let suppressSave = false
  let forcedStartPercent = null

  // 计算属性
  const pageProgress = computed(() => {
    if (!pageChunks.value.length) return 0
    if (pageChunks.value.length === 1) return 100
    return Number(((currentPageIndex.value / Math.max(pageChunks.value.length - 1, 1)) * 100).toFixed(2))
  })

  const displayPercent = computed(() => {
    if (isPageMode?.value) return pageProgress.value
    if (isEpubMode?.value) return epubPercent.value
    return scrollPercent.value
  })

  const percentLabel = computed(() => `${Math.round(displayPercent.value)}%`)

  // 设置/消费强制起始进度
  function setForcedStartPercent(value) {
    forcedStartPercent = Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : null
  }

  function consumeStartPercent(defaultPercent = 0) {
    const val = forcedStartPercent
    forcedStartPercent = null
    if (Number.isFinite(val)) return Math.max(0, Math.min(100, val))
    return Math.max(0, Math.min(100, Number(defaultPercent) || 0))
  }

  // 队列保存进度（防抖）
  function queueSaveProgress(offsetPx, percent) {
    if (suppressSave) return
    clearTimeout(saveTimer)
    const payload = {
      offset_px: Math.round(offsetPx || 0),
      percent: Number(percent.toFixed(2) || 0)
    }
    saveTimer = window.setTimeout(() => {
      readerStore?.saveProgress(payload).catch(err => {
        console.warn('Save progress failed', err)
      })
    }, 400)
  }

  // 更新滚动进度
  function updateScrollPercent(value, shouldSave = true) {
    scrollPercent.value = Number(value.toFixed(2))
    if (shouldSave && !suppressSave) {
      // 实际的 offsetPx 需要外部传入
      queueSaveProgress(0, scrollPercent.value)
    }
  }

  // 更新翻页进度
  function updatePageProgress(shouldSave = true) {
    if (!pageChunks.value.length) return
    if (shouldSave && !suppressSave) {
      queueSaveProgress(currentPageIndex.value * 1000, pageProgress.value)
    }
  }

  // 更新 EPUB 进度
  function updateEpubPercent(value, shouldSave = true) {
    const safePercent = Math.max(0, Math.min(100, Number(value.toFixed(2)) || 0))
    epubPercent.value = safePercent
    if (shouldSave && !suppressSave) {
      queueSaveProgress(0, safePercent)
    }
  }

  // 获取当前进度（用于书签等）
  function getCurrentProgress(contentRef, chapterRefs, currentChapterId) {
    const percent = displayPercent.value || 0
    if (isScrollMode?.value) {
      const container = contentRef?.value
      const activeEl = chapterRefs?.get(currentChapterId)
      if (container && activeEl) {
        const offset = Math.max(0, container.scrollTop - activeEl.offsetTop)
        return { offsetPx: Math.round(offset), percent }
      }
      return { offsetPx: container?.scrollTop || 0, percent }
    }
    if (isPageMode?.value) {
      return { offsetPx: currentPageIndex.value * 1000, percent: pageProgress.value }
    }
    return { offsetPx: 0, percent: epubPercent.value || percent }
  }

  // 设置抑制保存状态
  function setSuppressSave(value) {
    suppressSave = value
  }

  // 清理
  function cleanup() {
    clearTimeout(saveTimer)
    saveTimer = null
    suppressSave = false
  }

  return {
    // 状态
    scrollPercent,
    epubPercent,
    currentPageIndex,
    pageChunks,

    // 计算属性
    pageProgress,
    displayPercent,
    percentLabel,

    // 方法
    setForcedStartPercent,
    consumeStartPercent,
    queueSaveProgress,
    updateScrollPercent,
    updatePageProgress,
    updateEpubPercent,
    getCurrentProgress,
    setSuppressSave,
    cleanup
  }
}
