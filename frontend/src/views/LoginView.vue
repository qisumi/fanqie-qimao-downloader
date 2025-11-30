<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  NCard, NForm, NFormItem, NInput, NButton, NSpace, NH1,
  useMessage
} from 'naive-ui'
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
    <n-card style="max-width: 400px; margin: 100px auto;">
      <n-space vertical :size="24" align="center">
        <n-h1 style="margin: 0;">番茄七猫下载器</n-h1>
        
        <n-form style="width: 100%;">
          <n-form-item label="密码">
            <n-input 
              v-model:value="password" 
              type="password"
              placeholder="请输入访问密码"
              @keyup.enter="handleLogin"
            />
          </n-form-item>
          
          <n-button 
            type="primary" 
            block 
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </n-button>
        </n-form>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.login-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
</style>
