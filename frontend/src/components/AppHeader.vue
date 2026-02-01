<script setup>
import { computed, inject, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayoutHeader, NSpace, NButton, NIcon, NDropdown, NAvatar, NBadge, NTooltip
} from 'naive-ui'
import {
  PersonOutline, LogOutOutline, SettingsOutline, MenuOutline,
  SunnyOutline, MoonOutline, DesktopOutline
} from '@vicons/ionicons5'
import { useUserStore } from '@/stores/user'
import { useThemeStore, ThemeMode } from '@/stores/theme'
import PWAControlButton from './pwa/PWAControlButton.vue'

const props = defineProps({
  isMobile: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle-menu'])

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()

const pageTitle = computed(() => route.meta.title || '番茄·七猫·笔趣阁下载器')
const userInitial = computed(() => {
  if (userStore.currentUsername) {
    return userStore.currentUsername[0].toUpperCase()
  }
  return 'U'
})

// 主题图标组件
const themeIconComponent = computed(() => {
  switch (themeStore.mode) {
    case ThemeMode.LIGHT:
      return SunnyOutline
    case ThemeMode.DARK:
      return MoonOutline
    case ThemeMode.SYSTEM:
      return DesktopOutline
    default:
      return SunnyOutline
  }
})

function renderIcon(icon) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const userOptions = [
  { label: '设置', key: 'settings', icon: renderIcon(SettingsOutline) },
  { label: '退出登录', key: 'logout', icon: renderIcon(LogOutOutline) }
]

async function handleUserAction(key) {
  if (key === 'logout') {
    await userStore.logout()
    router.push({ name: 'login' })
  } else if (key === 'settings') {
    router.push({ name: 'settings' })
  }
}

function handleToggleMenu() {
  emit('toggle-menu')
}

function handleToggleTheme() {
  themeStore.toggleMode()
}
</script>

<template>
  <n-layout-header bordered class="app-header">
    <div class="header-content">
      <!-- 左侧区域 -->
      <div class="header-left">
        <!-- 移动端菜单按钮 -->
        <n-button 
          v-if="isMobile" 
          quaternary 
          circle 
          class="menu-btn"
          @click="handleToggleMenu"
        >
          <template #icon>
            <n-icon :size="22"><MenuOutline /></n-icon>
          </template>
        </n-button>
        
        <!-- 页面标题 -->
        <span class="page-title">{{ pageTitle }}</span>
      </div>
      
      <!-- 右侧区域 -->
      <div class="header-right">
        <!-- 主题切换按钮 -->
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-button
              quaternary
              circle
              class="theme-btn"
              @click="handleToggleTheme"
            >
              <template #icon>
                <n-icon :size="20">
                  <component :is="themeIconComponent" />
                </n-icon>
              </template>
            </n-button>
          </template>
          {{ themeStore.themeLabel }}
        </n-tooltip>
        
        <!-- PWA控制按钮 -->
        <PWAControlButton />
        
        <n-dropdown
          v-if="userStore.isAuthenticated && userStore.requireAuth"
          :options="userOptions"
          @select="handleUserAction"
          trigger="click"
        >
          <n-button quaternary circle class="user-btn">
            <n-avatar
              round
              :size="32"
              color="#18a058"
              style="font-size: 14px;"
            >
              {{ userInitial }}
            </n-avatar>
          </n-button>
        </n-dropdown>
      </div>
    </div>
  </n-layout-header>
</template>

<style scoped>
.app-header {
  height: var(--header-height, 64px);
  padding: 0 var(--spacing-lg, 24px);
  background: var(--card-bg, #ffffff);
  border-bottom: 1px solid var(--border-color-light, #efeff5);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky, 1020);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm, 8px);
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md, 16px);
  flex-shrink: 0;
}

.menu-btn {
  flex-shrink: 0;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color-primary, #333639);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-btn {
  transition: transform var(--transition-fast, 0.15s);
}

.user-btn:hover {
  transform: scale(1.05);
}

.theme-btn {
  transition: transform var(--transition-fast, 0.15s), color var(--transition-fast, 0.15s);
}

.theme-btn:hover {
  transform: scale(1.1);
  color: var(--primary-color);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 var(--spacing-md, 16px);
  }
  
  .page-title {
    font-size: 16px;
  }
}
</style>
