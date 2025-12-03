<script setup>
/**
 * 翻页模式内容组件（自定义实现）
 * 
 * 支持多章节无缝滑动：
 * - 轻量级实现，无第三方依赖
 * - 支持触摸和鼠标拖动
 * - 平滑动画 + 边缘回弹
 * - 动态页面增减无需重建
 */
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { NSkeleton } from 'naive-ui'

const props = defineProps({
  isMobile: { type: Boolean, default: false },
  pageChunks: { type: Array, default: () => [] },
  pagePanelStyle: { type: Object, default: () => ({}) },
  readerContentStyle: { type: Object, default: () => ({}) },
  paragraphStyle: { type: Object, default: () => ({}) },
  chapterTitle: { type: String, default: '' },
  chapterBoundaries: { type: Object, default: () => ({}) },
  multiChapterMode: { type: Boolean, default: false },
  hasNextChapter: { type: Boolean, default: false },
  hasPrevChapter: { type: Boolean, default: false },
  currentPageIndex: { type: Number, default: 0 }  // 外部传入的当前页索引
})

const emit = defineEmits(['page-changed', 'reach-edge', 'resize', 'chapter-changed', 'need-more-chapters'])

// ============ 核心状态 ============
const containerRef = ref(null)
const trackRef = ref(null)
const currentIndex = ref(0)
const dragOffset = ref(0)        // 拖动时的临时偏移
const isAnimating = ref(false)   // 是否正在动画中
const isDragging = ref(false)    // 是否正在拖动
const skipTransition = ref(false) // 是否跳过过渡动画（外部索引更新时）
let isInitialized = ref(false)
let lastEdgeTime = 0
let resizeObserver = null

// 拖动相关状态（不需要响应式）
let startX = 0
let startY = 0
let startTime = 0
let lastMoveX = 0
let velocityX = 0
let isHorizontalDrag = null  // null: 未确定方向, true: 水平, false: 垂直

// 配置
const THRESHOLD = 50           // 切换页面的最小拖动距离
const VELOCITY_THRESHOLD = 0.3 // 快速滑动的速度阈值
const BOUNCE_DISTANCE = 60     // 边缘回弹距离
const ANIMATION_DURATION = 250 // 动画时长(ms)

// ============ 安全过滤 ============
function filterValidChunks(chunks) {
  if (!Array.isArray(chunks)) return []
  return chunks.filter(chunk => {
    if (!Array.isArray(chunk) || chunk.length === 0) return false
    return chunk.every(item => item !== undefined && item !== null)
  })
}

const safePageChunks = computed(() => filterValidChunks(props.pageChunks))
const totalPages = computed(() => safePageChunks.value.length)

// ============ 计算位置 ============
const pageWidth = computed(() => {
  if (!containerRef.value) return 0
  return containerRef.value.offsetWidth
})

// 轨道样式（控制整体位移）
const trackStyle = computed(() => {
  const baseOffset = -currentIndex.value * pageWidth.value
  const totalOffset = baseOffset + dragOffset.value
  // 拖动中或跳过过渡时不使用动画
  const useTransition = !isDragging.value && !skipTransition.value
  return {
    transform: `translate3d(${totalOffset}px, 0, 0)`,
    transition: useTransition ? `transform ${ANIMATION_DURATION}ms cubic-bezier(0.25, 0.46, 0.45, 0.94)` : 'none'
  }
})

// ============ 章节信息计算 ============
const currentPageChapterInfo = computed(() => {
  if (!props.multiChapterMode || !Object.keys(props.chapterBoundaries).length) {
    return { title: props.chapterTitle, index: null }
  }
  
  for (const [chapterId, boundary] of Object.entries(props.chapterBoundaries)) {
    if (currentIndex.value >= boundary.startPage && currentIndex.value <= boundary.endPage) {
      return {
        chapterId,
        title: boundary.title,
        index: boundary.index,
        startPage: boundary.startPage,
        endPage: boundary.endPage
      }
    }
  }
  
  return { title: props.chapterTitle, index: null }
})

const displayChapterTitle = computed(() => {
  return currentPageChapterInfo.value.title || props.chapterTitle
})

const displayPageInfo = computed(() => {
  if (!props.multiChapterMode || currentPageChapterInfo.value.startPage === undefined) {
    return `${currentIndex.value + 1} / ${totalPages.value}`
  }
  
  const { startPage, endPage } = currentPageChapterInfo.value
  if (startPage === undefined || endPage === undefined) {
    return `${currentIndex.value + 1} / ${totalPages.value}`
  }
  
  const relativeIndex = currentIndex.value - startPage + 1
  const chapterPageCount = endPage - startPage + 1
  return `${relativeIndex} / ${chapterPageCount}`
})

// ============ 触摸/鼠标事件处理 ============
function getEventX(e) {
  return e.touches ? e.touches[0].clientX : e.clientX
}

function getEventY(e) {
  return e.touches ? e.touches[0].clientY : e.clientY
}

function onDragStart(e) {
  if (isAnimating.value) return
  
  // 鼠标事件只响应左键
  if (e.type === 'mousedown' && e.button !== 0) return
  
  isDragging.value = true
  isHorizontalDrag = null
  startX = getEventX(e)
  startY = getEventY(e)
  lastMoveX = startX
  startTime = Date.now()
  velocityX = 0
  dragOffset.value = 0
  
  // 添加全局事件监听（确保拖到元素外也能响应）
  if (e.type === 'mousedown') {
    document.addEventListener('mousemove', onDragMove)
    document.addEventListener('mouseup', onDragEnd)
  }
}

function onDragMove(e) {
  if (!isDragging.value) return
  
  const currentX = getEventX(e)
  const currentY = getEventY(e)
  const deltaX = currentX - startX
  const deltaY = currentY - startY
  
  // 首次移动时判断方向
  if (isHorizontalDrag === null) {
    const absDeltaX = Math.abs(deltaX)
    const absDeltaY = Math.abs(deltaY)
    
    // 需要至少移动 10px 才判断方向
    if (absDeltaX > 10 || absDeltaY > 10) {
      isHorizontalDrag = absDeltaX > absDeltaY
      
      // 如果是垂直滑动，取消拖动
      if (!isHorizontalDrag) {
        isDragging.value = false
        return
      }
    } else {
      return // 移动距离太小，继续等待
    }
  }
  
  // 只处理水平拖动
  if (!isHorizontalDrag) return
  
  // 阻止默认行为（防止页面滚动）
  e.preventDefault()
  
  // 计算速度
  const now = Date.now()
  const timeDelta = now - startTime
  if (timeDelta > 0) {
    velocityX = (currentX - lastMoveX) / timeDelta
  }
  lastMoveX = currentX
  startTime = now
  
  // 边缘阻尼效果
  let offset = deltaX
  if (currentIndex.value === 0 && deltaX > 0) {
    // 第一页向右拖动，增加阻尼
    offset = deltaX * 0.3
  } else if (currentIndex.value === totalPages.value - 1 && deltaX < 0) {
    // 最后一页向左拖动，增加阻尼
    offset = deltaX * 0.3
  }
  
  dragOffset.value = offset
}

function onDragEnd(e) {
  if (!isDragging.value) return
  
  // 移除全局事件监听
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
  
  isDragging.value = false
  
  // 如果方向未确定或是垂直滑动，直接复位
  if (isHorizontalDrag !== true) {
    dragOffset.value = 0
    return
  }
  
  const offset = dragOffset.value
  const absOffset = Math.abs(offset)
  const absVelocity = Math.abs(velocityX)
  
  // 判断是否切换页面
  let shouldSwitch = false
  let direction = 0 // -1: 向前, 1: 向后
  
  if (absOffset > THRESHOLD || absVelocity > VELOCITY_THRESHOLD) {
    if (offset > 0) {
      // 向右拖动 -> 显示上一页
      direction = -1
    } else {
      // 向左拖动 -> 显示下一页
      direction = 1
    }
    
    // 检查边界
    const targetIndex = currentIndex.value + direction
    if (targetIndex >= 0 && targetIndex < totalPages.value) {
      shouldSwitch = true
    }
  }
  
  // 开始动画
  isAnimating.value = true
  dragOffset.value = 0
  
  if (shouldSwitch) {
    const prevIndex = currentIndex.value
    currentIndex.value += direction
    
    // 触发事件
    emitPageChanged(prevIndex)
  } else {
    // 检查是否到达边缘
    if (currentIndex.value === 0 && offset > THRESHOLD) {
      emitReachEdge('PREV')
    } else if (currentIndex.value === totalPages.value - 1 && offset < -THRESHOLD) {
      emitReachEdge('NEXT')
    }
  }
  
  // 动画结束
  setTimeout(() => {
    isAnimating.value = false
  }, ANIMATION_DURATION)
}

// ============ 事件发射 ============
function emitPageChanged(prevIndex) {
  const event = { index: currentIndex.value, prevIndex }
  emit('page-changed', event)
  
  // 多章节模式下检测章节变化
  if (props.multiChapterMode && Object.keys(props.chapterBoundaries).length) {
    const prevChapterId = getChapterIdByPageIndex(prevIndex)
    const currentChapterId = getChapterIdByPageIndex(currentIndex.value)
    
    if (currentChapterId && currentChapterId !== prevChapterId) {
      emit('chapter-changed', {
        chapterId: currentChapterId,
        boundary: props.chapterBoundaries[currentChapterId],
        pageIndex: currentIndex.value
      })
    }
    
    checkAndEmitNeedMoreChapters(currentIndex.value)
  }
  
  // 标记已初始化
  if (!isInitialized.value && currentIndex.value >= 0) {
    setTimeout(() => {
      isInitialized.value = true
    }, 300)
  }
}

function getChapterIdByPageIndex(pageIndex) {
  for (const [chapterId, boundary] of Object.entries(props.chapterBoundaries)) {
    if (pageIndex >= boundary.startPage && pageIndex <= boundary.endPage) {
      return chapterId
    }
  }
  return null
}

function checkAndEmitNeedMoreChapters(pageIndex) {
  if (!props.multiChapterMode) return
  
  const chapterIds = Object.keys(props.chapterBoundaries)
  if (!chapterIds.length) return
  
  const currentChapterId = getChapterIdByPageIndex(pageIndex)
  if (!currentChapterId) return
  
  const boundary = props.chapterBoundaries[currentChapterId]
  const chapterIndex = chapterIds.indexOf(currentChapterId)
  const chapterPageCount = boundary.endPage - boundary.startPage + 1
  const relativeIndex = pageIndex - boundary.startPage
  
  // 接近章节末尾
  if (relativeIndex >= chapterPageCount - 2 && boundary.next_id) {
    const nextInLoaded = chapterIds.includes(boundary.next_id)
    if (!nextInLoaded || chapterIndex >= chapterIds.length - 2) {
      emit('need-more-chapters', { direction: 'next', currentChapterId })
    }
  }
  
  // 接近章节开头
  if (relativeIndex <= 1 && boundary.prev_id) {
    const prevInLoaded = chapterIds.includes(boundary.prev_id)
    if (!prevInLoaded || chapterIndex <= 1) {
      emit('need-more-chapters', { direction: 'prev', currentChapterId })
    }
  }
}

function emitReachEdge(direction) {
  if (!isInitialized.value) return
  
  const now = Date.now()
  if (now - lastEdgeTime < 500) return
  lastEdgeTime = now
  
  emit('reach-edge', { direction })
}

// ============ 公开方法 ============
function goToPage(index, animate = true) {
  if (index < 0 || index >= totalPages.value) return
  
  const prevIndex = currentIndex.value
  if (!animate) {
    currentIndex.value = index
    emitPageChanged(prevIndex)
    return
  }
  
  isAnimating.value = true
  currentIndex.value = index
  emitPageChanged(prevIndex)
  
  setTimeout(() => {
    isAnimating.value = false
  }, ANIMATION_DURATION)
}

function prev() {
  if (currentIndex.value > 0) {
    goToPage(currentIndex.value - 1)
  }
}

function next() {
  if (currentIndex.value < totalPages.value - 1) {
    goToPage(currentIndex.value + 1)
  }
}

function resetInitState() {
  isInitialized.value = false
}

// 暴露给父组件
defineExpose({ 
  resetInitState,
  goToPage,
  prev,
  next,
  get index() { return currentIndex.value },
  get initialized() { return isInitialized.value }
})

// ============ 监听数据变化 ============
// 监听外部传入的页索引变化（重新分页后同步索引）
watch(() => props.currentPageIndex, async (newIndex) => {
  await nextTick()  // 等待 pageChunks 更新后再检查
  if (newIndex !== currentIndex.value && newIndex >= 0 && newIndex < totalPages.value) {
    // 外部索引更新时跳过动画
    skipTransition.value = true
    currentIndex.value = newIndex
    // 在下一帧恢复动画
    requestAnimationFrame(() => {
      skipTransition.value = false
    })
  }
})

// 当页面数据变化时，同步外部传入的索引
watch(() => props.pageChunks, async (newChunks) => {
  await nextTick()
  
  const filtered = filterValidChunks(newChunks)
  const maxIndex = Math.max(0, filtered.length - 1)
  
  // 优先使用外部传入的索引（重新分页后的目标页）
  if (props.currentPageIndex >= 0 && props.currentPageIndex <= maxIndex) {
    // 外部索引更新时跳过动画
    skipTransition.value = true
    currentIndex.value = props.currentPageIndex
    // 在下一帧恢复动画
    requestAnimationFrame(() => {
      skipTransition.value = false
    })
  } else if (currentIndex.value > maxIndex) {
    // 如果当前索引超出范围，调整到最后一页
    currentIndex.value = maxIndex
  }
}, { deep: false })

// 初始化时发射一次页面变化事件
watch(totalPages, (newTotal, oldTotal) => {
  if (oldTotal === 0 && newTotal > 0) {
    // 首次有数据
    isInitialized.value = true
    emit('page-changed', { index: currentIndex.value, prevIndex: -1 })
  }
}, { immediate: true })

onMounted(() => {
  if (containerRef.value) {
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        emit('resize', { width, height })
      }
    })
    resizeObserver.observe(containerRef.value)
  }
})

// ============ 生命周期 ============
onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)
})
</script>

<template>
  <div 
    class="page-swiper" 
    :class="{ 'mobile-page': isMobile }" 
    ref="containerRef"
    @touchstart.passive="onDragStart"
    @touchmove="onDragMove"
    @touchend="onDragEnd"
    @touchcancel="onDragEnd"
    @mousedown="onDragStart"
  >
    <template v-if="safePageChunks.length">
      <div class="swiper-track" ref="trackRef" :style="trackStyle">
        <div
          v-for="(page, idx) in safePageChunks"
          :key="`page-${idx}`"
          class="page-panel"
          :style="pagePanelStyle"
        >
          <div class="page-panel-body" :style="readerContentStyle">
            <div class="page-text">
              <p
                v-for="(item, lineIdx) in page"
                :key="`line-${lineIdx}`"
                class="paragraph"
                :class="{ 'chapter-title-line': item?.isTitle }"
                :style="item?.isTitle ? {} : { ...paragraphStyle, textIndent: item?.isContinuation ? '0' : paragraphStyle.textIndent }"
              >
                {{ item?.text || item || '' }}
              </p>
            </div>
          </div>
          <!-- 底部固定信息栏 -->
          <div class="page-footer-info" v-if="isMobile">
            <span class="footer-chapter">{{ displayChapterTitle }}</span>
            <span class="footer-page">{{ displayPageInfo }}</span>
          </div>
        </div>
      </div>
    </template>
    <template v-else>
      <div class="chapter-placeholder">
        <n-skeleton v-for="n in 6" :key="n" text :height="18" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-swiper {
  height: 100%;
  width: 100%;
  padding: 24px;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
  touch-action: pan-y pinch-zoom; /* 允许垂直滚动，禁止水平滚动由浏览器处理 */
  user-select: none;
  -webkit-user-select: none;
}

.page-swiper.mobile-page {
  padding: 0;
  min-height: 100dvh;
}

.swiper-track {
  display: flex;
  height: 100%;
  will-change: transform;
}

.page-panel {
  flex-shrink: 0;
  width: calc(100% - 32px);
  height: 100%;
  max-width: 820px;
  margin: 0 16px;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: stretch;
  position: relative;
  box-sizing: border-box;
}

.page-swiper.mobile-page .page-panel {
  width: 100%;
  height: 100dvh;
  max-width: none;
  margin: 0;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
  position: relative;
  padding: 8px;
}

.page-panel-body {
  padding: 20px 16px 12px;
  overflow: visible;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

.page-swiper.mobile-page .page-panel-body {
  padding: 8px 8px calc(56px + env(safe-area-inset-bottom, 0px));
}

.page-text {
  flex: 1;
  min-height: 0;
  white-space: pre-wrap;
  overflow: visible;
  /* 中文排版优化 */
  line-break: strict;           /* 严格断行规则，避头尾标点 */
  word-break: normal;           /* 正常断词 */
  overflow-wrap: break-word;    /* 长单词换行 */
  hanging-punctuation: first allow-end;  /* 段首标点悬挂，行尾标点允许悬挂 */
  text-spacing-trim: space-first allow-end trim-adjacent; /* 标点挤压（现代浏览器） */
}

.paragraph {
  margin: 0;
  color: inherit;
  /* 标点挤压备用方案 */
  font-feature-settings: "halt" 1, "vhal" 1;  /* 标点半宽 */
  font-kerning: normal;         /* 启用字距调整 */
}

.paragraph.chapter-title-line {
  text-indent: 0;
  font-weight: bold;
  text-align: center;
  margin-bottom: 1.5em;
  font-size: 1.1em;
}

.chapter-placeholder {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
}

/* 底部固定信息栏 */
.page-footer-info {
  position: absolute;
  bottom: calc(env(safe-area-inset-bottom, 0px) + 8px);
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 16px;
  font-size: 11px;
  color: #999;
  background: transparent;
  pointer-events: none;
}

.footer-chapter {
  max-width: 60%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.footer-page {
  font-weight: 500;
  color: #18a058;
}
</style>
