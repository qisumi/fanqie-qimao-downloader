<script setup>
/**
 * 移动端底部控制栏组件
 */
import {
  NButton,
  NIcon,
  NSlider
} from 'naive-ui'
import {
  BookmarkOutline,
  CloudDownloadOutline,
  PauseOutline,
  PlayOutline,
  VolumeMuteOutline,
  VolumeHighOutline
} from '@vicons/ionicons5'

const props = defineProps({
  visible: { type: Boolean, default: true },
  isMobile: { type: Boolean, default: false },
  currentChapter: { type: Object, default: null },
  displayPercent: { type: Number, default: 0 },
  isLoadingChapter: { type: Boolean, default: false },
  ttsState: { type: String, default: 'idle' },
  caching: { type: Boolean, default: false },
  epubCached: { type: Boolean, default: false }
})

const emit = defineEmits([
  'prev',
  'next',
  'add-bookmark',
  'cache-epub',
  'toggle-tts',
  'stop-tts',
  'progress-change'
])

const percentLabel = computed(() => `${Math.round(props.displayPercent)}%`)

import { computed } from 'vue'
</script>

<template>
  <footer class="reader-footer" :class="{ 'mobile-footer': isMobile }" v-show="visible && isMobile">
    <!-- 章节标题已包含"第X章"信息，无需额外显示索引 -->
    <div class="progress-head">
      <div class="progress-chapter">
        <span class="chapter-name">{{ currentChapter?.title || '未命名章节' }}</span>
      </div>
      <span class="progress-percent">{{ percentLabel }}</span>
    </div>
    <div class="aux-actions">
      <n-button size="small" ghost @click="$emit('add-bookmark')">
        <template #icon>
          <n-icon><BookmarkOutline /></n-icon>
        </template>
        书签
      </n-button>
      <n-button size="small" :loading="caching" ghost @click="$emit('cache-epub')">
        <template #icon>
          <n-icon><CloudDownloadOutline /></n-icon>
        </template>
        {{ epubCached ? '已缓存 EPUB' : '缓存 EPUB' }}
      </n-button>
      <n-button
        size="small"
        ghost
        @click="$emit('toggle-tts')"
      >
        <template #icon>
          <n-icon>
            <component
              :is="ttsState === 'playing' ? PauseOutline : (ttsState === 'paused' ? VolumeHighOutline : PlayOutline)"
            />
          </n-icon>
        </template>
        {{ ttsState === 'playing' ? '暂停朗读' : (ttsState === 'paused' ? '继续朗读' : '朗读') }}
      </n-button>
      <n-button size="small" quaternary @click="$emit('stop-tts')" :disabled="ttsState === 'idle'">
        <template #icon>
          <n-icon><VolumeMuteOutline /></n-icon>
        </template>
        停止
      </n-button>
    </div>
    <n-slider
      :value="displayPercent"
      :step="1"
      :tooltip="true"
      :format-tooltip="(v) => `${Math.round(v)}%`"
      @update:value="$emit('progress-change', $event)"
    />
  </footer>
</template>

<style scoped>
.reader-footer {
  margin-top: 16px;
  width: 100%;
  max-width: 960px;
  margin-left: auto;
  margin-right: auto;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 14px;
  padding: 12px 16px 16px;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
}

.reader-footer.mobile-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px 12px 24px; /* 增加底部 padding 适配全面屏手势 */
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(10px);
  margin: 0;
  border-radius: 16px 16px 0 0;
}

.aux-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.progress-chapter {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chapter-name {
  font-weight: 600;
  color: #1f1f1f;
  max-width: 70vw;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-percent {
  font-weight: 700;
  color: #18a058;
}
.reader-footer.mobile-footer .progress-head {
  align-items: flex-start;
}

.reader-footer.mobile-footer .aux-actions {
  justify-content: space-between;
}

.progress-line :deep(.n-progress) {
  width: 100%;
}

@media (max-width: 768px) {
  .aux-actions {
    gap: 6px;
  }

  .progress-actions {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto;
  }

  .progress-line {
    grid-column: 1 / span 2;
  }
}
</style>
