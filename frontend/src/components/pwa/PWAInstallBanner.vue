<script setup>
import { NCard, NButton, NIcon } from 'naive-ui'
import { DownloadOutline, CloseOutline, PhonePortraitOutline } from '@vicons/ionicons5'

const emit = defineEmits(['install', 'dismiss'])
</script>

<template>
  <div class="pwa-install-banner">
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
          <n-button quaternary circle size="small" @click="emit('dismiss')">
            <template #icon>
              <n-icon><CloseOutline /></n-icon>
            </template>
          </n-button>
          <n-button type="primary" size="small" @click="emit('install')">
            <template #icon>
              <n-icon><DownloadOutline /></n-icon>
            </template>
            安装
          </n-button>
        </div>
      </div>
    </n-card>
  </div>
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

:root.dark .install-card {
  background: var(--card-bg);
}

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
