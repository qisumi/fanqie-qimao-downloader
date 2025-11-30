<script setup>
import { ref, computed, onMounted } from 'vue'
import { NCard, NGrid, NGi, NStatistic, NSpace, NH2, NIcon, NButton } from 'naive-ui'
import { BookOutline, DownloadOutline, CloudDownloadOutline, TimeOutline } from '@vicons/ionicons5'
import { useRouter } from 'vue-router'
import * as statsApi from '@/api/stats'

const router = useRouter()
const rawStats = ref(null)
const loading = ref(true)

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
    active_tasks: 0, // TODO: 从任务API获取
    today_words: todayWords,
    daily_limit: dailyLimit
  }
})

onMounted(async () => {
  try {
    const response = await statsApi.getStats()
    rawStats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  } finally {
    loading.value = false
  }
})

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
    <n-space vertical :size="24">
      <!-- 欢迎区域 -->
      <n-card>
        <n-space justify="space-between" align="center">
          <div>
            <n-h2 style="margin: 0;">欢迎使用番茄七猫下载器</n-h2>
            <p style="color: #666; margin: 8px 0 0 0;">
              支持番茄小说、七猫小说的批量下载和 EPUB 导出
            </p>
          </div>
          <n-button type="primary" size="large" @click="goToSearch">
            <template #icon>
              <n-icon><CloudDownloadOutline /></n-icon>
            </template>
            搜索书籍
          </n-button>
        </n-space>
      </n-card>

      <!-- 统计卡片 -->
      <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <n-gi span="4 m:2 l:1">
          <n-card hoverable @click="goToBooks" style="cursor: pointer;">
            <n-statistic label="书库总数">
              <template #prefix>
                <n-icon :size="24" color="#18a058"><BookOutline /></n-icon>
              </template>
              {{ stats.total_books }}
            </n-statistic>
          </n-card>
        </n-gi>
        
        <n-gi span="4 m:2 l:1">
          <n-card hoverable @click="goToBooks" style="cursor: pointer;">
            <n-statistic label="已完成">
              <template #prefix>
                <n-icon :size="24" color="#2080f0"><DownloadOutline /></n-icon>
              </template>
              {{ stats.completed_books }}
            </n-statistic>
          </n-card>
        </n-gi>
        
        <n-gi span="4 m:2 l:1">
          <n-card hoverable @click="goToTasks" style="cursor: pointer;">
            <n-statistic label="活跃任务">
              <template #prefix>
                <n-icon :size="24" color="#f0a020"><TimeOutline /></n-icon>
              </template>
              {{ stats.active_tasks }}
            </n-statistic>
          </n-card>
        </n-gi>
        
        <n-gi span="4 m:2 l:1">
          <n-card>
            <n-statistic label="今日已用字数">
              {{ (stats.today_words / 10000).toFixed(1) }}万 / {{ (stats.daily_limit / 10000).toFixed(0) }}万
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 快速入口 -->
      <n-card title="快速入口">
        <n-grid :cols="3" :x-gap="16" :y-gap="16">
          <n-gi>
            <n-button block size="large" @click="goToSearch">
              搜索新书
            </n-button>
          </n-gi>
          <n-gi>
            <n-button block size="large" @click="goToBooks">
              我的书库
            </n-button>
          </n-gi>
          <n-gi>
            <n-button block size="large" @click="goToTasks">
              下载任务
            </n-button>
          </n-gi>
        </n-grid>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
