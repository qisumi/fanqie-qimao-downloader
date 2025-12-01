<script setup>
import { computed } from 'vue'
import { 
  NCard, NSpace, NButton, NIcon, NTag, NProgress, NImage, NPopconfirm
} from 'naive-ui'
import { 
  DownloadOutline, TrashOutline, BookOutline, ChevronForwardOutline,
  BookmarkOutline, Bookmark
} from '@vicons/ionicons5'

const props = defineProps({
  book: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  },
  canToggleShelf: {
    type: Boolean,
    default: false
  },
  inShelf: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'download', 'delete', 'toggle-shelf'])

const progress = computed(() => {
  if (!props.book.total_chapters) return 0
  return Math.round((props.book.downloaded_chapters / props.book.total_chapters) * 100)
})

const platformTag = computed(() => {
  return props.book.platform === 'fanqie' 
    ? { color: '#ff6b35', label: '番茄' }
    : { color: '#2080f0', label: '七猫' }
})

const statusTag = computed(() => {
  const map = {
    'completed': { type: 'success', label: '已完成', color: '#18a058' },
    'downloading': { type: 'info', label: '下载中', color: '#2080f0' },
    'pending': { type: 'default', label: '未开始', color: '#909399' },
    'failed': { type: 'error', label: '失败', color: '#d03050' }
  }
  return map[props.book.download_status] || { type: 'default', label: '未知', color: '#909399' }
})

const isDownloading = computed(() => props.book.download_status === 'downloading')
const isCompleted = computed(() => props.book.download_status === 'completed')
const shelfIcon = computed(() => props.inShelf ? Bookmark : BookmarkOutline)
const shelfLabel = computed(() => props.inShelf ? '移出' : '收藏')

function handleClick() {
  emit('click')
}

function handleDownload(e) {
  e.stopPropagation()
  emit('download')
}

function handleDelete() {
  emit('delete')
}

function handleToggleShelf(e) {
  e.stopPropagation()
  emit('toggle-shelf')
}
</script>

<template>
  <div class="book-card" :class="{ 'compact': compact }" @click="handleClick">
    <!-- 封面 -->
    <div class="book-cover">
      <n-image 
        v-if="book.cover_url"
        :src="book.cover_url" 
        :width="compact ? 70 : 90"
        :height="compact ? 95 : 125"
        object-fit="cover"
        preview-disabled
        lazy
      />
      <div v-else class="cover-placeholder">
        <n-icon :size="compact ? 28 : 36" color="#ccc"><BookOutline /></n-icon>
      </div>
      
      <!-- 平台标签 -->
      <span class="platform-badge" :style="{ background: platformTag.color }">
        {{ platformTag.label }}
      </span>
    </div>
    
    <!-- 信息区域 -->
    <div class="book-info">
      <div class="book-header">
        <span class="book-title">{{ book.title }}</span>
        <n-tag 
          :bordered="false" 
          :color="{ color: statusTag.color + '15', textColor: statusTag.color }"
          size="small"
          round
          class="status-tag"
        >
          {{ statusTag.label }}
        </n-tag>
      </div>
      
      <div class="book-author">{{ book.author }}</div>
      
      <div class="book-meta">
        <span class="meta-item">
          <span class="meta-value">{{ book.downloaded_chapters }}</span>
          <span class="meta-divider">/</span>
          <span class="meta-total">{{ book.total_chapters }}</span>
          <span class="meta-label">章</span>
        </span>
        <span v-if="book.word_count" class="meta-item">
          {{ (book.word_count / 10000).toFixed(1) }}万字
        </span>
      </div>
      
      <!-- 进度条 -->
      <div v-if="book.total_chapters > 0" class="progress-wrapper">
        <n-progress 
          type="line" 
          :percentage="progress"
          :show-indicator="false"
          :height="6"
          :border-radius="3"
          :color="isDownloading ? '#2080f0' : isCompleted ? '#18a058' : '#909399'"
          rail-color="rgba(0,0,0,0.06)"
        />
        <span class="progress-text">{{ progress }}%</span>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="book-actions">
      <n-button 
        :size="compact ? 'small' : 'medium'"
        type="primary"
        :disabled="isDownloading"
        :quaternary="isCompleted"
        @click="handleDownload"
        class="action-btn"
      >
        <template #icon>
          <n-icon><DownloadOutline /></n-icon>
        </template>
        <span v-if="!compact" class="action-text">
          {{ isCompleted ? '重下' : '下载' }}
        </span>
      </n-button>

      <n-button
        v-if="canToggleShelf"
        :size="compact ? 'small' : 'medium'"
        quaternary
        type="default"
        @click="handleToggleShelf"
        class="action-btn"
      >
        <template #icon>
          <n-icon><component :is="shelfIcon" /></n-icon>
        </template>
        <span v-if="!compact" class="action-text">{{ shelfLabel }}</span>
      </n-button>
      
      <n-popconfirm 
        @positive-click="handleDelete"
        positive-text="确认删除"
        negative-text="取消"
      >
        <template #trigger>
          <n-button 
            :size="compact ? 'small' : 'medium'"
            type="error" 
            quaternary
            @click.stop
            class="action-btn delete-btn"
          >
            <template #icon>
              <n-icon><TrashOutline /></n-icon>
            </template>
          </n-button>
        </template>
        确定要删除《{{ book.title }}》吗？
      </n-popconfirm>
      
      <!-- 进入详情箭头 -->
      <n-icon class="arrow-icon" :size="20" color="#ccc">
        <ChevronForwardOutline />
      </n-icon>
    </div>
  </div>
</template>

<style scoped>
.book-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all var(--transition-base, 0.25s);
}

.book-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.book-card.compact {
  padding: 12px;
  gap: 12px;
}

/* 封面 */
.book-cover {
  position: relative;
  flex-shrink: 0;
}

.book-cover :deep(.n-image) {
  border-radius: var(--border-radius-md, 8px);
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.cover-placeholder {
  width: 90px;
  height: 125px;
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  border-radius: var(--border-radius-md, 8px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.compact .cover-placeholder {
  width: 70px;
  height: 95px;
}

.platform-badge {
  position: absolute;
  top: -4px;
  left: -4px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
  color: white;
  border-radius: 4px 4px 8px 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

/* 信息区域 */
.book-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.book-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.book-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.compact .book-title {
  font-size: 15px;
}

.status-tag {
  flex-shrink: 0;
}

.book-author {
  font-size: 13px;
  color: var(--text-color-secondary, #666);
}

.book-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-color-tertiary, #999);
}

.meta-item {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.meta-value {
  font-weight: 600;
  color: var(--primary-color, #18a058);
}

.meta-divider {
  margin: 0 1px;
}

.meta-total {
  color: var(--text-color-tertiary, #999);
}

.meta-label {
  margin-left: 2px;
}

/* 进度条 */
.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.progress-wrapper :deep(.n-progress) {
  flex: 1;
}

.progress-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-color-tertiary, #999);
  flex-shrink: 0;
  width: 36px;
  text-align: right;
}

/* 操作按钮 */
.book-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  transition: transform var(--transition-fast, 0.15s);
}

.action-btn:hover {
  transform: scale(1.05);
}

.delete-btn:hover {
  background-color: rgba(208, 48, 80, 0.08);
}

.action-text {
  margin-left: 4px;
}

.arrow-icon {
  margin-left: 4px;
  transition: transform var(--transition-fast, 0.15s);
}

.book-card:hover .arrow-icon {
  transform: translateX(4px);
  color: var(--primary-color, #18a058);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .book-card {
    gap: 12px;
  }
  
  .book-meta {
    font-size: 12px;
    gap: 12px;
  }
  
  .action-text {
    display: none;
  }
  
  .arrow-icon {
    display: none;
  }
}
</style>
