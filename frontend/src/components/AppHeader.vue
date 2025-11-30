<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  NLayoutHeader, NSpace, NButton, NIcon, NDropdown, NAvatar
} from 'naive-ui'
import { 
  PersonOutline, LogOutOutline, SettingsOutline 
} from '@vicons/ionicons5'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const pageTitle = computed(() => route.meta.title || '番茄七猫下载器')

const userOptions = [
  { label: '设置', key: 'settings', icon: SettingsOutline },
  { label: '退出登录', key: 'logout', icon: LogOutOutline }
]

function handleUserAction(key) {
  if (key === 'logout') {
    userStore.logout()
    router.push({ name: 'login' })
  } else if (key === 'settings') {
    // TODO: 跳转到设置页面
  }
}
</script>

<template>
  <n-layout-header bordered style="height: 64px; padding: 0 24px;">
    <n-space justify="space-between" align="center" style="height: 100%;">
      <span style="font-size: 18px; font-weight: 500;">{{ pageTitle }}</span>
      
      <n-dropdown 
        v-if="userStore.isAuthenticated && userStore.requireAuth"
        :options="userOptions" 
        @select="handleUserAction"
      >
        <n-button text>
          <n-icon :size="24"><PersonOutline /></n-icon>
        </n-button>
      </n-dropdown>
    </n-space>
  </n-layout-header>
</template>
