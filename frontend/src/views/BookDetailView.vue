<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  NButton, NIcon, NSpin, NAlert,
  useMessage
} from 'naive-ui'
import { 
  DownloadOutline, ChevronBackOutline
} from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'
import { useTaskStore } from '@/stores/task'
import { getEpubDownloadUrl, getChapterSummary } from '@/api/books'
import { useBookWebSocket } from '@/composables/useBookWebSocket'

// 子组件
import BookInfoCard from '@/components/BookInfoCard.vue'
import ChapterHeatmap from '@/components/ChapterHeatmap.vue'
import ChapterRangeSelector from '@/components/ChapterRangeSelector.vue'

const isMobile = inject('isMobile', ref(false))

const route = useRoute()
const router = useRouter()
const message = useMessage()
const bookStore = useBookStore()
const taskStore = useTaskStore()

const loading = ref(true)
const generating = ref(false)
const downloadLoading = ref(false)
const updateLoading = ref(false)
const book = computed(() => bookStore.currentBook)

// 章节热力图数据
const chapterSummary = ref({ segments: [] })

// 章节范围选择器引用
const rangeSelectorRef = ref(null)

// 当前任务进度（优先使用任务范围内的章节数）
const taskProgress = computed(() => {
  const downloaded = book.value?.task_downloaded_chapters ?? book.value?.downloaded_chapters ?? 0
  const total = book.value?.task_total_chapters ?? book.value?.total_chapters ?? 0
  const percent = total > 0 ? Math.round((downloaded / total) * 100) : 0
  return { downloaded, total, percent }
})

// 加载章节状态摘要
async function loadChapterSummary() {
  if (!book.value) return
  try {
    const data = await getChapterSummary(book.value.id)
    chapterSummary.value = data || { segments: [] }
  } catch (error) {
    console.error('Failed to load chapter summary:', error)
    chapterSummary.value = { segments: [] }
  }
}

// WebSocket 进度管理
const { wsConnected } = useBookWebSocket({
  book,
  onProgress: (data) => {
    // 只更新章节进度，不更新 download_status
    // 任务状态(running/pending)不应该覆盖书籍的下载状态(downloading)
    bookStore.updateCurrentBookProgress({
      downloaded_chapters: data.downloaded_chapters,
      total_chapters: data.total_chapters
    })
  },
  onCompleted: (data) => {
    bookStore.updateCurrentBookProgress({
      download_status: data.success ? 'completed' : 'failed'
    })
    if (data.success) {
      message.success('下载完成！')
    } else {
      message.error(data.message || '下载失败')
    }
    // 刷新书籍信息
    bookStore.fetchBook(route.params.id)
    loadChapterSummary()
  },
  onError: (data) => {
    message.error(data.error_message || '发生错误')
  },
  loadChapterSummary
})

onMounted(async () => {
  try {
    await bookStore.fetchBook(route.params.id)
    if (book.value) {
      await loadChapterSummary()
    }
  } catch (error) {
    message.error('加载书籍详情失败')
    router.push({ name: 'books' })
  } finally {
    loading.value = false
  }
})

function goBack() {
  router.push({ name: 'books' })
}

// 下载操作
async function startDownload() {
  downloadLoading.value = true
  try {
    await taskStore.startDownload(book.value.id)
    message.success('下载任务已启动')
    bookStore.updateCurrentBookProgress({ download_status: 'downloading' })
  } catch (error) {
    message.error(error.response?.data?.detail || '启动下载失败')
  } finally {
    downloadLoading.value = false
  }
}

async function downloadSelectedRange({ startIndex, endIndex }) {
  downloadLoading.value = true
  try {
    await taskStore.startDownload(book.value.id, startIndex, endIndex)
    message.success('下载任务已启动')
    bookStore.updateCurrentBookProgress({ download_status: 'downloading' })
  } catch (error) {
    message.error(error.response?.data?.detail || '启动下载失败')
  } finally {
    downloadLoading.value = false
  }
}

async function startUpdate() {
  updateLoading.value = true
  try {
    await bookStore.refreshBook(book.value.id)
    message.success('书籍信息已更新')
    await loadChapterSummary()
  } catch (error) {
    message.error(error.response?.data?.detail || '刷新书籍信息失败')
  } finally {
    updateLoading.value = false
  }
}

// EPUB 操作
async function generateEpub() {
  generating.value = true
  try {
    await bookStore.generateEpub(book.value.id)
    pollEpubStatus()
  } catch (error) {
    message.error(error.response?.data?.detail || 'EPUB 生成失败')
    generating.value = false
  }
}

async function pollEpubStatus() {
  const checkStatus = async () => {
    try {
      const response = await fetch(`/api/books/${book.value.id}/epub/status`)
      if (response.ok) {
        const data = await response.json()
        if (data.status === 'completed') {
          message.success('EPUB 生成完成！')
          generating.value = false
          await bookStore.fetchBook(route.params.id)
          downloadEpub()
        } else if (data.status === 'failed') {
          message.error('EPUB 生成失败')
          generating.value = false
        } else {
          setTimeout(checkStatus, 2000)
        }
      }
    } catch (error) {
      generating.value = false
    }
  }
  setTimeout(checkStatus, 1000)
}

function downloadEpub() {
  window.open(getEpubDownloadUrl(book.value.id), '_blank')
}

// 删除书籍
async function deleteBook() {
  try {
    await bookStore.deleteBook(book.value.id)
    message.success('书籍已删除')
    router.push({ name: 'books' })
  } catch (error) {
    message.error('删除失败')
  }
}

// 热力图点击选择章节范围
function handleSelectSegment(segment) {
  rangeSelectorRef.value?.selectSegment(segment)
}
</script>

<template>
  <div class="book-detail-view">
    <n-spin :show="loading">
      <template v-if="book">
        <!-- 返回按钮 -->
        <n-button text @click="goBack" class="back-btn">
          <template #icon>
            <n-icon :size="20"><ChevronBackOutline /></n-icon>
          </template>
          返回书库
        </n-button>

        <!-- 书籍信息卡片 -->
        <BookInfoCard
          :book="book"
          :task-progress="taskProgress"
          :download-loading="downloadLoading"
          :update-loading="updateLoading"
          :generating="generating"
          @download="startDownload"
          @update="startUpdate"
          @generate-epub="generateEpub"
          @download-epub="downloadEpub"
          @delete="deleteBook"
        />

        <!-- 下载状态提示 -->
        <n-alert 
          v-if="book.download_status === 'downloading'" 
          type="info" 
          class="download-alert"
        >
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          <template #header>下载进行中...</template>
          已下载 {{ taskProgress.downloaded || 0 }}/{{ taskProgress.total || 0 }} 章节
          ({{ taskProgress.percent }}%)
        </n-alert>

        <!-- 章节下载状态热力图 -->
        <ChapterHeatmap
          :segments="chapterSummary.segments"
          :start-chapter="rangeSelectorRef?.startChapter || 1"
          :end-chapter="rangeSelectorRef?.endChapter || book.total_chapters"
          @select-segment="handleSelectSegment"
        />

        <!-- 章节范围选择器 -->
        <ChapterRangeSelector
          ref="rangeSelectorRef"
          :total-chapters="book.total_chapters"
          :downloading="book.download_status === 'downloading'"
          :loading="downloadLoading"
          @download="downloadSelectedRange"
        />

        <!-- 简介 -->
        <div v-if="book.intro" class="section-card">
          <div class="section-header">
            <span class="section-title">简介</span>
          </div>
          <p class="intro-text">{{ book.intro }}</p>
        </div>
      </template>
    </n-spin>
  </div>
</template>

<style scoped>
.book-detail-view {
  max-width: 900px;
  margin: 0 auto;
}

/* 返回按钮 */
.back-btn {
  margin-bottom: 16px;
  font-weight: 500;
  color: var(--text-color-secondary, #666);
}

.back-btn:hover {
  color: var(--primary-color, #18a058);
}

/* 下载提示 */
.download-alert {
  margin-bottom: 20px;
  border-radius: var(--border-radius-lg, 12px);
}

/* 区块卡片 */
.section-card {
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  padding: 20px;
  box-shadow: var(--shadow-card);
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light, #efeff5);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
}

/* 简介 */
.intro-text {
  white-space: pre-wrap;
  color: var(--text-color-secondary, #666);
  line-height: 1.8;
  margin: 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .section-card {
    padding: 16px;
  }
}
</style>
