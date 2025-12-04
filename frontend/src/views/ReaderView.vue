<script setup>
/**
 * ReaderView - 阅读器主视图
 * 拆分逻辑到 composables 保持文件精简
 */
import { NSpin, NBackTop } from 'naive-ui'
import {
  ReaderToolbar,
  ReaderTocDrawer,
  ReaderSettingsDrawer,
  ReaderFooter,
  ReaderScrollContent,
  ReaderPageContent,
  ReaderEpubContent
} from '@/components/reader'
import { useReaderView } from './reader/useReaderView'

const {
  tocVisible,
  settingsVisible,
  initializing,
  isMobile,
  showChrome,
  isScrollMode,
  isPageMode,
  isEpubMode,
  isFullscreen,
  caching,
  readerSettings,
  textColor,
  backgroundColor,
  backgroundStyle,
  readerContentStyle,
  paragraphStyle,
  pagePanelStyle,
  currentBookTitle,
  chapterLabel,
  cacheStatus,
  scrollContentRef,
  epubContainerRef,
  multiChapterMode,
  readerStore,
  chapterComposable,
  progressComposable,
  pageComposable,
  epubComposable,
  ttsComposable,
  handleContentTap,
  handleSelectChapter,
  reloadChapter,
  handlePrev,
  handleNext,
  changeMode,
  handleUpdateSetting,
  toggleFullscreen,
  addBookmarkAtCurrent,
  handleCacheEpub,
  handleToggleTts,
  handleProgressChange,
  handleScroll,
  handlePageChanged,
  handleChapterChanged,
  handleNeedMoreChapters,
  handleReachEdge,
  handlePageResize,
  goBack
} = useReaderView()
</script>

<template>
  <div class="reader-view" :style="backgroundStyle" :class="{ 'is-mobile': isMobile }">
    <!-- 工具栏 -->
    <ReaderToolbar
      :is-mobile="isMobile"
      :show-chrome="showChrome"
      :is-scroll-mode="isScrollMode"
      :is-page-mode="isPageMode"
      :is-epub-mode="isEpubMode"
      :is-fullscreen="isFullscreen"
      :is-loading-chapter="chapterComposable.isLoadingChapter.value"
      :current-book-title="currentBookTitle"
      :chapter-label="chapterLabel"
      :display-percent="progressComposable.displayPercent.value"
      :has-prev="!!chapterComposable.currentChapter.value?.prev_id"
      :has-next="!!chapterComposable.currentChapter.value?.next_id"
      :tts-state="ttsComposable.ttsState.value"
      :caching="caching"
      :epub-cached="cacheStatus.epub_cached"
      @back="goBack"
      @open-toc="tocVisible = true"
      @open-settings="settingsVisible = true"
      @reload="reloadChapter"
      @prev="handlePrev"
      @next="handleNext"
      @change-mode="changeMode"
      @toggle-fullscreen="toggleFullscreen"
      @add-bookmark="addBookmarkAtCurrent"
      @cache-epub="handleCacheEpub"
      @toggle-tts="handleToggleTts"
      @progress-change="handleProgressChange"
    />

    <div class="reader-body">
      <!-- 目录抽屉 -->
      <ReaderTocDrawer
        v-model:visible="tocVisible"
        :is-mobile="isMobile"
        :toc="chapterComposable.toc.value"
        :total="readerStore.tocTotal"
        :loading="readerStore.tocLoading"
        :has-more-next="readerStore.tocHasMoreNext"
        :has-more-prev="readerStore.tocHasMorePrev"
        :current-chapter-id="readerStore.currentChapterId"
        :current-book-title="currentBookTitle"
        :cached-chapters="cacheStatus.cached_chapters"
        @load-more-next="readerStore.loadMoreTocDown"
        @load-more-prev="readerStore.loadMoreTocUp"
        @select-chapter="handleSelectChapter"
      />

      <!-- 设置抽屉 -->
      <ReaderSettingsDrawer
        v-model:visible="settingsVisible"
        :is-mobile="isMobile"
        :settings="readerSettings"
        :is-scroll-mode="isScrollMode"
        :is-page-mode="isPageMode"
        :is-epub-mode="isEpubMode"
        :is-fullscreen="isFullscreen"
        :background-color="backgroundColor"
        :text-color="textColor"
        @update-setting="handleUpdateSetting"
        @change-mode="changeMode"
        @toggle-fullscreen="toggleFullscreen"
        @reset-settings="readerStore.resetSettings()"
      />

      <!-- 内容区域 -->
      <div class="reader-content" :class="{ 'mobile-content': isMobile }" @click="handleContentTap">
        <n-spin :show="initializing || chapterComposable.isLoadingChapter.value || (isEpubMode && epubComposable.epubLoading.value)">
          <!-- EPUB模式 -->
          <template v-if="isEpubMode">
            <ReaderEpubContent
              v-model:epub-container-ref="epubContainerRef"
              :error="epubComposable.epubError.value"
            />
          </template>

          <!-- 翻页模式 -->
          <template v-else-if="isPageMode">
            <ReaderPageContent
              :is-mobile="isMobile"
              :page-chunks="pageComposable.pageChunks.value"
              :page-panel-style="pagePanelStyle"
              :reader-content-style="readerContentStyle"
              :paragraph-style="paragraphStyle"
              :chapter-title="chapterComposable.currentChapter.value?.title || ''"
              :chapter-boundaries="pageComposable.chapterBoundaries.value"
              :multi-chapter-mode="multiChapterMode"
              :has-next-chapter="!!chapterComposable.currentChapter.value?.next_id"
              :has-prev-chapter="!!chapterComposable.currentChapter.value?.prev_id"
              :current-page-index="pageComposable.currentPageIndex.value"
              @page-changed="handlePageChanged"
              @chapter-changed="handleChapterChanged"
              @need-more-chapters="handleNeedMoreChapters"
              @reach-edge="handleReachEdge"
              @resize="handlePageResize"
            />
          </template>

          <!-- 滚动模式 -->
          <template v-else>
            <ReaderScrollContent
              ref="scrollContentRef"
              :is-mobile="isMobile"
              :display-chapters="chapterComposable.displayChapters.value"
              :has-content="chapterComposable.hasContent.value"
              :is-fetching="chapterComposable.isFetching.value"
              :error="readerStore.error"
              :initializing="initializing"
              :is-loading-chapter="chapterComposable.isLoadingChapter.value"
              :current-book-title="currentBookTitle"
              :current-chapter-id="readerStore.currentChapterId"
              :reader-content-style="readerContentStyle"
              :paragraph-style="paragraphStyle"
              @scroll="handleScroll"
              @reload="reloadChapter"
              @register-ref="chapterComposable.registerChapterRef"
            />
          </template>
        </n-spin>
      </div>
    </div>

    <!-- 移动端底部控制栏 -->
    <ReaderFooter
      :visible="showChrome"
      :is-mobile="isMobile"
      :current-chapter="chapterComposable.currentChapter.value"
      :display-percent="progressComposable.displayPercent.value"
      :is-loading-chapter="chapterComposable.isLoadingChapter.value"
      :tts-state="ttsComposable.ttsState.value"
      :caching="caching"
      :epub-cached="cacheStatus.epub_cached"
      @prev="handlePrev"
      @next="handleNext"
      @add-bookmark="addBookmarkAtCurrent"
      @cache-epub="handleCacheEpub"
      @toggle-tts="handleToggleTts"
      @stop-tts="ttsComposable.stopTts"
      @progress-change="handleProgressChange"
    />

    <n-back-top
      v-if="isScrollMode"
      :right="24"
      :bottom="isMobile ? 96 : 32"
      listen-to=".chapter-scroll"
    />
  </div>
</template>

<style scoped>
.reader-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 12px 12px 24px;
  box-sizing: border-box;
}

.reader-view:not(.is-mobile) {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 24px;
  padding: 0 12px 0 0;
  height: 100vh;
  min-height: unset;
}

.reader-view.is-mobile {
  padding: 0;
  overflow: hidden;
  height: 100vh;
  min-height: unset;
}

.reader-body {
  display: flex;
  gap: 12px;
  margin-top: 0;
  flex: 1;
  min-height: 0; /* 允许 flex 子元素收缩，确保内部滚动正常 */
  justify-content: center;
}

.reader-view.is-mobile .reader-body {
  margin-top: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.reader-content {
  flex: 1;
  width: 100%;
  max-width: 960px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  /* 桌面端需要明确高度以支持内部滚动 */
  height: calc(100vh - 24px);
  min-height: 0; /* 允许 flex 子元素收缩 */
  overflow: hidden;
  overflow-anchor: none;
  display: flex;
  flex-direction: column;
}

/* n-spin 需要撑满父容器以传递高度 */
.reader-content :deep(.n-spin-container),
.reader-content :deep(.n-spin-content) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.reader-view.is-mobile .reader-content {
  height: 100%;
  max-width: none;
  overflow: hidden;
  padding: 0;
}

.reader-content.mobile-content {
  background: transparent;
  box-shadow: none;
  padding: 0;
}

@media (max-width: 768px) {
  .reader-view {
    padding: 0;
  }

  .reader-content {
    height: 100%;
  }
}
</style>

<style>
/* 工具栏响应式样式 - 需要全局以覆盖子组件 */
.reader-view.is-mobile .reader-toolbar {
  padding: 10px 12px;
  top: 0;
  position: fixed;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  transition: transform 0.3s ease;
}

.reader-view:not(.is-mobile) .reader-toolbar {
  flex-direction: column;
  width: 80px;
  padding: 16px 10px;
  height: calc(100vh - 24px);
  position: sticky;
  top: 12px;
  align-self: flex-start;
  gap: 16px;
  justify-content: flex-start;
}

.reader-view:not(.is-mobile) .toolbar-group {
  flex-direction: column;
  width: 100%;
}

.reader-view:not(.is-mobile) .toolbar-group.center {
  flex: 1;
  justify-content: center;
  gap: 16px;
}

.reader-view:not(.is-mobile) .toolbar-group.bottom {
  margin-top: auto;
  gap: 16px;
}

.reader-view:not(.is-mobile) .mode-switch {
  flex-direction: column;
  width: 100%;
  padding: 8px 6px;
}

.reader-view.is-mobile .toolbar-group.top {
  justify-content: space-between;
  width: 100%;
}

.reader-view.is-mobile .toolbar-group.center {
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}

.reader-view.is-mobile .toolbar-group.bottom {
  display: none;
}

.reader-view.is-mobile .mode-switch {
  width: 100%;
  justify-content: center;
  padding: 6px 8px;
}

.reader-view.is-mobile .chapter-title {
  max-width: 60vw;
}
</style>
