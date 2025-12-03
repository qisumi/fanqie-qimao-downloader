/**
 * 章节内容处理 composable
 * 负责章节数据管理、段落构建、相邻章节缓存
 */
import { ref, computed, nextTick } from 'vue'

export function useReaderChapter(options = {}) {
  const { readerStore, bookStore, userStore, readerApi, isMobile } = options

  // 章节缓存
  const prevChapterContent = ref(null)
  const nextChapterContent = ref(null)
  const loadedChapters = ref([])
  const chapterRefs = new Map()
  const pendingChapterRequests = new Map()

  // 加载状态
  const autoLoadingNext = ref(false)
  const autoLoadingPrev = ref(false)

  // 计算当前章节内容
  const chapterContent = computed(() => readerStore?.chapterContent || {})
  const currentChapter = computed(() => readerStore?.currentChapter)
  const toc = computed(() => readerStore?.toc || [])
  const isLoadingChapter = computed(() => readerStore?.loading)
  const isFetching = computed(() => chapterContent.value.status === 'fetching')

  // 构建段落数据
  function buildParagraphs(content) {
    if (!content || content.content_html) return []
    const raw = content.content_text || ''
    if (!raw) return []
    return raw
      .split(/\n+/)
      .map((line, idx) => ({
        id: `${content.id || idx}-${idx}`,
        text: line.trim(),
        isSpacer: line.trim().length === 0
      }))
  }

  // 当前章节的段落
  const textParagraphs = computed(() => buildParagraphs(chapterContent.value))

  // 显示的章节列表（用于无限滚动）
  const displayChapters = computed(() => {
    if (loadedChapters.value.length) {
      const currentIdx = loadedChapters.value.findIndex(c => c.id === readerStore?.currentChapterId)
      return loadedChapters.value.map((data, idx) => ({
        role: idx === currentIdx ? 'current' : (idx < currentIdx ? 'prev' : 'next'),
        data,
        paragraphs: data.paragraphs || buildParagraphs(data)
      }))
    }
    const sections = []
    if (prevChapterContent.value?.content_html || prevChapterContent.value?.content_text) {
      sections.push({
        role: 'prev',
        data: prevChapterContent.value,
        paragraphs: prevChapterContent.value.paragraphs || buildParagraphs(prevChapterContent.value)
      })
    }
    if (chapterContent.value?.content_html || chapterContent.value?.content_text) {
      sections.push({
        role: 'current',
        data: chapterContent.value,
        paragraphs: chapterContent.value.paragraphs || textParagraphs.value
      })
    }
    if (nextChapterContent.value?.content_html || nextChapterContent.value?.content_text) {
      sections.push({
        role: 'next',
        data: nextChapterContent.value,
        paragraphs: nextChapterContent.value.paragraphs || buildParagraphs(nextChapterContent.value)
      })
    }
    return sections
  })

  const hasContent = computed(() => displayChapters.value.length > 0)

  // 根据ID查找已加载的章节
  function findInLoaded(id) {
    return loadedChapters.value.find(c => c.id === id)
  }

  function findChapterDataById(id) {
    if (!id) return null
    const loaded = findInLoaded(id)
    if (loaded) return loaded
    if (chapterContent.value?.id === id) return chapterContent.value
    if (prevChapterContent.value?.id === id) return prevChapterContent.value
    if (nextChapterContent.value?.id === id) return nextChapterContent.value
    return null
  }

  // 获取章节内容
  async function fetchChapterById(chapterId) {
    if (!chapterId || !bookStore?.currentBook?.id || !userStore?.currentUserId) return null
    // 优先返回本地缓存或正在进行的请求，避免重复发起
    const cached = findChapterDataById(chapterId)
    if (cached) {
      if (!cached.paragraphs) cached.paragraphs = buildParagraphs(cached)
      return cached
    }
    if (pendingChapterRequests.has(chapterId)) {
      return pendingChapterRequests.get(chapterId)
    }

    const request = (async () => {
      try {
        const response = await readerApi.getChapterContent(bookStore.currentBook.id, chapterId, {
          userId: userStore.currentUserId,
          format: 'text',
          prefetch: 5
        })
        const data = response.data || {}
        if (!data.id) data.id = chapterId
        data.paragraphs = buildParagraphs(data)
        return data
      } catch (error) {
        console.warn('Fetch chapter failed', error)
        return null
      } finally {
        pendingChapterRequests.delete(chapterId)
      }
    })()

    pendingChapterRequests.set(chapterId, request)
    return request
  }

  // 注册章节DOM引用
  function registerChapterRef(id, el) {
    if (!id) return
    if (el) {
      chapterRefs.set(id, el)
    } else {
      chapterRefs.delete(id)
    }
  }

  // 重置相邻缓存
  function resetAdjacentCaches() {
    prevChapterContent.value = null
    nextChapterContent.value = null
    chapterRefs.clear()
  }

  // 添加章节到已加载列表
  // 注意：此函数不再自动调用 pruneLoadedAroundCurrent，调用方需要在适当时机手动调用
  function addLoadedChapter(data, position = 'end') {
    if (!data?.id) return
    const exists = findInLoaded(data.id)
    if (exists) return
    if (position === 'start') {
      loadedChapters.value.unshift(data)
    } else {
      loadedChapters.value.push(data)
    }
  }

  // 裁剪已加载章节（保留当前章节附近2章，即当前章+前后各2章=最多5章）
  async function pruneLoadedAroundCurrent(contentRef) {
    if (!loadedChapters.value.length) return
    const currentId = readerStore?.currentChapterId
    const idx = loadedChapters.value.findIndex(c => c.id === currentId)
    if (idx === -1) return
    const container = contentRef?.value
    const start = Math.max(0, idx - 2)
    const end = Math.min(loadedChapters.value.length, idx + 3) // idx + 2 + 1 因为 slice 的 end 是排他的
    
    // 如果没有需要裁剪的，直接返回
    if (start === 0 && end === loadedChapters.value.length) {
      const newIdx = loadedChapters.value.findIndex(c => c.id === currentId)
      prevChapterContent.value = newIdx > 0 ? loadedChapters.value[newIdx - 1] : null
      nextChapterContent.value = newIdx >= 0 && newIdx + 1 < loadedChapters.value.length
        ? loadedChapters.value[newIdx + 1]
        : null
      return
    }
    
    // 计算将要移除的前面章节的总高度
    let removedBeforeHeight = 0
    for (let i = 0; i < start; i++) {
      const el = chapterRefs.get(loadedChapters.value[i].id)
      if (el) removedBeforeHeight += el.offsetHeight
    }
    
    // 移动端和桌面端都使用容器滚动
    const beforeScroll = container?.scrollTop || 0
    
    loadedChapters.value = loadedChapters.value.slice(start, end)
    const newIdx = loadedChapters.value.findIndex(c => c.id === currentId)
    prevChapterContent.value = newIdx > 0 ? loadedChapters.value[newIdx - 1] : null
    nextChapterContent.value = newIdx >= 0 && newIdx + 1 < loadedChapters.value.length
      ? loadedChapters.value[newIdx + 1]
      : null

    if (removedBeforeHeight > 0 && container) {
      await nextTick()
      await nextTick() // 双重 nextTick 确保 DOM 完全更新
      const newScroll = Math.max(0, beforeScroll - removedBeforeHeight)
      container.scrollTop = newScroll
    }
  }

  // 预取相邻章节
  async function prefetchAdjacentChapters(contentRef, isScrollMode) {
    if (!isScrollMode?.value || !currentChapter.value) return
    const container = contentRef?.value
    const prevId = currentChapter.value.prev_id
    const nextId = currentChapter.value.next_id

    if (prevId && !findInLoaded(prevId) && !prevChapterContent.value) {
      // 移动端和桌面端都使用容器滚动
      const beforeHeight = container?.scrollHeight || 0
      const beforeScroll = container?.scrollTop || 0
      
      const prevData = await fetchChapterById(prevId)
      if (prevData) {
        prevChapterContent.value = prevData
        addLoadedChapter(prevData, 'start')
        
        // 等待 DOM 更新
        await nextTick()
        await nextTick() // 双重 nextTick 确保 DOM 完全渲染
        
        const afterHeight = container?.scrollHeight || beforeHeight
        const diff = afterHeight - beforeHeight
        
        if (diff > 0 && container) {
          container.scrollTop = beforeScroll + diff
        }
      }
    } else if (!prevId) {
      prevChapterContent.value = null
    }

    if (nextId && !findInLoaded(nextId) && !nextChapterContent.value) {
      const nextData = await fetchChapterById(nextId)
      if (nextData) {
        nextChapterContent.value = nextData
        addLoadedChapter(nextData, 'end')
      }
    } else if (!nextId) {
      nextChapterContent.value = null
    }
  }

  // 激活指定章节
  async function activateChapter(targetId, opts = {}) {
    const targetData = findChapterDataById(targetId) || await fetchChapterById(targetId)
    if (!targetData || !readerStore) return

    // 移动缓存
    if (nextChapterContent.value?.id === targetId) {
      prevChapterContent.value = chapterContent.value
      nextChapterContent.value = null
    } else if (prevChapterContent.value?.id === targetId) {
      nextChapterContent.value = chapterContent.value
      prevChapterContent.value = null
    } else {
      prevChapterContent.value = null
      nextChapterContent.value = null
    }

    addLoadedChapter(targetData)
    readerStore.chapterContent = targetData
    readerStore.currentChapterId = targetData.id
    readerStore.currentChapter = {
      id: targetData.id,
      title: targetData.title,
      index: targetData.index,
      prev_id: targetData.prev_id,
      next_id: targetData.next_id
    }

    return { targetData, scrollIntoView: opts.scroll !== false }
  }

  // 清空已加载章节
  function clearLoadedChapters() {
    loadedChapters.value = []
  }

  // 初始化当前章节到已加载列表
  function initCurrentChapter() {
    loadedChapters.value = []
    if (chapterContent.value?.content_html || chapterContent.value?.content_text) {
      loadedChapters.value.push(chapterContent.value)
    }
  }

  return {
    // 状态
    prevChapterContent,
    nextChapterContent,
    loadedChapters,
    chapterRefs,
    autoLoadingNext,
    autoLoadingPrev,

    // 计算属性
    chapterContent,
    currentChapter,
    toc,
    isLoadingChapter,
    isFetching,
    hasContent,
    textParagraphs,
    displayChapters,

    // 方法
    buildParagraphs,
    findInLoaded,
    findChapterDataById,
    fetchChapterById,
    registerChapterRef,
    resetAdjacentCaches,
    addLoadedChapter,
    pruneLoadedAroundCurrent,
    prefetchAdjacentChapters,
    activateChapter,
    clearLoadedChapters,
    initCurrentChapter
  }
}
