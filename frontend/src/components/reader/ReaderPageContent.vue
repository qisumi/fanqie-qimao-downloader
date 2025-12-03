<script setup>
/**
 * 翻页模式内容组件
 * 
 * 支持多章节无缝滑动：
 * - 使用 renderOnlyVisible 实现虚拟渲染，优化性能
 * - 通过 chapterBoundaries 跟踪章节边界
 * - 底部显示当前章节标题（根据页面位置动态更新）
 */
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import Flicking from '@egjs/vue3-flicking'
import '@egjs/vue3-flicking/dist/flicking.css'
import { NSkeleton } from 'naive-ui'

const props = defineProps({
  isMobile: { type: Boolean, default: false },
  pageChunks: { type: Array, default: () => [] },
  pagePanelStyle: { type: Object, default: () => ({}) },
  readerContentStyle: { type: Object, default: () => ({}) },
  paragraphStyle: { type: Object, default: () => ({}) },
  // 当前活跃章节标题（用于底部显示）
  chapterTitle: { type: String, default: '' },
  // 章节边界映射 { chapterId: { startPage, endPage, title, index } }
  chapterBoundaries: { type: Object, default: () => ({}) },
  // 是否启用多章节模式
  multiChapterMode: { type: Boolean, default: false },
  hasNextChapter: { type: Boolean, default: false },
  hasPrevChapter: { type: Boolean, default: false }
})

const emit = defineEmits(['page-changed', 'reach-edge', 'resize', 'chapter-changed', 'need-more-chapters'])

// 暴露 flicking ref 给父组件
const flickingRef = defineModel('flickingRef')
const containerRef = ref(null)
let resizeObserver = null
let isInitialized = ref(false)
let lastEdgeTime = 0

// 当前页面索引（用于计算当前章节）
const currentPageIdx = ref(0)

// 内部缓存的页面数据，避免在 Flicking 动画期间更新
const internalPageChunks = ref([])
// 是否正在动画中
const isAnimating = ref(false)
// 待更新的页面数据
let pendingPageChunks = null

// 安全过滤页面数据，确保 Flicking 子节点有效
function filterValidChunks(chunks) {
  if (!Array.isArray(chunks)) return []
  return chunks.filter(chunk => {
    // chunk 必须是有效数组且每个元素都有效
    if (!Array.isArray(chunk) || chunk.length === 0) return false
    // 确保 chunk 中没有 undefined/null 元素
    return chunk.every(item => item !== undefined && item !== null)
  })
}

// 同步外部 pageChunks 到内部缓存
watch(() => props.pageChunks, (newChunks) => {
  const filtered = filterValidChunks(newChunks)
  
  if (isAnimating.value) {
    // 动画中，暂存更新
    console.log('[ReaderPageContent] Animation in progress, deferring pageChunks update')
    pendingPageChunks = filtered
  } else {
    // 非动画状态，直接更新
    internalPageChunks.value = filtered
  }
}, { immediate: true })

// 过滤掉异常值，确保 Flicking 子节点有效
const safePageChunks = computed(() => {
  // 二次校验，确保在渲染时数据是安全的
  return filterValidChunks(internalPageChunks.value)
})

// Flicking 组件的 key，用于在数据结构大幅变化时强制重新创建组件
// 使用稳定的 key 策略：只基于章节数量，避免在追加章节时频繁重建
// 注意：章节内容变化时不改变 key，让 Flicking 自己处理面板更新
const flickingKeyCounter = ref(0)
const flickingKey = computed(() => {
  return `flicking-${flickingKeyCounter.value}`
})

// 监听章节数量变化，仅当数量减少或清空时才重建
// （追加章节时不需要重建，Flicking 可以动态处理新增面板）
let lastChapterCount = 0
watch(() => Object.keys(props.chapterBoundaries).length, (newCount) => {
  // 只有当章节数从多变少（比如切换书籍）时才重建
  if (newCount < lastChapterCount || (lastChapterCount > 0 && newCount === 0)) {
    flickingKeyCounter.value++
  }
  lastChapterCount = newCount
}, { immediate: true })

// 计算当前页面所属的章节信息
const currentPageChapterInfo = computed(() => {
  if (!props.multiChapterMode || !Object.keys(props.chapterBoundaries).length) {
    return { title: props.chapterTitle, index: null }
  }
  
  for (const [chapterId, boundary] of Object.entries(props.chapterBoundaries)) {
    if (currentPageIdx.value >= boundary.startPage && currentPageIdx.value <= boundary.endPage) {
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

// 底部显示的章节标题
// 注：API 返回的章节名已包含"第X章"信息，无需额外拼接
const displayChapterTitle = computed(() => {
  return currentPageChapterInfo.value.title || props.chapterTitle
})

// 底部显示的页码（在章节内的相对页码）
const displayPageInfo = computed(() => {
  if (!props.multiChapterMode || currentPageChapterInfo.value.startPage === undefined) {
    return `${currentPageIdx.value + 1} / ${safePageChunks.value.length}`
  }
  
  const { startPage, endPage } = currentPageChapterInfo.value
  if (startPage === undefined || endPage === undefined) {
    return `${currentPageIdx.value + 1} / ${safePageChunks.value.length}`
  }
  
  const relativeIndex = currentPageIdx.value - startPage + 1
  const chapterPageCount = endPage - startPage + 1
  return `${relativeIndex} / ${chapterPageCount}`
})

// Flicking ready 事件：组件初始化完成
function handleReady() {
  console.log('[ReaderPageContent] handleReady called, flickingRef:', {
    exists: !!flickingRef.value,
    initialized: flickingRef.value?.initialized,
    index: flickingRef.value?.index
  })
  if (flickingRef.value?.index !== undefined) {
    currentPageIdx.value = flickingRef.value.index
  }
}

// 动画开始
function handleMoveStart() {
  isAnimating.value = true
}

// 动画结束
function handleMoveEnd() {
  isAnimating.value = false
  // 如果有待更新的数据，使用 nextTick 确保当前渲染周期完成后再应用
  if (pendingPageChunks !== null) {
    console.log('[ReaderPageContent] Applying deferred pageChunks update')
    const chunksToApply = pendingPageChunks
    pendingPageChunks = null
    // 使用 nextTick 避免在 Flicking 内部状态更新期间修改数据
    nextTick(() => {
      internalPageChunks.value = filterValidChunks(chunksToApply)
    })
  }
}

function handleChanged(event) {
  console.log('[ReaderPageContent] handleChanged:', {
    eventIndex: event.index,
    prevIndex: currentPageIdx.value,
    flickingInitialized: flickingRef.value?.initialized
  })
  const prevPageIdx = currentPageIdx.value
  currentPageIdx.value = event.index
  
  emit('page-changed', event)
  
  // 多章节模式下检测章节变化
  if (props.multiChapterMode && Object.keys(props.chapterBoundaries).length) {
    const prevChapterId = getChapterIdByPageIndex(prevPageIdx)
    const currentChapterId = getChapterIdByPageIndex(event.index)
    
    if (currentChapterId && currentChapterId !== prevChapterId) {
      emit('chapter-changed', {
        chapterId: currentChapterId,
        boundary: props.chapterBoundaries[currentChapterId],
        pageIndex: event.index
      })
    }
    
    // 检查是否需要加载更多章节（接近边界时提前触发）
    checkAndEmitNeedMoreChapters(event.index)
  }
  
  // 标记已初始化
  if (!isInitialized.value && event.index >= 0) {
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
  
  // 找到当前章节和其在列表中的位置
  const currentChapterId = getChapterIdByPageIndex(pageIndex)
  if (!currentChapterId) return
  
  const boundary = props.chapterBoundaries[currentChapterId]
  const chapterIndex = chapterIds.indexOf(currentChapterId)
  
  // 当前章节内的相对位置
  const chapterPageCount = boundary.endPage - boundary.startPage + 1
  const relativeIndex = pageIndex - boundary.startPage
  
  // 如果接近章节末尾（最后2页），且有下一章，且下一章不在已加载列表中
  if (relativeIndex >= chapterPageCount - 2 && boundary.next_id) {
    const nextInLoaded = chapterIds.includes(boundary.next_id)
    if (!nextInLoaded || chapterIndex >= chapterIds.length - 2) {
      emit('need-more-chapters', { direction: 'next', currentChapterId })
    }
  }
  
  // 如果接近章节开头（前2页），且有上一章，且上一章不在已加载列表中
  if (relativeIndex <= 1 && boundary.prev_id) {
    const prevInLoaded = chapterIds.includes(boundary.prev_id)
    if (!prevInLoaded || chapterIndex <= 1) {
      emit('need-more-chapters', { direction: 'prev', currentChapterId })
    }
  }
}

function handleReachEdge(event) {
  console.log('[ReaderPageContent] handleReachEdge called:', {
    direction: event?.direction,
    isInitialized: isInitialized.value,
    timeSinceLastEdge: Date.now() - lastEdgeTime
  })
  
  // 未初始化完成时不触发
  if (!isInitialized.value) {
    console.log('[ReaderPageContent] handleReachEdge: skipped (not initialized)')
    return
  }
  
  // 防抖：避免短时间内重复触发
  const now = Date.now()
  if (now - lastEdgeTime < 500) {
    console.log('[ReaderPageContent] handleReachEdge: skipped (debounced)')
    return
  }
  lastEdgeTime = now
  
  // 多章节模式下，边缘事件仅用于提示（不再自动切章）
  // 因为章节已经预加载到 pageChunks 中，滑动是连续的
  console.log('[ReaderPageContent] handleReachEdge: emitting reach-edge')
  emit('reach-edge', event)
}

// 重置初始化状态（用于章节切换时）
function resetInitState() {
  isInitialized.value = false
}

// 暴露给父组件
defineExpose({ resetInitState })

// 监听内部 pageChunks 变化，同步更新 currentPageIdx
watch(internalPageChunks, async () => {
  console.log('[ReaderPageContent] internalPageChunks changed:', {
    length: internalPageChunks.value?.length,
    flickingExists: !!flickingRef.value,
    flickingInitialized: flickingRef.value?.initialized
  })
  // 当 pageChunks 更新后，等待 DOM 更新，然后从 flickingRef 获取当前索引
  await nextTick()
  // 确保 Flicking 实例存在且已初始化
  if (flickingRef.value?.initialized && flickingRef.value?.index !== undefined) {
    console.log('[ReaderPageContent] internalPageChunks watcher: updating currentPageIdx to', flickingRef.value.index)
    currentPageIdx.value = flickingRef.value.index
  }
}, { deep: false })

// 监听 flickingRef 的初始化
watch(flickingRef, async (newRef) => {
  console.log('[ReaderPageContent] flickingRef changed:', {
    exists: !!newRef,
    initialized: newRef?.initialized,
    index: newRef?.index
  })
  // 确保 Flicking 实例已初始化
  if (newRef?.initialized && newRef?.index !== undefined) {
    await nextTick()
    console.log('[ReaderPageContent] flickingRef watcher: updating currentPageIdx to', newRef.index)
    currentPageIdx.value = newRef.index
  }
})

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

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<template>
  <div class="page-flicking" :class="{ 'mobile-page': isMobile }" ref="containerRef">
    <template v-if="safePageChunks.length">
      <Flicking
        :key="flickingKey"
        ref="flickingRef"
        :options="{
          align: 'prev',
          circular: false,
          autoResize: true,
          bounce: 10,
          duration: 180,
          renderOnlyVisible: false,
          moveType: 'strict',
          threshold: 40,
          preventDefaultOnDrag: true
        }"
        @ready="handleReady"
        @move-start="handleMoveStart"
        @move-end="handleMoveEnd"
        @changed="handleChanged"
        @reach-edge="handleReachEdge"
      >
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
      </Flicking>
    </template>
    <template v-else>
      <div class="chapter-placeholder">
        <n-skeleton v-for="n in 6" :key="n" text :height="18" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-flicking {
  height: 100%;
  width: 100%;
  padding: 24px;
  box-sizing: border-box;
  overflow: hidden;
}

.page-flicking.mobile-page {
  padding: 0;
  min-height: 100dvh;
}

.page-panel {
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

.page-flicking.mobile-page .page-panel {
  width: 100%;
  height: 100dvh; /* 使用动态视口高度，适应移动端浏览器 UI */
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

.page-flicking.mobile-page .page-panel-body {
  padding: 8px 8px calc(56px + env(safe-area-inset-bottom, 0px)); /* 移动端统一8px边距，底部额外预留信息栏和安全区 */
}

.page-text {
  flex: 1;
  min-height: 0; /* 防止 flex 子元素溢出 */
  white-space: pre-wrap;
  overflow: visible;
}

.paragraph {
  margin: 0;
  color: inherit;
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
