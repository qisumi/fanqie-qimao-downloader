<script setup>
import { computed, ref, provide, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { 
  NConfigProvider, NMessageProvider, NDialogProvider, NNotificationProvider,
  NLayout, NLayoutSider, NLayoutContent, NDrawer, NDrawerContent, zhCN, dateZhCN,
  darkTheme
} from 'naive-ui'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import PWAManager from '@/components/PWAManager.vue'
import UploadBookModal from '@/components/UploadBookModal.vue'
import { useThemeStore } from '@/stores/theme'
import themeColorManager from '@/utils/themeColorManager'

const route = useRoute()
const themeStore = useThemeStore()

const showUploadModal = ref(false)

function openUploadModal() {
  showUploadModal.value = true
}

provide('openUploadModal', openUploadModal)

// 初始化主题
onMounted(() => {
  themeStore.init()
  // 初始化时设置默认状态栏颜色
  if (!isReaderRoute.value) {
    themeColorManager.setPageThemeColor()
  }
})

// 监听路由变化，设置状态栏颜色
watch(() => route.name, (routeName) => {
  if (routeName !== 'reader') {
    // 非阅读页面，使用默认状态栏颜色
    themeColorManager.setPageThemeColor()
  }
}, { immediate: true })

// Naive UI 主题
const naiveTheme = computed(() => themeStore.isDark ? darkTheme : null)

const isReaderRoute = computed(() => route.name === 'reader' || route.meta.readerLayout)
// 登录页不显示侧边栏
const showSidebar = computed(() => route.name !== 'login' && !isReaderRoute.value)

// 移动端侧边栏抽屉
const isMobile = ref(false)
const drawerActive = ref(false)

// 侧边栏折叠状态
const sidebarCollapsed = ref(false)

// 检测屏幕宽度
function checkMobile() {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) {
    drawerActive.value = false
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// 提供给子组件的方法
function toggleDrawer() {
  drawerActive.value = !drawerActive.value
}

function closeDrawer() {
  drawerActive.value = false
}

// 提供移动端状态给子组件
provide('isMobile', isMobile)
provide('toggleDrawer', toggleDrawer)
provide('closeDrawer', closeDrawer)
</script>

<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN" :theme="naiveTheme">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <!-- 全局上传书籍弹窗 -->
          <UploadBookModal v-model:show="showUploadModal" />
          
          <!-- PWA 管理组件 -->
          <PWAManager />
          
          <!-- 阅读器全屏布局 -->
          <template v-if="isReaderRoute">
            <router-view />
          </template>
          
          <!-- 登录页面独立布局 -->
          <template v-else-if="!showSidebar">
            <router-view />
          </template>
          
          <!-- 主应用布局 -->
          <template v-else>
            <!-- 移动端布局 -->
            <template v-if="isMobile">
              <n-layout class="app-layout">
                <AppHeader :is-mobile="true" @toggle-menu="toggleDrawer" />
                <n-layout-content class="main-content mobile-content">
                  <router-view />
                </n-layout-content>
              </n-layout>
              
              <!-- 移动端抽屉菜单 -->
              <n-drawer
                v-model:show="drawerActive"
                :width="280"
                placement="left"
                :trap-focus="true"
                :block-scroll="true"
              >
                <n-drawer-content body-content-style="padding: 0;">
                  <AppSidebar @navigate="closeDrawer" />
                </n-drawer-content>
              </n-drawer>
            </template>
            
            <!-- 桌面端布局 -->
            <n-layout v-else class="app-layout" has-sider>
              <!-- 侧边栏 -->
              <n-layout-sider
                bordered
                :width="240"
                :collapsed-width="64"
                collapse-mode="width"
                show-trigger
                :collapsed="sidebarCollapsed"
                @collapse="sidebarCollapsed = true"
                @expand="sidebarCollapsed = false"
                :native-scrollbar="false"
                class="app-sider"
              >
                <AppSidebar :collapsed="sidebarCollapsed" />
              </n-layout-sider>
              
              <!-- 主内容区 -->
              <n-layout>
                <AppHeader />
                <n-layout-content class="main-content">
                  <router-view />
                </n-layout-content>
              </n-layout>
            </n-layout>
          </template>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
}

.app-layout {
  height: 100vh;
  background-color: var(--bg-color, #f5f7f9);
}

.app-sider {
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.main-content {
  padding: var(--spacing-lg, 24px);
  background-color: var(--bg-color, #f5f7f9);
  min-height: calc(100vh - var(--header-height, 64px));
  overflow-x: hidden;
}

/* 移动端内容区适配 */
.mobile-content {
  padding: var(--spacing-md, 16px);
  padding-bottom: calc(var(--spacing-lg, 24px) + env(safe-area-inset-bottom, 0px));
}

/* 移动端内容动画 */
@media (max-width: 768px) {
  .main-content {
    animation: fadeInUp 0.3s ease-out;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Naive UI 抽屉样式覆盖 */
.n-drawer .n-drawer-body-content-wrapper {
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
}

/* 深色模式抽屉样式 */
:root.dark .n-drawer .n-drawer-body-content-wrapper {
  background: linear-gradient(180deg, #18181c 0%, #101014 100%);
}
</style>
