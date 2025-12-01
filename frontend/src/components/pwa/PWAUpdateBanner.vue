<script setup>
import { NCard, NButton, NIcon } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'

const emit = defineEmits(['update', 'skip'])
</script>

<template>
  <div class="pwa-update-banner">
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
          <n-button quaternary size="small" @click="emit('skip')">
            稍后
          </n-button>
          <n-button type="info" size="small" @click="emit('update')">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            更新
          </n-button>
        </div>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
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
</style>
