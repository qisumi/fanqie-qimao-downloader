<script setup>
/**
 * EPUB模式内容组件
 */
import { NAlert } from 'naive-ui'

const props = defineProps({
  error: { type: String, default: '' }
})

// 暴露 container ref 给父组件
const epubContainerRef = defineModel('epubContainerRef')
</script>

<template>
  <div class="epub-shell">
    <div ref="epubContainerRef" class="epub-container" />
    <n-alert v-if="error" type="error" :bordered="false" class="state-alert">
      {{ error }}
    </n-alert>
  </div>
</template>

<style scoped>
.epub-shell {
  height: calc(100vh - 210px);
  background: #111;
  border-radius: 14px;
  overflow: hidden;
}

.epub-container {
  width: 100%;
  height: 100%;
  background: #111;
}

.state-alert {
  margin: 12px;
}
</style>
