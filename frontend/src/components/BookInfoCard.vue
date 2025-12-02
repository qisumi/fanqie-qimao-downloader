<script setup>
import { computed, inject } from 'vue'
import { 
  NButton, NIcon, NTag, NProgress, NImage, NPopconfirm 
} from 'naive-ui'
import { 
  DownloadOutline, RefreshOutline, 
  TrashOutline, BookOutline, DocumentOutline
} from '@vicons/ionicons5'

const props = defineProps({
  book: {
    type: Object,
    required: true
  },
  downloadLoading: {
    type: Boolean,
    default: false
  },
  updateLoading: {
    type: Boolean,
    default: false
  },
  generating: {
    type: Boolean,
    default: false
  },
  taskProgress: {
    type: Object,
    default: null
  }
})

const emit = defineEmits([
  'download', 
  'update', 
  'generate-epub', 
  'download-epub', 
  'delete'
])

const isMobile = inject('isMobile', { value: false })

function getPlatformTag(platform) {
  return platform === 'fanqie' 
    ? { type: 'warning', label: '番茄小说' }
    : { type: 'info', label: '七猫小说' }
}

function getStatusTag(status) {
  const map = {
    'completed': { type: 'success', label: '已完成' },
    'downloading': { type: 'info', label: '下载中' },
    'pending': { type: 'default', label: '未开始' },
    'failed': { type: 'error', label: '失败' }
  }
  return map[status] || { type: 'default', label: status }
}

function getStatusColor(status) {
  const statusInfo = getStatusTag(status)
  const colorMap = {
    'success': { color: '#18a05815', textColor: '#18a058' },
    'info': { color: '#2080f015', textColor: '#2080f0' },
    'error': { color: '#d0305015', textColor: '#d03050' },
    'default': { color: '#90939915', textColor: '#909399' }
  }
  return colorMap[statusInfo.type] || colorMap['default']
}

const progressDownloaded = computed(() => {
  return props.taskProgress?.downloaded 
    ?? props.book.task_downloaded_chapters 
    ?? props.book.downloaded_chapters 
    ?? 0
})

const progressTotal = computed(() => {
  return props.taskProgress?.total 
    ?? props.book.task_total_chapters 
    ?? props.book.total_chapters 
    ?? 0
})

const progressPercent = computed(() => {
  if (!progressTotal.value) return 0
  return Math.round((progressDownloaded.value / progressTotal.value) * 100)
})
</script>

<template>
  <div class="book-info-card">
    <div class="book-layout" :class="{ 'mobile': isMobile }">
      <!-- 封面 -->
      <div class="cover-section">
        <n-image 
          v-if="book.cover_url"
          :src="book.cover_url" 
          :width="isMobile ? 120 : 160"
          object-fit="cover"
          class="book-cover"
        />
        <div v-else class="cover-placeholder" :style="{ width: isMobile ? '120px' : '160px', height: isMobile ? '165px' : '220px' }">
          <n-icon :size="48" color="#ccc"><BookOutline /></n-icon>
        </div>
        
        <!-- 平台标签 -->
        <span class="platform-badge" :class="book.platform">
          {{ getPlatformTag(book.platform).label }}
        </span>
      </div>
      
      <!-- 信息 -->
      <div class="info-section">
        <div class="book-header">
          <h1 class="book-title">{{ book.title }}</h1>
          <n-tag 
            :bordered="false"
            :color="getStatusColor(book.download_status)"
            size="small"
            round
          >
            {{ getStatusTag(book.download_status).label }}
          </n-tag>
        </div>
        
        <div class="book-author">✍️ {{ book.author || '未知作者' }}</div>
        
        <div class="book-stats">
          <div class="stat-item">
            <span class="stat-label">章节</span>
            <span class="stat-value">{{ progressDownloaded }}<span class="stat-divider">/</span>{{ progressTotal }}</span>
          </div>
          <div class="stat-item" v-if="book.word_count">
            <span class="stat-label">字数</span>
            <span class="stat-value">{{ (book.word_count / 10000).toFixed(1) }}万</span>
          </div>
          <div class="stat-item" v-if="book.creation_status">
            <span class="stat-label">状态</span>
            <span class="stat-value">{{ book.creation_status }}</span>
          </div>
        </div>
        
        <!-- 下载进度 -->
        <div v-if="(progressTotal || 0) > 0" class="progress-section">
          <n-progress 
            type="line" 
            :percentage="progressPercent"
            :show-indicator="false"
            :height="8"
            :border-radius="4"
            :color="book.download_status === 'completed' ? '#18a058' : '#2080f0'"
          />
          <span class="progress-text">{{ progressPercent }}%</span>
        </div>
      </div>
    </div>
    
    <!-- 操作按钮区域 -->
    <div class="action-buttons" :class="{ 'mobile': isMobile }">
      <n-button 
        type="primary" 
        :size="isMobile ? 'medium' : 'large'"
        @click="emit('download')"
        :loading="downloadLoading"
        :disabled="book.download_status === 'downloading'"
        class="action-btn primary-btn"
      >
        <template #icon>
          <n-icon><DownloadOutline /></n-icon>
        </template>
        {{ book.download_status === 'completed' ? '重新下载' : '开始下载' }}
      </n-button>
      
      <n-button 
        v-if="book.download_status === 'completed'"
        :size="isMobile ? 'medium' : 'large'"
        @click="emit('update')"
        :loading="updateLoading"
        class="action-btn"
      >
        <template #icon>
          <n-icon><RefreshOutline /></n-icon>
        </template>
        检查更新
      </n-button>
      
      <n-button 
        v-if="book.download_status === 'completed'"
        :size="isMobile ? 'medium' : 'large'"
        @click="emit('generate-epub')"
        :loading="generating"
        class="action-btn"
      >
        <template #icon>
          <n-icon><DocumentOutline /></n-icon>
        </template>
        生成 EPUB
      </n-button>
      
      <n-button 
        v-if="book.epub_path"
        type="success"
        :size="isMobile ? 'medium' : 'large'"
        @click="emit('download-epub')"
        class="action-btn"
      >
        下载 EPUB
      </n-button>
      
      <n-popconfirm @positive-click="emit('delete')">
        <template #trigger>
          <n-button 
            type="error" 
            quaternary
            :size="isMobile ? 'medium' : 'large'"
            class="action-btn delete-btn"
          >
            <template #icon>
              <n-icon><TrashOutline /></n-icon>
            </template>
            删除
          </n-button>
        </template>
        确定要删除这本书吗？所有已下载的章节都将被删除。
      </n-popconfirm>
    </div>
  </div>
</template>

<style scoped>
/* 书籍信息卡片 */
.book-info-card {
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-xl, 16px);
  padding: 24px;
  box-shadow: var(--shadow-card);
  margin-bottom: 20px;
}

.book-layout {
  display: flex;
  gap: 24px;
}

.book-layout.mobile {
  flex-direction: column;
  align-items: center;
  text-align: center;
}

/* 封面区域 */
.cover-section {
  position: relative;
  flex-shrink: 0;
}

.book-cover {
  border-radius: var(--border-radius-lg, 12px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.cover-placeholder {
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  border-radius: var(--border-radius-lg, 12px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.platform-badge {
  position: absolute;
  top: -8px;
  left: -8px;
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  border-radius: 6px 6px 12px 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.platform-badge.fanqie {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
}

.platform-badge.qimao {
  background: linear-gradient(135deg, #2080f0 0%, #409eff 100%);
}

/* 信息区域 */
.info-section {
  flex: 1;
  min-width: 0;
}

.book-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.book-layout.mobile .book-header {
  justify-content: center;
}

.book-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: var(--text-color-primary, #333);
}

.book-author {
  font-size: 14px;
  color: var(--text-color-secondary, #666);
  margin-bottom: 16px;
}

.book-stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.book-layout.mobile .book-stats {
  justify-content: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-color-tertiary, #999);
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
}

.stat-divider {
  margin: 0 2px;
  color: #ccc;
}

/* 进度区域 */
.progress-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.progress-section :deep(.n-progress) {
  flex: 1;
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color-secondary, #666);
  flex-shrink: 0;
}

/* 操作按钮区域 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color-light, #efeff5);
}

.action-buttons.mobile {
  flex-direction: column;
}

.action-btn {
  transition: transform var(--transition-fast, 0.15s);
}

.action-btn:hover {
  transform: translateY(-2px);
}

.action-buttons.mobile .action-btn {
  width: 100%;
}

.primary-btn {
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
  border: none;
}

.delete-btn:hover {
  background: rgba(208, 48, 80, 0.1);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .book-info-card {
    padding: 16px;
  }
  
  .book-title {
    font-size: 20px;
  }
  
  .book-stats {
    gap: 16px;
  }
}
</style>
