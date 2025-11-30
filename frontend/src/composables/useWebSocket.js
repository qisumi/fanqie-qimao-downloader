import { ref, onMounted, onUnmounted } from 'vue'

/**
 * WebSocket 连接管理组合式函数
 * @param {string} url - WebSocket URL
 * @param {Object} options - 配置选项
 */
export function useWebSocket(url, options = {}) {
  const {
    autoConnect = true,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onMessage = null,
    onOpen = null,
    onClose = null,
    onError = null
  } = options

  const ws = ref(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const lastMessage = ref(null)

  let reconnectTimer = null

  function connect() {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const fullUrl = url.startsWith('ws') ? url : `${protocol}//${window.location.host}${url}`
    
    ws.value = new WebSocket(fullUrl)

    ws.value.onopen = (event) => {
      isConnected.value = true
      reconnectAttempts.value = 0
      onOpen?.(event)
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        lastMessage.value = data
        onMessage?.(data, event)
      } catch (e) {
        // 如果不是 JSON，直接传递原始数据
        lastMessage.value = event.data
        onMessage?.(event.data, event)
      }
    }

    ws.value.onclose = (event) => {
      isConnected.value = false
      onClose?.(event)

      // 尝试重连
      if (reconnect && reconnectAttempts.value < maxReconnectAttempts) {
        reconnectTimer = setTimeout(() => {
          reconnectAttempts.value++
          connect()
        }, reconnectInterval)
      }
    }

    ws.value.onerror = (event) => {
      onError?.(event)
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    
    isConnected.value = false
  }

  function send(data) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      ws.value.send(message)
      return true
    }
    return false
  }

  // 发送心跳
  function ping() {
    return send({ type: 'ping' })
  }

  onMounted(() => {
    if (autoConnect) {
      connect()
    }
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    isConnected,
    lastMessage,
    reconnectAttempts,
    connect,
    disconnect,
    send,
    ping
  }
}

export default useWebSocket
