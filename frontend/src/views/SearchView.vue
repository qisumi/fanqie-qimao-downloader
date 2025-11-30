<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NCard, NInput, NInputGroup, NButton, NSelect, NSpace, 
  NList, NListItem, NThing, NTag, NEmpty, NSpin, NIcon, NImage,
  useMessage
} from 'naive-ui'
import { SearchOutline, AddOutline, BookOutline } from '@vicons/ionicons5'
import { useBookStore } from '@/stores/book'

const router = useRouter()
const message = useMessage()
const bookStore = useBookStore()

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
    // 可选：跳转到书籍详情页
    // router.push({ name: 'book-detail', params: { id: newBook.id } })
  } catch (error) {
    const msg = error.response?.data?.detail || '添加失败'
    message.error(msg)
  } finally {
    addingBook.value = null
  }
}

function getPlatformLabel(value) {
  return value === 'fanqie' ? '番茄小说' : '七猫小说'
}
</script>

<template>
  <div class="search-view">
    <n-space vertical :size="24">
      <!-- 搜索区域 -->
      <n-card title="搜索书籍">
        <n-space vertical :size="16">
          <n-input-group>
            <n-select 
              v-model:value="platform" 
              :options="platformOptions" 
              :style="{ width: '140px' }"
            />
            <n-input 
              v-model:value="keyword" 
              placeholder="输入书名或作者"
              @keyup.enter="handleSearch"
              clearable
            />
            <n-button type="primary" @click="handleSearch" :loading="loading">
              <template #icon>
                <n-icon><SearchOutline /></n-icon>
              </template>
              搜索
            </n-button>
          </n-input-group>
        </n-space>
      </n-card>

      <!-- 搜索结果 -->
      <n-card title="搜索结果">
        <n-spin :show="loading">
          <template v-if="searchResults.length > 0">
            <n-list hoverable clickable>
              <n-list-item v-for="book in searchResults" :key="book.book_id">
                <template #prefix>
                  <n-image 
                    v-if="book.cover_url"
                    :src="book.cover_url" 
                    :width="60"
                    :height="80"
                    object-fit="cover"
                    preview-disabled
                    style="border-radius: 4px;"
                  />
                  <div 
                    v-else 
                    style="width: 60px; height: 80px; background: #f0f0f0; border-radius: 4px; display: flex; align-items: center; justify-content: center;"
                  >
                    <n-icon :size="24" color="#ccc"><BookOutline /></n-icon>
                  </div>
                </template>
                <n-thing>
                  <template #header>
                    {{ book.book_name || book.title }}
                    <n-tag :type="platform === 'fanqie' ? 'warning' : 'info'" size="small" style="margin-left: 8px;">
                      {{ getPlatformLabel(platform) }}
                    </n-tag>
                  </template>
                  <template #header-extra>
                    <n-button 
                      type="primary" 
                      size="small"
                      :loading="addingBook === book.book_id"
                      @click.stop="addToLibrary(book)"
                    >
                      <template #icon>
                        <n-icon><AddOutline /></n-icon>
                      </template>
                      添加
                    </n-button>
                  </template>
                  <template #description>
                    <n-space :size="16">
                      <span>作者: {{ book.author }}</span>
                      <span v-if="book.word_count">字数: {{ (book.word_count / 10000).toFixed(1) }}万</span>
                      <span v-if="book.creation_status || book.status">状态: {{ book.creation_status || book.status }}</span>
                    </n-space>
                  </template>
                  <div v-if="book.abstract || book.intro" style="color: #666; margin-top: 8px;">
                    {{ (book.abstract || book.intro)?.substring(0, 100) }}...
                  </div>
                </n-thing>
              </n-list-item>
            </n-list>
            
            <n-space justify="center" style="margin-top: 16px;">
              <n-button @click="loadMore" :loading="loading">
                加载更多
              </n-button>
            </n-space>
          </template>
          
          <n-empty v-else description="暂无搜索结果，请输入关键词搜索" />
        </n-spin>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.search-view {
  max-width: 900px;
  margin: 0 auto;
}
</style>
