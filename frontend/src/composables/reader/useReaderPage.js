/**
 * 翻页模式 composable
 * 负责分页计算、Flicking控制等
 * 
 * 支持多章节无缝滑动：将多个章节内容合并分页，记录章节边界
 */
import { ref, nextTick } from 'vue'

export function useReaderPage(options = {}) {
  const { readerSettings, textColor, chapterContent, textParagraphs, chapterIndex, chapterTitle } = options

  const pageContainerRef = ref(null)
  const flickingRef = ref(null)
  const pageChunks = ref([])
  const currentPageIndex = ref(0)
  const containerWidth = ref(0)
  const containerHeight = ref(0)
  
  // 多章节支持：章节边界映射 { chapterId: { startPage, endPage, title, index, prev_id, next_id } }
  const chapterBoundaries = ref({})
  // 当前活跃章节ID（基于页面位置）
  const activeChapterId = ref(null)
  // 已加载的章节列表（有序）
  const loadedChapterIds = ref([])
  
  let suppressSave = false

  function updateDimensions(width, height) {
    containerWidth.value = width
    containerHeight.value = height
  }

  // 判断章节标题是否已包含类似“第X章/节/回”的前缀，避免重复拼接
  function hasNumberPrefix(title = '') {
    return /^第\s*[0-9一二三四五六七八九十百千万零〇两]+\s*(章|节|回|话|卷)/i.test(title.trim())
  }

  /**
   * 格式化章节标题，统一为 "第 X 章 · 标题" 格式
   */
  function formatChapterTitle(chapter) {
    if (!chapter) return null
    const title = (chapter.title || '').trim()
    if (!title) return null
    if (hasNumberPrefix(title)) return title
    if (chapter.index !== undefined) {
      return `第 ${chapter.index} 章 · ${title}`
    }
    if (title) return title
    return null
  }

  /**
   * 计算单个章节的段落数据
   */
  function buildChapterParagraphs(chapterData) {
    if (!chapterData) return []
    
    const raw = chapterData.content_text || ''
    if (!raw) return []
    
    return raw
      .split(/\n+/)
      .filter(Boolean)
      .map(t => ({ text: t, isTitle: false, chapterId: chapterData.id }))
  }

  /**
   * 多章节分页
   * @param {Array} chapters - 章节数据数组 [{ id, title, index, content_text, prev_id, next_id }, ...]
   * @param {string} currentChapterId - 当前阅读的章节ID
   * @param {number} targetPercent - 目标进度百分比（相对于当前章节）
   */
  function paginateMultipleChapters(chapters, currentChapterId, targetPercent = 0) {
    if (!chapters || !chapters.length) {
      pageChunks.value = []
      chapterBoundaries.value = {}
      loadedChapterIds.value = []
      currentPageIndex.value = 0
      activeChapterId.value = null
      return { pages: [], targetIndex: 0, boundaries: {} }
    }

    // 计算布局尺寸
    const width = containerWidth.value || window.innerWidth
    const height = containerHeight.value || window.innerHeight
    const isMobile = window.innerWidth < 768
    const vPadding = isMobile ? 110 : 100
    const hPadding = isMobile ? 50 : 140
    const availableHeight = Math.max(200, height - vPadding)
    const availableWidth = Math.max(200, width - hPadding)

    // 创建临时测量容器
    const temp = document.createElement('div')
    temp.style.position = 'fixed'
    temp.style.visibility = 'hidden'
    temp.style.pointerEvents = 'none'
    temp.style.left = '-9999px'
    temp.style.top = '-9999px'
    temp.style.width = `${availableWidth}px`
    temp.style.fontSize = `${readerSettings?.value?.fontSize || 18}px`
    temp.style.lineHeight = String(readerSettings?.value?.lineHeight || 1.8)
    temp.style.color = textColor?.value || '#333'
    temp.style.boxSizing = 'border-box'
    document.body.appendChild(temp)

    const createPage = () => {
      const page = document.createElement('div')
      page.style.width = '100%'
      page.style.boxSizing = 'border-box'
      return page
    }

    const createParagraphEl = (item) => {
      const p = document.createElement('p')
      p.style.margin = `0 0 ${readerSettings?.value?.paragraphSpacing || 12}px 0`
      if (item.isTitle) {
        p.style.textIndent = '0'
        p.style.fontWeight = 'bold'
        p.style.textAlign = 'center'
        p.style.marginBottom = '1.5em'
      } else {
        p.style.textIndent = readerSettings?.value?.firstLineIndent === false ? '0' : '2em'
      }
      p.textContent = item.text || '　'
      return p
    }

    const allPages = []
    const boundaries = {}
    const chapterIds = []
    let currentChapterStartPage = 0
    let targetIndex = 0

    // 遍历每个章节进行分页
    chapters.forEach((chapter) => {
      if (!chapter?.id) return
      
      chapterIds.push(chapter.id)
      const startPageIndex = allPages.length
      
      // 构建章节段落，首行插入标题
      let paragraphs = buildChapterParagraphs(chapter)
      const titleText = formatChapterTitle(chapter)
      if (titleText) {
        paragraphs = [{ text: titleText, isTitle: true, chapterId: chapter.id }, ...paragraphs]
      }

      if (!paragraphs.length) {
        // 空章节，至少添加一个空页
        allPages.push([{ text: '（本章内容为空）', isTitle: false, chapterId: chapter.id }])
        boundaries[chapter.id] = {
          startPage: startPageIndex,
          endPage: startPageIndex,
          title: chapter.title,
          index: chapter.index,
          prev_id: chapter.prev_id,
          next_id: chapter.next_id
        }
        return
      }

      // 分页逻辑
      let pageEl = createPage()
      temp.innerHTML = ''
      temp.appendChild(pageEl)
      let currentPageParas = []

      paragraphs.forEach((item) => {
        const paraEl = createParagraphEl(item)
        pageEl.appendChild(paraEl)
        
        if (pageEl.offsetHeight > availableHeight && pageEl.childElementCount > 1) {
          pageEl.removeChild(paraEl)
          // 为页面数据添加章节信息
          allPages.push(currentPageParas.map(p => ({ ...p, chapterId: chapter.id })))
          
          temp.innerHTML = ''
          pageEl = createPage()
          temp.appendChild(pageEl)
          pageEl.appendChild(paraEl)
          currentPageParas = [item]
        } else {
          currentPageParas.push(item)
        }
      })

      if (currentPageParas.length) {
        allPages.push(currentPageParas.map(p => ({ ...p, chapterId: chapter.id })))
      }

      const endPageIndex = allPages.length - 1

      // 记录章节边界
      boundaries[chapter.id] = {
        startPage: startPageIndex,
        endPage: endPageIndex,
        title: chapter.title,
        index: chapter.index,
        prev_id: chapter.prev_id,
        next_id: chapter.next_id
      }

      // 如果是当前章节，计算目标页索引
      if (chapter.id === currentChapterId) {
        currentChapterStartPage = startPageIndex
        const chapterPageCount = endPageIndex - startPageIndex + 1
        const relativePageIndex = chapterPageCount > 1
          ? Math.min(chapterPageCount - 1, Math.round((targetPercent / 100) * (chapterPageCount - 1)))
          : 0
        targetIndex = startPageIndex + relativePageIndex
      }
    })

    temp.remove()

    // 如果没有找到当前章节，默认定位到第一页
    if (!boundaries[currentChapterId]) {
      targetIndex = 0
    }

    // 更新状态
    suppressSave = true
    pageChunks.value = allPages
    chapterBoundaries.value = boundaries
    loadedChapterIds.value = chapterIds
    currentPageIndex.value = targetIndex
    activeChapterId.value = currentChapterId

    nextTick(() => {
      flickingRef.value?.moveTo(targetIndex, 0)
      suppressSave = false
    })

    return { pages: allPages, targetIndex, boundaries }
  }

  /**
   * 单章节分页（向后兼容）
   */
  function paginateText(targetPercent = null, chapterTitleText = null) {
    let paragraphs = textParagraphs?.value?.length
      ? textParagraphs.value.map(p => ({ text: p.text || '　', isTitle: false }))
      : (chapterContent?.value?.content_text || '').split(/\n+/).filter(Boolean).map(t => ({ text: t, isTitle: false }))

    if (!paragraphs.length) {
      pageChunks.value = []
      currentPageIndex.value = 0
      return
    }

    // 在正文前插入章节标题
    if (chapterTitleText) {
      paragraphs = [{ text: chapterTitleText, isTitle: true }, ...paragraphs]
    }

    const width = containerWidth.value || window.innerWidth
    const height = containerHeight.value || window.innerHeight
    const isMobile = window.innerWidth < 768
    const vPadding = isMobile ? 110 : 100
    const hPadding = isMobile ? 50 : 140
    const availableHeight = Math.max(200, height - vPadding)
    const availableWidth = Math.max(200, width - hPadding)

    const temp = document.createElement('div')
    temp.style.position = 'fixed'
    temp.style.visibility = 'hidden'
    temp.style.pointerEvents = 'none'
    temp.style.left = '-9999px'
    temp.style.top = '-9999px'
    temp.style.width = `${availableWidth}px`
    temp.style.fontSize = `${readerSettings?.value?.fontSize || 18}px`
    temp.style.lineHeight = String(readerSettings?.value?.lineHeight || 1.8)
    temp.style.color = textColor?.value || '#333'
    temp.style.boxSizing = 'border-box'
    document.body.appendChild(temp)

    const createPage = () => {
      const page = document.createElement('div')
      page.style.width = '100%'
      page.style.boxSizing = 'border-box'
      return page
    }

    const createParagraphEl = (item) => {
      const p = document.createElement('p')
      p.style.margin = `0 0 ${readerSettings?.value?.paragraphSpacing || 12}px 0`
      if (item.isTitle) {
        p.style.textIndent = '0'
        p.style.fontWeight = 'bold'
        p.style.textAlign = 'center'
        p.style.marginBottom = '1.5em'
      } else {
        p.style.textIndent = readerSettings?.value?.firstLineIndent === false ? '0' : '2em'
      }
      p.textContent = item.text || '　'
      return p
    }

    let pageEl = createPage()
    temp.appendChild(pageEl)
    const pages = []
    let currentPageParas = []

    paragraphs.forEach((item) => {
      const paraEl = createParagraphEl(item)
      pageEl.appendChild(paraEl)
      if (pageEl.offsetHeight > availableHeight && pageEl.childElementCount > 1) {
        pageEl.removeChild(paraEl)
        pages.push(currentPageParas.slice())
        temp.innerHTML = ''
        pageEl = createPage()
        temp.appendChild(pageEl)
        pageEl.appendChild(paraEl)
        currentPageParas = [item]
      } else {
        currentPageParas.push(item)
      }
    })

    if (currentPageParas.length) {
      pages.push(currentPageParas.slice())
    }

    temp.remove()

    if (!pages.length && paragraphs.length) {
      pages.push(paragraphs.slice())
    }

    const savedPercent = Number.isFinite(targetPercent)
      ? targetPercent
      : (typeof chapterContent?.value?.percent === 'number' ? chapterContent.value.percent : 0)
    const targetIndex = pages.length > 1
      ? Math.min(pages.length - 1, Math.round((savedPercent / 100) * (pages.length - 1)))
      : 0

    suppressSave = true
    pageChunks.value = pages
    currentPageIndex.value = targetIndex

    nextTick(() => {
      flickingRef.value?.moveTo(targetIndex, 0)
      suppressSave = false
    })

    return { pages, targetIndex }
  }

  /**
   * 根据页面索引获取所属章节ID
   */
  function getChapterIdByPageIndex(pageIndex) {
    for (const [chapterId, boundary] of Object.entries(chapterBoundaries.value)) {
      if (pageIndex >= boundary.startPage && pageIndex <= boundary.endPage) {
        return chapterId
      }
    }
    return null
  }

  /**
   * 获取章节信息
   */
  function getChapterBoundary(chapterId) {
    return chapterBoundaries.value[chapterId] || null
  }

  /**
   * 计算当前章节内的进度百分比
   */
  function calculateChapterProgress(chapterId = null) {
    const targetChapterId = chapterId || activeChapterId.value
    if (!targetChapterId) return 0
    
    const boundary = chapterBoundaries.value[targetChapterId]
    if (!boundary) return 0
    
    const chapterPageCount = boundary.endPage - boundary.startPage + 1
    if (chapterPageCount <= 1) return 100
    
    const relativePageIndex = currentPageIndex.value - boundary.startPage
    return Number(((relativePageIndex / (chapterPageCount - 1)) * 100).toFixed(2))
  }

  /**
   * 跳转到指定章节
   */
  async function moveToChapter(chapterId, percent = 0) {
    const boundary = chapterBoundaries.value[chapterId]
    if (!boundary) return false
    
    const chapterPageCount = boundary.endPage - boundary.startPage + 1
    const relativePageIndex = chapterPageCount > 1
      ? Math.min(chapterPageCount - 1, Math.round((percent / 100) * (chapterPageCount - 1)))
      : 0
    const targetIndex = boundary.startPage + relativePageIndex
    
    suppressSave = true
    currentPageIndex.value = targetIndex
    activeChapterId.value = chapterId
    await nextTick()
    await flickingRef.value?.moveTo(targetIndex, 200)
    suppressSave = false
    
    return true
  }

  // 根据进度跳转页面（相对于当前章节）
  async function moveToPageByPercent(value) {
    if (!pageChunks.value.length) return
    
    // 如果有章节边界信息，在当前章节内跳转
    if (activeChapterId.value && chapterBoundaries.value[activeChapterId.value]) {
      return moveToChapter(activeChapterId.value, value)
    }
    
    // 向后兼容：全局跳转
    const target = Math.round((value / 100) * Math.max(pageChunks.value.length - 1, 0))
    suppressSave = true
    currentPageIndex.value = target
    await nextTick()
    await flickingRef.value?.moveTo(target, 200)
    suppressSave = false
    return target
  }

  // 处理页面变化
  function handlePageChanged(event) {
    currentPageIndex.value = event.index
    
    // 更新当前活跃章节
    const newChapterId = getChapterIdByPageIndex(event.index)
    if (newChapterId && newChapterId !== activeChapterId.value) {
      activeChapterId.value = newChapterId
    }
    
    return {
      pageIndex: event.index,
      chapterId: newChapterId,
      chapterChanged: newChapterId !== activeChapterId.value
    }
  }

  // 计算页面进度（全局）
  function calculatePageProgress() {
    if (!pageChunks.value.length) return 0
    if (pageChunks.value.length === 1) return 100
    return Number(
      ((currentPageIndex.value / Math.max(pageChunks.value.length - 1, 1)) * 100).toFixed(2)
    )
  }

  /**
   * 检查是否需要加载更多章节
   * @returns {{ needPrev: boolean, needNext: boolean }}
   */
  function checkNeedMoreChapters() {
    if (!loadedChapterIds.value.length || !activeChapterId.value) {
      return { needPrev: false, needNext: false }
    }
    
    const currentIdx = loadedChapterIds.value.indexOf(activeChapterId.value)
    const boundary = chapterBoundaries.value[activeChapterId.value]
    
    if (!boundary) return { needPrev: false, needNext: false }
    
    // 当前章节在已加载列表中的位置
    // 如果当前章节是第一个且有前一章，可能需要加载前面的章节
    const needPrev = currentIdx <= 1 && boundary.prev_id && !loadedChapterIds.value.includes(boundary.prev_id)
    // 如果当前章节是倒数第二个或最后一个且有下一章，可能需要加载后面的章节
    const needNext = currentIdx >= loadedChapterIds.value.length - 2 && 
                     boundary.next_id && 
                     !loadedChapterIds.value.includes(boundary.next_id)
    
    return { needPrev, needNext }
  }

  // 设置抑制保存状态
  function setSuppressSave(value) {
    suppressSave = value
  }

  function isSuppressSave() {
    return suppressSave
  }

  return {
    pageContainerRef,
    flickingRef,
    pageChunks,
    currentPageIndex,
    
    // 多章节支持
    chapterBoundaries,
    activeChapterId,
    loadedChapterIds,
    
    // 方法
    paginateText,
    paginateMultipleChapters,
    formatChapterTitle,
    getChapterIdByPageIndex,
    getChapterBoundary,
    calculateChapterProgress,
    moveToChapter,
    moveToPageByPercent,
    handlePageChanged,
    calculatePageProgress,
    checkNeedMoreChapters,
    setSuppressSave,
    isSuppressSave,
    updateDimensions
  }
}
