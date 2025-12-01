import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as taskApi from '@/api/tasks'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const loading = ref(false)
  // taskId -> connection meta: { ws, heartbeat, reconnectAttempts, reconnectTimer, pollTimer }
  const wsConnections = ref(new Map())
  const maxReconnectAttempts = 5
  const heartbeatIntervalMs = 15000
  
  // 活跃任务（运行中或等待中）
  const activeTasks = computed(() => 
    tasks.value.filter(t => t.status === 'running' || t.status === 'pending')
  )
  
  // 已完成任务
  const completedTasks = computed(() => 
    tasks.value.filter(t => t.status === 'completed' || t.status === 'failed')
  )
  
  /**
   * 获取任务列表
   */
  async function fetchTasks() {
    loading.value = true
    try {
      const response = await taskApi.listTasks()
      const serverTasks = response.data.tasks || []
      
      // 合并服务器任务和本地新创建的任务
      // 本地任务可能还没同步到服务器（刚创建），需要保留
      const serverTaskIds = new Set(serverTasks.map(t => t.id))
      const localOnlyTasks = tasks.value.filter(t => 
        !serverTaskIds.has(t.id) && 
        (t.status === 'pending' || t.status === 'running')
      )
      
      // 服务器任务优先，再加上本地独有的活跃任务
      tasks.value = [...serverTasks, ...localOnlyTasks]
      
      // 为活跃任务建立 WebSocket 连接
      activeTasks.value.forEach(t => connectWebSocket(t.id))
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 建立 WebSocket 连接
   */
  function connectWebSocket(taskId) {
    if (!taskId) return
    
    const existing = wsConnections.value.get(taskId)
    if (existing?.ws && (
      existing.ws.readyState === WebSocket.OPEN || 
      existing.ws.readyState === WebSocket.CONNECTING
    )) {
      return
    }
    
    cleanupConnection(taskId)
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    let ws
    try {
      ws = new WebSocket(`${protocol}//${window.location.host}/ws/tasks/${taskId}`)
    } catch (error) {
      console.error(`Failed to create WebSocket for task ${taskId}:`, error)
      startPolling(taskId)
      return
    }
    
    const connection = {
      ws,
      heartbeat: null,
      reconnectAttempts: existing?.reconnectAttempts || 0,
      reconnectTimer: null,
      pollTimer: null,
    }
    wsConnections.value.set(taskId, connection)
    
    ws.onopen = () => {
      console.log(`WebSocket connected for task ${taskId}`)
      connection.reconnectAttempts = 0
      stopPolling(taskId)
      startHeartbeat(taskId)
    }
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        switch (data.type) {
          case 'progress':
            updateTaskProgress(taskId, data.data)
            break
          case 'completed':
            handleTaskCompleted(taskId, data.data)
            stopHeartbeat(taskId)
            stopPolling(taskId)
            break
          case 'pong':
            // 心跳响应
            break
          default:
            console.warn(`Unknown WebSocket message for task ${taskId}:`, data.type)
        }
      } catch (error) {
        console.error(`Failed to parse WebSocket message for task ${taskId}:`, error)
      }
    }
    
    ws.onerror = (error) => {
      console.error(`WebSocket error for task ${taskId}:`, error)
      stopHeartbeat(taskId)
    }
    
    ws.onclose = (event) => {
      console.log(`WebSocket closed for task ${taskId}:`, event.code, event.reason)
      stopHeartbeat(taskId)
      stopPolling(taskId)
      
      const existingConnection = wsConnections.value.get(taskId) || { reconnectAttempts: 0 }
      existingConnection.ws = null
      wsConnections.value.set(taskId, existingConnection)
      
      if (event.code === 4001) {
        console.error(`WebSocket unauthorized for task ${taskId}, falling back to polling`)
        startPolling(taskId)
        return
      }
      
      if (isTaskActive(taskId)) {
        attemptReconnect(taskId)
      } else {
        wsConnections.value.delete(taskId)
      }
    }
  }
  
  /**
   * 断开 WebSocket 连接
   */
  function disconnectWebSocket(taskId) {
    const connection = wsConnections.value.get(taskId)
    if (connection?.ws) {
      connection.ws.close()
    }
    cleanupConnection(taskId)
  }
  
  /**
   * 断开所有连接
   */
  function disconnectAll() {
    wsConnections.value.forEach((_conn, taskId) => {
      disconnectWebSocket(taskId)
    })
    wsConnections.value.clear()
  }

  function cleanupConnection(taskId) {
    const connection = wsConnections.value.get(taskId)
    if (!connection) return
    
    stopHeartbeat(taskId)
    stopPolling(taskId)
    
    if (connection.reconnectTimer) {
      clearTimeout(connection.reconnectTimer)
    }
    
    if (connection.ws && (
      connection.ws.readyState === WebSocket.OPEN ||
      connection.ws.readyState === WebSocket.CONNECTING
    )) {
      connection.ws.close()
    }
    
    wsConnections.value.delete(taskId)
  }
  
  function isTaskActive(taskId) {
    const task = tasks.value.find(t => t.id === taskId)
    return task && (task.status === 'running' || task.status === 'pending')
  }
  
  function attemptReconnect(taskId) {
    const connection = wsConnections.value.get(taskId) || { reconnectAttempts: 0 }
    if (connection.reconnectAttempts >= maxReconnectAttempts) {
      console.warn(`Max reconnect attempts reached for task ${taskId}, switching to polling`)
      startPolling(taskId)
      return
    }
    
    const delay = Math.min(1000 * Math.pow(2, connection.reconnectAttempts), 30000)
    connection.reconnectAttempts += 1
    connection.reconnectTimer = setTimeout(() => {
      connectWebSocket(taskId)
    }, delay)
    wsConnections.value.set(taskId, connection)
  }
  
  function startHeartbeat(taskId) {
    const connection = wsConnections.value.get(taskId)
    if (!connection?.ws) return
    
    stopHeartbeat(taskId)
    connection.heartbeat = setInterval(() => {
      if (connection.ws?.readyState === WebSocket.OPEN) {
        try {
          connection.ws.send(JSON.stringify({ type: 'ping' }))
        } catch (error) {
          console.error(`Failed to send heartbeat for task ${taskId}:`, error)
        }
      }
    }, heartbeatIntervalMs)
  }
  
  function stopHeartbeat(taskId) {
    const connection = wsConnections.value.get(taskId)
    if (connection?.heartbeat) {
      clearInterval(connection.heartbeat)
      connection.heartbeat = null
    }
  }
  
  function startPolling(taskId) {
    const connection = wsConnections.value.get(taskId) || { reconnectAttempts: 0 }
    if (connection.pollTimer) return
    
    connection.pollTimer = setInterval(() => refreshTaskStatus(taskId), 3000)
    wsConnections.value.set(taskId, connection)
  }
  
  function stopPolling(taskId) {
    const connection = wsConnections.value.get(taskId)
    if (connection?.pollTimer) {
      clearInterval(connection.pollTimer)
      connection.pollTimer = null
    }
  }
  
  async function refreshTaskStatus(taskId) {
    if (!taskId) return
    try {
      const response = await taskApi.getTask(taskId)
      const data = response.data
      if (!data) return
      
      const task = tasks.value.find(t => t.id === taskId)
      if (task) {
        Object.assign(task, data)
      } else {
        tasks.value.unshift(data)
      }
      
      if (!isTaskActive(taskId)) {
        stopPolling(taskId)
        disconnectWebSocket(taskId)
      }
    } catch (error) {
      console.error(`Failed to refresh task ${taskId}:`, error)
    }
  }
  
  /**
   * 更新任务进度
   */
  function updateTaskProgress(taskId, progress) {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      // 更新进度相关字段
      if (progress.status !== undefined) task.status = progress.status
      if (progress.total_chapters !== undefined) task.total_chapters = progress.total_chapters
      if (progress.downloaded_chapters !== undefined) task.downloaded_chapters = progress.downloaded_chapters
      if (progress.failed_chapters !== undefined) task.failed_chapters = progress.failed_chapters
      if (progress.progress !== undefined) task.progress = progress.progress
      if (progress.error_message !== undefined) task.error_message = progress.error_message
      if (progress.book_title !== undefined) task.book_title = progress.book_title
    }
  }
  
  /**
   * 处理任务完成
   */
  function handleTaskCompleted(taskId, result) {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.status = result.success ? 'completed' : 'failed'
      task.message = result.message
    }
    disconnectWebSocket(taskId)
  }
  
  /**
   * 启动下载任务
   * @param {string} bookId - 书籍UUID
   * @param {number} startChapter - 起始章节索引（可选，0-indexed）
   * @param {number} endChapter - 结束章节索引（可选，0-indexed）
   */
  async function startDownload(bookId, startChapter, endChapter) {
    const response = await taskApi.startDownload(bookId, startChapter, endChapter)
    const data = response.data || {}
    const taskId = data.task_id || data.id
    
    // 创建完整的任务对象，API返回的是简略信息
    const task = {
      id: taskId,
      book_id: data.book_id || bookId,
      task_type: 'download',
      status: 'pending',
      total_chapters: 0,
      downloaded_chapters: 0,
      failed_chapters: 0,
      progress: 0,
      created_at: new Date().toISOString(),
    }
    
    tasks.value.unshift(task)
    if (taskId) {
      connectWebSocket(taskId)
    }
    return task
  }
  
  /**
   * 取消任务
   */
  async function cancelTask(taskId) {
    await taskApi.cancelTask(taskId)
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.status = 'cancelled'
    }
    disconnectWebSocket(taskId)
  }
  
  return {
    tasks,
    loading,
    activeTasks,
    completedTasks,
    fetchTasks,
    connectWebSocket,
    disconnectWebSocket,
    disconnectAll,
    startDownload,
    cancelTask
  }
})
