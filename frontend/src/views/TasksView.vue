<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { 
  NCard, NSpace, NButton, NIcon, NEmpty, NSpin,
  NList, NListItem, NThing, NTag, NProgress,
  useMessage
} from 'naive-ui'
import { RefreshOutline, CloseOutline } from '@vicons/ionicons5'
import { useTaskStore } from '@/stores/task'
import TaskProgress from '@/components/TaskProgress.vue'

const message = useMessage()
const taskStore = useTaskStore()

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

function getStatusTag(status) {
  const map = {
    'running': { type: 'info', label: '运行中' },
    'pending': { type: 'warning', label: '等待中' },
    'completed': { type: 'success', label: '已完成' },
    'failed': { type: 'error', label: '失败' },
    'cancelled': { type: 'default', label: '已取消' }
  }
  return map[status] || { type: 'default', label: status }
}
</script>

<template>
  <div class="tasks-view">
    <n-space vertical :size="24">
      <!-- 工具栏 -->
      <n-card>
        <n-space justify="space-between" align="center">
          <span style="font-size: 16px; font-weight: 500;">下载任务管理</span>
          <n-button @click="refreshTasks" :loading="loading">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </n-card>

      <!-- 活跃任务 -->
      <n-card title="进行中的任务">
        <n-spin :show="loading">
          <template v-if="activeTasks.length > 0">
            <n-space vertical :size="16">
              <TaskProgress 
                v-for="task in activeTasks" 
                :key="task.id"
                :task="task"
                @cancel="cancelTask(task)"
              />
            </n-space>
          </template>
          <n-empty v-else description="暂无进行中的任务" />
        </n-spin>
      </n-card>

      <!-- 已完成任务 -->
      <n-card title="历史任务">
        <n-spin :show="loading">
          <template v-if="completedTasks.length > 0">
            <n-list>
              <n-list-item v-for="task in completedTasks" :key="task.id">
                <n-thing>
                  <template #header>
                    {{ task.book_id }}
                  </template>
                  <template #header-extra>
                    <n-tag v-bind="getStatusTag(task.status)" size="small">
                      {{ getStatusTag(task.status).label }}
                    </n-tag>
                  </template>
                  <template #description>
                    <n-space :size="16">
                      <span>类型: {{ task.task_type === 'download' ? '下载' : '更新' }}</span>
                      <span>章节: {{ task.downloaded_chapters }} / {{ task.total_chapters }}</span>
                      <span v-if="task.message">{{ task.message }}</span>
                    </n-space>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </template>
          <n-empty v-else description="暂无历史任务" />
        </n-spin>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.tasks-view {
  max-width: 900px;
  margin: 0 auto;
}
</style>
