<script setup>
import { computed, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NMenu, NIcon, NDivider } from 'naive-ui'
import { 
  HomeOutline, SearchOutline, LibraryOutline, 
  DownloadOutline, SettingsOutline 
} from '@vicons/ionicons5'
import { h } from 'vue'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['navigate'])

const route = useRoute()
const router = useRouter()

// 从父组件获取关闭抽屉的方法
const closeDrawer = inject('closeDrawer', () => {})

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
  },
  {
    label: '设置',
    key: 'settings',
    icon: renderIcon(SettingsOutline)
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
  emit('navigate')
  closeDrawer()
}
</script>

<template>
  <div class="sidebar">
    <!-- Logo -->
    <div class="logo" :class="{ 'logo-collapsed': collapsed }">
      <div class="logo-icon">📚</div>
      <transition name="fade">
        <span v-if="!collapsed" class="logo-text">番茄七猫</span>
      </transition>
    </div>
    
    <n-divider style="margin: 0;" />
    
    <!-- Navigation Menu -->
    <n-menu
      :value="activeKey"
      :options="menuOptions"
      :collapsed="collapsed"
      :collapsed-width="64"
      :collapsed-icon-size="22"
      :indent="24"
      @update:value="handleMenuSelect"
      class="nav-menu"
    />
    
    <!-- 底部信息 -->
    <div v-if="!collapsed" class="sidebar-footer">
<div class="version-info">
        <span class="version-label">v1.6.0</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--card-bg, #ffffff);
  transition: background-color 0.3s ease;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
  transition: all var(--transition-base, 0.25s);
}

.logo-collapsed {
  padding: 0;
}

.logo-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  white-space: nowrap;
}

.nav-menu {
  flex: 1;
  padding: 8px 0;
}

/* 菜单项悬停效果增强 */
.nav-menu :deep(.n-menu-item) {
  margin: 4px 8px;
  border-radius: 8px;
  transition: all var(--transition-fast, 0.15s);
}

.nav-menu :deep(.n-menu-item:hover) {
  background-color: rgba(24, 160, 88, 0.08);
}

.nav-menu :deep(.n-menu-item-content--selected) {
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.12) 0%, rgba(54, 173, 106, 0.08) 100%);
}

.nav-menu :deep(.n-menu-item-content--selected::before) {
  border-left: 3px solid #18a058;
  border-radius: 0 4px 4px 0;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color-light, #efeff5);
}

.version-info {
  text-align: center;
}

.version-label {
  font-size: 12px;
  color: var(--text-color-tertiary, #999);
  padding: 4px 12px;
  background: var(--bg-color-tertiary, rgba(0, 0, 0, 0.04));
  border-radius: 12px;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
