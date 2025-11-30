<script setup>
import { inject } from 'vue'
import { NCard, NGrid, NGi, NButton, NIcon } from 'naive-ui'
import { CloudDownloadOutline, BookOutline, DownloadOutline } from '@vicons/ionicons5'

const emit = defineEmits(['go-search', 'go-books', 'go-tasks'])

const isMobile = inject('isMobile', { value: false })
</script>

<template>
  <n-card class="quick-actions-card" :bordered="false">
    <template #header>
      <span class="section-title">快速入口</span>
    </template>
    <n-grid :cols="isMobile ? 1 : 3" :x-gap="16" :y-gap="12">
      <n-gi>
        <n-button 
          block 
          size="large" 
          class="action-btn action-btn-search"
          @click="emit('go-search')"
        >
          <template #icon>
            <n-icon><CloudDownloadOutline /></n-icon>
          </template>
          搜索新书
        </n-button>
      </n-gi>
      <n-gi>
        <n-button 
          block 
          size="large" 
          class="action-btn action-btn-library"
          @click="emit('go-books')"
        >
          <template #icon>
            <n-icon><BookOutline /></n-icon>
          </template>
          我的书库
        </n-button>
      </n-gi>
      <n-gi>
        <n-button 
          block 
          size="large" 
          class="action-btn action-btn-tasks"
          @click="emit('go-tasks')"
        >
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          下载任务
        </n-button>
      </n-gi>
    </n-grid>
  </n-card>
</template>

<style scoped>
.quick-actions-card {
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  box-shadow: var(--shadow-card, 0 1px 3px rgba(0,0,0,0.1));
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
}

.action-btn {
  height: 52px;
  font-weight: 500;
  border-radius: var(--border-radius-md, 8px);
  transition: all var(--transition-base, 0.25s);
}

.action-btn-search {
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
  border: none;
  color: white;
}

.action-btn-search:hover {
  background: linear-gradient(135deg, #0c7a43 0%, #18a058 100%);
  transform: translateY(-2px);
}

.action-btn-library {
  background: linear-gradient(135deg, #2080f0 0%, #409eff 100%);
  border: none;
  color: white;
}

.action-btn-library:hover {
  background: linear-gradient(135deg, #1060c0 0%, #2080f0 100%);
  transform: translateY(-2px);
}

.action-btn-tasks {
  background: linear-gradient(135deg, #f0a020 0%, #faad14 100%);
  border: none;
  color: white;
}

.action-btn-tasks:hover {
  background: linear-gradient(135deg, #d08010 0%, #f0a020 100%);
  transform: translateY(-2px);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .action-btn {
    height: 48px;
  }
}
</style>
