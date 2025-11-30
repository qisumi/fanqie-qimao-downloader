<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as statsApi from '@/api/stats'
import * as taskApi from '@/api/tasks'

// 子组件
import WelcomeCard from '@/components/WelcomeCard.vue'
import StatsGrid from '@/components/StatsGrid.vue'
import QuickActions from '@/components/QuickActions.vue'

const router = useRouter()
const rawStats = ref(null)
const loading = ref(true)
const activeTasksCount = ref(0)

// 计算属性：从后端数据中提取需要的字段
const stats = computed(() => {
  if (!rawStats.value) {
    return {
      total_books: 0,
      completed_books: 0,
      active_tasks: 0,
      today_words: 0,
      daily_limit: 20000000
    }
  }
  
  const data = rawStats.value
  // 已完成的书籍数量
  const completedBooks = data.books_by_status?.completed || 0
  
  // 今日已用字数（番茄+七猫）
  const fanqieDownloaded = data.quota?.fanqie?.downloaded || 0
  const qimaoDownloaded = data.quota?.qimao?.downloaded || 0
  const todayWords = fanqieDownloaded + qimaoDownloaded
  
  // 每日限制
  const dailyLimit = data.quota?.fanqie?.limit || 20000000
  
  return {
    total_books: data.total_books || 0,
    completed_books: completedBooks,
    active_tasks: activeTasksCount.value,
    today_words: todayWords,
    daily_limit: dailyLimit
  }
})

onMounted(async () => {
  fetchActiveTasksCount()
  try {
    const response = await statsApi.getStats()
    rawStats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    loading.value = false
  }
})

async function fetchActiveTasksCount() {
  try {
    const [runningResponse, pendingResponse] = await Promise.all([
      taskApi.listTasks({ status: 'running', limit: 1 }),
      taskApi.listTasks({ status: 'pending', limit: 1 }),
    ])
    const runningTotal = runningResponse?.data?.total || 0
    const pendingTotal = pendingResponse?.data?.total || 0
    activeTasksCount.value = runningTotal + pendingTotal
  } catch (error) {
    console.error('Failed to load active tasks:', error)
    activeTasksCount.value = 0
  }
}

function goToSearch() {
  router.push({ name: 'search' })
}

function goToBooks() {
  router.push({ name: 'books' })
}

function goToTasks() {
  router.push({ name: 'tasks' })
}
</script>

<template>
  <div class="home-view">
    <!-- 欢迎区域 -->
    <WelcomeCard @search="goToSearch" />

    <!-- 统计卡片 -->
    <StatsGrid 
      :stats="stats" 
      :loading="loading"
      @go-books="goToBooks"
      @go-tasks="goToTasks"
    />

    <!-- 快速入口 -->
    <QuickActions 
      @go-search="goToSearch"
      @go-books="goToBooks"
      @go-tasks="goToTasks"
    />
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
