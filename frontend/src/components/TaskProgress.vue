<script setup>
import { computed } from 'vue'
import { 
  NCard, NSpace, NButton, NIcon, NTag, NProgress
} from 'naive-ui'
import { CloseOutline } from '@vicons/ionicons5'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['cancel'])

const progress = computed(() => {
  if (!props.task.total_chapters) return 0
  return Math.round((props.task.downloaded_chapters / props.task.total_chapters) * 100)
})

const statusTag = computed(() => {
  const map = {
    'running': { type: 'info', label: '运行中' },
    'pending': { type: 'warning', label: '等待中' },
    'completed': { type: 'success', label: '已完成' },
    'failed': { type: 'error', label: '失败' },
    'cancelled': { type: 'default', label: '已取消' }
  }
  return map[props.task.status] || { type: 'default', label: props.task.status }
})

const taskTypeLabel = computed(() => {
  return props.task.task_type === 'download' ? '下载' : '更新'
})

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <n-card size="small">
    <n-space justify="space-between" align="center">
      <div style="flex: 1; min-width: 0;">
        <n-space :size="8" style="align-items: center;">
          <span style="font-weight: 500; font-family: monospace; font-size: 12px;">{{ task.book_id }}</span>
          <n-tag v-bind="statusTag" size="small">{{ statusTag.label }}</n-tag>
          <n-tag size="small">{{ taskTypeLabel }}</n-tag>
        </n-space>
        
        <div style="color: #666; font-size: 13px; margin-top: 4px;">
          进度: {{ task.downloaded_chapters || 0 }} / {{ task.total_chapters || 0 }} 章
          <span v-if="task.failed_chapters > 0" style="color: #d03050;">
            ({{ task.failed_chapters }} 失败)
          </span>
        </div>
        
        <n-progress 
          type="line" 
          :percentage="progress"
          :status="task.status === 'failed' ? 'error' : 'default'"
          style="margin-top: 8px;"
        />
      </div>
      
      <n-button 
        v-if="task.status === 'running' || task.status === 'pending'"
        size="small" 
        type="error" 
        ghost
        @click="handleCancel"
      >
        <template #icon>
          <n-icon><CloseOutline /></n-icon>
        </template>
        取消
      </n-button>
    </n-space>
  </n-card>
</template>
