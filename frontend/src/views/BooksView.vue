<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NCard, NGrid, NGi, NSpace, NEmpty, NSpin, NButton, 
  NSelect, NInput, NIcon, NTag, NImage, NCollapse, NCollapseItem,
  useMessage
} from 'naive-ui'
import { RefreshOutline, TrashOutline, DownloadOutline, FilterOutline, SearchOutline } from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'
import { useTaskStore } from '@/stores/task'
import BookCard from '@/components/BookCard.vue'

const router = useRouter()
const message = useMessage()
const bookStore = useBookStore()
const taskStore = useTaskStore()
const isMobile = inject('isMobile', ref(false))

const filterPlatform = ref(null)
const filterStatus = ref(null)
const searchKeyword = ref('')
const showFilters = ref(false)

const platformOptions = [
  { label: '全部平台', value: null },
  { label: '番茄小说', value: 'fanqie' },
  { label: '七猫小说', value: 'qimao' }
]

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '已完成', value: 'completed' },
  { label: '下载中', value: 'downloading' },
  { label: '未开始', value: 'pending' }
]

const loading = computed(() => bookStore.loading)

const filteredBooks = computed(() => {
  let result = bookStore.books
  
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
})

const hasFilters = computed(() => {
  return filterPlatform.value || filterStatus.value || searchKeyword.value
})

onMounted(() => {
  bookStore.fetchBooks()
})

async function refreshBooks() {
  await bookStore.fetchBooks()
  message.success('书库已刷新')
}

function goToDetail(book) {
  router.push({ name: 'book-detail', params: { id: book.id } })
}

async function startDownload(book) {
  try {
    await taskStore.startDownload(book.id)
    message.success(`《${book.title}》开始下载`)
  } catch (error) {
    message.error(error.response?.data?.detail || '启动下载失败')
  }
}

async function deleteBook(book) {
  try {
    await bookStore.deleteBook(book.id)
    message.success(`《${book.title}》已删除`)
  } catch (error) {
    message.error('删除失败')
  }
}

function clearFilters() {
  filterPlatform.value = null
  filterStatus.value = null
  searchKeyword.value = ''
}
</script>

<template>
  <div class="books-view">
    <!-- 页面标题和工具栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">我的书库</h2>
        <span class="book-count">共 {{ filteredBooks.length }} 本书</span>
      </div>
      <n-space :size="8">
        <n-button 
          v-if="isMobile"
          :type="showFilters ? 'primary' : 'default'"
          @click="showFilters = !showFilters"
        >
          <template #icon>
            <n-icon><FilterOutline /></n-icon>
          </template>
        </n-button>
        <n-button @click="refreshBooks" :loading="loading">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          <span class="hide-mobile">刷新</span>
        </n-button>
      </n-space>
    </div>

    <!-- 筛选工具栏 -->
    <transition name="slide-down">
      <div v-if="!isMobile || showFilters" class="filter-bar">
        <div class="filter-controls">
          <n-select 
            v-model:value="filterPlatform" 
            :options="platformOptions"
            class="filter-select"
            placeholder="选择平台"
          />
          <n-select 
            v-model:value="filterStatus" 
            :options="statusOptions"
            class="filter-select"
            placeholder="选择状态"
          />
          <n-input 
            v-model:value="searchKeyword" 
            placeholder="搜索书名/作者"
            clearable
            class="filter-input"
          >
            <template #prefix>
              <n-icon color="#999"><SearchOutline /></n-icon>
            </template>
          </n-input>
        </div>
        <n-button 
          v-if="hasFilters" 
          text 
          type="primary" 
          @click="clearFilters"
          class="clear-btn"
        >
          清除筛选
        </n-button>
      </div>
    </transition>

    <!-- 书籍列表 -->
    <n-spin :show="loading">
      <template v-if="filteredBooks.length > 0">
        <n-grid 
          :cols="isMobile ? 1 : 2" 
          :x-gap="16" 
          :y-gap="16"
          class="book-grid"
        >
          <n-gi 
            v-for="book in filteredBooks" 
            :key="book.id"
          >
            <BookCard 
              :book="book"
              :compact="isMobile"
              @click="goToDetail(book)"
              @download="startDownload(book)"
              @delete="deleteBook(book)"
            />
          </n-gi>
        </n-grid>
      </template>
      
      <n-empty v-else class="empty-state">
        <template #icon>
          <div class="empty-icon">📚</div>
        </template>
        <template #description>
          <span class="empty-text">{{ hasFilters ? '没有找到匹配的书籍' : '书库为空，去搜索添加一些书籍吧' }}</span>
        </template>
        <template #extra>
          <n-space :size="12">
            <n-button 
              v-if="hasFilters"
              @click="clearFilters"
            >
              清除筛选
            </n-button>
            <n-button 
              type="primary" 
              @click="router.push({ name: 'search' })"
            >
              搜索书籍
            </n-button>
          </n-space>
        </template>
      </n-empty>
    </n-spin>
  </div>
</template>

<style scoped>
.books-view {
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: var(--text-color-primary, #333);
}

.book-count {
  font-size: 14px;
  color: var(--text-color-tertiary, #999);
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  margin-bottom: 20px;
  box-shadow: var(--shadow-card);
  gap: 16px;
  flex-wrap: wrap;
}

.filter-controls {
  display: flex;
  gap: 12px;
  flex: 1;
  flex-wrap: wrap;
}

.filter-select {
  width: 130px;
}

.filter-input {
  width: 200px;
}

.clear-btn {
  flex-shrink: 0;
}

/* 书籍网格 */
.book-grid {
  animation: fadeIn 0.3s ease-out;
}

/* 空状态 */
.empty-state {
  padding: 80px 20px;
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  box-shadow: var(--shadow-card);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-text {
  color: var(--text-color-secondary, #666);
  font-size: 15px;
}

/* 动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .page-header {
    margin-bottom: 16px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .book-count {
    font-size: 12px;
  }
  
  .hide-mobile {
    display: none;
  }
  
  .filter-bar {
    flex-direction: column;
    padding: 12px 16px;
    margin-bottom: 16px;
  }
  
  .filter-controls {
    width: 100%;
  }
  
  .filter-select,
  .filter-input {
    width: 100%;
    flex: 1;
  }
  
  .clear-btn {
    width: 100%;
    margin-top: 4px;
  }
  
  .empty-state {
    padding: 60px 16px;
  }
  
  .empty-icon {
    font-size: 48px;
  }
}
</style>
