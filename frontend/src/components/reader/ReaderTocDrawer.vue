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
  cachedChapters: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible', 'select-chapter'])

const cachedSet = computed(() => new Set(props.cachedChapters || []))
const tocListRef = ref(null)
const activeItemRef = ref(null)

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
          <span class="toc-count">{{ toc.length }} 章</span>
        </div>
        <div class="toc-subtitle">{{ currentBookTitle }}</div>
      </div>
      <div class="toc-list" ref="tocListRef">
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
</style>
