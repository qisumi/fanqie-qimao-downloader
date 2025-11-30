<script setup>
import { computed, onMounted, onUnmounted, inject, ref } from 'vue'
import { 
  NCard, NSpace, NButton, NIcon, NEmpty, NSpin,
  NList, NListItem, NThing, NTag, NProgress, NCollapse, NCollapseItem,
  useMessage
} from 'naive-ui'
import { RefreshOutline, CloseOutline, CheckmarkCircleOutline, AlertCircleOutline, TimeOutline } from '@vicons/ionicons5'
import { useTaskStore } from '@/stores/task'
import TaskProgress from '@/components/TaskProgress.vue'

const message = useMessage()
const taskStore = useTaskStore()
const isMobile = inject('isMobile', ref(false))

const loading = computed(() => taskStore.loading)
const activeTasks = computed(() => taskStore.activeTasks)
const completedTasks = computed(() => taskStore.completedTasks)

onMounted(() => {
  taskStore.fetchTasks()
})

onUnmounted(() => {
  // 离开页面时断开所有 WebSocket 连接
  taskStore.disconnectAll()
})

async function refreshTasks() {
  await taskStore.fetchTasks()
  message.success('任务列表已刷新')
}

async function cancelTask(task) {
  try {
    await taskStore.cancelTask(task.id)
    message.success('任务已取消')
  } catch (error) {
    message.error('取消任务失败')
  }
}

function getStatusInfo(status) {
  const map = {
    'running': { color: '#2080f0', label: '运行中', icon: TimeOutline },
    'pending': { color: '#f0a020', label: '等待中', icon: TimeOutline },
    'completed': { color: '#18a058', label: '已完成', icon: CheckmarkCircleOutline },
    'failed': { color: '#d03050', label: '失败', icon: AlertCircleOutline },
    'cancelled': { color: '#909399', label: '已取消', icon: CloseOutline }
  }
  return map[status] || { color: '#909399', label: status, icon: TimeOutline }
}

function formatTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<template>
  <div class="tasks-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">下载任务</h2>
        <span class="task-count">{{ activeTasks.length }} 进行中</span>
      </div>
      <n-button @click="refreshTasks" :loading="loading">
        <template #icon>
          <n-icon><RefreshOutline /></n-icon>
        </template>
        <span class="hide-mobile">刷新</span>
      </n-button>
    </div>

    <!-- 活跃任务 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">进行中的任务</span>
        <span class="section-badge" v-if="activeTasks.length">{{ activeTasks.length }}</span>
      </div>
      
      <n-spin :show="loading">
        <template v-if="activeTasks.length > 0">
          <div class="task-list">
            <TaskProgress 
              v-for="task in activeTasks" 
              :key="task.id"
              :task="task"
              @cancel="cancelTask(task)"
            />
          </div>
        </template>
        <div v-else class="empty-section">
          <n-icon :size="40" color="#ddd"><TimeOutline /></n-icon>
          <span>暂无进行中的任务</span>
        </div>
      </n-spin>
    </div>

    <!-- 历史任务 -->
    <div class="section">
      <div class="section-header">
        <span class="section-title">历史任务</span>
        <span class="section-badge secondary" v-if="completedTasks.length">{{ completedTasks.length }}</span>
      </div>
      
      <n-spin :show="loading">
        <template v-if="completedTasks.length > 0">
          <div class="history-list">
            <div 
              v-for="task in completedTasks" 
              :key="task.id"
              class="history-item"
            >
              <div class="history-status">
                <div 
                  class="status-dot"
                  :style="{ background: getStatusInfo(task.status).color }"
                ></div>
              </div>
              
              <div class="history-info">
                <div class="history-header">
                  <span class="history-id">{{ task.book_id?.substring(0, 8) }}...</span>
                  <n-tag 
                    :bordered="false"
                    :color="{ color: getStatusInfo(task.status).color + '15', textColor: getStatusInfo(task.status).color }"
                    size="small"
                    round
                  >
                    {{ getStatusInfo(task.status).label }}
                  </n-tag>
                </div>
                
                <div class="history-meta">
                  <span class="meta-item">
                    {{ task.task_type === 'download' ? '下载' : '更新' }}
                  </span>
                  <span class="meta-divider">·</span>
                  <span class="meta-item">
                    {{ task.downloaded_chapters }}/{{ task.total_chapters }} 章
                  </span>
                  <template v-if="task.message">
                    <span class="meta-divider">·</span>
                    <span class="meta-item message">{{ task.message }}</span>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="empty-section">
          <n-icon :size="40" color="#ddd"><CheckmarkCircleOutline /></n-icon>
          <span>暂无历史任务</span>
        </div>
      </n-spin>
    </div>
  </div>
</template>

<style scoped>
.tasks-view {
  max-width: 900px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: var(--text-color-primary, #333);
}

.task-count {
  font-size: 14px;
  color: var(--primary-color, #18a058);
  background: rgba(24, 160, 88, 0.1);
  padding: 2px 10px;
  border-radius: 12px;
}

/* 区块 */
.section {
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-card);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light, #efeff5);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
}

.section-badge {
  font-size: 12px;
  font-weight: 600;
  color: white;
  background: var(--primary-color, #18a058);
  padding: 2px 8px;
  border-radius: 10px;
}

.section-badge.secondary {
  background: var(--text-color-tertiary, #999);
}

/* 任务列表 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 历史任务列表 */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: var(--bg-color-tertiary, #fafafa);
  border-radius: var(--border-radius-md, 8px);
  transition: background var(--transition-fast);
}

.history-item:hover {
  background: #f0f5ff;
}

.history-status {
  padding-top: 6px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.history-id {
  font-family: monospace;
  font-size: 13px;
  color: var(--text-color-primary, #333);
}

.history-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 12px;
  color: var(--text-color-tertiary, #999);
}

.meta-divider {
  color: #ddd;
}

.meta-item.message {
  color: var(--text-color-secondary, #666);
}

/* 空状态 */
.empty-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px 20px;
  color: var(--text-color-tertiary, #999);
  font-size: 14px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .page-header {
    margin-bottom: 16px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .hide-mobile {
    display: none;
  }
  
  .section {
    padding: 16px;
    margin-bottom: 16px;
  }
  
  .history-item {
    padding: 10px;
  }
  
  .empty-section {
    padding: 32px 16px;
  }
}
</style>
