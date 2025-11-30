<script setup>
import { NButton, NIcon } from 'naive-ui'
import { CloudDownloadOutline } from '@vicons/ionicons5'

const emit = defineEmits(['search'])
</script>

<template>
  <div class="welcome-card animate-fade-in">
    <div class="welcome-content">
      <div class="welcome-text">
        <h1 class="welcome-title">欢迎使用番茄七猫下载器</h1>
        <p class="welcome-desc">
          支持番茄小说、七猫小说的批量下载和 EPUB 导出
        </p>
      </div>
      <n-button 
        type="primary" 
        size="large" 
        round
        class="search-btn"
        @click="emit('search')"
      >
        <template #icon>
          <n-icon><CloudDownloadOutline /></n-icon>
        </template>
        搜索书籍
      </n-button>
    </div>
    <div class="welcome-decoration"></div>
  </div>
</template>

<style scoped>
.welcome-card {
  position: relative;
  padding: 32px;
  background: var(--gradient-primary, linear-gradient(135deg, #18a058 0%, #36ad6a 100%));
  border-radius: var(--border-radius-xl, 16px);
  color: white;
  margin-bottom: 24px;
  overflow: hidden;
}

.welcome-content {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.welcome-text {
  flex: 1;
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.welcome-desc {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.search-btn {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  font-weight: 500;
}

.search-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.welcome-decoration {
  position: absolute;
  top: -50px;
  right: -50px;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

/* 动画 */
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .welcome-card {
    padding: 24px 20px;
    margin-bottom: 16px;
  }
  
  .welcome-content {
    flex-direction: column;
    text-align: center;
  }
  
  .welcome-title {
    font-size: 20px;
  }
  
  .welcome-desc {
    font-size: 13px;
  }
  
  .search-btn {
    width: 100%;
  }
}
</style>
