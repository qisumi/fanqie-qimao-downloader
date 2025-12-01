<script setup>
import { NAlert, NIcon } from 'naive-ui'
import { CloudOfflineOutline } from '@vicons/ionicons5'

const emit = defineEmits(['close'])
</script>

<template>
  <div class="pwa-offline-banner">
    <n-alert type="warning" :show-icon="true" closable @close="emit('close')">
      <template #icon>
        <n-icon>
          <CloudOfflineOutline />
        </n-icon>
      </template>
      <span>您当前处于离线状态，部分功能可能不可用</span>
    </n-alert>
  </div>
</template>

<style scoped>
.pwa-offline-banner {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 400px;
  width: calc(100% - 32px);
}
</style>
