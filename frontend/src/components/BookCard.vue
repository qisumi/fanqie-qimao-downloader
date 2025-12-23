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
  const map = {
    fanqie: { color: '#ff6b35', label: '番茄' },
    qimao: { color: '#2080f0', label: '七猫' },
    biquge: { color: '#18a058', label: '笔趣阁' },
    local: { color: '#909399', label: '本地上传' }
  }
  return map[props.book.platform] || { color: '#909399', label: props.book.platform === 'local' ? '本地上传' : (props.book.platform || '未知') }
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

const coverBackground = computed(() => {
  const colors = [
    'linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)',
    'linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%)',
    'linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%)',
    'linear-gradient(120deg, #e0c3fc 0%, #8ec5fc 100%)',
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
  ]
  if (!props.book.title) return colors[0]
  let hash = 0
  for (let i = 0; i < props.book.title.length; i++) {
    hash = props.book.title.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
})

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
        :width="compact ? 70 : 100"
        :height="compact ? 95 : 135"
        object-fit="cover"
        preview-disabled
        lazy
      />
      <div v-else class="cover-placeholder" :style="{ background: coverBackground }">
        <div class="placeholder-content">
          <span class="placeholder-title">{{ book.title }}</span>
          <span class="placeholder-author">{{ book.author }}</span>
        </div>
      </div>
      
      <!-- 平台标签 -->
      <span class="platform-badge" :style="{ background: platformTag.color }">
        {{ platformTag.label }}
      </span>
    </div>
    
    <!-- 信息区域 -->
    <div class="book-info">
      <div class="info-top">
        <div class="book-header">
          <span class="book-title">{{ book.title }}</span>
          <n-tag 
            v-if="book.platform !== 'local'"
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
      </div>
      
      <div class="info-bottom">
        <div class="book-meta">
          <span class="meta-item">
            <template v-if="book.platform === 'local'">
              <span class="meta-total">{{ book.total_chapters }}</span>
            </template>
            <template v-else>
              <span class="meta-value">{{ book.downloaded_chapters }}</span>
              <span class="meta-divider">/</span>
              <span class="meta-total">{{ book.total_chapters }}</span>
            </template>
            <span class="meta-label">章</span>
          </span>
          <span v-if="book.word_count" class="meta-item">
            {{ (book.word_count / 10000).toFixed(1) }}万字
          </span>
        </div>
        
        <!-- 进度条 -->
        <div v-if="book.total_chapters > 0 && book.platform !== 'local'" class="progress-wrapper">
          <n-progress 
            type="line" 
            :percentage="progress"
            :show-indicator="false"
            :height="6"
            :border-radius="3"
            :color="isDownloading ? '#2080f0' : isCompleted ? '#18a058' : '#909399'"
            rail-color="rgba(0,0,0,0.06)"
            class="book-progress"
          />
          <span class="progress-text">{{ progress }}%</span>
        </div>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="book-actions">
      <n-button 
        v-if="book.platform !== 'local'"
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
        <span class="action-text">
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
        <span class="action-text">{{ shelfLabel }}</span>
      </n-button>
      
      <div class="action-bottom-row">
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
  </div>
</template>

<style scoped>
.book-card {
  display: flex;
  align-items: stretch;
  gap: 16px;
  padding: 16px;
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06), 0 4px 12px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: all var(--transition-base, 0.25s);
  height: 100%;
  box-sizing: border-box;
}

.book-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1), 0 8px 24px rgba(0, 0, 0, 0.05);
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
  display: flex;
  align-items: flex-start;
}

.book-cover :deep(.n-image) {
  border-radius: var(--border-radius-md, 6px);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0,0,0,0.05);
}

.cover-placeholder {
  width: 100px;
  height: 135px;
  border-radius: var(--border-radius-md, 6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  text-align: center;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.placeholder-title {
  font-size: 13px;
  font-weight: bold;
  color: #fff;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  overflow: hidden;
  word-break: break-all;
  text-shadow: 0 1px 2px rgba(0,0,0,0.15);
}

.placeholder-author {
  font-size: 11px;
  color: rgba(255,255,255,0.95);
  margin-top: 4px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  overflow: hidden;
  text-shadow: 0 1px 2px rgba(0,0,0,0.15);
}

.compact .cover-placeholder {
  width: 70px;
  height: 95px;
  padding: 4px;
}

.compact .placeholder-title {
  font-size: 10px;
  -webkit-line-clamp: 3;
  line-clamp: 3;
}

.compact .placeholder-author {
  display: none;
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
  z-index: 1;
}

/* 信息区域 */
.book-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 2px 0;
}

.info-top {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.book-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.book-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
  flex: 1;
}

.compact .book-title {
  font-size: 15px;
}

.status-tag {
  flex-shrink: 0;
  margin-top: 2px;
}

.book-author {
  font-size: 13px;
  color: var(--text-color-secondary, #666);
  line-height: 1.4;
}

.info-bottom {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
}

.book-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
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
  font-family: var(--font-family-mono, monospace);
}

.meta-divider {
  margin: 0 1px;
}

.meta-total {
  color: var(--text-color-tertiary, #999);
}

.meta-label {
  margin-left: 2px;
  font-size: 12px;
}

/* 进度条 */
.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-wrapper :deep(.n-progress).book-progress {
  max-width: 140px;
}

.progress-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-color-tertiary, #999);
  flex-shrink: 0;
  width: 36px;
  text-align: right;
  font-family: var(--font-family-mono, monospace);
}

/* 操作按钮 */
.book-actions {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-end;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 4px;
  padding-top: 2px;
}

.action-bottom-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: auto;
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
    padding: 12px;
    gap: 12px;
    flex-wrap: wrap;
    align-items: flex-start;
  }
  
  .book-header {
    gap: 6px;
  }
  
  .book-title {
    font-size: 15px;
    -webkit-line-clamp: 2;
    line-clamp: 2;
  }
  
  .book-meta {
    font-size: 12px;
    gap: 10px;
  }
  
  .info-bottom {
    padding-top: 8px;
    gap: 6px;
  }
  
  .progress-wrapper {
    margin-top: 0;
  }
  
  .book-actions {
    flex-direction: row;
    width: 100%;
    padding-top: 10px;
    border-top: 1px solid var(--divider-color, #f0f0f0);
    justify-content: space-between;
    gap: 10px;
    align-items: stretch;
    flex-wrap: wrap;
    margin-left: 0;
  }

  .action-bottom-row {
    flex: 1;
    display: flex;
    justify-content: center;
    margin-top: 0;
  }
  
  .book-actions > *:not(.action-bottom-row) {
    flex: 1;
    min-width: 0;
  }
  
  .book-actions :deep(.n-button) {
    width: 100%;
  }
  
  .book-actions :deep(.n-button__content) {
    justify-content: center;
  }
  
  .action-text {
    display: inline;
    margin-left: 6px;
  }
  
  .arrow-icon {
    display: none;
  }

  .progress-wrapper :deep(.n-progress).book-progress {
    max-width: none;
    flex: 1;
  }
}
</style>
