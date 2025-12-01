import { ref, onMounted, onUnmounted } from 'vue'
import { useMessage, useNotification } from 'naive-ui'

const SW_VERSION = '1.4.3'

/**
 * PWA 状态与生命周期管理
 */
export function usePwaManager() {
  const isOnline = ref(navigator.onLine)
  const isInstallable = ref(false)
  const isInstalled = ref(false)
  const updateAvailable = ref(false)

  const showInstallBanner = ref(false)
  const showOfflineBanner = ref(false)
  const showUpdateBanner = ref(false)

  const deferredPrompt = ref(null)
  const swRegistration = ref(null)

  const message = useMessage()
  const notification = useNotification()

  let installBannerTimer = null

  function checkInstalledStatus() {
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches
    const isInWebAppiOS = window.navigator.standalone === true
    const isInWebAppChrome = window.matchMedia('(display-mode: minimal-ui)').matches

    return (
      isStandalone ||
      isInWebAppiOS ||
      isInWebAppChrome ||
      localStorage.getItem('pwa_installed') === 'true'
    )
  }

  function shouldShowInstallPrompt() {
    if (isInstalled.value || !isInstallable.value) return false

    const dismissedTime = localStorage.getItem('pwa_install_dismissed')
    if (dismissedTime) {
      const dismissedDate = new Date(dismissedTime)
      const now = new Date()
      const daysSinceDismissed = (now - dismissedDate) / (1000 * 60 * 60 * 24)
      if (daysSinceDismissed < 7) return false
    }

    return true
  }

  function scheduleInstallBanner() {
    clearTimeout(installBannerTimer)
    installBannerTimer = setTimeout(() => {
      showInstallBanner.value = true
    }, 5000)
  }

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

  function dismissInstall() {
    showInstallBanner.value = false
    localStorage.setItem('pwa_install_dismissed', new Date().toISOString())
  }

  async function handleUpdate() {
    if (!swRegistration.value?.waiting) return

    swRegistration.value.waiting.postMessage({ type: 'SKIP_WAITING' })

    notification.info({
      title: '正在更新',
      content: '应用正在更新，请稍候...',
      duration: 3000
    })
  }

  function skipUpdate() {
    updateAvailable.value = false
    showUpdateBanner.value = false
    localStorage.setItem('pwa_skip_version', SW_VERSION)
  }

  function markUpdateAvailable() {
    updateAvailable.value = true
    showUpdateBanner.value = true
  }

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

  async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      })

      swRegistration.value = registration

      if (registration.waiting) {
        const skipVersion = localStorage.getItem('pwa_skip_version')
        if (skipVersion !== SW_VERSION) {
          markUpdateAvailable()
        }
      }

      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing

        newWorker?.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            const skipVersion = localStorage.getItem('pwa_skip_version')
            if (skipVersion !== SW_VERSION) {
              markUpdateAvailable()
            }
          }
        })
      })

      navigator.serviceWorker.addEventListener('controllerchange', () => {
        window.location.reload()
      })

      console.log('[PWA] Service Worker 注册成功')
    } catch (error) {
      console.error('[PWA] Service Worker 注册失败:', error)
    }
  }

  function beforeInstallPromptHandler(event) {
    event.preventDefault()
    deferredPrompt.value = event
    isInstallable.value = true

    if (shouldShowInstallPrompt()) {
      scheduleInstallBanner()
    }
  }

  function handleAppInstalled() {
    isInstalled.value = true
    showInstallBanner.value = false
    message.success('应用已成功安装到您的设备！')
  }

  function closeOfflineBanner() {
    showOfflineBanner.value = false
  }

  function init() {
    isInstalled.value = checkInstalledStatus()

    window.addEventListener('beforeinstallprompt', beforeInstallPromptHandler)
    window.addEventListener('appinstalled', handleAppInstalled)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    registerServiceWorker()
  }

  function cleanup() {
    window.removeEventListener('beforeinstallprompt', beforeInstallPromptHandler)
    window.removeEventListener('appinstalled', handleAppInstalled)
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
    clearTimeout(installBannerTimer)
  }

  onMounted(init)
  onUnmounted(cleanup)

  return {
    isOnline,
    isInstallable,
    isInstalled,
    updateAvailable,
    showInstallBanner,
    showOfflineBanner,
    showUpdateBanner,
    handleInstall,
    handleUpdate,
    dismissInstall,
    skipUpdate,
    closeOfflineBanner
  }
}

export default usePwaManager
