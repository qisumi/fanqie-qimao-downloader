/**
 * EPUB模式 composable
 * 负责epub.js加载、显示、导航
 */
import { ref, nextTick } from 'vue'

export function useReaderEpub(options = {}) {
  const { getEpubDownloadUrl, bookId } = options

  const epubContainerRef = ref(null)
  const epubLoading = ref(false)
  const epubError = ref(null)
  const epubBook = ref(null)
  const epubRendition = ref(null)
  const epubLocationsReady = ref(false)
  const epubPercent = ref(0)

  let epubModule = null
  let relocatedHandler = null

  // 动态加载epub.js
  async function ensureEpubModule() {
    if (epubModule) return epubModule
    const mod = await import('epubjs')
    epubModule = mod.default || mod
    return epubModule
  }

  // 处理位置变化
  function handleEpubRelocated(location, onPercentChange) {
    if (!epubBook.value) return
    const percent = epubLocationsReady.value && location?.start?.cfi
      ? epubBook.value.locations.percentageFromCfi(location.start.cfi) * 100
      : 0
    const safePercent = Math.max(0, Math.min(100, Number(percent.toFixed(2)) || 0))
    epubPercent.value = safePercent
    onPercentChange?.(safePercent)
  }

  // 加载EPUB
  async function loadEpub(savedPercent = 0, onPercentChange) {
    try {
      epubLoading.value = true
      epubError.value = null
      disposeEpub()
      await ensureEpubModule()
      await nextTick()

      if (!epubContainerRef.value) {
        throw new Error('EPUB container not found')
      }

      const url = getEpubDownloadUrl?.(bookId?.value || bookId)
      if (!url) {
        throw new Error('EPUB URL not available')
      }

      const book = epubModule(url)
      const rendition = book.renderTo(epubContainerRef.value, {
        width: '100%',
        height: '100%',
        flow: 'paginated',
        allowScriptedContent: false
      })

      // 保存handler以便移除
      relocatedHandler = (location) => handleEpubRelocated(location, onPercentChange)
      rendition.on('relocated', relocatedHandler)

      epubBook.value = book
      epubRendition.value = rendition

      await book.ready
      await book.locations.generate(1200)
      epubLocationsReady.value = true

      // 跳转到保存的进度
      const percent = Math.max(0, Math.min(100, savedPercent || 0))
      if (percent > 0 && book.locations && book.locations.length() > 0) {
        const cfi = book.locations.cfiFromPercentage(percent / 100)
        await rendition.display(cfi)
      } else {
        await rendition.display()
      }
    } catch (error) {
      epubError.value = error?.message || 'EPUB 加载失败'
      console.error('Load epub failed', error)
    } finally {
      epubLoading.value = false
    }
  }

  // 销毁EPUB
  function disposeEpub() {
    if (epubRendition.value) {
      if (relocatedHandler) {
        epubRendition.value.off?.('relocated', relocatedHandler)
      }
      epubRendition.value.destroy()
    }
    epubBook.value = null
    epubRendition.value = null
    epubLocationsReady.value = false
    relocatedHandler = null
  }

  // 跳转到指定进度
  function jumpToEpubPercent(value) {
    if (!epubBook.value || !epubRendition.value || !epubLocationsReady.value) return
    const target = epubBook.value.locations.cfiFromPercentage(
      Math.min(1, Math.max(0, value / 100))
    )
    epubRendition.value.display(target)
  }

  // 下一页
  function nextPage() {
    epubRendition.value?.next()
  }

  // 上一页
  function prevPage() {
    epubRendition.value?.prev()
  }

  return {
    epubContainerRef,
    epubLoading,
    epubError,
    epubBook,
    epubRendition,
    epubLocationsReady,
    epubPercent,
    loadEpub,
    disposeEpub,
    jumpToEpubPercent,
    nextPage,
    prevPage
  }
}
