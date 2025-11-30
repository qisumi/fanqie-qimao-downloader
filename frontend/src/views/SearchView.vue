<script setup>
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NInput, NInputGroup, NButton, NSelect, 
  NEmpty, NSpin, NIcon,
  useMessage
} from 'naive-ui'
import { SearchOutline, ChevronDownOutline } from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'

// 子组件
import SearchResultItem from '@/components/SearchResultItem.vue'

const router = useRouter()
const message = useMessage()
const bookStore = useBookStore()
const isMobile = inject('isMobile', ref(false))

const platform = ref('fanqie')
const keyword = ref('')
const currentPage = ref(0)
const addingBook = ref(null)

const platformOptions = [
  { label: '番茄小说', value: 'fanqie' },
  { label: '七猫小说', value: 'qimao' }
]

const searchResults = computed(() => bookStore.searchResults)
const loading = computed(() => bookStore.searchLoading)
const hasMore = computed(() => bookStore.searchResults.length > 0 && bookStore.searchResults.length % 10 === 0)

async function handleSearch() {
  if (!keyword.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }
  
  currentPage.value = 0
  await bookStore.searchBooks(platform.value, keyword.value.trim(), 0)
}

async function loadMore() {
  currentPage.value++
  await bookStore.searchBooks(platform.value, keyword.value.trim(), currentPage.value)
}

async function addToLibrary(book) {
  addingBook.value = book.book_id
  try {
    const newBook = await bookStore.addBook(platform.value, book.book_id)
    message.success(`《${book.book_name || book.title}》已添加到书库`)
  } catch (error) {
    const msg = error.response?.data?.detail || '添加失败'
    message.error(msg)
  } finally {
    addingBook.value = null
  }
}
</script>

<template>
  <div class="search-view">
    <!-- 搜索区域 -->
    <div class="search-header">
      <h2 class="page-title">搜索书籍</h2>
      <p class="page-desc">在番茄小说和七猫小说中搜索你想要的书籍</p>
      
      <div class="search-form">
        <!-- 移动端竖排布局 -->
        <template v-if="isMobile">
          <n-select 
            v-model:value="platform" 
            :options="platformOptions" 
            class="platform-select mobile-full"
            size="large"
          />
          <div class="search-input-group">
            <n-input 
              v-model:value="keyword" 
              placeholder="输入书名或作者"
              @keyup.enter="handleSearch"
              clearable
              size="large"
              class="search-input"
            >
              <template #prefix>
                <n-icon :size="18" color="#999"><SearchOutline /></n-icon>
              </template>
            </n-input>
            <n-button 
              type="primary" 
              size="large"
              @click="handleSearch" 
              :loading="loading"
              class="search-btn"
            >
              搜索
            </n-button>
          </div>
        </template>
        
        <!-- 桌面端横排布局 -->
        <template v-else>
          <n-input-group class="search-input-group-desktop">
            <n-select 
              v-model:value="platform" 
              :options="platformOptions" 
              class="platform-select"
              size="large"
            />
            <n-input 
              v-model:value="keyword" 
              placeholder="输入书名或作者"
              @keyup.enter="handleSearch"
              clearable
              size="large"
            >
              <template #prefix>
                <n-icon :size="18" color="#999"><SearchOutline /></n-icon>
              </template>
            </n-input>
            <n-button 
              type="primary" 
              size="large"
              @click="handleSearch" 
              :loading="loading"
            >
              <template #icon>
                <n-icon><SearchOutline /></n-icon>
              </template>
              搜索
            </n-button>
          </n-input-group>
        </template>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div class="search-results">
      <n-spin :show="loading && currentPage === 0">
        <template v-if="searchResults.length > 0">
          <div class="results-header">
            <span class="results-count">找到 {{ searchResults.length }} 本书籍</span>
          </div>
          
          <div class="book-list">
            <SearchResultItem
              v-for="book in searchResults"
              :key="book.book_id"
              :book="book"
              :platform="platform"
              :adding="addingBook === book.book_id"
              @add="addToLibrary"
            />
          </div>
          
          <!-- 加载更多 -->
          <div v-if="hasMore" class="load-more">
            <n-button 
              @click="loadMore" 
              :loading="loading"
              size="large"
              round
            >
              <template #icon>
                <n-icon><ChevronDownOutline /></n-icon>
              </template>
              加载更多
            </n-button>
          </div>
        </template>
        
        <n-empty v-else class="empty-state">
          <template #icon>
            <n-icon :size="64" color="#ddd"><SearchOutline /></n-icon>
          </template>
          <template #description>
            <span class="empty-text">暂无搜索结果，请输入关键词搜索</span>
          </template>
        </n-empty>
      </n-spin>
    </div>
  </div>
</template>

<style scoped>
.search-view {
  max-width: 900px;
  margin: 0 auto;
}

/* 搜索头部 */
.search-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 32px;
  border-radius: var(--border-radius-xl, 16px);
  color: white;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.page-desc {
  font-size: 14px;
  opacity: 0.85;
  margin: 0 0 24px 0;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.platform-select {
  width: 140px;
}

.mobile-full {
  width: 100%;
}

.search-input-group {
  display: flex;
  gap: 12px;
}

.search-input {
  flex: 1;
}

.search-btn {
  flex-shrink: 0;
}

.search-input-group-desktop {
  display: flex;
}

.search-input-group-desktop .platform-select {
  width: 140px;
}

/* 搜索结果 */
.search-results {
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  padding: 20px;
  box-shadow: var(--shadow-card);
}

.results-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light, #efeff5);
}

.results-count {
  font-size: 14px;
  color: var(--text-color-secondary, #666);
}

/* 书籍列表 */
.book-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 加载更多 */
.load-more {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 空状态 */
.empty-state {
  padding: 60px 20px;
}

.empty-text {
  color: var(--text-color-tertiary, #999);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .search-header {
    padding: 24px 16px;
    border-radius: var(--border-radius-lg, 12px);
    margin-bottom: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .page-desc {
    margin-bottom: 20px;
  }
  
  .search-results {
    padding: 16px;
  }
  
  .empty-state {
    padding: 40px 16px;
  }
}
</style>
