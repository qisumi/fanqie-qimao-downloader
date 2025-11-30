<script setup>
import { inject } from 'vue'
import { NGrid, NGi, NSkeleton, NIcon, NProgress } from 'naive-ui'
import { BookOutline, DownloadOutline, TimeOutline, FlashOutline } from '@vicons/ionicons5'

const props = defineProps({
  stats: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['go-books', 'go-tasks'])

const isMobile = inject('isMobile', { value: false })

// 今日配额使用百分比
function getQuotaPercent() {
  if (!props.stats.daily_limit) return 0
  return Math.min(100, Math.round((props.stats.today_words / props.stats.daily_limit) * 100))
}
</script>

<template>
  <n-grid 
    :cols="isMobile ? 2 : 4" 
    :x-gap="isMobile ? 12 : 16" 
    :y-gap="isMobile ? 12 : 16" 
    class="stats-grid"
  >
    <n-gi>
      <div class="stat-card stat-card-books" @click="emit('go-books')">
        <n-skeleton v-if="loading" text :repeat="2" />
        <template v-else>
          <div class="stat-icon">
            <n-icon :size="isMobile ? 28 : 32"><BookOutline /></n-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total_books }}</div>
            <div class="stat-label">书库总数</div>
          </div>
        </template>
      </div>
    </n-gi>
    
    <n-gi>
      <div class="stat-card stat-card-completed" @click="emit('go-books')">
        <n-skeleton v-if="loading" text :repeat="2" />
        <template v-else>
          <div class="stat-icon">
            <n-icon :size="isMobile ? 28 : 32"><DownloadOutline /></n-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.completed_books }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </template>
      </div>
    </n-gi>
    
    <n-gi>
      <div class="stat-card stat-card-tasks" @click="emit('go-tasks')">
        <n-skeleton v-if="loading" text :repeat="2" />
        <template v-else>
          <div class="stat-icon">
            <n-icon :size="isMobile ? 28 : 32"><TimeOutline /></n-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.active_tasks }}</div>
            <div class="stat-label">活跃任务</div>
          </div>
        </template>
      </div>
    </n-gi>
    
    <n-gi>
      <div class="stat-card stat-card-quota">
        <n-skeleton v-if="loading" text :repeat="2" />
        <template v-else>
          <div class="stat-icon">
            <n-icon :size="isMobile ? 28 : 32"><FlashOutline /></n-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value-small">
              {{ (stats.today_words / 10000).toFixed(1) }}万
              <span class="stat-divider">/</span>
              {{ (stats.daily_limit / 10000).toFixed(0) }}万
            </div>
            <div class="stat-label">今日配额</div>
            <n-progress 
              type="line" 
              :percentage="getQuotaPercent()"
              :show-indicator="false"
              :height="4"
              :rail-color="'rgba(255,255,255,0.2)'"
              :fill-color="getQuotaPercent() > 80 ? '#ff6b6b' : '#ffffff'"
              style="margin-top: 8px;"
            />
          </div>
        </template>
      </div>
    </n-gi>
  </n-grid>
</template>

<style scoped>
.stats-grid {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: var(--border-radius-lg, 12px);
  cursor: pointer;
  transition: transform var(--transition-base, 0.25s), box-shadow var(--transition-base, 0.25s);
  color: white;
  min-height: 100px;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.stat-card-books {
  background: linear-gradient(135deg, #18a058 0%, #2ecc71 100%);
}

.stat-card-completed {
  background: linear-gradient(135deg, #2080f0 0%, #409eff 100%);
}

.stat-card-tasks {
  background: linear-gradient(135deg, #f0a020 0%, #faad14 100%);
}

.stat-card-quota {
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  cursor: default;
}

.stat-card-quota:hover {
  transform: none;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-value-small {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.2;
}

.stat-divider {
  opacity: 0.6;
  margin: 0 2px;
}

.stat-label {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 4px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;
    min-height: 90px;
  }
  
  .stat-icon {
    width: 44px;
    height: 44px;
  }
  
  .stat-value {
    font-size: 22px;
  }
  
  .stat-value-small {
    font-size: 15px;
  }
  
  .stat-label {
    font-size: 12px;
  }
}
</style>
