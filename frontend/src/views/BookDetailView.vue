<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  NCard, NSpace, NButton, NIcon, NTag, NProgress, 
  NDescriptions, NDescriptionsItem, NImage, NH2, NSpin,
  NPopconfirm, NDivider, NInputNumber, NTooltip, NAlert,
  useMessage
} from 'naive-ui'
import { 
  ArrowBackOutline, DownloadOutline, RefreshOutline, 
  TrashOutline, BookOutline, DocumentOutline, GridOutline
} from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'
import { useTaskStore } from '@/stores/task'
import { getEpubDownloadUrl, getChapterSummary, getBookStatus } from '@/api/books'

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

// 章节范围选择
const startChapter = ref(1)
const endChapter = ref(1)

// 章节热力图数据
const chapterSummary = ref({ segments: [] })
const hoveredSegment = ref(null)

// WebSocket 相关
let websocket = null
let heartbeatInterval = null
let pollInterval = null
let reconnectAttempts = 0
const maxReconnectAttempts = 5
const wsConnected = ref(false)

onMounted(async () => {
  try {
    await bookStore.fetchBook(route.params.id)
    if (book.value) {
      startChapter.value = 1
      endChapter.value = book.value.total_chapters || 1
      await loadChapterSummary()
      
      // 如果正在下载，连接 WebSocket
      if (book.value.download_status === 'downloading') {
        setTimeout(() => connectWebSocket(), 200)
      }
    }
  } catch (error) {
    message.error('加载书籍详情失败')
    router.push({ name: 'books' })
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  disconnectWebSocket()
  stopPolling()
})

// 监听下载状态变化
watch(() => book.value?.download_status, (newStatus, oldStatus) => {
  console.log(`📡 Download status changed: ${oldStatus} -> ${newStatus}`)
  if (newStatus === 'downloading' && oldStatus !== 'downloading') {
    // 延迟连接 WebSocket，给后端时间创建任务
    setTimeout(() => {
      if (!wsConnected.value) {
        connectWebSocket()
      }
    }, 100)
  } else if (newStatus !== 'downloading') {
    disconnectWebSocket()
    stopPolling()
  }
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

// WebSocket 连接
function getWebSocketUrl() {
  if (!book.value) return null
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/books/${book.value.id}`
}

function connectWebSocket() {
  // 防止重复连接
  if (websocket) {
    if (websocket.readyState === WebSocket.OPEN) {
      console.log('✅ WebSocket already connected')
      return
    }
    if (websocket.readyState === WebSocket.CONNECTING) {
      console.log('⏳ WebSocket is connecting...')
      return
    }
    // 清理旧连接
    websocket.onopen = null
    websocket.onmessage = null
    websocket.onerror = null
    websocket.onclose = null
    websocket = null
  }
  
  const url = getWebSocketUrl()
  if (!url) {
    console.error('❌ Cannot get WebSocket URL - book is null')
    return
  }
  
  console.log('🔌 Connecting WebSocket:', url)
  
  try {
    websocket = new WebSocket(url)
  } catch (error) {
    console.error('❌ Failed to create WebSocket:', error)
    startPolling()
    return
  }
  
  websocket.onopen = () => {
    console.log('✅ WebSocket connected successfully')
    wsConnected.value = true
    reconnectAttempts = 0
    stopPolling()  // 确保停止轮询
    startHeartbeat()
  }
  
  websocket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.type !== 'pong') {
        console.log('📨 WebSocket message:', msg.type, msg.data)
      }
      handleWebSocketMessage(msg)
    } catch (error) {
      console.error('❌ Failed to parse WebSocket message:', error, event.data)
    }
  }
  
  websocket.onclose = (event) => {
    console.log('🔌 WebSocket closed:', event.code, event.reason)
    wsConnected.value = false
    stopHeartbeat()
    
    // 4001 = 未授权，不再重试
    if (event.code === 4001) {
      console.error('❌ WebSocket unauthorized, falling back to polling')
      startPolling()
      return
    }
    
    // 如果书籍还在下载中，尝试重连
    if (book.value?.download_status === 'downloading') {
      attemptReconnect()
    }
  }
  
  websocket.onerror = (error) => {
    console.error('❌ WebSocket error:', error)
    wsConnected.value = false
  }
}

function handleWebSocketMessage(msg) {
  switch (msg.type) {
    case 'progress':
      console.log('📊 Progress update:', msg.data)
      bookStore.updateCurrentBookProgress({
        downloaded_chapters: msg.data.downloaded_chapters,
        total_chapters: msg.data.total_chapters,
        status: msg.data.status
      })
      loadChapterSummary()
      break
      
    case 'completed':
      console.log('✅ Task completed:', msg.data)
      bookStore.updateCurrentBookProgress({
        download_status: msg.data.success ? 'completed' : 'failed'
      })
      disconnectWebSocket()
      if (msg.data.success) {
        message.success('下载完成！')
      } else {
        message.error(msg.data.message || '下载失败')
      }
      refreshBookStatus()
      break
    
    case 'status':
      console.log('ℹ️ Book status:', msg.data)
      break
      
    case 'error':
      console.error('❌ WebSocket error message:', msg.data)
      message.error(msg.data.error_message || '发生错误')
      break
      
    case 'pong':
      // 心跳响应，不需要处理
      break
      
    default:
      console.warn('Unknown WebSocket message type:', msg.type)
  }
}

function attemptReconnect() {
  if (reconnectAttempts >= maxReconnectAttempts) {
    console.log('⚠️ Max reconnect attempts reached, falling back to polling')
    startPolling()
    return
  }
  
  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
  console.log(`🔄 Reconnecting WebSocket in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`)
  reconnectAttempts++
  
  setTimeout(() => {
    if (book.value?.download_status === 'downloading') {
      connectWebSocket()
    }
  }, delay)
}

function startHeartbeat() {
  stopHeartbeat()
  // 每 15 秒发送一次心跳
  heartbeatInterval = setInterval(() => {
    if (websocket?.readyState === WebSocket.OPEN) {
      try {
        websocket.send(JSON.stringify({ type: 'ping' }))
      } catch (error) {
        console.error('Failed to send heartbeat:', error)
      }
    }
  }, 15000)
}

function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }
}

function disconnectWebSocket() {
  console.log('🔌 Disconnecting WebSocket...')
  stopHeartbeat()
  if (websocket) {
    websocket.onopen = null
    websocket.onmessage = null
    websocket.onerror = null
    websocket.onclose = null
    if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
      websocket.close()
    }
    websocket = null
  }
  wsConnected.value = false
}

// 轮询（WebSocket 失败时使用）
function startPolling() {
  if (pollInterval) {
    console.log('⏰ Polling already started')
    return
  }
  console.log('⏰ Starting polling fallback')
  pollInterval = setInterval(() => {
    refreshBookStatus()
  }, 3000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

async function refreshBookStatus() {
  if (!book.value) return
  try {
    const data = await getBookStatus(book.value.id)
    if (data.book) {
      Object.assign(book.value, data.book)
      await loadChapterSummary()
      
      if (data.book.download_status !== 'downloading') {
        stopPolling()
        if (data.book.download_status === 'completed') {
          message.success('下载完成！')
        }
      }
    }
  } catch (error) {
    console.error('Refresh failed:', error)
  }
}

// 章节范围选择方法
function validateRange() {
  const total = book.value?.total_chapters || 1
  if (startChapter.value < 1) startChapter.value = 1
  if (startChapter.value > total) startChapter.value = total
  if (endChapter.value < 1) endChapter.value = 1
  if (endChapter.value > total) endChapter.value = total
  if (endChapter.value < startChapter.value) endChapter.value = startChapter.value
}

function selectAll() {
  startChapter.value = 1
  endChapter.value = book.value?.total_chapters || 1
}

function selectRange(start, end) {
  startChapter.value = start
  endChapter.value = Math.min(end, book.value?.total_chapters || 1)
}

function selectLastN(n) {
  const total = book.value?.total_chapters || 1
  endChapter.value = total
  startChapter.value = Math.max(1, total - n + 1)
}

function selectSegment(segment) {
  startChapter.value = segment.start_index + 1
  endChapter.value = segment.end_index + 1
}

function isSegmentSelected(segment) {
  const segStart = segment.start_index + 1
  const segEnd = segment.end_index + 1
  return startChapter.value <= segStart && endChapter.value >= segEnd
}

function getSelectedCount() {
  if (!book.value) return 0
  return Math.max(0, endChapter.value - startChapter.value + 1)
}

function getSegmentClass(segment) {
  if (segment.failed > 0) return 'bg-red-400'
  if (segment.completion_rate === 1) return 'bg-green-500'
  if (segment.completion_rate >= 0.8) return 'bg-green-400'
  if (segment.completion_rate >= 0.5) return 'bg-yellow-400'
  if (segment.completion_rate >= 0.2) return 'bg-yellow-300'
  return 'bg-gray-300'
}

function goBack() {
  router.push({ name: 'books' })
}

async function startDownload() {
  downloadLoading.value = true
  try {
    await taskStore.startDownload(book.value.id)
    message.success('下载任务已启动')
    // 通过 store 更新状态，这会触发 watch
    bookStore.updateCurrentBookProgress({ download_status: 'downloading' })
  } catch (error) {
    message.error(error.response?.data?.detail || '启动下载失败')
  } finally {
    downloadLoading.value = false
  }
}

async function downloadSelectedRange() {
  downloadLoading.value = true
  try {
    const startIdx = startChapter.value - 1
    const endIdx = endChapter.value - 1
    await taskStore.startDownload(book.value.id, startIdx, endIdx)
    message.success('下载任务已启动')
    // 通过 store 更新状态，这会触发 watch
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
    await taskStore.startUpdate(book.value.id)
    message.success('更新任务已启动')
    // 通过 store 更新状态，这会触发 watch
    bookStore.updateCurrentBookProgress({ download_status: 'downloading' })
  } catch (error) {
    message.error(error.response?.data?.detail || '启动更新失败')
  } finally {
    updateLoading.value = false
  }
}

async function generateEpub() {
  generating.value = true
  try {
    await bookStore.generateEpub(book.value.id)
    // 轮询检查EPUB生成状态
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

async function deleteBook() {
  try {
    await bookStore.deleteBook(book.value.id)
    message.success('书籍已删除')
    router.push({ name: 'books' })
  } catch (error) {
    message.error('删除失败')
  }
}

function getPlatformTag(platform) {
  return platform === 'fanqie' 
    ? { type: 'warning', label: '番茄小说' }
    : { type: 'info', label: '七猫小说' }
}

function getStatusTag(status) {
  const map = {
    'completed': { type: 'success', label: '已完成' },
    'downloading': { type: 'info', label: '下载中' },
    'pending': { type: 'default', label: '未开始' },
    'failed': { type: 'error', label: '失败' }
  }
  return map[status] || { type: 'default', label: status }
}

function getProgressPercent() {
  if (!book.value || book.value.total_chapters === 0) return 0
  return Math.round((book.value.downloaded_chapters / book.value.total_chapters) * 100)
}
</script>

<template>
  <div class="book-detail-view">
    <n-spin :show="loading">
      <template v-if="book">
        <n-space vertical :size="24">
          <!-- 返回按钮 -->
          <n-button text @click="goBack">
            <template #icon>
              <n-icon><ArrowBackOutline /></n-icon>
            </template>
            返回书库
          </n-button>

          <!-- 书籍信息卡片 -->
          <n-card>
            <n-space :size="24">
              <!-- 封面 -->
              <n-image 
                v-if="book.cover_url"
                :src="book.cover_url" 
                :width="160"
                object-fit="cover"
                style="border-radius: 8px;"
              />
              <div v-else style="width: 160px; height: 220px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <n-icon :size="48" color="#ccc"><BookOutline /></n-icon>
              </div>
              
              <!-- 信息 -->
              <div style="flex: 1;">
                <n-space :size="12" style="align-items: center;">
                  <n-h2 style="margin: 0;">{{ book.title }}</n-h2>
                  <n-tag v-bind="getPlatformTag(book.platform)" size="small">
                    {{ getPlatformTag(book.platform).label }}
                  </n-tag>
                  <n-tag v-bind="getStatusTag(book.download_status)" size="small">
                    {{ getStatusTag(book.download_status).label }}
                  </n-tag>
                </n-space>
                
                <n-descriptions :column="2" style="margin-top: 16px;">
                  <n-descriptions-item label="作者">{{ book.author || '未知' }}</n-descriptions-item>
                  <n-descriptions-item label="总章节">{{ book.total_chapters || 0 }}</n-descriptions-item>
                  <n-descriptions-item label="已下载">{{ book.downloaded_chapters || 0 }}</n-descriptions-item>
                  <n-descriptions-item label="总字数">{{ book.word_count ? (book.word_count / 10000).toFixed(1) + '万' : '未知' }}</n-descriptions-item>
                  <n-descriptions-item label="连载状态">{{ book.creation_status || '未知' }}</n-descriptions-item>
                </n-descriptions>
                
                <!-- 下载进度 -->
                <div v-if="(book.total_chapters || 0) > 0" style="margin-top: 16px;">
                  <n-progress 
                    type="line" 
                    :percentage="getProgressPercent()"
                    :show-indicator="true"
                  />
                </div>
                
                <!-- 操作按钮 -->
                <n-space style="margin-top: 24px;">
                  <n-button 
                    type="primary" 
                    @click="startDownload"
                    :loading="downloadLoading"
                    :disabled="book.download_status === 'downloading'"
                  >
                    <template #icon>
                      <n-icon><DownloadOutline /></n-icon>
                    </template>
                    {{ book.download_status === 'completed' ? '重新下载' : '开始下载' }}
                  </n-button>
                  
                  <n-button 
                    v-if="book.download_status === 'completed'"
                    @click="startUpdate"
                    :loading="updateLoading"
                  >
                    <template #icon>
                      <n-icon><RefreshOutline /></n-icon>
                    </template>
                    检查更新
                  </n-button>
                  
                  <n-button 
                    v-if="book.download_status === 'completed'"
                    @click="generateEpub"
                    :loading="generating"
                  >
                    <template #icon>
                      <n-icon><DocumentOutline /></n-icon>
                    </template>
                    生成 EPUB
                  </n-button>
                  
                  <n-button 
                    v-if="book.epub_path"
                    type="success"
                    @click="downloadEpub"
                  >
                    下载 EPUB
                  </n-button>
                  
                  <n-popconfirm @positive-click="deleteBook">
                    <template #trigger>
                      <n-button type="error" ghost>
                        <template #icon>
                          <n-icon><TrashOutline /></n-icon>
                        </template>
                        删除
                      </n-button>
                    </template>
                    确定要删除这本书吗？所有已下载的章节都将被删除。
                  </n-popconfirm>
                </n-space>
              </div>
            </n-space>
          </n-card>

          <!-- 下载状态提示 -->
          <n-alert 
            v-if="book.download_status === 'downloading'" 
            type="info" 
            title="下载进行中..."
          >
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            已下载 {{ book.downloaded_chapters || 0 }}/{{ book.total_chapters || 0 }} 章节
            ({{ getProgressPercent() }}%)
          </n-alert>

          <!-- 章节下载状态热力图 -->
          <n-card v-if="chapterSummary.segments && chapterSummary.segments.length > 0" title="章节下载状态">
            <template #header-extra>
              <n-space :size="16">
                <span class="legend-item"><span class="legend-color bg-green-500"></span>已完成</span>
                <span class="legend-item"><span class="legend-color bg-yellow-400"></span>部分完成</span>
                <span class="legend-item"><span class="legend-color bg-gray-300"></span>未下载</span>
                <span class="legend-item"><span class="legend-color bg-red-400"></span>有失败</span>
              </n-space>
            </template>
            
            <div class="heatmap-container">
              <n-tooltip 
                v-for="(segment, index) in chapterSummary.segments" 
                :key="index"
                trigger="hover"
              >
                <template #trigger>
                  <div
                    class="heatmap-cell"
                    :class="[getSegmentClass(segment), { 'ring-selected': isSegmentSelected(segment) }]"
                    @click="selectSegment(segment)"
                  />
                </template>
                <div>
                  <div style="font-weight: 500;">第 {{ segment.start_index + 1 }} - {{ segment.end_index + 1 }} 章</div>
                  <div style="color: #999; margin-top: 4px;">
                    {{ segment.first_chapter_title }}
                    <template v-if="segment.first_chapter_title !== segment.last_chapter_title">
                      ~ {{ segment.last_chapter_title }}
                    </template>
                  </div>
                  <div style="margin-top: 4px;">
                    <span style="color: #52c41a;">已完成: {{ segment.completed }}</span> / 
                    <span style="color: #999;">待下载: {{ segment.pending }}</span>
                    <span v-if="segment.failed > 0" style="color: #ff4d4f;"> / 失败: {{ segment.failed }}</span>
                  </div>
                </div>
              </n-tooltip>
            </div>
          </n-card>

          <!-- 章节范围选择器 -->
          <n-card v-if="book.total_chapters > 0" title="选择下载范围">
            <template #header-extra>
              <n-icon><GridOutline /></n-icon>
            </template>
            
            <n-space vertical :size="16">
              <n-space :size="24">
                <n-space style="align-items: center;">
                  <span>起始章节:</span>
                  <n-input-number 
                    v-model:value="startChapter"
                    :min="1" 
                    :max="book.total_chapters"
                    @update:value="validateRange"
                    style="width: 100px;"
                  />
                  <span>章</span>
                  <n-button size="small" text @click="startChapter = 1">第一章</n-button>
                </n-space>
                
                <n-space style="align-items: center;">
                  <span>结束章节:</span>
                  <n-input-number 
                    v-model:value="endChapter"
                    :min="1" 
                    :max="book.total_chapters"
                    @update:value="validateRange"
                    style="width: 100px;"
                  />
                  <span>章</span>
                  <n-button size="small" text @click="endChapter = book.total_chapters">最后一章</n-button>
                </n-space>
              </n-space>
              
              <!-- 快捷选择按钮 -->
              <n-space>
                <n-button size="small" @click="selectAll">全选</n-button>
                <n-button v-if="book.total_chapters >= 100" size="small" @click="selectRange(1, 100)">前100章</n-button>
                <n-button v-if="book.total_chapters >= 500" size="small" @click="selectRange(1, 500)">前500章</n-button>
                <n-button v-if="book.total_chapters >= 100" size="small" @click="selectLastN(100)">最新100章</n-button>
              </n-space>
              
              <n-divider style="margin: 8px 0;" />
              
              <!-- 选择信息和下载按钮 -->
              <n-space justify="space-between" align="center">
                <span style="color: #666;">
                  已选择 <span style="color: #1890ff; font-weight: 500;">{{ getSelectedCount() }}</span> 章
                  <span style="color: #999; margin-left: 8px;">(第 {{ startChapter }} - {{ endChapter }} 章)</span>
                </span>
                <n-button 
                  type="primary"
                  @click="downloadSelectedRange"
                  :loading="downloadLoading"
                  :disabled="book.download_status === 'downloading' || getSelectedCount() === 0"
                >
                  <template #icon>
                    <n-icon><DownloadOutline /></n-icon>
                  </template>
                  下载选中章节
                </n-button>
              </n-space>
            </n-space>
          </n-card>

          <!-- 简介 -->
          <n-card v-if="book.intro" title="简介">
            <p style="white-space: pre-wrap; color: #666;">{{ book.intro }}</p>
          </n-card>
        </n-space>
      </template>
    </n-spin>
  </div>
</template>

<style scoped>
.book-detail-view {
  max-width: 900px;
  margin: 0 auto;
}

.heatmap-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.heatmap-cell {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.heatmap-cell:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.ring-selected {
  box-shadow: 0 0 0 2px #1890ff;
}

.bg-green-500 { background-color: #52c41a; }
.bg-green-400 { background-color: #73d13d; }
.bg-yellow-400 { background-color: #fadb14; }
.bg-yellow-300 { background-color: #fff566; }
.bg-gray-300 { background-color: #d9d9d9; }
.bg-red-400 { background-color: #ff7875; }

.legend-item {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.legend-color {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
  margin-right: 4px;
}
</style>
