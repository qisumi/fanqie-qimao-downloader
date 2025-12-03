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

// 过滤掉异常值，确保 Flicking 子节点有效
const safePageChunks = computed(() => {
  if (!Array.isArray(props.pageChunks)) return []
  return props.pageChunks
    .filter(chunk => Array.isArray(chunk)) // 只保留数组页
    .map(chunk => chunk || []) // 避免 undefined/null
})

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

function handleChanged(event) {
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
  // 未初始化完成时不触发
  if (!isInitialized.value) return
  
  // 防抖：避免短时间内重复触发
  const now = Date.now()
  if (now - lastEdgeTime < 500) return
  lastEdgeTime = now
  
  // 多章节模式下，边缘事件仅用于提示（不再自动切章）
  // 因为章节已经预加载到 pageChunks 中，滑动是连续的
  emit('reach-edge', event)
}

// 重置初始化状态（用于章节切换时）
function resetInitState() {
  isInitialized.value = false
}

// 暴露给父组件
defineExpose({ resetInitState })

// 监听 pageChunks 变化，同步更新 currentPageIdx
watch(() => props.pageChunks, async () => {
  // 当 pageChunks 更新后，等待 DOM 更新，然后从 flickingRef 获取当前索引
  await nextTick()
  if (flickingRef.value?.index !== undefined) {
    currentPageIdx.value = flickingRef.value.index
  }
}, { deep: false })

// 监听 flickingRef 的初始化
watch(flickingRef, async (newRef) => {
  if (newRef?.index !== undefined) {
    await nextTick()
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
        ref="flickingRef"
        :key="safePageChunks.length" 
        :options="{
          align: 'prev',
          circular: false,
          autoResize: true,
          bounce: 10,
          duration: 180,
          renderOnlyVisible: safePageChunks.length > 20
        }"
        @changed="handleChanged"
        @reach-edge="handleReachEdge"
      >
        <div
          v-for="(page, idx) in safePageChunks"
          :key="idx"
          class="page-panel"
          :style="pagePanelStyle"
        >
          <div class="page-panel-body" :style="readerContentStyle">
            <div class="page-text">
              <p
                v-for="(item, lineIdx) in page"
                :key="lineIdx"
                class="paragraph"
                :class="{ 'chapter-title-line': item.isTitle }"
                :style="item.isTitle ? {} : paragraphStyle"
              >
                {{ item.text || item }}
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
}

.page-flicking.mobile-page .page-panel {
  width: 100vw;
  height: 100vh;
  max-width: none;
  margin: 0;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
  position: relative;
}

.page-panel-body {
  padding: 20px 22px 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  box-sizing: border-box;
}

.page-flicking.mobile-page .page-panel-body {
  padding: 48px 20px 8px; /* 上方避开工具栏，底部缩小 */
}

.page-text {
  flex: 1;
  white-space: pre-wrap;
  overflow: hidden;
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
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 16px;
  padding-bottom: calc(6px + env(safe-area-inset-bottom, 0px));
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
