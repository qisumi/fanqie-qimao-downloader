<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NCard, NGrid, NGi, NSpace, NEmpty, NSpin, NButton, 
  NSelect, NInput, NIcon, NTag, NImage,
  useMessage
} from 'naive-ui'
import { RefreshOutline, TrashOutline, DownloadOutline } from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'
import { useTaskStore } from '@/stores/task'
import BookCard from '@/components/BookCard.vue'

const router = useRouter()
const message = useMessage()
const bookStore = useBookStore()
const taskStore = useTaskStore()

const filterPlatform = ref(null)
const filterStatus = ref(null)
const searchKeyword = ref('')

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
</script>

<template>
  <div class="books-view">
    <n-space vertical :size="24">
      <!-- 工具栏 -->
      <n-card>
        <n-space justify="space-between" align="center" wrap>
          <n-space :size="12">
            <n-select 
              v-model:value="filterPlatform" 
              :options="platformOptions"
              :style="{ width: '130px' }"
            />
            <n-select 
              v-model:value="filterStatus" 
              :options="statusOptions"
              :style="{ width: '130px' }"
            />
            <n-input 
              v-model:value="searchKeyword" 
              placeholder="搜索书名/作者"
              clearable
              :style="{ width: '180px' }"
            />
          </n-space>
          
          <n-button @click="refreshBooks" :loading="loading">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </n-card>

      <!-- 书籍列表 -->
      <n-spin :show="loading">
        <template v-if="filteredBooks.length > 0">
          <n-grid :cols="1" :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
            <n-gi 
              v-for="book in filteredBooks" 
              :key="book.id"
              span="1 m:1 l:1"
            >
              <BookCard 
                :book="book"
                @click="goToDetail(book)"
                @download="startDownload(book)"
                @delete="deleteBook(book)"
              />
            </n-gi>
          </n-grid>
        </template>
        
        <n-empty v-else description="书库为空，去搜索添加一些书籍吧">
          <template #extra>
            <n-button type="primary" @click="router.push({ name: 'search' })">
              搜索书籍
            </n-button>
          </template>
        </n-empty>
      </n-spin>
    </n-space>
  </div>
</template>

<style scoped>
.books-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
