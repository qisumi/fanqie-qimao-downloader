<script setup>
/**
 * 目录抽屉组件
 */
import { computed, nextTick, ref, watch } from 'vue'
import {
  NDrawer,
  NDrawerContent,
  NTag
} from 'naive-ui'

const props = defineProps({
  visible: { type: Boolean, default: false },
  isMobile: { type: Boolean, default: false },
  toc: { type: Array, default: () => [] },
  currentChapterId: { type: String, default: '' },
  currentBookTitle: { type: String, default: '' },
  cachedChapters: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
  hasMoreNext: { type: Boolean, default: false },
  hasMorePrev: { type: Boolean, default: false },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'select-chapter', 'load-more-next', 'load-more-prev'])

const cachedSet = computed(() => new Set(props.cachedChapters || []))
const tocListRef = ref(null)
const activeItemRef = ref(null)
const waitingLoadMore = ref(false)
const waitingLoadPrev = ref(false)

function handleClose() {
  emit('update:visible', false)
}

function handleSelectChapter(chapter) {
  emit('select-chapter', chapter)
}

function isCached(chapterId) {
  return cachedSet.value.has(chapterId)
}

function setActiveItemRef(el, isActive) {
  if (isActive) {
    activeItemRef.value = el
  } else if (activeItemRef.value === el) {
    activeItemRef.value = null
  }
}

function scrollToActiveChapter() {
  const container = tocListRef.value
  const activeEl = activeItemRef.value
  if (!container || !activeEl) return
  const target = activeEl.offsetTop - container.clientHeight / 2 + activeEl.clientHeight / 2
  container.scrollTop = Math.max(0, target)
}

function handleScroll() {
  const container = tocListRef.value
  if (!container) return

  const threshold = 120

  if (props.hasMoreNext && !props.loading && !waitingLoadMore.value) {
    if (container.scrollTop + container.clientHeight >= container.scrollHeight - threshold) {
      waitingLoadMore.value = true
      emit('load-more-next')
    }
  }

  if (props.hasMorePrev && !props.loading && !waitingLoadPrev.value) {
    if (container.scrollTop <= threshold) {
      waitingLoadPrev.value = true
      emit('load-more-prev')
    }
  }
}

watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      await nextTick()
      scrollToActiveChapter()
    }
  }
)

watch(
  () => props.currentChapterId,
  async () => {
    if (props.visible) {
      await nextTick()
      scrollToActiveChapter()
    } else {
      activeItemRef.value = null
    }
  }
)

watch(
  () => props.loading,
  (loading) => {
    if (!loading) {
      waitingLoadMore.value = false
      waitingLoadPrev.value = false
    }
  }
)
</script>

<template>
  <n-drawer
    :show="visible"
    :width="isMobile ? 280 : 360"
    placement="left"
    :native-scrollbar="false"
    class="toc-drawer"
    @update:show="$emit('update:visible', $event)"
  >
    <n-drawer-content :style="{ display: 'block' }" body-content-style="padding: 0;">
      <div class="toc-header">
        <div class="toc-title">
          <span>目录</span>
          <span class="toc-count">{{ total || toc.length }} 章</span>
        </div>
        <div class="toc-subtitle">{{ currentBookTitle }}</div>
        <div class="toc-tip" v-if="hasMorePrev">
          上滑继续加载更早的章节
        </div>
      </div>
      <div class="toc-list" ref="tocListRef" @scroll="handleScroll">
        <!-- 章节标题已包含"第X章"信息，无需额外显示索引 -->
        <div
          v-for="chapter in toc"
          :key="chapter.id"
          class="toc-item"
          :class="{ active: chapter.id === currentChapterId }"
          @click="handleSelectChapter(chapter)"
          :ref="el => setActiveItemRef(el, chapter.id === currentChapterId)"
        >
          <div class="toc-row">
            <div class="toc-tags" v-if="chapter.id === currentChapterId || isCached(chapter.id)">
              <n-tag size="tiny" type="success" v-if="chapter.id === currentChapterId" round>当前</n-tag>
              <n-tag size="tiny" type="info" v-if="isCached(chapter.id)" round>已缓存</n-tag>
            </div>
            <div class="toc-name">{{ chapter.title || '未命名章节' }}</div>
          </div>
        </div>
        <div class="toc-load-more" v-if="hasMoreNext || loading">
          <span v-if="loading">加载中...</span>
          <span v-else>下滑加载更多章节</span>
        </div>
        <div class="toc-end" v-else>
          已加载全部章节
        </div>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<style scoped>
.toc-header {
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--border-color-light, #efeff5);
  background: rgba(255, 255, 255, 0.9);
}

.toc-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
}

.toc-count {
  font-size: 13px;
  color: var(--text-color-tertiary, #999);
}

.toc-subtitle {
  margin-top: 6px;
  color: var(--text-color-secondary, #666);
  font-size: 13px;
}

.toc-tip {
  margin-top: 4px;
  color: var(--text-color-tertiary, #999);
  font-size: 12px;
}

.toc-list {
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  padding: 10px 0 16px;
}

.toc-item {
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.toc-item:hover {
  background: rgba(24, 160, 88, 0.08);
}

.toc-item.active {
  background: rgba(24, 160, 88, 0.12);
  border-left: 4px solid #18a058;
}

.toc-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toc-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-color-tertiary, #999);
}

.toc-name {
  flex: 1;
  color: var(--text-color-primary, #333);
  font-weight: 600;
}

.toc-load-more,
.toc-end {
  padding: 12px 16px;
  text-align: center;
  color: var(--text-color-tertiary, #888);
  font-size: 13px;
}
</style>
