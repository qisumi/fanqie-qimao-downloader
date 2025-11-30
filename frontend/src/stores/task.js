import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as taskApi from '@/api/tasks'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const loading = ref(false)
  const wsConnections = ref(new Map())
  
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
      // 后端返回 { tasks: [...], total, page, limit }
      tasks.value = response.data.tasks || []
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
    if (wsConnections.value.has(taskId)) return
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/tasks/${taskId}`)
    
    ws.onopen = () => {
      console.log(`WebSocket connected for task ${taskId}`)
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'progress') {
        updateTaskProgress(taskId, data.data)
      } else if (data.type === 'completed') {
        handleTaskCompleted(taskId, data.data)
      }
    }
    
    ws.onerror = (error) => {
      console.error(`WebSocket error for task ${taskId}:`, error)
    }
    
    ws.onclose = () => {
      console.log(`WebSocket closed for task ${taskId}`)
      wsConnections.value.delete(taskId)
    }
    
    wsConnections.value.set(taskId, ws)
  }
  
  /**
   * 断开 WebSocket 连接
   */
  function disconnectWebSocket(taskId) {
    const ws = wsConnections.value.get(taskId)
    if (ws) {
      ws.close()
      wsConnections.value.delete(taskId)
    }
  }
  
  /**
   * 断开所有连接
   */
  function disconnectAll() {
    wsConnections.value.forEach((ws, taskId) => {
      ws.close()
    })
    wsConnections.value.clear()
  }
  
  /**
   * 更新任务进度
   */
  function updateTaskProgress(taskId, progress) {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      Object.assign(task, progress)
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
    const task = response.data
    tasks.value.unshift(task)
    connectWebSocket(task.id)
    return task
  }
  
  /**
   * 启动更新任务
   */
  async function startUpdate(bookId) {
    const response = await taskApi.startUpdate(bookId)
    const task = response.data
    tasks.value.unshift(task)
    connectWebSocket(task.id)
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
    startUpdate,
    cancelTask
  }
})
