<script setup>
import { inject } from 'vue'
import { NButton, NIcon, NImage, NTag } from 'naive-ui'
import { AddOutline, BookOutline } from '@vicons/ionicons5'

const props = defineProps({
  book: {
    type: Object,
    required: true
  },
  platform: {
    type: String,
    required: true
  },
  adding: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['add'])

const isMobile = inject('isMobile', { value: false })

function getPlatformLabel(value) {
  return value === 'fanqie' ? '番茄小说' : '七猫小说'
}

function getIntroText() {
  const intro = props.book.abstract || props.book.intro
  if (!intro) return ''
  const maxLen = isMobile.value ? 60 : 100
  return intro.length > maxLen ? intro.substring(0, maxLen) + '...' : intro
}
</script>

<template>
  <div class="book-item">
    <!-- 封面 -->
    <div class="book-cover">
      <n-image 
        v-if="book.cover_url"
        :src="book.cover_url" 
        :width="isMobile ? 70 : 80"
        :height="isMobile ? 95 : 110"
        object-fit="cover"
        preview-disabled
        lazy
      />
      <div v-else class="cover-placeholder">
        <n-icon :size="28" color="#ccc"><BookOutline /></n-icon>
      </div>
    </div>
    
    <!-- 书籍信息 -->
    <div class="book-info">
      <div class="book-header">
        <span class="book-title">{{ book.book_name || book.title }}</span>
        <n-tag 
          :type="platform === 'fanqie' ? 'warning' : 'info'" 
          size="small"
          :bordered="false"
          class="platform-tag"
        >
          {{ getPlatformLabel(platform) }}
        </n-tag>
      </div>
      
      <div class="book-meta">
        <span class="author">{{ book.author }}</span>
        <span v-if="book.word_count" class="word-count">
          {{ (book.word_count / 10000).toFixed(1) }}万字
        </span>
        <span v-if="book.creation_status || book.status" class="status">
          {{ book.creation_status || book.status }}
        </span>
      </div>
      
      <div class="book-intro" v-if="book.abstract || book.intro">
        {{ getIntroText() }}
      </div>
    </div>
    
    <!-- 添加按钮 -->
    <n-button 
      type="primary" 
      :size="isMobile ? 'small' : 'medium'"
      :loading="adding"
      @click.stop="emit('add', book)"
      class="add-btn"
    >
      <template #icon>
        <n-icon><AddOutline /></n-icon>
      </template>
      <span class="hide-mobile">添加</span>
    </n-button>
  </div>
</template>

<style scoped>
.book-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: var(--bg-color-tertiary, #fafafa);
  border-radius: var(--border-radius-md, 8px);
  transition: all var(--transition-base);
}

.book-item:hover {
  background: #f0f5ff;
  transform: translateX(4px);
}

.book-cover {
  flex-shrink: 0;
}

.book-cover :deep(.n-image) {
  border-radius: var(--border-radius-sm, 4px);
  overflow: hidden;
}

.cover-placeholder {
  width: 80px;
  height: 110px;
  background: #f0f0f0;
  border-radius: var(--border-radius-sm, 4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

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
  flex-wrap: wrap;
}

.book-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
}

.platform-tag {
  flex-shrink: 0;
}

.book-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
  color: var(--text-color-secondary, #666);
}

.author::before {
  content: '✍️ ';
}

.word-count::before {
  content: '📖 ';
}

.status {
  color: var(--success-color, #18a058);
}

.book-intro {
  font-size: 13px;
  color: var(--text-color-tertiary, #999);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.add-btn {
  flex-shrink: 0;
  align-self: center;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .book-item {
    padding: 12px;
    gap: 12px;
  }
  
  .cover-placeholder {
    width: 70px;
    height: 95px;
  }
  
  .book-title {
    font-size: 15px;
  }
  
  .book-meta {
    font-size: 12px;
    gap: 8px;
  }
  
  .book-intro {
    font-size: 12px;
  }
  
  .add-btn {
    padding: 0 12px;
  }
  
  .hide-mobile {
    display: none;
  }
}
</style>
