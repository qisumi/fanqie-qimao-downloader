<script setup>
import usePwaManager from '@/composables/usePwaManager'
import PWAInstallBanner from './pwa/PWAInstallBanner.vue'
import PWAOfflineBanner from './pwa/PWAOfflineBanner.vue'
import PWAUpdateBanner from './pwa/PWAUpdateBanner.vue'

const {
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
} = usePwaManager()

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
  <Transition name="slide-down">
    <PWAInstallBanner
      v-if="showInstallBanner"
      @install="handleInstall"
      @dismiss="dismissInstall"
    />
  </Transition>

  <Transition name="slide-down">
    <PWAOfflineBanner
      v-if="showOfflineBanner"
      @close="closeOfflineBanner"
    />
  </Transition>

  <Transition name="slide-down">
    <PWAUpdateBanner
      v-if="showUpdateBanner"
      @update="handleUpdate"
      @skip="skipUpdate"
    />
  </Transition>
</template>

<style scoped>
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
</style>
