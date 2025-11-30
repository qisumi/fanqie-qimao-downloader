import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as bookApi from '@/api/books'

export const useBookStore = defineStore('book', () => {
  const books = ref([])
  const currentBook = ref(null)
  const loading = ref(false)
  const searchResults = ref([])
  const searchLoading = ref(false)
  
  // 按平台分组
  const booksByPlatform = computed(() => {
    const grouped = { fanqie: [], qimao: [] }
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
      // 后端返回 {book: {...}, chapters: [...], statistics: {...}}
      // 合并 book 和 statistics 信息
      const data = response.data
      currentBook.value = {
        ...data.book,
        chapters: data.chapters || [],
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
   * 删除书籍
   */
  async function deleteBook(id) {
    await bookApi.deleteBook(id)
    const index = books.value.findIndex(b => b.id === id)
    if (index !== -1) {
      books.value.splice(index, 1)
    }
    if (currentBook.value?.id === id) {
      currentBook.value = null
    }
  }
  
  /**
   * 生成 EPUB
   */
  async function generateEpub(id) {
    const response = await bookApi.generateEpub(id)
    return response.data
  }
  
  /**
   * 清除搜索结果
   */
  function clearSearch() {
    searchResults.value = []
  }
  
  /**
   * 更新当前书籍的下载进度
   */
  function updateCurrentBookProgress(progress) {
    if (currentBook.value) {
      if (progress.downloaded_chapters !== undefined) {
        currentBook.value.downloaded_chapters = progress.downloaded_chapters
      }
      if (progress.total_chapters !== undefined) {
        currentBook.value.total_chapters = progress.total_chapters
      }
      if (progress.download_status !== undefined) {
        currentBook.value.download_status = progress.download_status
      }
      if (progress.status !== undefined) {
        currentBook.value.download_status = progress.status
      }
    }
  }
  
  return {
    books,
    currentBook,
    loading,
    searchResults,
    searchLoading,
    booksByPlatform,
    booksByStatus,
    fetchBooks,
    fetchBook,
    searchBooks,
    addBook,
    deleteBook,
    generateEpub,
    clearSearch,
    updateCurrentBookProgress
  }
})
