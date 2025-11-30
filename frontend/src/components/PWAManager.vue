<script setup>
/**
 * PWA 管理组件
 * 整合安装提示、更新通知、离线状态管理
 * 使用 Naive UI 组件替代原生 DOM
 */
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { useMessage, useNotification, useDialog, NButton, NIcon, NSpace, NAlert, NCard } from 'naive-ui'
import { 
  CloudOfflineOutline, CloudDoneOutline, RefreshOutline, 
  DownloadOutline, CloseOutline, PhonePortraitOutline
} from '@vicons/ionicons5'

// PWA 状态
const isOnline = ref(navigator.onLine)
const isInstallable = ref(false)
const isInstalled = ref(false)
const updateAvailable = ref(false)
const showInstallBanner = ref(false)
const showOfflineBanner = ref(false)
const deferredPrompt = ref(null)
const swRegistration = ref(null)

// Naive UI hooks
const message = useMessage()
const notification = useNotification()
const dialog = useDialog()

// Service Worker 版本
const SW_VERSION = '1.5.0'

/**
 * 检查应用是否已安装
 */
function checkInstalledStatus() {
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches
  const isInWebAppiOS = window.navigator.standalone === true
  const isInWebAppChrome = window.matchMedia('(display-mode: minimal-ui)').matches
  
  return isStandalone || isInWebAppiOS || isInWebAppChrome || localStorage.getItem('pwa_installed') === 'true'
}

/**
 * 检查是否应该显示安装提示
 */
function shouldShowInstallPrompt() {
  if (isInstalled.value || !isInstallable.value) return false
  
  const dismissedTime = localStorage.getItem('pwa_install_dismissed')
  if (dismissedTime) {
    const dismissedDate = new Date(dismissedTime)
    const now = new Date()
    const daysSinceDismissed = (now - dismissedDate) / (1000 * 60 * 60 * 24)
    // 7天内拒绝过则不显示
    if (daysSinceDismissed < 7) return false
  }
  
  return true
}

/**
 * 处理安装
 */
async function handleInstall() {
  if (!deferredPrompt.value) return
  
  try {
    deferredPrompt.value.prompt()
    const { outcome } = await deferredPrompt.value.userChoice
    
    if (outcome === 'accepted') {
      message.success('应用安装成功！')
      isInstalled.value = true
      localStorage.setItem('pwa_installed', 'true')
      localStorage.setItem('pwa_install_date', new Date().toISOString())
    }
    
    showInstallBanner.value = false
    deferredPrompt.value = null
  } catch (error) {
    console.error('安装失败:', error)
    message.error('安装失败，请稍后重试')
  }
}

/**
 * 关闭安装提示
 */
function dismissInstall() {
  showInstallBanner.value = false
  localStorage.setItem('pwa_install_dismissed', new Date().toISOString())
}

/**
 * 处理更新
 */
async function handleUpdate() {
  if (!swRegistration.value?.waiting) return
  
  // 发送 skip waiting 消息
  swRegistration.value.waiting.postMessage({ type: 'SKIP_WAITING' })
  
  notification.info({
    title: '正在更新',
    content: '应用正在更新，请稍候...',
    duration: 3000
  })
}

/**
 * 跳过此版本
 */
function skipUpdate() {
  updateAvailable.value = false
  localStorage.setItem('pwa_skip_version', SW_VERSION)
}

/**
 * 注册 Service Worker
 */
async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return
  
  try {
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    })
    
    swRegistration.value = registration
    
    // 检查是否有等待中的更新
    if (registration.waiting) {
      const skipVersion = localStorage.getItem('pwa_skip_version')
      if (skipVersion !== SW_VERSION) {
        updateAvailable.value = true
        showUpdateNotification()
      }
    }
    
    // 监听新的 Service Worker 安装
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing
      
      newWorker?.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          const skipVersion = localStorage.getItem('pwa_skip_version')
          if (skipVersion !== SW_VERSION) {
            updateAvailable.value = true
            showUpdateNotification()
          }
        }
      })
    })
    
    // 监听 controller 变化（更新完成）
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      // 更新完成，刷新页面
      window.location.reload()
    })
    
    console.log('[PWA] Service Worker 注册成功')
  } catch (error) {
    console.error('[PWA] Service Worker 注册失败:', error)
  }
}

// 显示更新提示横幅
const showUpdateBanner = ref(false)

/**
 * 显示更新通知
 */
function showUpdateNotification() {
  showUpdateBanner.value = true
}

/**
 * 网络状态变化处理
 */
function handleOnline() {
  isOnline.value = true
  showOfflineBanner.value = false
  message.success('网络连接已恢复')
}

function handleOffline() {
  isOnline.value = false
  showOfflineBanner.value = true
  notification.warning({
    title: '网络已断开',
    content: '您当前处于离线状态，部分功能可能受限。',
    duration: 5000
  })
}

/**
 * 初始化 PWA
 */
onMounted(() => {
  // 检查安装状态
  isInstalled.value = checkInstalledStatus()
  
  // 监听 beforeinstallprompt 事件
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferredPrompt.value = e
    isInstallable.value = true
    
    if (shouldShowInstallPrompt()) {
      // 延迟显示安装提示
      setTimeout(() => {
        showInstallBanner.value = true
      }, 5000)
    }
  })
  
  // 监听安装完成事件
  window.addEventListener('appinstalled', () => {
    isInstalled.value = true
    showInstallBanner.value = false
    message.success('应用已成功安装到您的设备！')
  })
  
  // 监听网络状态
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  
  // 注册 Service Worker
  registerServiceWorker()
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})

// 导出状态供其他组件使用
defineExpose({
  isOnline,
  isInstallable,
  isInstalled,
  updateAvailable,
  handleInstall,
  handleUpdate
})
</script>

<template>
  <!-- 安装提示横幅 -->
  <Transition name="slide-down">
    <div v-if="showInstallBanner" class="pwa-install-banner">
      <n-card size="small" :bordered="false" class="install-card">
        <div class="install-content">
          <div class="install-icon">
            <n-icon :size="32" color="var(--primary-color)">
              <PhonePortraitOutline />
            </n-icon>
          </div>
          <div class="install-text">
            <div class="install-title">安装番茄七猫下载器</div>
            <div class="install-desc">添加到主屏幕，获得更好的体验</div>
          </div>
          <div class="install-actions">
            <n-button quaternary circle size="small" @click="dismissInstall">
              <template #icon>
                <n-icon><CloseOutline /></n-icon>
              </template>
            </n-button>
            <n-button type="primary" size="small" @click="handleInstall">
              <template #icon>
                <n-icon><DownloadOutline /></n-icon>
              </template>
              安装
            </n-button>
          </div>
        </div>
      </n-card>
    </div>
  </Transition>
  
  <!-- 离线状态提示 -->
  <Transition name="slide-down">
    <div v-if="showOfflineBanner" class="pwa-offline-banner">
      <n-alert type="warning" :show-icon="true" closable @close="showOfflineBanner = false">
        <template #icon>
          <n-icon>
            <CloudOfflineOutline />
          </n-icon>
        </template>
        <span>您当前处于离线状态，部分功能可能不可用</span>
      </n-alert>
    </div>
  </Transition>
  
  <!-- 更新提示横幅 -->
  <Transition name="slide-down">
    <div v-if="showUpdateBanner" class="pwa-update-banner">
      <n-card size="small" :bordered="false" class="update-card">
        <div class="update-content">
          <div class="update-icon">
            <n-icon :size="28" color="var(--info-color)">
              <RefreshOutline />
            </n-icon>
          </div>
          <div class="update-text">
            <div class="update-title">发现新版本</div>
            <div class="update-desc">建议立即更新以获得最佳体验</div>
          </div>
          <div class="update-actions">
            <n-button quaternary size="small" @click="skipUpdate(); showUpdateBanner = false">
              稍后
            </n-button>
            <n-button type="info" size="small" @click="handleUpdate">
              <template #icon>
                <n-icon><RefreshOutline /></n-icon>
              </template>
              更新
            </n-button>
          </div>
        </div>
      </n-card>
    </div>
  </Transition>
</template>

<style scoped>
.pwa-install-banner {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 420px;
  width: calc(100% - 32px);
}

.install-card {
  background: var(--card-bg);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
}

.install-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.install-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.1) 0%, rgba(54, 173, 106, 0.1) 100%);
}

.install-text {
  flex: 1;
  min-width: 0;
}

.install-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color-primary);
  margin-bottom: 2px;
}

.install-desc {
  font-size: 13px;
  color: var(--text-color-secondary);
}

.install-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.pwa-offline-banner {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 400px;
  width: calc(100% - 32px);
}

.pwa-update-banner {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 420px;
  width: calc(100% - 32px);
}

.update-card {
  background: var(--card-bg);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
  border-left: 4px solid var(--info-color);
}

.update-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(32, 128, 240, 0.1) 0%, rgba(64, 152, 255, 0.1) 100%);
}

.update-text {
  flex: 1;
  min-width: 0;
}

.update-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color-primary);
  margin-bottom: 2px;
}

.update-desc {
  font-size: 13px;
  color: var(--text-color-secondary);
}

.update-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* 深色模式适配 */
:root.dark .install-card {
  background: var(--card-bg);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .pwa-install-banner {
    bottom: calc(16px + env(safe-area-inset-bottom, 0px));
  }
  
  .install-content {
    flex-wrap: wrap;
  }
  
  .install-actions {
    width: 100%;
    justify-content: flex-end;
    margin-top: 8px;
  }
}
</style>
