<template>
  <n-spin :show="loading">
    <template v-if="books.length > 0">
      <n-grid
        :cols="isMobile ? 1 : 2"
        :x-gap="isMobile ? 12 : 16"
        :y-gap="isMobile ? 12 : 16"
        class="book-grid"
      >
        <n-gi v-for="book in books" :key="book.id">
          <BookCard
            :book="book"
            :compact="isMobile"
            :can-toggle-shelf="canToggleShelf"
            :in-shelf="isInShelf ? isInShelf(book) : undefined"
            @click="$emit('book-click', book)"
            @download="$emit('book-download', book)"
            @delete="$emit('book-delete', book)"
            @toggle-shelf="$emit('book-toggle-shelf', book)"
          />
        </n-gi>
      </n-grid>
    </template>

    <n-empty v-else class="empty-state">
      <template #icon>
        <div class="empty-icon">📚</div>
      </template>
      <template #description>
        <span class="empty-text">{{ emptyText }}</span>
      </template>
      <template #extra>
        <n-space :size="12">
          <n-button
            v-if="showClearFilters"
            @click="$emit('clear-filters')"
          >
            清除筛选
          </n-button>
          <n-button
            type="primary"
            @click="$emit('search-books')"
          >
            搜索书籍
          </n-button>
        </n-space>
      </template>
    </n-empty>
  </n-spin>
</template>

<script setup>
import { NSpin, NGrid, NGi, NEmpty, NSpace, NButton } from 'naive-ui'
import BookCard from '@/components/BookCard.vue'

defineProps({
  books: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  isMobile: {
    type: Boolean,
    default: false
  },
  canToggleShelf: {
    type: Boolean,
    default: false
  },
  isInShelf: {
    type: Function,
    default: null
  },
  emptyText: {
    type: String,
    default: '书库为空，去搜索添加一些书籍吧'
  },
  showClearFilters: {
    type: Boolean,
    default: false
  }
})

defineEmits(['book-click', 'book-download', 'book-delete', 'book-toggle-shelf', 'clear-filters', 'search-books'])
</script>

<style scoped>
.book-grid {
  animation: fadeIn 0.3s ease-out;
}

.empty-state {
  padding: 80px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  color: var(--text-color-tertiary, #999);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
