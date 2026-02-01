/**
 * Book Filter Composable
 * Reusable filter logic for book lists
 */
import { ref, computed } from 'vue'

export function useBookFilters(books, userBooks = null) {
  // Filter state
  const filterPlatform = ref(null)
  const filterStatus = ref(null)
  const searchKeyword = ref('')
  const showFilters = ref(false)

  // Filter options
  const platformOptions = [
    { label: '全部平台', value: null },
    { label: '番茄小说', value: 'fanqie' },
    { label: '七猫小说', value: 'qimao' },
    { label: '笔趣阁', value: 'biquge' },
    { label: '本地上传', value: 'local' }
  ]

  const statusOptions = [
    { label: '全部状态', value: null },
    { label: '已完成', value: 'completed' },
    { label: '下载中', value: 'downloading' },
    { label: '未开始', value: 'pending' }
  ]

  /**
   * Filter books based on current filter criteria
   */
  function filterBooks(list) {
    let result = list

    if (filterPlatform.value) {
      result = result.filter(b => b.platform === filterPlatform.value)
    }

    if (filterStatus.value) {
      result = result.filter(b => b.download_status === filterStatus.value)
    }

    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      result = result.filter(b =>
        b.title.toLowerCase().includes(keyword) ||
        b.author.toLowerCase().includes(keyword)
      )
    }

    return result
  }

  // Computed properties
  const filteredBooks = computed(() => filterBooks(books.value || []))
  const filteredUserBooks = computed(() => {
    if (userBooks) {
      return filterBooks(userBooks.value || [])
    }
    return []
  })

  const hasFilters = computed(() => {
    return filterPlatform.value || filterStatus.value || searchKeyword.value
  })

  /**
   * Clear all filters
   */
  function clearFilters() {
    filterPlatform.value = null
    filterStatus.value = null
    searchKeyword.value = ''
  }

  return {
    // State
    filterPlatform,
    filterStatus,
    searchKeyword,
    showFilters,

    // Options
    platformOptions,
    statusOptions,

    // Computed
    filteredBooks,
    filteredUserBooks,
    hasFilters,

    // Methods
    clearFilters,
    filterBooks
  }
}
