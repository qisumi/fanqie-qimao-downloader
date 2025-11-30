<script setup>
import { computed } from 'vue'
import { 
  NCard, NSpace, NButton, NIcon, NTag, NProgress, NImage
} from 'naive-ui'
import { 
  DownloadOutline, TrashOutline, BookOutline 
} from '@vicons/ionicons5'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'download', 'delete'])

const progress = computed(() => {
  if (!props.book.total_chapters) return 0
  return Math.round((props.book.downloaded_chapters / props.book.total_chapters) * 100)
})

const platformTag = computed(() => {
  return props.book.platform === 'fanqie' 
    ? { type: 'warning', label: '番茄' }
    : { type: 'info', label: '七猫' }
})

const statusTag = computed(() => {
  const map = {
    'completed': { type: 'success', label: '已完成' },
    'downloading': { type: 'info', label: '下载中' },
    'pending': { type: 'default', label: '未开始' },
    'failed': { type: 'error', label: '失败' }
  }
  return map[props.book.download_status] || { type: 'default', label: '未知' }
})

function handleClick() {
  emit('click')
}

function handleDownload(e) {
  e.stopPropagation()
  emit('download')
}

function handleDelete(e) {
  e.stopPropagation()
  emit('delete')
}
</script>

<template>
  <n-card hoverable @click="handleClick" style="cursor: pointer;">
    <n-space :size="16">
      <!-- 封面 -->
      <n-image 
        v-if="book.cover_url"
        :src="book.cover_url" 
        :width="80"
        :height="110"
        object-fit="cover"
        preview-disabled
        style="border-radius: 4px; flex-shrink: 0;"
      />
      <div 
        v-else 
        style="width: 80px; height: 110px; background: #f0f0f0; border-radius: 4px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;"
      >
        <n-icon :size="32" color="#ccc"><BookOutline /></n-icon>
      </div>
      
      <!-- 信息 -->
      <div style="flex: 1; min-width: 0;">
        <n-space :size="8" style="align-items: center;">
          <span style="font-size: 16px; font-weight: 500;">{{ book.title }}</span>
          <n-tag v-bind="platformTag" size="small">{{ platformTag.label }}</n-tag>
          <n-tag v-bind="statusTag" size="small">{{ statusTag.label }}</n-tag>
        </n-space>
        
        <div style="color: #666; margin-top: 4px;">
          作者: {{ book.author }}
        </div>
        
        <div style="color: #999; font-size: 13px; margin-top: 4px;">
          {{ book.downloaded_chapters }} / {{ book.total_chapters }} 章 
          <span v-if="book.word_count"> · {{ (book.word_count / 10000).toFixed(1) }}万字</span>
        </div>
        
        <!-- 进度条 -->
        <n-progress 
          v-if="book.total_chapters > 0"
          type="line" 
          :percentage="progress"
          :show-indicator="false"
          style="margin-top: 8px;"
        />
      </div>
      
      <!-- 操作按钮 -->
      <n-space :size="8" style="flex-shrink: 0;">
        <n-button 
          size="small" 
          type="primary"
          :disabled="book.download_status === 'completed'"
          @click="handleDownload"
        >
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
        </n-button>
        <n-button size="small" type="error" ghost @click="handleDelete">
          <template #icon>
            <n-icon><TrashOutline /></n-icon>
          </template>
        </n-button>
      </n-space>
    </n-space>
  </n-card>
</template>
