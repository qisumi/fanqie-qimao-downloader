import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as bookApi from '@/api/books'
import * as userApi from '@/api/users'

export const useBookStore = defineStore('book', () => {
  const books = ref([])
  const userBooks = ref([])
  const currentBook = ref(null)
  const loading = ref(false)
  const userBooksLoading = ref(false)
  const searchResults = ref([])
  const searchLoading = ref(false)
  
  // 按平台分组
  const booksByPlatform = computed(() => {
    const grouped = { fanqie: [], qimao: [], biquge: [] }
    books.value.forEach(book => {
      if (grouped[book.platform]) {
        grouped[book.platform].push(book)
      }
    })
    return grouped
  })
  
  // 按状态分组
  const booksByStatus = computed(() => {
    const grouped = { downloading: [], completed: [], pending: [] }
    books.value.forEach(book => {
      const key = book.download_status || 'pending'
      if (grouped[key]) {
        grouped[key].push(book)
      }
    })
    return grouped
  })

  const userBookIds = computed(() => new Set(userBooks.value.map(b => b.id)))
  
  /**
   * 获取书籍列表
   */
  async function fetchBooks(params = {}) {
    loading.value = true
    try {
      const response = await bookApi.listBooks(params)
      // 后端返回 {books: [...], total, page, limit, pages}
      books.value = response.data.books || []
    } catch (error) {
      console.error('Failed to fetch books:', error)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取书籍详情
   */
  async function fetchBook(id) {
    loading.value = true
    try {
      const response = await bookApi.getBook(id)
      // 后端返回 {book: {...}, statistics: {...}}，不再附带完整章节列表
      const data = response.data
      currentBook.value = {
        ...data.book,
        statistics: data.statistics || {}
      }
      return currentBook.value
    } catch (error) {
      console.error('Failed to fetch book:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 刷新书籍信息
   */
  async function refreshBook(id) {
    try {
      const response = await bookApi.refreshBook(id)
      const updatedBook = response.data
      const index = books.value.findIndex(b => b.id === id)
      if (index !== -1) {
        books.value[index] = { ...books.value[index], ...updatedBook }
      }
      if (currentBook.value?.id === id) {
        Object.assign(currentBook.value, updatedBook)
      }
      return updatedBook
    } catch (error) {
      console.error('Failed to refresh book:', error)
      throw error
    }
  }
  
  /**
   * 搜索书籍
   */
  async function searchBooks(platform, keyword, page = 0) {
    searchLoading.value = true
    try {
      const response = await bookApi.searchBooks(platform, keyword, page)
      // 后端返回 {books: [...], total, page, platform}
      searchResults.value = response.data.books || []
      return response.data
    } catch (error) {
      console.error('Failed to search books:', error)
      searchResults.value = []
      throw error
    } finally {
      searchLoading.value = false
    }
  }
  
  /**
   * 添加书籍
   */
  async function addBook(platform, bookId) {
    const response = await bookApi.addBook(platform, bookId)
    const book = response.data
    books.value.unshift(book)
    return book
  }
  
  /**
   * 上传书籍
   */
  async function uploadBook(data) {
    const response = await bookApi.uploadBook(data)
    const book = response.data
    books.value.unshift(book)
    return book
  }
  
  /**
   * 删除书籍
   */
  async function deleteBook(id) {
    await bookApi.deleteBook(id)
    const index = books.value.findIndex(b => b.id === id)
    if (index !== -1) {
      books.value.splice(index, 1)
    }
    const userIndex = userBooks.value.findIndex(b => b.id === id)
    if (userIndex !== -1) {
      userBooks.value.splice(userIndex, 1)
    }
    if (currentBook.value?.id === id) {
      currentBook.value = null
    }
  }

  /**
   * 获取私人书架
   */
  async function fetchUserBooks(userId, params = {}) {
    if (!userId) {
      userBooks.value = []
      return
    }
    userBooksLoading.value = true
    try {
      const response = await userApi.listUserBooks(userId, params)
      userBooks.value = response.data.books || []
    } catch (error) {
      console.error('Failed to fetch user books:', error)
      userBooks.value = []
    } finally {
      userBooksLoading.value = false
    }
  }

  /**
   * 加入私人书架
   */
  async function addToUserShelf(userId, bookId) {
    if (!userId) throw new Error('未选择用户')
    const response = await userApi.addBookToUser(userId, bookId)
    const payload = response.data?.book || response.data?.data?.book
    const existing = userBooks.value.find(b => b.id === bookId)
    const publicBook = books.value.find(b => b.id === bookId)
    const book = existing || publicBook || payload
    if (book && !userBookIds.value.has(bookId)) {
      userBooks.value.unshift(book)
    }
    return book
  }

  /**
   * 从私人书架移除
   */
  async function removeFromUserShelf(userId, bookId) {
    if (!userId) throw new Error('未选择用户')
    await userApi.removeBookFromUser(userId, bookId)
    const index = userBooks.value.findIndex(b => b.id === bookId)
    if (index !== -1) {
      userBooks.value.splice(index, 1)
    }
  }

  function isInUserShelf(bookId) {
    return userBookIds.value.has(bookId)
  }
  
  // EPUB/TXT 生成由后端在下载时自动处理，前端仅提供下载操作
  
  /**
   * 清除搜索结果
   */
  function clearSearch() {
    searchResults.value = []
  }
  
  /**
   * 更新当前书籍的下载进度
   * 注意：只更新明确传入的字段，不要将任务状态(status)映射到书籍下载状态(download_status)
   */
  function updateCurrentBookProgress(progress) {
    if (currentBook.value) {
      if (progress.downloaded_chapters !== undefined) {
        currentBook.value.task_downloaded_chapters = progress.downloaded_chapters
      }
      if (progress.total_chapters !== undefined) {
        currentBook.value.task_total_chapters = progress.total_chapters
      }
      if (progress.task_downloaded_chapters !== undefined) {
        currentBook.value.task_downloaded_chapters = progress.task_downloaded_chapters
      }
      if (progress.task_total_chapters !== undefined) {
        currentBook.value.task_total_chapters = progress.task_total_chapters
      }
      if (progress.download_status !== undefined) {
        currentBook.value.download_status = progress.download_status
      }
      // 注意：不再将 progress.status 映射到 download_status
      // 任务状态(running/pending/completed)与书籍下载状态(downloading/completed/failed)是不同的概念
    }

    const targetId = progress.book_id || currentBook.value?.id
    const index = targetId ? userBooks.value.findIndex(b => b.id === targetId) : -1
    if (index !== -1) {
      const target = userBooks.value[index]
      if (progress.downloaded_chapters !== undefined) {
        target.task_downloaded_chapters = progress.downloaded_chapters
      }
      if (progress.total_chapters !== undefined) {
        target.task_total_chapters = progress.total_chapters
      }
      if (progress.task_downloaded_chapters !== undefined) {
        target.task_downloaded_chapters = progress.task_downloaded_chapters
      }
      if (progress.task_total_chapters !== undefined) {
        target.task_total_chapters = progress.task_total_chapters
      }
      if (progress.download_status !== undefined) {
        target.download_status = progress.download_status
      }
    }
  }
  
  return {
    books,
    userBooks,
    currentBook,
    loading,
    userBooksLoading,
    searchResults,
    searchLoading,
    booksByPlatform,
    booksByStatus,
    fetchBooks,
    fetchBook,
    searchBooks,
    addBook,
    uploadBook,
    deleteBook,
    fetchUserBooks,
    addToUserShelf,
    removeFromUserShelf,
    isInUserShelf,
    clearSearch,
    updateCurrentBookProgress,
    refreshBook
  }
})
