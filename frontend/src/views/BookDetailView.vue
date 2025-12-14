<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NIcon, NSpin, NAlert, NSkeleton,
  useMessage
} from 'naive-ui'
import { 
  DownloadOutline, ChevronBackOutline
} from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'
import { useTaskStore } from '@/stores/task'
import { useUserStore } from '@/stores/user'
import { getEpubDownloadUrl, getTxtDownloadUrl, getChapterSummary, downloadEpub as apiDownloadEpub, getEpubStatus, downloadTxt as apiDownloadTxt, getTxtStatus } from '@/api/books'
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
const userStore = useUserStore()

const loading = ref(true)
const generating = ref(false)
const downloadLoading = ref(false)
const updateLoading = ref(false)
const book = computed(() => bookStore.currentBook)
const chapterSummaryLoading = ref(false)
const chapterSummaryLoaded = ref(false)
const showChapterSummarySkeleton = computed(
  () => chapterSummaryLoading.value && !chapterSummaryLoaded.value
)

// 章节热力图数据
const chapterSummary = ref({ segments: [] })
let lastChapterSummaryFetch = 0

// 章节范围选择器引用
const rangeSelectorRef = ref(null)

// 当前任务进度（优先使用任务范围内的章节数）
const taskProgress = computed(() => {
  const stats = book.value?.statistics
  const downloaded = book.value?.task_downloaded_chapters 
    ?? stats?.completed_chapters 
    ?? book.value?.downloaded_chapters 
    ?? 0
  const total = book.value?.task_total_chapters 
    ?? stats?.total_chapters 
    ?? book.value?.total_chapters 
    ?? 0
  const percent = total > 0 ? Math.round((downloaded / total) * 100) : 0
  return { downloaded, total, percent }
})

// 加载章节状态摘要
async function loadChapterSummary(options = {}) {
  const { force = false } = options
  if (!book.value) return

  const now = Date.now()
  const shouldThrottle = !force && chapterSummaryLoaded.value && now - lastChapterSummaryFetch < 1500
  if (chapterSummaryLoading.value || shouldThrottle) return

  chapterSummaryLoading.value = true
  lastChapterSummaryFetch = now
  try {
    const data = await getChapterSummary(book.value.id)
    chapterSummary.value = data || { segments: [] }
    chapterSummaryLoaded.value = true
  } catch (error) {
    console.error('Failed to load chapter summary:', error)
    chapterSummary.value = { segments: [] }
  } finally {
    chapterSummaryLoading.value = false
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
    loadChapterSummary({ force: true })
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
      await loadChapterSummary({ force: true })
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
    const result = await taskStore.startUpdate(book.value.id)
    
    if (result.hasNewChapters) {
      message.success(result.message || `发现${result.newChaptersCount}个新章节，更新任务已启动`)
      bookStore.updateCurrentBookProgress({ download_status: 'downloading' })
    } else {
      message.success(result.message || '已是最新版本')
      // 即使没有新章节，也刷新一下书籍信息以确保显示最新的章节数
      await bookStore.fetchBook(book.value.id)
      await loadChapterSummary({ force: true })
    }
  } catch (error) {
    message.error(error.response?.data?.detail || '更新失败')
  } finally {
    updateLoading.value = false
  }
}

// EPUB 生成逻辑已由后端统一为自动生成，前端仅触发下载

async function downloadEpub() {
  if (!book.value?.id) return
  downloadLoading.value = true
  try {
    // 尝试直接请求下载（可能返回 200 文件 或 202 表示后台生成中）
    const resp = await apiDownloadEpub(book.value.id)
    if (resp.status === 200) {
      // 直接下载文件
      const blob = new Blob([resp.data], { type: resp.headers['content-type'] || 'application/epub+zip' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${book.value.title}.epub`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      return
    }

    // 如果返回 202，开始轮询状态接口，直到完成
    if (resp.status === 202) {
      message.info('EPUB正在生成，开始轮询并将在完成后自动下载')
      const intervalMs = 2000
      const maxAttempts = 60
      let attempts = 0
      while (attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, intervalMs))
        attempts += 1
        try {
          const status = await getEpubStatus(book.value.id)
          if (status.status === 'completed') {
            // 发起最终下载请求
            const final = await apiDownloadEpub(book.value.id)
            if (final.status === 200) {
              const blob = new Blob([final.data], { type: final.headers['content-type'] || 'application/epub+zip' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `${book.value.title}.epub`
              document.body.appendChild(a)
              a.click()
              a.remove()
              URL.revokeObjectURL(url)
              message.success('EPUB 下载已开始')
              return
            }
          }
          if (status.status === 'failed') {
            throw new Error(status.message || 'EPUB 生成失败')
          }
        } catch (e) {
          // 若轮询过程中请求失败，不立刻终止，继续重试直至达到最大次数
          console.debug('轮询 EPUB 状态出错，继续重试：', e)
        }
      }
      throw new Error('等待EPUB生成超时，请稍后重试')
    }
  } catch (error) {
    console.error('下载 EPUB 错误', error)
    message.error(error.response?.data?.detail || error.message || 'EPUB 下载失败')
  } finally {
    downloadLoading.value = false
  }
}

// TXT 操作已移除，使用下载功能代替生成逻辑

async function downloadTxt() {
  if (!book.value?.id) return
  downloadLoading.value = true
  try {
    const resp = await apiDownloadTxt(book.value.id)
    if (resp.status === 200) {
      const blob = new Blob([resp.data], { type: resp.headers['content-type'] || 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${book.value.title}.txt`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      return
    }

    if (resp.status === 202) {
      message.info('TXT正在生成，开始轮询并将在完成后自动下载')
      const intervalMs = 2000
      const maxAttempts = 60
      let attempts = 0
      while (attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, intervalMs))
        attempts += 1
        try {
          const status = await getTxtStatus(book.value.id)
          if (status.status === 'completed') {
            const final = await apiDownloadTxt(book.value.id)
            if (final.status === 200) {
              const blob = new Blob([final.data], { type: final.headers['content-type'] || 'text/plain' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `${book.value.title}.txt`
              document.body.appendChild(a)
              a.click()
              a.remove()
              URL.revokeObjectURL(url)
              message.success('TXT 下载已开始')
              return
            }
          }
          if (status.status === 'failed') {
            throw new Error(status.message || 'TXT 生成失败')
          }
        } catch (e) {
          console.debug('轮询 TXT 状态出错，继续重试：', e)
        }
      }
      throw new Error('等待TXT生成超时，请稍后重试')
    }
  } catch (error) {
    console.error('下载 TXT 错误', error)
    message.error(error.response?.data?.detail || error.message || 'TXT 下载失败')
  } finally {
    downloadLoading.value = false
  }
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

function openReader() {
  if (!book.value?.id) return
  router.push({ name: 'reader', params: { bookId: book.value.id } })
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
          @read="openReader"
          @download-epub="downloadEpub"
          @download-txt="downloadTxt"
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

        <!-- 章节下载状态 - 骨架屏 + 懒加载 -->
        <template v-if="showChapterSummarySkeleton">
          <div class="section-card">
            <n-skeleton height="140px" :sharp="false" />
          </div>
          <div class="section-card">
            <n-skeleton text :repeat="3" :sharp="false" />
          </div>
        </template>
        <template v-else>
          <n-spin :show="chapterSummaryLoading">
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
          </n-spin>
        </template>

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
