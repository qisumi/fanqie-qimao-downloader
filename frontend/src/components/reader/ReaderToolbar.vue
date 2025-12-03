<script setup>
/**
 * 阅读器工具栏组件
 * 包含模式切换、设置、目录等按钮
 */
import {
  NButton,
  NIcon,
  NTooltip,
  NSlider
} from 'naive-ui'
import {
  ChevronBackOutline,
  ListOutline,
  RefreshOutline,
  PlaySkipBackOutline,
  PlaySkipForwardOutline,
  BookOutline,
  SwapVerticalOutline,
  SwapHorizontalOutline,
  DocumentTextOutline,
  SettingsOutline,
  ExpandOutline,
  ContractOutline,
  BookmarkOutline,
  CloudDownloadOutline,
  PauseOutline,
  PlayOutline
} from '@vicons/ionicons5'

const props = defineProps({
  isMobile: { type: Boolean, default: false },
  showChrome: { type: Boolean, default: true },
  isScrollMode: { type: Boolean, default: true },
  isPageMode: { type: Boolean, default: false },
  isEpubMode: { type: Boolean, default: false },
  isFullscreen: { type: Boolean, default: false },
  isLoadingChapter: { type: Boolean, default: false },
  currentBookTitle: { type: String, default: '' },
  chapterLabel: { type: String, default: '' },
  displayPercent: { type: Number, default: 0 },
  hasPrev: { type: Boolean, default: false },
  hasNext: { type: Boolean, default: false },
  ttsState: { type: String, default: 'idle' },
  caching: { type: Boolean, default: false },
  epubCached: { type: Boolean, default: false }
})

const emit = defineEmits([
  'back',
  'open-toc',
  'open-settings',
  'reload',
  'prev',
  'next',
  'change-mode',
  'toggle-fullscreen',
  'add-bookmark',
  'cache-epub',
  'toggle-tts',
  'progress-change'
])

function handleProgressChange(value) {
  emit('progress-change', value)
}
</script>

<template>
  <header class="reader-toolbar" v-show="showChrome">
    <div class="toolbar-group top">
      <n-button quaternary circle size="large" @click="$emit('back')">
        <template #icon>
          <n-icon :size="20"><ChevronBackOutline /></n-icon>
        </template>
      </n-button>
      <div class="toolbar-titles" v-if="isMobile">
        <div class="book-title">
          <n-icon :size="16"><BookOutline /></n-icon>
          <span class="book-name">{{ currentBookTitle }}</span>
        </div>
        <div class="chapter-title">{{ chapterLabel }}</div>
      </div>
    </div>

    <div class="toolbar-group center">
      <div class="mode-switch">
        <n-tooltip trigger="hover" placement="right">
          <template #trigger>
            <n-button
              quaternary
              circle
              size="large"
              :type="isScrollMode ? 'primary' : 'default'"
              @click="$emit('change-mode', 'scroll')"
            >
              <template #icon>
                <n-icon :size="18"><SwapVerticalOutline /></n-icon>
              </template>
            </n-button>
          </template>
          滚动模式
        </n-tooltip>
        <n-tooltip trigger="hover" placement="right">
          <template #trigger>
            <n-button
              quaternary
              circle
              size="large"
              :type="isPageMode ? 'primary' : 'default'"
              :disabled="!isMobile"
              @click="$emit('change-mode', 'page')"
            >
              <template #icon>
                <n-icon :size="18"><SwapHorizontalOutline /></n-icon>
              </template>
            </n-button>
          </template>
          翻页模式
        </n-tooltip>
        <n-tooltip trigger="hover" placement="right">
          <template #trigger>
            <n-button
              quaternary
              circle
              size="large"
              :type="isEpubMode ? 'primary' : 'default'"
              @click="$emit('change-mode', 'epub')"
            >
              <template #icon>
                <n-icon :size="18"><DocumentTextOutline /></n-icon>
              </template>
            </n-button>
          </template>
          EPUB 模式
        </n-tooltip>
      </div>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle size="large" @click="$emit('open-settings')">
            <template #icon>
              <n-icon :size="20"><SettingsOutline /></n-icon>
            </template>
          </n-button>
        </template>
        阅读设置
      </n-tooltip>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle size="large" @click="$emit('toggle-fullscreen')">
            <template #icon>
              <n-icon :size="20">
                <component :is="isFullscreen ? ContractOutline : ExpandOutline" />
              </n-icon>
            </template>
          </n-button>
        </template>
        {{ isFullscreen ? '退出全屏' : '进入全屏' }}
      </n-tooltip>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle size="large" @click="$emit('open-toc')">
            <template #icon>
              <n-icon :size="20"><ListOutline /></n-icon>
            </template>
          </n-button>
        </template>
        目录
      </n-tooltip>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button quaternary circle size="large" :loading="isLoadingChapter" @click="$emit('reload')">
            <template #icon>
              <n-icon :size="20"><RefreshOutline /></n-icon>
            </template>
          </n-button>
        </template>
        重新加载
      </n-tooltip>

      <template v-if="!isMobile">
        <div class="toolbar-divider"></div>
        <n-tooltip trigger="hover" placement="right">
          <template #trigger>
            <n-button quaternary circle size="large" @click="$emit('add-bookmark')">
              <template #icon><n-icon :size="20"><BookmarkOutline /></n-icon></template>
            </n-button>
          </template>
          添加书签
        </n-tooltip>
        <n-tooltip trigger="hover" placement="right">
          <template #trigger>
            <n-button quaternary circle size="large" :loading="caching" @click="$emit('cache-epub')">
              <template #icon><n-icon :size="20"><CloudDownloadOutline /></n-icon></template>
            </n-button>
          </template>
          {{ epubCached ? '已缓存 EPUB' : '缓存 EPUB' }}
        </n-tooltip>
        <n-tooltip trigger="hover" placement="right">
          <template #trigger>
            <n-button quaternary circle size="large" @click="$emit('toggle-tts')">
              <template #icon>
                <n-icon :size="20">
                  <component :is="ttsState === 'playing' ? PauseOutline : PlayOutline" />
                </n-icon>
              </template>
            </n-button>
          </template>
          {{ ttsState === 'playing' ? '暂停朗读' : (ttsState === 'paused' ? '继续朗读' : '朗读') }}
        </n-tooltip>
      </template>
    </div>

    <div class="toolbar-group bottom">
      <template v-if="!isMobile">
        <div class="pc-slider-container">
          <n-slider
            vertical
            :value="displayPercent"
            :step="1"
            :tooltip="true"
            :format-tooltip="(v) => `${Math.round(v)}%`"
            @update:value="handleProgressChange"
            style="height: 100px;"
          />
        </div>
      </template>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button secondary circle size="large" :disabled="!hasPrev || isLoadingChapter" @click="$emit('prev')">
            <template #icon>
              <n-icon :size="18"><PlaySkipBackOutline /></n-icon>
            </template>
          </n-button>
        </template>
        上一章
      </n-tooltip>
      <n-tooltip trigger="hover" placement="right">
        <template #trigger>
          <n-button type="primary" circle size="large" :disabled="!hasNext || isLoadingChapter" @click="$emit('next')">
            <template #icon>
              <n-icon :size="18"><PlaySkipForwardOutline /></n-icon>
            </template>
          </n-button>
        </template>
        下一章
      </n-tooltip>
    </div>
  </header>
</template>

<style scoped>
.reader-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(8px);
  position: sticky;
  top: 12px;
  z-index: 10;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-titles {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.book-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #5c5c5c;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.book-name {
  font-weight: 700;
}

.chapter-title {
  font-size: 16px;
  font-weight: 700;
  color: #161616;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mode-switch {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(24, 160, 88, 0.08);
  border-radius: 999px;
}

.pc-slider-container {
  display: flex;
  justify-content: center;
  padding: 10px 0;
}

.toolbar-divider {
  width: 24px;
  height: 1px;
  background-color: rgba(0, 0, 0, 0.1);
  margin: 4px 0;
}
</style>
