/**
 * 翻页模式 composable
 * 负责分页计算、多章节管理
 * 
 * 重构后的精简版本，配合 ReaderPageContent.vue 使用
 * - 移除 Flicking 依赖相关代码
 * - 简化接口，由组件自己管理页面跳转
 * - 保留核心分页算法和章节边界管理
 */
import { ref, computed, nextTick } from 'vue'

/**
 * @typedef {Object} ChapterData
 * @property {string} id - 章节ID
 * @property {string} title - 章节标题
 * @property {number} [index] - 章节序号
 * @property {string} content_text - 章节内容
 * @property {string} [prev_id] - 上一章ID
 * @property {string} [next_id] - 下一章ID
 */

/**
 * @typedef {Object} ChapterBoundary
 * @property {number} startPage - 起始页索引
 * @property {number} endPage - 结束页索引
 * @property {string} title - 章节标题
 * @property {number} [index] - 章节序号
 * @property {string} [prev_id] - 上一章ID
 * @property {string} [next_id] - 下一章ID
 */

/**
 * @typedef {Object} PaginationResult
 * @property {Array<Array<Object>>} pages - 分页后的段落数组
 * @property {number} targetIndex - 目标页索引
 * @property {Object<string, ChapterBoundary>} boundaries - 章节边界映射
 */

export function useReaderPage(options = {}) {
  const { readerSettings, textColor } = options

  // ============ 核心状态 ============
  /** @type {import('vue').Ref<Array<Array<Object>>>} 分页后的段落数组 */
  const pageChunks = ref([])
  /** @type {import('vue').Ref<number>} 当前页索引 */
  const currentPageIndex = ref(0)
  /** @type {import('vue').Ref<Object<string, ChapterBoundary>>} 章节边界映射 */
  const chapterBoundaries = ref({})
  /** @type {import('vue').Ref<string|null>} 当前活跃章节ID */
  const activeChapterId = ref(null)
  /** @type {import('vue').Ref<string[]>} 已加载的章节ID列表（有序） */
  const loadedChapterIds = ref([])

  // 内部状态
  let suppressSave = false

  // ============ 计算属性 ============
  const totalPages = computed(() => pageChunks.value.length)
  
  const currentChapterBoundary = computed(() => {
    if (!activeChapterId.value) return null
    return chapterBoundaries.value[activeChapterId.value] || null
  })

  // ============ 工具函数 ============

  /**
   * 判断章节标题是否已包含"第X章"前缀
   */
  function hasNumberPrefix(title = '') {
    return /^第\s*[0-9一二三四五六七八九十百千万零〇两]+\s*(章|节|回|话|卷)/i.test(title.trim())
  }

  /**
   * 格式化章节标题
   */
  function formatChapterTitle(chapter) {
    if (!chapter) return null
    const title = (chapter.title || '').trim()
    if (!title) return null
    if (hasNumberPrefix(title)) return title
    if (chapter.index !== undefined) {
      return `第 ${chapter.index} 章 · ${title}`
    }
    return title
  }

  /**
   * 构建章节段落数据
   */
  function buildChapterParagraphs(chapterData) {
    if (!chapterData?.content_text) return []
    
    return chapterData.content_text
      .split(/\n+/)
      .map(t => t.trim())
      .filter(t => t.length > 0)
      .map(t => ({ text: t, isTitle: false, chapterId: chapterData.id }))
  }

  /**
   * 获取内容区域尺寸
   */
  function getContentDimensions() {
    const isMobile = window.innerWidth < 768
    const panelBody = document.querySelector('.page-panel-body')
    
    if (panelBody) {
      const style = getComputedStyle(panelBody)
      const rect = panelBody.getBoundingClientRect()
      const paddingX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight)
      const paddingY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom)
      
      return {
        width: Math.max(200, rect.width - paddingX),
        height: Math.max(200, rect.height - paddingY)
      }
    }
    
    // 回退方案
    const width = window.innerWidth
    const height = window.innerHeight
    const hPadding = isMobile ? 32 : 144
    const vPadding = isMobile ? 88 : 80
    
    let availableWidth = Math.max(200, width - hPadding)
    if (!isMobile) {
      availableWidth = Math.min(availableWidth, 820 - 32)
    }
    
    return {
      width: availableWidth,
      height: Math.max(200, height - vPadding)
    }
  }

  /**
   * 创建测量容器
   * 尽可能从实际页面元素获取样式，确保测量准确
   */
  function createMeasureContainer(contentWidth) {
    const container = document.createElement('div')
    
    // 尝试从实际的 .page-text 元素获取计算后的样式
    const pageText = document.querySelector('.page-text')
    if (pageText) {
      const computedStyle = getComputedStyle(pageText)
      Object.assign(container.style, {
        position: 'fixed',
        visibility: 'hidden',
        pointerEvents: 'none',
        left: '-9999px',
        top: '-9999px',
        width: `${contentWidth}px`,
        fontSize: computedStyle.fontSize,
        fontWeight: computedStyle.fontWeight,
        lineHeight: computedStyle.lineHeight,
        fontFamily: computedStyle.fontFamily,
        color: computedStyle.color,
        boxSizing: 'border-box',
        wordBreak: computedStyle.wordBreak || 'break-word',
        overflowWrap: computedStyle.overflowWrap || 'break-word',
        whiteSpace: computedStyle.whiteSpace || 'pre-wrap'
      })
    } else {
      // 回退方案：使用设置中的值
      const fontSize = readerSettings?.value?.fontSize || 18
      const fontWeight = readerSettings?.value?.fontWeight || 400
      const lineHeight = readerSettings?.value?.lineHeight || 1.8
      const fontFamily = readerSettings?.value?.fontFamily || 'serif'
      const color = textColor?.value || '#333'

      Object.assign(container.style, {
        position: 'fixed',
        visibility: 'hidden',
        pointerEvents: 'none',
        left: '-9999px',
        top: '-9999px',
        width: `${contentWidth}px`,
        fontSize: `${fontSize}px`,
        fontWeight: String(fontWeight),
        lineHeight: String(lineHeight),
        fontFamily,
        color,
        boxSizing: 'border-box',
        wordBreak: 'break-word',
        overflowWrap: 'break-word',
        whiteSpace: 'pre-wrap'
      })
    }
    
    document.body.appendChild(container)
    return container
  }

  /**
   * 创建段落元素用于测量
   */
  function createParagraphElement(item, paragraphSpacing, titleSpacing, isLast = false) {
    const p = document.createElement('p')
    const bottomMargin = isLast ? 0 : (item.isTitle ? titleSpacing : paragraphSpacing)
    const shouldIndent = readerSettings?.value?.firstLineIndent !== false && !item.isContinuation
    
    Object.assign(p.style, {
      margin: `0 0 ${bottomMargin}px 0`,
      textIndent: item.isTitle ? '0' : (shouldIndent ? '2em' : '0'),
      fontWeight: item.isTitle ? 'bold' : 'normal',
      textAlign: item.isTitle ? 'center' : 'left',
      fontSize: item.isTitle ? '1.1em' : 'inherit'
    })
    
    p.textContent = item.text || '　'
    return p
  }

  // ============ 分页算法 ============

  /**
   * 多章节分页
   * @param {ChapterData[]} chapters - 章节数据数组
   * @param {string} currentChapterId - 当前章节ID
   * @param {number} targetPercent - 目标进度百分比
   * @returns {PaginationResult}
   */
  function paginateMultipleChapters(chapters, currentChapterId, targetPercent = 0) {
    if (!chapters?.length) {
      resetState()
      return { pages: [], targetIndex: 0, boundaries: {} }
    }

    const { width, height } = getContentDimensions()
    const container = createMeasureContainer(width)
    
    const paragraphSpacing = readerSettings?.value?.paragraphSpacing || 12
    const fontSize = readerSettings?.value?.fontSize || 18
    const titleSpacing = Math.round(fontSize * 1.1 * 1.5)

    const allPages = []
    const boundaries = {}
    const chapterIds = []
    let targetIndex = 0

    // 测量辅助函数
    const measureHeight = (pageEl) => {
      const children = pageEl.children
      if (!children.length) return 0
      const last = children[children.length - 1]
      const saved = last.style.marginBottom
      last.style.marginBottom = '0'
      const h = pageEl.getBoundingClientRect().height
      last.style.marginBottom = saved
      return h
    }

    const tryFit = (pageEl, text, item, isContinuation) => {
      const p = createParagraphElement({ ...item, text, isContinuation }, paragraphSpacing, titleSpacing, true)
      pageEl.appendChild(p)
      const measuredH = measureHeight(pageEl)
      const fits = measuredH <= height
      pageEl.removeChild(p)
      return fits
    }

    const findMaxFit = (pageEl, text, item, isContinuation) => {
      let low = 1, high = text.length, best = 0
      
      while (low <= high) {
        const mid = Math.floor((low + high) / 2)
        if (tryFit(pageEl, text.slice(0, mid), item, isContinuation)) {
          best = mid
          low = mid + 1
        } else {
          high = mid - 1
        }
      }
      
      // 返回实际结果，不再强制返回 1
      // 调用方需要处理 best=0 的情况（当前页已满，需要换页）
      return best
    }

    // 遍历章节
    for (const chapter of chapters) {
      if (!chapter?.id) continue
      
      chapterIds.push(chapter.id)
      const startPage = allPages.length
      
      // 构建段落
      let paragraphs = buildChapterParagraphs(chapter)
      const titleText = formatChapterTitle(chapter)
      if (titleText) {
        paragraphs = [{ text: titleText, isTitle: true, chapterId: chapter.id }, ...paragraphs]
      }

      if (!paragraphs.length) {
        allPages.push([{ text: '（本章内容为空）', isTitle: false, chapterId: chapter.id }])
        boundaries[chapter.id] = {
          startPage,
          endPage: startPage,
          title: chapter.title,
          index: chapter.index,
          prev_id: chapter.prev_id,
          next_id: chapter.next_id
        }
        continue
      }

      // 分页处理
      container.innerHTML = ''
      const pageEl = document.createElement('div')
      pageEl.style.width = '100%'
      container.appendChild(pageEl)
      
      let currentPageItems = []

      const finishPage = () => {
        if (currentPageItems.length) {
          allPages.push(currentPageItems.map(p => ({ ...p, chapterId: chapter.id })))
          currentPageItems = []
        }
        container.innerHTML = ''
        const newPage = document.createElement('div')
        newPage.style.width = '100%'
        container.appendChild(newPage)
        return newPage
      }

      let activePageEl = pageEl

      for (const para of paragraphs) {
        let remainingText = para.text
        let isContinuation = false

        while (remainingText) {
          // 尝试放入整段
          const testP = createParagraphElement({ ...para, text: remainingText, isContinuation }, paragraphSpacing, titleSpacing, true)
          activePageEl.appendChild(testP)
          
          if (measureHeight(activePageEl) <= height) {
            const spacing = para.isTitle ? titleSpacing : paragraphSpacing
            testP.style.marginBottom = `${spacing}px`
            currentPageItems.push({ ...para, text: remainingText, isContinuation })
            break
          }
          
          activePageEl.removeChild(testP)

          // 需要分割
          const maxChars = findMaxFit(activePageEl, remainingText, para, isContinuation)
          
          // 当前页放不下任何字符
          if (maxChars === 0) {
            if (currentPageItems.length) {
              // 当前页有内容，换页后重试
              activePageEl = finishPage()
              continue
            } else {
              // 空页也放不下，强制放 1 个字符避免死循环
              // 这是边缘情况：可能是字体太大或页面太小
              console.warn('[Pagination] 空页无法容纳任何字符，强制放置 1 个字符')
              const forceHead = remainingText.slice(0, 1)
              remainingText = remainingText.slice(1)
              const forceP = createParagraphElement({ ...para, text: forceHead, isContinuation }, paragraphSpacing, titleSpacing, true)
              activePageEl.appendChild(forceP)
              currentPageItems.push({ ...para, text: forceHead, isContinuation })
              
              if (remainingText) {
                activePageEl = finishPage()
                isContinuation = true
              }
              continue
            }
          }

          const head = remainingText.slice(0, maxChars)
          remainingText = remainingText.slice(maxChars)
          
          if (head) {
            const headP = createParagraphElement({ ...para, text: head, isContinuation }, paragraphSpacing, titleSpacing, true)
            activePageEl.appendChild(headP)
            currentPageItems.push({ ...para, text: head, isContinuation })
          }
          
          if (remainingText) {
            activePageEl = finishPage()
            isContinuation = true
          }
        }
      }

      if (currentPageItems.length) {
        allPages.push(currentPageItems.map(p => ({ ...p, chapterId: chapter.id })))
      }

      const endPage = allPages.length - 1

      boundaries[chapter.id] = {
        startPage,
        endPage,
        title: chapter.title,
        index: chapter.index,
        prev_id: chapter.prev_id,
        next_id: chapter.next_id
      }

      if (chapter.id === currentChapterId) {
        const pageCount = endPage - startPage + 1
        const relativeIndex = pageCount > 1
          ? Math.min(pageCount - 1, Math.round((targetPercent / 100) * (pageCount - 1)))
          : 0
        targetIndex = startPage + relativeIndex
      }
    }

    container.remove()

    // 更新状态
    suppressSave = true
    pageChunks.value = allPages
    chapterBoundaries.value = boundaries
    loadedChapterIds.value = chapterIds
    currentPageIndex.value = targetIndex
    activeChapterId.value = currentChapterId || chapterIds[0] || null

    nextTick(() => {
      suppressSave = false
    })

    return { pages: allPages, targetIndex, boundaries }
  }

  /**
   * 重置状态
   */
  function resetState() {
    pageChunks.value = []
    chapterBoundaries.value = {}
    loadedChapterIds.value = []
    currentPageIndex.value = 0
    activeChapterId.value = null
  }

  // ============ 章节导航 ============

  /**
   * 根据页索引获取章节ID
   */
  function getChapterIdByPageIndex(pageIndex) {
    for (const [id, boundary] of Object.entries(chapterBoundaries.value)) {
      if (pageIndex >= boundary.startPage && pageIndex <= boundary.endPage) {
        return id
      }
    }
    return null
  }

  /**
   * 获取章节边界信息
   */
  function getChapterBoundary(chapterId) {
    return chapterBoundaries.value[chapterId] || null
  }

  /**
   * 计算章节内进度百分比
   */
  function calculateChapterProgress(chapterId = null) {
    const targetId = chapterId || activeChapterId.value
    if (!targetId) return 0
    
    const boundary = chapterBoundaries.value[targetId]
    if (!boundary) return 0
    
    const pageCount = boundary.endPage - boundary.startPage + 1
    if (pageCount <= 1) return 100
    
    const relativeIndex = currentPageIndex.value - boundary.startPage
    return Number(((relativeIndex / (pageCount - 1)) * 100).toFixed(2))
  }

  /**
   * 获取章节内页码的跳转目标索引
   */
  function getChapterPageIndex(chapterId, percent = 0) {
    const boundary = chapterBoundaries.value[chapterId]
    if (!boundary) return null
    
    const pageCount = boundary.endPage - boundary.startPage + 1
    const relativeIndex = pageCount > 1
      ? Math.min(pageCount - 1, Math.round((percent / 100) * (pageCount - 1)))
      : 0
    
    return boundary.startPage + relativeIndex
  }

  /**
   * 获取当前章节内的相对位置
   */
  function getChapterRelativePosition(chapterId = null) {
    const targetId = chapterId || activeChapterId.value
    if (!targetId) return null
    
    const boundary = chapterBoundaries.value[targetId]
    if (!boundary) return null
    
    const pageCount = boundary.endPage - boundary.startPage + 1
    const relativeIndex = currentPageIndex.value - boundary.startPage
    
    return {
      relativeIndex: Math.max(0, Math.min(relativeIndex, pageCount - 1)),
      totalPages: pageCount,
      atStart: relativeIndex <= 0,
      atEnd: relativeIndex >= pageCount - 1
    }
  }

  /**
   * 检查是否需要加载更多章节
   */
  function checkNeedMoreChapters() {
    if (!loadedChapterIds.value.length || !activeChapterId.value) {
      return { needPrev: false, needNext: false }
    }
    
    const idx = loadedChapterIds.value.indexOf(activeChapterId.value)
    const boundary = chapterBoundaries.value[activeChapterId.value]
    
    if (!boundary) return { needPrev: false, needNext: false }
    
    return {
      needPrev: idx <= 1 && boundary.prev_id && !loadedChapterIds.value.includes(boundary.prev_id),
      needNext: idx >= loadedChapterIds.value.length - 2 && boundary.next_id && !loadedChapterIds.value.includes(boundary.next_id)
    }
  }

  // ============ 事件处理 ============

  /**
   * 处理页面变化事件（由 ReaderPageContent 触发）
   */
  function handlePageChanged(event) {
    currentPageIndex.value = event.index
    
    const newChapterId = getChapterIdByPageIndex(event.index)
    const chapterChanged = newChapterId && newChapterId !== activeChapterId.value
    
    if (chapterChanged) {
      activeChapterId.value = newChapterId
    }
    
    return {
      pageIndex: event.index,
      chapterId: newChapterId,
      chapterChanged,
      progress: calculateChapterProgress(newChapterId)
    }
  }

  // ============ 状态控制 ============

  function setSuppressSave(value) {
    suppressSave = value
  }

  function isSuppressSave() {
    return suppressSave
  }

  // ============ 导出 ============
  return {
    // 状态
    pageChunks,
    currentPageIndex,
    chapterBoundaries,
    activeChapterId,
    loadedChapterIds,
    
    // 计算属性
    totalPages,
    currentChapterBoundary,
    
    // 分页方法
    paginateMultipleChapters,
    resetState,
    formatChapterTitle,
    
    // 章节导航
    getChapterIdByPageIndex,
    getChapterBoundary,
    getChapterPageIndex,
    getChapterRelativePosition,
    calculateChapterProgress,
    checkNeedMoreChapters,
    
    // 事件处理
    handlePageChanged,
    
    // 状态控制
    setSuppressSave,
    isSuppressSave
  }
}
