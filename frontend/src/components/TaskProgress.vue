<script setup>
import { computed } from 'vue'
import { 
  NCard, NSpace, NButton, NIcon, NTag, NProgress
} from 'naive-ui'
import { CloseOutline, SyncOutline, DownloadOutline } from '@vicons/ionicons5'

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

const statusInfo = computed(() => {
  const map = {
    'running': { color: '#2080f0', label: '运行中', pulse: true },
    'pending': { color: '#f0a020', label: '等待中', pulse: false },
    'completed': { color: '#18a058', label: '已完成', pulse: false },
    'failed': { color: '#d03050', label: '失败', pulse: false },
    'cancelled': { color: '#909399', label: '已取消', pulse: false }
  }
  return map[props.task.status] || { color: '#909399', label: props.task.status, pulse: false }
})

const taskTypeLabel = computed(() => {
  return props.task.task_type === 'download' ? '下载' : '更新'
})

const isActive = computed(() => {
  return props.task.status === 'running' || props.task.status === 'pending'
})

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <div class="task-progress" :class="{ 'is-active': isActive }">
    <!-- 状态指示器 -->
    <div class="status-indicator">
      <div 
        class="status-dot"
        :class="{ 'pulse': statusInfo.pulse }"
        :style="{ background: statusInfo.color }"
      ></div>
    </div>
    
    <!-- 任务信息 -->
    <div class="task-info">
      <div class="task-header">
        <div class="task-id-row">
          <n-icon v-if="task.task_type === 'download'" :size="16" color="#666">
            <DownloadOutline />
          </n-icon>
          <n-icon v-else :size="16" color="#666">
            <SyncOutline />
          </n-icon>
          <span class="task-id">{{ task.book_id?.substring(0, 12) }}...</span>
        </div>
        <div class="task-tags">
          <n-tag 
            :bordered="false"
            :color="{ color: statusInfo.color + '15', textColor: statusInfo.color }"
            size="small"
            round
          >
            {{ statusInfo.label }}
          </n-tag>
          <n-tag size="small" :bordered="false" round>
            {{ taskTypeLabel }}
          </n-tag>
        </div>
      </div>
      
      <div class="task-progress-bar">
        <n-progress 
          type="line" 
          :percentage="progress"
          :show-indicator="false"
          :height="8"
          :border-radius="4"
          :color="statusInfo.color"
          :rail-color="statusInfo.color + '20'"
        />
      </div>
      
      <div class="task-stats">
        <span class="progress-text">
          <span class="progress-value">{{ task.downloaded_chapters || 0 }}</span>
          <span class="progress-divider">/</span>
          <span class="progress-total">{{ task.total_chapters || 0 }}</span>
          <span class="progress-unit">章</span>
        </span>
        <span v-if="task.failed_chapters > 0" class="failed-text">
          {{ task.failed_chapters }} 失败
        </span>
        <span class="progress-percent">{{ progress }}%</span>
      </div>
    </div>
    
    <!-- 取消按钮 -->
    <n-button 
      v-if="isActive"
      size="small" 
      type="error" 
      quaternary
      @click="handleCancel"
      class="cancel-btn"
    >
      <template #icon>
        <n-icon><CloseOutline /></n-icon>
      </template>
      取消
    </n-button>
  </div>
</template>

<style scoped>
.task-progress {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--bg-color-tertiary, #fafafa);
  border-radius: var(--border-radius-md, 8px);
  transition: all var(--transition-base);
}

.task-progress.is-active {
  background: linear-gradient(135deg, rgba(32, 128, 240, 0.05) 0%, rgba(32, 128, 240, 0.02) 100%);
  border: 1px solid rgba(32, 128, 240, 0.1);
}

/* 状态指示器 */
.status-indicator {
  padding-top: 4px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: all var(--transition-base);
}

.status-dot.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 currentColor;
    opacity: 1;
  }
  50% {
    box-shadow: 0 0 0 6px transparent;
    opacity: 0.8;
  }
  100% {
    box-shadow: 0 0 0 0 transparent;
    opacity: 1;
  }
}

/* 任务信息 */
.task-info {
  flex: 1;
  min-width: 0;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}

.task-id-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.task-id {
  font-family: monospace;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color-primary, #333);
}

.task-tags {
  display: flex;
  gap: 6px;
}

/* 进度条 */
.task-progress-bar {
  margin-bottom: 8px;
}

/* 任务统计 */
.task-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.progress-text {
  color: var(--text-color-secondary, #666);
}

.progress-value {
  font-weight: 600;
  color: var(--primary-color, #18a058);
}

.progress-divider {
  margin: 0 2px;
  color: #ccc;
}

.progress-total {
  color: var(--text-color-tertiary, #999);
}

.progress-unit {
  margin-left: 2px;
  color: var(--text-color-tertiary, #999);
}

.failed-text {
  color: var(--error-color, #d03050);
  font-weight: 500;
}

.progress-percent {
  margin-left: auto;
  font-weight: 600;
  color: var(--text-color-secondary, #666);
}

/* 取消按钮 */
.cancel-btn {
  flex-shrink: 0;
  align-self: center;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .task-progress {
    padding: 12px;
  }
  
  .task-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .task-stats {
    font-size: 12px;
    gap: 8px;
  }
}
</style>
