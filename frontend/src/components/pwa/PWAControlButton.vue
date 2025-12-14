<script setup>
import { computed } from 'vue'
import { NButton, NIcon, NTooltip, NBadge } from 'naive-ui'
import { 
  DownloadOutline, RefreshOutline, CheckmarkCircleOutline, 
  WifiOutline, CloudOfflineOutline 
} from '@vicons/ionicons5'
import usePwaManager from '@/composables/usePwaManager'

const {
  isOnline,
  isInstallable,
  isInstalled,
  updateAvailable,
  handleInstall,
  handleUpdate
} = usePwaManager()

// 计算按钮各项属性（拆分为多个 computed 避免在响应式对象中保留函数/组件引用）
const iconComponent = computed(() => {
  if (updateAvailable.value) return RefreshOutline
  if (isInstallable.value && !isInstalled.value) return DownloadOutline
  if (isInstalled.value) return CheckmarkCircleOutline
  return isOnline.value ? WifiOutline : CloudOfflineOutline
})

const tooltip = computed(() => {
  if (updateAvailable.value) return '有新版本可用，点击更新'
  if (isInstallable.value && !isInstalled.value) return '安装应用到桌面'
  if (isInstalled.value) return '应用已安装'
  return isOnline.value ? '在线状态' : '离线状态'
})

const btnType = computed(() => {
  if (updateAvailable.value) return 'info'
  if (isInstallable.value && !isInstalled.value) return 'primary'
  if (isInstalled.value) return 'success'
  return isOnline.value ? 'default' : 'warning'
})

const showBadge = computed(() => {
  return updateAvailable.value || (isInstallable.value && !isInstalled.value)
})

// 处理按钮点击
function handleClick() {
  if (updateAvailable.value) {
    handleUpdate()
  } else if (isInstallable.value && !isInstalled.value) {
    handleInstall()
  }
  // 其他状态不需要特殊处理
}
</script>

<template>
  <n-tooltip trigger="hover">
    <template #trigger>
      <n-badge 
        :value="showBadge ? '•' : null" 
        :color="btnType === 'info' ? '#2080f0' : btnType === 'primary' ? '#18a058' : undefined"
        :show="showBadge"
      >
          <n-button 
          quaternary 
          circle 
          class="pwa-control-btn"
          :type="btnType"
          :disabled="!isInstallable && !updateAvailable"
          @click="handleClick"
        >
          <template #icon>
            <n-icon :size="20">
              <component :is="iconComponent" />
            </n-icon>
          </template>
        </n-button>
      </n-badge>
    </template>
    {{ tooltip }}
  </n-tooltip>
</template>

<style scoped>
.pwa-control-btn {
  transition: transform var(--transition-fast, 0.15s), color var(--transition-fast, 0.15s);
}

.pwa-control-btn:hover {
  transform: scale(1.1);
}

.pwa-control-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.pwa-control-btn:disabled:hover {
  transform: none;
}

/* 更新状态动画 */
@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

.pwa-control-btn:deep(.n-icon) {
  animation: pulse 2s infinite;
}

/* 只有在更新或可安装状态下才显示动画 */
.pwa-control-btn:not(:disabled):deep(.n-icon) {
  animation: none;
}

.pwa-control-btn[type="info"]:deep(.n-icon),
.pwa-control-btn[type="primary"]:deep(.n-icon) {
  animation: pulse 2s infinite;
}
</style>