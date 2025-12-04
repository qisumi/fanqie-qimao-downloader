<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NGrid, NGi, NSpace, NEmpty, NSpin, NButton, 
  NSelect, NInput, NIcon, NTabs, NTabPane, NAlert, NTag,
  useMessage
} from 'naive-ui'
import { RefreshOutline, FilterOutline, SearchOutline } from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'
import { useTaskStore } from '@/stores/task'
import { useUserStore } from '@/stores/user'
import BookCard from '@/components/BookCard.vue'

const router = useRouter()
const message = useMessage()
const bookStore = useBookStore()
const taskStore = useTaskStore()
const userStore = useUserStore()
const isMobile = inject('isMobile', ref(false))

const filterPlatform = ref(null)
const filterStatus = ref(null)
const searchKeyword = ref('')
const showFilters = ref(false)
const activeTab = ref('public')

const platformOptions = [
  { label: '全部平台', value: null },
  { label: '番茄小说', value: 'fanqie' },
  { label: '七猫小说', value: 'qimao' },
  { label: '笔趣阁', value: 'biquge' }
]

const statusOptions = [
  { label: '全部状态', value: null },
  { label: '已完成', value: 'completed' },
  { label: '下载中', value: 'downloading' },
  { label: '未开始', value: 'pending' }
]

const loading = computed(() => bookStore.loading)
const userShelfLoading = computed(() => bookStore.userBooksLoading)

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

const filteredBooks = computed(() => filterBooks(bookStore.books))
const filteredUserBooks = computed(() => filterBooks(bookStore.userBooks))

const hasFilters = computed(() => {
  return filterPlatform.value || filterStatus.value || searchKeyword.value
})

const hasUser = computed(() => !!userStore.currentUserId)
const currentUserLabel = computed(() => userStore.currentUsername || '未选择')

onMounted(async () => {
  await userStore.initUserContext()
  await bookStore.fetchBooks()
  if (userStore.currentUserId) {
    await bookStore.fetchUserBooks(userStore.currentUserId)
  }
})

watch(
  () => userStore.currentUserId,
  async (id) => {
    if (id) {
      await bookStore.fetchUserBooks(id)
    } else {
      await bookStore.fetchUserBooks(null)
    }
  }
)

watch(activeTab, async (tab) => {
  if (tab === 'private' && userStore.currentUserId && bookStore.userBooks.length === 0) {
    await bookStore.fetchUserBooks(userStore.currentUserId)
  }
})

async function refreshBooks() {
  await bookStore.fetchBooks()
  if (userStore.currentUserId) {
    await bookStore.fetchUserBooks(userStore.currentUserId)
  }
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
    if (userStore.currentUserId) {
      await bookStore.fetchUserBooks(userStore.currentUserId)
    }
  } catch (error) {
    message.error('删除失败')
  }
}

function clearFilters() {
  filterPlatform.value = null
  filterStatus.value = null
  searchKeyword.value = ''
}

async function toggleShelf(book) {
  if (!userStore.currentUserId) {
    message.warning('请先在设置中选择用户名')
    router.push({ name: 'settings' })
    return
  }
  try {
    if (bookStore.isInUserShelf(book.id)) {
      await bookStore.removeFromUserShelf(userStore.currentUserId, book.id)
      message.success('已从私人书架移除')
    } else {
      await bookStore.addToUserShelf(userStore.currentUserId, book.id)
      message.success('已加入私人书架')
    }
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || '操作失败'
    message.error(msg)
  }
}
</script>

<template>
  <div class="books-view">
    <!-- 页面标题和工具栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">书架</h2>
        <span class="book-count">
          公共 {{ filteredBooks.length }} 本 · 私人 {{ filteredUserBooks.length }} 本
        </span>
        <n-tag v-if="hasUser" type="success" size="small" round>
          当前用户：{{ currentUserLabel }}
        </n-tag>
        <n-tag v-else type="warning" size="small" round>未选择用户</n-tag>
      </div>
      <n-space :size="8" class="header-actions">
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

    <n-tabs v-model:value="activeTab" type="line" animated>
      <n-tab-pane name="public" tab="公共书架">
        <n-spin :show="loading">
            <template v-if="filteredBooks.length > 0">
              <n-grid 
                :cols="isMobile ? 1 : 2" 
                :x-gap="isMobile ? 12 : 16" 
                :y-gap="isMobile ? 12 : 16"
                class="book-grid"
              >
              <n-gi 
                v-for="book in filteredBooks" 
                :key="book.id"
              >
                <BookCard 
                  :book="book"
                  :compact="isMobile"
                  :can-toggle-shelf="hasUser"
                  :in-shelf="bookStore.isInUserShelf(book.id)"
                  @click="goToDetail(book)"
                  @download="startDownload(book)"
                  @delete="deleteBook(book)"
                  @toggle-shelf="toggleShelf(book)"
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
      </n-tab-pane>

      <n-tab-pane :tab="`私人书架（${currentUserLabel}）`" name="private">
        <template v-if="hasUser">
          <n-spin :show="userShelfLoading">
            <template v-if="filteredUserBooks.length > 0">
              <n-grid 
                :cols="isMobile ? 1 : 2" 
                :x-gap="isMobile ? 12 : 16" 
                :y-gap="isMobile ? 12 : 16"
                class="book-grid"
              >
                <n-gi 
                  v-for="book in filteredUserBooks" 
                  :key="book.id"
                >
                  <BookCard 
                    :book="book"
                    :compact="isMobile"
                    :can-toggle-shelf="true"
                    :in-shelf="true"
                    @click="goToDetail(book)"
                    @download="startDownload(book)"
                    @delete="deleteBook(book)"
                    @toggle-shelf="toggleShelf(book)"
                  />
                </n-gi>
              </n-grid>
            </template>
            <n-empty v-else class="empty-state">
              <template #icon>
                <div class="empty-icon">📚</div>
              </template>
              <template #description>
                <span class="empty-text">私人书架为空，去公共书架收藏或添加吧</span>
              </template>
              <template #extra>
                <n-space :size="12">
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
        </template>
        <n-alert v-else type="warning" show-icon>
          还未选择用户，前往“设置”输入用户名后即可使用私人书架。
          <template #action>
            <n-button size="small" type="primary" text @click="router.push({ name: 'settings' })">
              去设置
            </n-button>
          </template>
        </n-alert>
      </n-tab-pane>
    </n-tabs>
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
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
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
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .book-count {
    font-size: 12px;
  }
  
  .header-left {
    width: 100%;
    align-items: center;
    gap: 8px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
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
