<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NSpace, NButton, NIcon, NTabs, NTabPane, NAlert, NTag, NSelect, NInput,
  useMessage
} from 'naive-ui'
import { RefreshOutline, FilterOutline, CloudUploadOutline } from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'
import { useTaskStore } from '@/stores/task'
import { useUserStore } from '@/stores/user'
import { useBookFilters } from '@/composables/useBookFilters'
import UploadBookModal from '@/components/UploadBookModal.vue'
import BookGrid from '@/components/BookGrid.vue'

const router = useRouter()
const message = useMessage()
const bookStore = useBookStore()
const taskStore = useTaskStore()
const userStore = useUserStore()
const isMobile = inject('isMobile', ref(false))

const showUploadModal = ref(false)
const activeTab = ref('public')

// Use book filters composable
const {
  filterPlatform,
  filterStatus,
  searchKeyword,
  showFilters,
  platformOptions,
  statusOptions,
  filteredBooks,
  filteredUserBooks,
  hasFilters,
  clearFilters
} = useBookFilters(
  computed(() => bookStore.books),
  computed(() => bookStore.userBooks)
)

const loading = computed(() => bookStore.loading)
const userShelfLoading = computed(() => bookStore.userBooksLoading)

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
        <n-button @click="showUploadModal = true">
          <template #icon>
            <n-icon><CloudUploadOutline /></n-icon>
          </template>
          <span class="hide-mobile">上传</span>
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
          />
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
        <BookGrid
          :books="filteredBooks"
          :loading="loading"
          :is-mobile="isMobile"
          :can-toggle-shelf="hasUser"
          :is-in-shelf="(book) => bookStore.isInUserShelf(book.id)"
          :empty-text="hasFilters ? '没有找到匹配的书籍' : '书库为空，去搜索添加一些书籍吧'"
          :show-clear-filters="hasFilters"
          @book-click="goToDetail"
          @book-download="startDownload"
          @book-delete="deleteBook"
          @book-toggle-shelf="toggleShelf"
          @clear-filters="clearFilters"
          @search-books="router.push({ name: 'search' })"
        />
      </n-tab-pane>

      <n-tab-pane :tab="`私人书架（${currentUserLabel}）`" name="private">
        <template v-if="hasUser">
          <BookGrid
            :books="filteredUserBooks"
            :loading="userShelfLoading"
            :is-mobile="isMobile"
            :can-toggle-shelf="true"
            :is-in-shelf="() => true"
            empty-text="私人书架为空，去公共书架收藏或添加吧"
            @book-click="goToDetail"
            @book-download="startDownload"
            @book-delete="deleteBook"
            @book-toggle-shelf="toggleShelf"
            @search-books="router.push({ name: 'search' })"
          />
        </template>
        <n-alert v-else type="warning" show-icon>
          还未选择用户，前往"设置"输入用户名后即可使用私人书架。
          <template #action>
            <n-button size="small" type="primary" text @click="router.push({ name: 'settings' })">
              去设置
            </n-button>
          </template>
        </n-alert>
      </n-tab-pane>
    </n-tabs>

    <UploadBookModal v-model:show="showUploadModal" @success="refreshBooks" />
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

/* Slide down animation */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    justify-content: flex-end;
  }

  .hide-mobile {
    display: none;
  }

  .filter-controls {
    flex-direction: column;
  }

  .filter-select,
  .filter-input {
    width: 100%;
  }
}
</style>
