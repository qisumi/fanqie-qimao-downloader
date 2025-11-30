<script setup>
import { inject } from 'vue'
import { NTooltip } from 'naive-ui'

const props = defineProps({
  segments: {
    type: Array,
    default: () => []
  },
  startChapter: {
    type: Number,
    default: 1
  },
  endChapter: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['select-segment'])

const isMobile = inject('isMobile', { value: false })

function getSegmentClass(segment) {
  if (segment.failed > 0) return 'bg-red-400'
  if (segment.completion_rate === 1) return 'bg-green-500'
  if (segment.completion_rate >= 0.8) return 'bg-green-400'
  if (segment.completion_rate >= 0.5) return 'bg-yellow-400'
  if (segment.completion_rate >= 0.2) return 'bg-yellow-300'
  return 'bg-gray-300'
}

function isSegmentSelected(segment) {
  const segStart = segment.start_index + 1
  const segEnd = segment.end_index + 1
  return props.startChapter <= segStart && props.endChapter >= segEnd
}

function handleSelectSegment(segment) {
  emit('select-segment', segment)
}
</script>

<template>
  <div class="section-card" v-if="segments && segments.length > 0">
    <div class="section-header">
      <span class="section-title">章节下载状态</span>
      <div class="legend-group" v-if="!isMobile">
        <span class="legend-item"><span class="legend-color bg-green-500"></span>已完成</span>
        <span class="legend-item"><span class="legend-color bg-yellow-400"></span>部分完成</span>
        <span class="legend-item"><span class="legend-color bg-gray-300"></span>未下载</span>
        <span class="legend-item"><span class="legend-color bg-red-400"></span>有失败</span>
      </div>
    </div>
    
    <div class="heatmap-container">
      <n-tooltip 
        v-for="(segment, index) in segments" 
        :key="index"
        trigger="hover"
      >
        <template #trigger>
          <div
            class="heatmap-cell"
            :class="[getSegmentClass(segment), { 'ring-selected': isSegmentSelected(segment) }]"
            @click="handleSelectSegment(segment)"
          />
        </template>
        <div>
          <div style="font-weight: 500;">第 {{ segment.start_index + 1 }} - {{ segment.end_index + 1 }} 章</div>
          <div style="color: #999; margin-top: 4px;">
            {{ segment.first_chapter_title }}
            <template v-if="segment.first_chapter_title !== segment.last_chapter_title">
              ~ {{ segment.last_chapter_title }}
            </template>
          </div>
          <div style="margin-top: 4px;">
            <span style="color: #52c41a;">已完成: {{ segment.completed }}</span> / 
            <span style="color: #999;">待下载: {{ segment.pending }}</span>
            <span v-if="segment.failed > 0" style="color: #ff4d4f;"> / 失败: {{ segment.failed }}</span>
          </div>
        </div>
      </n-tooltip>
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

.legend-group {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.legend-color {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
  margin-right: 4px;
}

/* 热力图 */
.heatmap-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.heatmap-cell {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.heatmap-cell:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.ring-selected {
  box-shadow: 0 0 0 2px #1890ff;
}

.bg-green-500 { background-color: #52c41a; }
.bg-green-400 { background-color: #73d13d; }
.bg-yellow-400 { background-color: #fadb14; }
.bg-yellow-300 { background-color: #fff566; }
.bg-gray-300 { background-color: #d9d9d9; }
.bg-red-400 { background-color: #ff7875; }

/* 移动端适配 */
@media (max-width: 768px) {
  .section-card {
    padding: 16px;
  }
  
  .heatmap-cell {
    width: 24px;
    height: 24px;
  }
}
</style>
