<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NMenu, NIcon } from 'naive-ui'
import { 
  HomeOutline, SearchOutline, LibraryOutline, 
  DownloadOutline, SettingsOutline 
} from '@vicons/ionicons5'
import { h } from 'vue'

const route = useRoute()
const router = useRouter()

function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = [
  {
    label: '首页',
    key: 'home',
    icon: renderIcon(HomeOutline)
  },
  {
    label: '搜索书籍',
    key: 'search',
    icon: renderIcon(SearchOutline)
  },
  {
    label: '我的书库',
    key: 'books',
    icon: renderIcon(LibraryOutline)
  },
  {
    label: '下载任务',
    key: 'tasks',
    icon: renderIcon(DownloadOutline)
  }
]

const activeKey = computed(() => {
  // 从路由名称映射到菜单 key
  const name = route.name
  if (name === 'book-detail') return 'books'
  return name
})

function handleMenuSelect(key) {
  router.push({ name: key })
}
</script>

<template>
  <div class="sidebar">
    <!-- Logo -->
    <div class="logo">
      <span class="logo-text">📚 番茄七猫</span>
    </div>
    
    <!-- Navigation Menu -->
    <n-menu
      :value="activeKey"
      :options="menuOptions"
      @update:value="handleMenuSelect"
    />
  </div>
</template>

<style scoped>
.sidebar {
  height: 100%;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #efeff5;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #18a058;
}
</style>
