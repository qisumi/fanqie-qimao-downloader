<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  NCard, NForm, NFormItem, NInput, NButton, NSpace, NH1, NIcon,
  useMessage
} from 'naive-ui'
import { LockClosedOutline, LogInOutline } from '@vicons/ionicons5'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const userStore = useUserStore()

const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!password.value) {
    message.warning('请输入密码')
    return
  }
  
  loading.value = true
  try {
    const result = await userStore.login(password.value)
    if (result.success) {
      message.success('登录成功')
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    } else {
      message.error(result.message || '登录失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-view">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
    
    <!-- 登录卡片 -->
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">书</div>
        <h1 class="login-title">番茄·七猫·笔趣阁下载器</h1>
        <p class="login-subtitle">请输入访问密码以继续</p>
      </div>
      
      <n-form class="login-form">
        <n-form-item :show-label="false">
          <n-input 
            v-model:value="password" 
            type="password"
            placeholder="请输入访问密码"
            size="large"
            @keyup.enter="handleLogin"
            class="password-input"
          >
            <template #prefix>
              <n-icon color="#999"><LockClosedOutline /></n-icon>
            </template>
          </n-input>
        </n-form-item>
        
        <n-button 
          type="primary" 
          size="large"
          block 
          :loading="loading"
          @click="handleLogin"
          class="login-btn"
        >
          <template #icon>
            <n-icon><LogInOutline /></n-icon>
          </template>
          登录
        </n-button>
      </n-form>
      
      <div class="login-footer">
        <span class="footer-text">支持番茄小说、七猫小说、笔趣阁下载</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -50px;
  left: -50px;
  animation: float 6s ease-in-out infinite reverse;
}

.circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 10%;
  animation: float 7s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.05);
  }
}

/* 登录卡片 */
.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--card-bg, rgba(255, 255, 255, 0.95));
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.5s ease-out;
  position: relative;
  z-index: 1;
  transition: background-color 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 登录头部 */
.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  font-size: 56px;
  margin-bottom: 16px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

.login-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  font-size: 14px;
  color: var(--text-color-tertiary, #999);
  margin: 0;
}

/* 登录表单 */
.login-form {
  margin-bottom: 24px;
}

.password-input {
  border-radius: 12px;
}

.password-input :deep(.n-input__border) {
  border-radius: 12px;
}

.password-input :deep(.n-input__state-border) {
  border-radius: 12px;
}

.login-btn {
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.login-btn:active {
  transform: translateY(0);
}

/* 登录页脚 */
.login-footer {
  text-align: center;
}

.footer-text {
  font-size: 12px;
  color: var(--text-color-disabled, #bbb);
}

/* 移动端适配 */
@media (max-width: 480px) {
  .login-card {
    padding: 36px 24px;
    border-radius: 20px;
  }
  
  .logo-icon {
    font-size: 48px;
  }
  
  .login-title {
    font-size: 22px;
  }
  
  .circle-1 {
    width: 250px;
    height: 250px;
  }
  
  .circle-2 {
    width: 180px;
    height: 180px;
  }
  
  .circle-3 {
    width: 120px;
    height: 120px;
  }
}
</style>
