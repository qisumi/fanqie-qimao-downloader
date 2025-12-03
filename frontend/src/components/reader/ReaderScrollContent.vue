<script setup>
/**
 * 滚动模式内容组件
 */
import { ref, defineExpose } from 'vue'
import { NAlert, NEmpty, NSkeleton, NSpin, NIcon, NButton } from 'naive-ui'
import { TimeOutline } from '@vicons/ionicons5'

// 暴露滚动容器 ref
const scrollContainerRef = ref(null)

defineExpose({
  scrollContainerRef
})

const props = defineProps({
  isMobile: { type: Boolean, default: false },
  displayChapters: { type: Array, default: () => [] },
  hasContent: { type: Boolean, default: false },
  isFetching: { type: Boolean, default: false },
  error: { type: String, default: '' },
  initializing: { type: Boolean, default: false },
  isLoadingChapter: { type: Boolean, default: false },
  currentBookTitle: { type: String, default: '' },
  currentChapterId: { type: String, default: '' },
  readerContentStyle: { type: Object, default: () => ({}) },
  paragraphStyle: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['scroll', 'reload', 'register-ref'])

function handleScroll(event) {
  emit('scroll', event)
}

function registerChapterRef(id, el) {
  emit('register-ref', id, el)
}
</script>

<template>
  <div
    ref="scrollContainerRef"
    class="chapter-scroll"
    :class="{ 'mobile-scroll': isMobile }"
    @scroll.passive="handleScroll"
  >
    <n-alert v-if="isFetching" type="info" :bordered="false" class="state-alert">
      正在后台获取该章节内容，稍后会自动替换为完整文本...
    </n-alert>
    <n-alert
      v-if="error"
      type="error"
      :bordered="false"
      class="state-alert"
    >
      <template #header>加载章节失败</template>
      <template #action>
        <n-button size="tiny" quaternary @click="$emit('reload')">重试</n-button>
      </template>
    </n-alert>

    <template v-if="hasContent">
      <div class="chapter-sections">
        <section
          v-for="section in displayChapters"
          :key="section.data.id || section.role"
          class="chapter-block"
          :data-chapter-id="section.data.id"
          :ref="el => registerChapterRef(section.data.id, el)"
        >
          <!-- 章节字数信息（章节名已包含"第X章"，无需重复显示） -->
          <div class="chapter-meta">
            <span class="meta-pill">
              <n-icon :size="14"><TimeOutline /></n-icon>
              <span>{{ section.data.word_count ? `${Math.round(section.data.word_count / 1000)}k` : '未知' }} 字</span>
            </span>
          </div>
          <div v-if="section.data.title" class="chapter-heading-block">
            <div class="chapter-heading-sub">{{ currentBookTitle }}</div>
            <h1 class="chapter-heading">{{ section.data.title }}</h1>
          </div>

          <div v-if="section.data.content_html" class="chapter-html" :style="readerContentStyle" v-html="section.data.content_html" />
          <div v-else class="chapter-text" :style="readerContentStyle">
            <p
              v-for="para in section.paragraphs"
              :key="para.id"
              :class="['paragraph', { spacer: para.isSpacer }]"
              :style="para.isSpacer ? null : paragraphStyle"
            >
              {{ para.text || '　' }}
            </p>
          </div>
        </section>
      </div>
    </template>

    <template v-else-if="!initializing && !isLoadingChapter">
      <n-empty description="暂时没有可展示的章节内容" />
    </template>

    <template v-else>
      <div class="chapter-placeholder">
        <n-skeleton v-for="n in 6" :key="n" text :height="18" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.chapter-scroll {
  max-height: calc(100vh - 40px);
  overflow-y: auto;
  padding: 16px;
  box-sizing: border-box;
}

.chapter-scroll.mobile-scroll {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 16px 14px 24px;
  /* 移动端需要固定高度才能滚动，使用 100vh 减去工具栏和底部控制栏的高度 */
  max-height: calc(100vh - 120px);
  min-height: calc(100vh - 200px);
  overflow-y: auto;
}

.chapter-sections {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.chapter-block {
  padding-bottom: 8px;
}

.chapter-block + .chapter-block {
  padding-top: 12px;
}

.chapter-meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}

.chapter-heading-block {
  margin-bottom: 18px;
}

.chapter-heading-sub {
  font-size: 13px;
  color: #6b6b6b;
  margin-bottom: 6px;
}

.chapter-heading {
  margin: 0;
  font-size: 30px;
  line-height: 1.2;
  letter-spacing: 0.02em;
  color: inherit;
  font-weight: 800;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(24, 160, 88, 0.08);
  color: #1d7c4f;
  font-size: 12px;
}

.chapter-text {
  word-break: break-word;
}

.paragraph {
  margin: 0;
  color: inherit;
}

.paragraph.spacer {
  height: 12px;
}

.chapter-html :deep(p) {
  margin: 0 0 12px 0;
  text-indent: 2em;
}

.state-alert {
  margin-bottom: 12px;
}

.chapter-placeholder {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (max-width: 768px) {
  .chapter-scroll {
    max-height: calc(100vh - 240px);
    padding: 18px;
  }

  .chapter-heading {
    font-size: 28px;
  }
}
</style>
