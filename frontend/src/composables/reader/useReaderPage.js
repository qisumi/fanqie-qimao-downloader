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
  let moveQueue = Promise.resolve()

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
      .map(t => t.trim())  // 去除首尾空白
      .filter(t => t.length > 0)  // 过滤空行和纯空白行
      .map(t => ({ text: t, isTitle: false, chapterId: chapterData.id }))
  }

  /**
   * 实际测量一行文字的渲染高度，获得精确的安全边距
   * @param {HTMLElement} measureContainer - 已配置好样式的测量容器
   * @returns {number} 安全边距像素值
   */
  function measureActualLineHeight(measureContainer) {
    const paragraphSpacing = readerSettings?.value?.paragraphSpacing || 12
    
    // 创建测量用的单行文字元素
    const testLine = document.createElement('p')
    testLine.style.margin = '0'
    testLine.style.padding = '0'
    // 使用一个典型的中文字符来测量
    testLine.textContent = '测'
    
    measureContainer.appendChild(testLine)
    const singleLineHeight = testLine.getBoundingClientRect().height
    measureContainer.removeChild(testLine)
    
    // 调试：临时将安全边距设为0
    console.log('[useReaderPage] measureActualLineHeight:', { singleLineHeight, paragraphSpacing })
    return 0
  }

  // 向后兼容：基于公式估算的安全边距（用于无法实际测量时）
  function computeSafetyMarginFallback() {
    const fontSize = readerSettings?.value?.fontSize || 18
    const lineHeight = readerSettings?.value?.lineHeight || 1.8
    const paragraphSpacing = readerSettings?.value?.paragraphSpacing || 12
    const linePixels = fontSize * lineHeight
    const spacingPixels = paragraphSpacing * 0.5
    return Math.max(12, Math.round(linePixels * 0.7 + spacingPixels))
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
    // 垂直 padding 与 CSS 保持精确一致：
    // 移动端: .page-panel padding 8*2=16 + .page-panel-body padding-top 8 + padding-bottom 56 = 80px
    // 桌面端: .page-panel-body padding-top 20 + padding-bottom 12 = 32px
    const vPadding = isMobile ? 80 : 32
    const hPadding = isMobile ? 24 : 80
    const availableWidth = Math.max(200, width - hPadding)

    // 创建临时测量容器，样式需与实际阅读器容器完全一致
    const temp = document.createElement('div')
    temp.style.position = 'fixed'
    temp.style.visibility = 'hidden'
    temp.style.pointerEvents = 'none'
    temp.style.left = '-9999px'
    temp.style.top = '-9999px'
    temp.style.width = `${availableWidth}px`
    temp.style.fontSize = `${readerSettings?.value?.fontSize || 18}px`
    temp.style.lineHeight = String(readerSettings?.value?.lineHeight || 1.8)
    if (readerSettings?.value?.fontFamily) {
      temp.style.fontFamily = readerSettings.value.fontFamily
    }
    temp.style.color = textColor?.value || '#333'
    temp.style.boxSizing = 'border-box'
    // 补充可能影响布局的样式属性
    temp.style.letterSpacing = readerSettings?.value?.letterSpacing || 'normal'
    temp.style.wordBreak = 'break-word'
    temp.style.overflowWrap = 'break-word'
    temp.style.textRendering = 'optimizeLegibility'
    document.body.appendChild(temp)

    // 实际测量一行文字高度，获得精确的安全边距
    const safetyMargin = measureActualLineHeight(temp)
    const availableHeight = Math.max(200, height - vPadding - safetyMargin)

    const createPage = () => {
      const page = document.createElement('div')
      page.style.width = '100%'
      page.style.boxSizing = 'border-box'
      return page
    }

    const paragraphSpacing = readerSettings?.value?.paragraphSpacing || 12
    // 标题底部间距：CSS 中标题字号放大 1.1 倍，margin-bottom 为 1.5em
    // 因此实际间距 = fontSize * 1.1 * 1.5
    const titleBottomSpacing = Math.round((readerSettings?.value?.fontSize || 18) * 1.1 * 1.5)

    const createParagraphEl = (item, isLastInPage = false) => {
      const p = document.createElement('p')
      // 测量时：最后一段不计入底部间距，避免页面留白过多
      const bottomMargin = isLastInPage ? 0 : paragraphSpacing
      p.style.margin = `0 0 ${bottomMargin}px 0`
      if (item.isTitle) {
        p.style.textIndent = '0'
        p.style.fontWeight = 'bold'
        p.style.textAlign = 'center'
        // 标题字号放大 1.1 倍，与 CSS 一致
        p.style.fontSize = '1.1em'
        // 标题底部间距也使用px单位
        p.style.marginBottom = isLastInPage ? '0' : `${titleBottomSpacing}px`
      } else {
        const shouldIndent = readerSettings?.value?.firstLineIndent !== false && !item.isContinuation
        p.style.textIndent = shouldIndent ? '2em' : '0'
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

      const splitAndAppendParagraph = (paragraph) => {
        const withChapter = (payload) => ({ ...payload, chapterId: chapter.id })

        // 获取段落应有的底部边距
        const getBottomMargin = (para) => {
          return para.isTitle ? titleBottomSpacing : paragraphSpacing
        }

        // 测量当前页高度
        // 规则：已有段落保持正常边距，只有最后一段不计入边距
        const measurePageHeight = () => {
          const children = pageEl.children
          if (children.length === 0) return 0
          // 最后一段不计入底部边距
          const lastChild = children[children.length - 1]
          const savedMargin = lastChild.style.marginBottom
          lastChild.style.marginBottom = '0'
          const height = pageEl.getBoundingClientRect().height
          lastChild.style.marginBottom = savedMargin
          return height
        }

        const tryAppend = (textChunk, isContinuation) => {
          // 测量时：新段落作为最后一段，不计入底部边距
          const paraEl = createParagraphEl({ ...paragraph, text: textChunk, isContinuation }, true)
          pageEl.appendChild(paraEl)
          const fits = measurePageHeight() <= availableHeight
          pageEl.removeChild(paraEl)
          return fits
        }

        // 测量文本渲染后的行数
        const measureLineCount = (textChunk, isContinuation) => {
          const paraEl = createParagraphEl({ ...paragraph, text: textChunk, isContinuation }, true)
          pageEl.appendChild(paraEl)
          const lineHeight = parseFloat(temp.style.lineHeight) * parseFloat(temp.style.fontSize)
          const paraHeight = paraEl.getBoundingClientRect().height
          pageEl.removeChild(paraEl)
          return Math.round(paraHeight / lineHeight)
        }

        // 在完整行边界处切割文本
        const findLineBreakPoint = (text, isContinuation, maxChars) => {
          if (maxChars >= text.length) return text.length
          if (maxChars <= 0) return 0
          
          // 获取maxChars字符时的行数
          const linesAtMax = measureLineCount(text.slice(0, maxChars), isContinuation)
          
          // 如果只有1行或更少，直接返回
          if (linesAtMax <= 1) return maxChars
          
          // 二分查找：找到刚好能显示 linesAtMax-1 行的最大字符数
          // 这确保我们在完整行的末尾切割
          let low = 1
          let high = maxChars
          let lastValidBreak = 0
          
          while (low <= high) {
            const mid = Math.floor((low + high) / 2)
            const lines = measureLineCount(text.slice(0, mid), isContinuation)
            
            if (lines < linesAtMax) {
              // 当前字符数产生的行数小于目标，可以尝试更多字符
              lastValidBreak = mid
              low = mid + 1
            } else {
              // 行数已达到或超过目标，需要减少字符
              high = mid - 1
            }
          }
          
          return lastValidBreak > 0 ? lastValidBreak : maxChars
        }

        const findMaxChunkForCurrentPage = (text, isContinuation) => {
          let low = 1
          let high = text.length
          let best = 0
          while (low <= high) {
            const mid = Math.floor((low + high) / 2)
            const chunk = text.slice(0, mid)
            if (tryAppend(chunk, isContinuation)) {
              best = mid
              low = mid + 1
            } else {
              high = mid - 1
            }
          }
          
          if (best <= 0) return ''
          
          // 在行边界处切割，避免切在行中间
          const lineBreakPoint = findLineBreakPoint(text, isContinuation, best)
          return text.slice(0, lineBreakPoint > 0 ? lineBreakPoint : best)
        }

        const appendWithSplit = (text, isContinuation = false) => {
          if (!text) return

          // 尝试完整放入当前页（测量时假设是最后一段，不计入底部边距）
          const paraEl = createParagraphEl({ ...paragraph, text, isContinuation }, true)
          pageEl.appendChild(paraEl)
          if (measurePageHeight() <= availableHeight) {
            // 段落确定保留，更新其底部边距为正常值（为下一段落预留空间）
            paraEl.style.marginBottom = `${getBottomMargin(paragraph)}px`
            currentPageParas.push(withChapter({ ...paragraph, text, isContinuation }))
            return
          }
          pageEl.removeChild(paraEl)

          // 计算当前页还能容纳的最大子串
          let head = findMaxChunkForCurrentPage(text, isContinuation)

          if (!head && currentPageParas.length) {
            // 当前页放不下任何字符，换页前移除最后一段的底部边距
            const lastEl = pageEl.lastElementChild
            if (lastEl) lastEl.style.marginBottom = '0'
            allPages.push(currentPageParas.slice())
            temp.innerHTML = ''
            pageEl = createPage()
            temp.appendChild(pageEl)
            currentPageParas = []
            appendWithSplit(text, isContinuation)
            return
          }

          // 兜底：即便 best 为 0，也强制至少切出1个字符，避免死循环
          if (!head) {
            head = text.slice(0, 1)
          }
          const tail = text.slice(head.length)

          if (head) {
            // 添加分割后的头部，不计入底部边距（因为这是该页最后内容）
            const headEl = createParagraphEl({ ...paragraph, text: head, isContinuation }, true)
            pageEl.appendChild(headEl)
            currentPageParas.push(withChapter({ ...paragraph, text: head, isContinuation }))
          }

          // 换页处理剩余部分
          if (tail.length) {
            allPages.push(currentPageParas.slice())
            temp.innerHTML = ''
            pageEl = createPage()
            temp.appendChild(pageEl)
            currentPageParas = []
            appendWithSplit(tail, true)
          } else if (head) {
            // 没有剩余内容，但可能还有后续段落，添加底部边距
            const lastEl = pageEl.lastElementChild
            if (lastEl) lastEl.style.marginBottom = `${getBottomMargin(paragraph)}px`
          }
        }

        // 跳过空段落（防御性检查，正常情况下不应该有空段落）
        if (paragraph.text && paragraph.text.trim()) {
          appendWithSplit(paragraph.text)
        }
      }

      paragraphs.forEach(splitAndAppendParagraph)

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
      safeMoveTo(targetIndex, 0).finally(() => {
        suppressSave = false
      })
    })

    return { pages: allPages, targetIndex, boundaries }
  }

  /**
   * 单章节分页（向后兼容）
   */
  function paginateText(targetPercent = null, chapterTitleText = null) {
    let paragraphs = textParagraphs?.value?.length
      ? textParagraphs.value
          .map(p => ({ text: (p.text || '').trim(), isTitle: false }))
          .filter(p => p.text.length > 0)
      : (chapterContent?.value?.content_text || '')
          .split(/\n+/)
          .map(t => t.trim())
          .filter(t => t.length > 0)
          .map(t => ({ text: t, isTitle: false }))

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
    // 垂直 padding 与 CSS 保持精确一致：
    // 移动端: .page-panel padding 8*2=16 + .page-panel-body padding-top 8 + padding-bottom 56 = 80px
    // 桌面端: .page-panel-body padding-top 20 + padding-bottom 12 = 32px
    const vPadding = isMobile ? 80 : 32
    const hPadding = isMobile ? 24 : 80
    const availableWidth = Math.max(200, width - hPadding)

    // 创建临时测量容器，样式需与实际阅读器容器完全一致
    const temp = document.createElement('div')
    temp.style.position = 'fixed'
    temp.style.visibility = 'hidden'
    temp.style.pointerEvents = 'none'
    temp.style.left = '-9999px'
    temp.style.top = '-9999px'
    temp.style.width = `${availableWidth}px`
    temp.style.fontSize = `${readerSettings?.value?.fontSize || 18}px`
    temp.style.lineHeight = String(readerSettings?.value?.lineHeight || 1.8)
    if (readerSettings?.value?.fontFamily) {
      temp.style.fontFamily = readerSettings.value.fontFamily
    }
    temp.style.color = textColor?.value || '#333'
    temp.style.boxSizing = 'border-box'
    // 补充可能影响布局的样式属性
    temp.style.letterSpacing = readerSettings?.value?.letterSpacing || 'normal'
    temp.style.wordBreak = 'break-word'
    temp.style.overflowWrap = 'break-word'
    temp.style.textRendering = 'optimizeLegibility'
    document.body.appendChild(temp)

    // 实际测量一行文字高度，获得精确的安全边距
    const safetyMargin = measureActualLineHeight(temp)
    const availableHeight = Math.max(200, height - vPadding - safetyMargin)

    const paragraphSpacingVal = readerSettings?.value?.paragraphSpacing || 12
    // 标题底部间距：CSS 中标题字号放大 1.1 倍，margin-bottom 为 1.5em
    // 因此实际间距 = fontSize * 1.1 * 1.5
    const titleBottomSpacingVal = Math.round((readerSettings?.value?.fontSize || 18) * 1.1 * 1.5)

    const createPage = () => {
      const page = document.createElement('div')
      page.style.width = '100%'
      page.style.boxSizing = 'border-box'
      return page
    }

    const createParagraphEl = (item, isLastInPage = false) => {
      const p = document.createElement('p')
      // 测量时：最后一段不计入底部间距
      const bottomMargin = isLastInPage ? 0 : paragraphSpacingVal
      p.style.margin = `0 0 ${bottomMargin}px 0`
      if (item.isTitle) {
        p.style.textIndent = '0'
        p.style.fontWeight = 'bold'
        p.style.textAlign = 'center'
        // 标题字号放大 1.1 倍，与 CSS 一致
        p.style.fontSize = '1.1em'
        p.style.marginBottom = isLastInPage ? '0' : `${titleBottomSpacingVal}px`
      } else {
        const shouldIndent = readerSettings?.value?.firstLineIndent !== false && !item.isContinuation
        p.style.textIndent = shouldIndent ? '2em' : '0'
      }
      p.textContent = item.text || '　'
      return p
    }

    let pageEl = createPage()
    temp.appendChild(pageEl)
    const pages = []
    let currentPageParas = []

    const splitAndAppendParagraph = (paragraph) => {
      // 获取段落应有的底部边距
      const getBottomMargin = (para) => {
        return para.isTitle ? titleBottomSpacingVal : paragraphSpacingVal
      }

      // 测量当前页高度（不含最后一段的底部间距）
      const measurePageHeight = () => {
        const children = pageEl.children
        if (children.length === 0) return 0
        const lastChild = children[children.length - 1]
        const savedMargin = lastChild.style.marginBottom
        lastChild.style.marginBottom = '0'
        const height = pageEl.getBoundingClientRect().height
        lastChild.style.marginBottom = savedMargin
        return height
      }

      const tryAppend = (textChunk, isContinuation) => {
        // 测量时假设这是页面最后一段
        const paraEl = createParagraphEl({ ...paragraph, text: textChunk, isContinuation }, true)
        pageEl.appendChild(paraEl)
        const fits = measurePageHeight() <= availableHeight
        pageEl.removeChild(paraEl)
        return fits
      }

      // 测量文本渲染后的行数
      const measureLineCount = (textChunk, isContinuation) => {
        const paraEl = createParagraphEl({ ...paragraph, text: textChunk, isContinuation }, true)
        pageEl.appendChild(paraEl)
        const lineHeight = parseFloat(temp.style.lineHeight) * parseFloat(temp.style.fontSize)
        const paraHeight = paraEl.getBoundingClientRect().height
        pageEl.removeChild(paraEl)
        return Math.round(paraHeight / lineHeight)
      }

      // 在完整行边界处切割文本
      const findLineBreakPoint = (text, isContinuation, maxChars) => {
        if (maxChars >= text.length) return text.length
        if (maxChars <= 0) return 0
        
        // 获取maxChars字符时的行数
        const linesAtMax = measureLineCount(text.slice(0, maxChars), isContinuation)
        
        // 如果只有1行或更少，直接返回
        if (linesAtMax <= 1) return maxChars
        
        // 二分查找：找到刚好能显示 linesAtMax-1 行的最大字符数
        // 这确保我们在完整行的末尾切割
        let low = 1
        let high = maxChars
        let lastValidBreak = 0
        
        while (low <= high) {
          const mid = Math.floor((low + high) / 2)
          const lines = measureLineCount(text.slice(0, mid), isContinuation)
          
          if (lines < linesAtMax) {
            // 当前字符数产生的行数小于目标，可以尝试更多字符
            lastValidBreak = mid
            low = mid + 1
          } else {
            // 行数已达到或超过目标，需要减少字符
            high = mid - 1
          }
        }
        
        return lastValidBreak > 0 ? lastValidBreak : maxChars
      }

      const findMaxChunkForCurrentPage = (text, isContinuation) => {
        let low = 1
        let high = text.length
        let best = 0
        while (low <= high) {
          const mid = Math.floor((low + high) / 2)
          const chunk = text.slice(0, mid)
          if (tryAppend(chunk, isContinuation)) {
            best = mid
            low = mid + 1
          } else {
            high = mid - 1
          }
        }
        
        if (best <= 0) return ''
        
        // 在行边界处切割，避免切在行中间
        const lineBreakPoint = findLineBreakPoint(text, isContinuation, best)
        return text.slice(0, lineBreakPoint > 0 ? lineBreakPoint : best)
      }

      const appendWithSplit = (text, isContinuation = false) => {
        if (!text) return
        // 测量时假设是最后一段（不计入底部边距）
        const paraEl = createParagraphEl({ ...paragraph, text, isContinuation }, true)
        pageEl.appendChild(paraEl)
        if (measurePageHeight() <= availableHeight) {
          // 段落确定保留，更新其底部边距为正常值
          paraEl.style.marginBottom = `${getBottomMargin(paragraph)}px`
          currentPageParas.push({ ...paragraph, text, isContinuation })
          return
        }
        pageEl.removeChild(paraEl)

        let head = findMaxChunkForCurrentPage(text, isContinuation)

        if (!head && currentPageParas.length) {
          // 换页前移除最后一段的底部边距
          const lastEl = pageEl.lastElementChild
          if (lastEl) lastEl.style.marginBottom = '0'
          pages.push(currentPageParas.slice())
          temp.innerHTML = ''
          pageEl = createPage()
          temp.appendChild(pageEl)
          currentPageParas = []
          appendWithSplit(text, isContinuation)
          return
        }

        if (!head) {
          head = text.slice(0, 1)
        }
        const tail = text.slice(head.length)

        if (head) {
          // 添加分割后的头部，不计入底部边距
          const headEl = createParagraphEl({ ...paragraph, text: head, isContinuation }, true)
          pageEl.appendChild(headEl)
          currentPageParas.push({ ...paragraph, text: head, isContinuation })
        }

        if (tail.length) {
          pages.push(currentPageParas.slice())
          temp.innerHTML = ''
          pageEl = createPage()
          temp.appendChild(pageEl)
          currentPageParas = []
          appendWithSplit(tail, true)
        } else if (head) {
          // 没有剩余内容，但可能还有后续段落，添加底部边距
          const lastEl = pageEl.lastElementChild
          if (lastEl) lastEl.style.marginBottom = `${getBottomMargin(paragraph)}px`
        }
      }

      // 跳过空段落（防御性检查，正常情况下不应该有空段落）
      if (paragraph.text && paragraph.text.trim()) {
        appendWithSplit(paragraph.text)
      }
    }

    paragraphs.forEach(splitAndAppendParagraph)

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
      safeMoveTo(targetIndex, 0).finally(() => {
        suppressSave = false
      })
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
   * 获取当前章节内的相对页码偏移信息（用于在重新分页时保持位置）
   * @param {string} chapterId - 章节ID，默认使用当前活跃章节
   * @returns {{ relativeIndex: number, totalPages: number, atEnd: boolean, atStart: boolean } | null}
   */
  function getChapterRelativePosition(chapterId = null) {
    const targetChapterId = chapterId || activeChapterId.value
    if (!targetChapterId) return null
    
    const boundary = chapterBoundaries.value[targetChapterId]
    if (!boundary) return null
    
    const chapterPageCount = boundary.endPage - boundary.startPage + 1
    const relativeIndex = currentPageIndex.value - boundary.startPage
    
    return {
      relativeIndex: Math.max(0, Math.min(relativeIndex, chapterPageCount - 1)),
      totalPages: chapterPageCount,
      atEnd: relativeIndex >= chapterPageCount - 1,
      atStart: relativeIndex <= 0
    }
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
    try {
      await safeMoveTo(targetIndex, 200)
    } finally {
      suppressSave = false
    }
    
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
    try {
      await safeMoveTo(target, 200)
    } finally {
      suppressSave = false
    }
    return target
  }

  // 处理页面变化
  function handlePageChanged(event) {
    currentPageIndex.value = event.index
    
    // 更新当前活跃章节
    const newChapterId = getChapterIdByPageIndex(event.index)
    const oldActiveChapterId = activeChapterId.value
    if (newChapterId && newChapterId !== activeChapterId.value) {
      activeChapterId.value = newChapterId
    }
    
    return {
      pageIndex: event.index,
      chapterId: newChapterId,
      chapterChanged: newChapterId !== oldActiveChapterId
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

  function safeMoveTo(targetIndex, duration = 200) {
    moveQueue = moveQueue.then(async () => {
      const flicking = flickingRef.value
      // 确保 Flicking 实例存在且已完成初始化
      if (!flicking || !flicking.initialized) return
      try {
        await flicking.moveTo(targetIndex, duration)
      } catch (error) {
        // 忽略 Flicking 正在动画中的异常，避免未捕获报错
        if (import.meta.env?.DEV) {
          console.debug('safeMoveTo skipped:', error?.message || error)
        }
      }
    })
    return moveQueue
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
    getChapterRelativePosition,
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
