<script setup>
import { ref, watch, computed, inject } from 'vue'
import { NButton, NIcon, NInputNumber, NDivider } from 'naive-ui'
import { DownloadOutline, GridOutline } from '@vicons/ionicons5'

const props = defineProps({
  totalChapters: {
    type: Number,
    required: true
  },
  downloading: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['download'])

const isMobile = inject('isMobile', { value: false })

const startChapter = ref(1)
const endChapter = ref(props.totalChapters || 1)

// 监听总章节数变化
watch(() => props.totalChapters, (newTotal) => {
  if (newTotal > 0) {
    endChapter.value = newTotal
  }
}, { immediate: true })

const selectedCount = computed(() => {
  return Math.max(0, endChapter.value - startChapter.value + 1)
})

function validateRange() {
  const total = props.totalChapters || 1
  if (startChapter.value < 1) startChapter.value = 1
  if (startChapter.value > total) startChapter.value = total
  if (endChapter.value < 1) endChapter.value = 1
  if (endChapter.value > total) endChapter.value = total
  if (endChapter.value < startChapter.value) endChapter.value = startChapter.value
}

function selectAll() {
  startChapter.value = 1
  endChapter.value = props.totalChapters || 1
}

function selectRange(start, end) {
  startChapter.value = start
  endChapter.value = Math.min(end, props.totalChapters || 1)
}

function selectLastN(n) {
  const total = props.totalChapters || 1
  endChapter.value = total
  startChapter.value = Math.max(1, total - n + 1)
}

// 暴露给父组件的方法
function selectSegment(segment) {
  startChapter.value = segment.start_index + 1
  endChapter.value = segment.end_index + 1
}

function handleDownload() {
  emit('download', {
    startIndex: startChapter.value - 1,
    endIndex: endChapter.value - 1
  })
}

// 暴露给父组件
defineExpose({
  startChapter,
  endChapter,
  selectSegment
})
</script>

<template>
  <div v-if="totalChapters > 0" class="section-card">
    <div class="section-header">
      <span class="section-title">选择下载范围</span>
      <n-icon color="#999"><GridOutline /></n-icon>
    </div>
    
    <div class="range-selector">
      <div class="range-inputs" :class="{ 'mobile': isMobile }">
        <div class="range-group">
          <span class="range-label">起始章节:</span>
          <n-input-number 
            v-model:value="startChapter"
            :min="1" 
            :max="totalChapters"
            @update:value="validateRange"
            size="small"
            class="range-input"
          />
          <n-button size="small" text @click="startChapter = 1">第一章</n-button>
        </div>
        
        <div class="range-group">
          <span class="range-label">结束章节:</span>
          <n-input-number 
            v-model:value="endChapter"
            :min="1" 
            :max="totalChapters"
            @update:value="validateRange"
            size="small"
            class="range-input"
          />
          <n-button size="small" text @click="endChapter = totalChapters">最后一章</n-button>
        </div>
      </div>
      
      <!-- 快捷选择按钮 -->
      <div class="quick-select">
        <n-button size="small" @click="selectAll">全选</n-button>
        <n-button v-if="totalChapters >= 100" size="small" @click="selectRange(1, 100)">前100章</n-button>
        <n-button v-if="totalChapters >= 500" size="small" @click="selectRange(1, 500)">前500章</n-button>
        <n-button v-if="totalChapters >= 100" size="small" @click="selectLastN(100)">最新100章</n-button>
      </div>
      
      <n-divider style="margin: 12px 0;" />
      
      <!-- 选择信息和下载按钮 -->
      <div class="range-footer" :class="{ 'mobile': isMobile }">
        <span class="selected-info">
          已选择 <span class="selected-count">{{ selectedCount }}</span> 章
          <span class="selected-range">(第 {{ startChapter }} - {{ endChapter }} 章)</span>
        </span>
        <n-button 
          type="primary"
          @click="handleDownload"
          :loading="loading"
          :disabled="downloading || selectedCount === 0"
        >
          <template #icon>
            <n-icon><DownloadOutline /></n-icon>
          </template>
          下载选中章节
        </n-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 区块卡片 */
.section-card {
  background: var(--card-bg, #fff);
  border-radius: var(--border-radius-lg, 12px);
  padding: 20px;
  box-shadow: var(--shadow-card);
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light, #efeff5);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-primary, #333);
}

/* 章节范围选择器 */
.range-selector {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.range-inputs {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.range-inputs.mobile {
  flex-direction: column;
  gap: 12px;
}

.range-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-label {
  font-size: 14px;
  color: var(--text-color-secondary, #666);
  flex-shrink: 0;
}

.range-input {
  width: 100px;
}

.quick-select {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.range-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.range-footer.mobile {
  flex-direction: column;
  align-items: stretch;
}

.selected-info {
  color: var(--text-color-secondary, #666);
  font-size: 14px;
}

.selected-count {
  color: var(--info-color, #2080f0);
  font-weight: 600;
}

.selected-range {
  color: var(--text-color-tertiary, #999);
  margin-left: 8px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .section-card {
    padding: 16px;
  }
}
</style>
