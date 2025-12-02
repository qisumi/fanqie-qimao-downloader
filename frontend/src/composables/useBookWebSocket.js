import { ref, watch, onUnmounted } from 'vue'
import { getBookStatus } from '@/api/books'

/**
 * 书籍下载进度 WebSocket 管理
 * @param {Object} options
 * @param {import('vue').Ref} options.book - 书籍响应式引用
 * @param {Function} options.onProgress - 进度更新回调
 * @param {Function} options.onCompleted - 完成回调
 * @param {Function} options.onError - 错误回调
 * @param {Function} options.loadChapterSummary - 加载章节摘要回调
 */
export function useBookWebSocket(options) {
  const { book, onProgress, onCompleted, onError, loadChapterSummary } = options

  let websocket = null
  let heartbeatInterval = null
  let pollInterval = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 5
  const wsConnected = ref(false)

  // 获取 WebSocket URL
  function getWebSocketUrl() {
    if (!book.value) return null
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws/books/${book.value.id}`
  }

  // 连接 WebSocket
  function connect() {
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
      cleanup()
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
      stopPolling()
      startHeartbeat()
    }

    websocket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type !== 'pong') {
          console.log('📨 WebSocket message:', msg.type, msg.data)
        }
        handleMessage(msg)
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

  // 处理 WebSocket 消息
  function handleMessage(msg) {
    switch (msg.type) {
      case 'progress':
        console.log('📊 Progress update:', msg.data)
        onProgress?.(msg.data)
        loadChapterSummary?.()
        break

      case 'completed':
        console.log('✅ Task completed:', msg.data)
        onCompleted?.(msg.data)
        disconnect()
        break

      case 'status':
        console.log('ℹ️ Book status:', msg.data)
        // 同步服务端状态，避免前端停留在过期的 downloading 状态导致循环重连
        if (book.value && msg.data) {
          Object.assign(book.value, msg.data)
        }
        // 如果服务器仍标记 downloading 但未返回任务进度，切换为轮询防止死循环
        if ((msg.data?.download_status || book.value?.download_status) === 'downloading') {
          console.log('🔄 Book downloading but no active task found, fallback to polling')
          startPolling()
        }
        break

      case 'error':
        console.error('❌ WebSocket error message:', msg.data)
        onError?.(msg.data)
        break

      case 'pong':
        // 心跳响应，不需要处理
        break

      default:
        console.warn('Unknown WebSocket message type:', msg.type)
    }
  }

  // 尝试重连
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
        connect()
      }
    }, delay)
  }

  // 心跳
  function startHeartbeat() {
    stopHeartbeat()
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

  // 清理 WebSocket 连接
  function cleanup() {
    if (websocket) {
      websocket.onopen = null
      websocket.onmessage = null
      websocket.onerror = null
      websocket.onclose = null
      websocket = null
    }
  }

  // 断开连接
  function disconnect() {
    console.log('🔌 Disconnecting WebSocket...')
    stopHeartbeat()
    if (websocket) {
      if (websocket.readyState === WebSocket.OPEN || websocket.readyState === WebSocket.CONNECTING) {
        websocket.close()
      }
      cleanup()
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
        await loadChapterSummary?.()

        if (data.book.download_status !== 'downloading') {
          stopPolling()
          if (data.book.download_status === 'completed') {
            onCompleted?.({ success: true, message: '下载完成！' })
          }
        }
      }
    } catch (error) {
      console.error('Refresh failed:', error)
    }
  }

  // 监听下载状态变化
  const stopWatch = watch(
    () => book.value?.download_status,
    (newStatus, oldStatus) => {
      console.log(`📡 Download status changed: ${oldStatus} -> ${newStatus}`)
      if (newStatus === 'downloading') {
        // 当状态变为 downloading 或初始加载时已是 downloading，尝试连接
        // oldStatus 为 undefined 表示是初始加载（页面刷新或重新进入）
        setTimeout(() => {
          if (!wsConnected.value && book.value?.download_status === 'downloading') {
            console.log('🔌 Initiating WebSocket connection for downloading book...')
            connect()
          }
        }, 100)
      } else if (oldStatus === 'downloading' && newStatus !== 'downloading') {
        // 只有从 downloading 变为其他状态时才断开
        disconnect()
        stopPolling()
      }
    },
    { immediate: true } // 立即执行一次，处理页面刷新或重新进入时书籍已在下载中的情况
  )

  // 组件卸载时清理
  onUnmounted(() => {
    stopWatch()
    disconnect()
    stopPolling()
  })

  return {
    wsConnected,
    connect,
    disconnect,
    refreshBookStatus
  }
}
