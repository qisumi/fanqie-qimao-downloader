<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  NConfigProvider, NMessageProvider, NDialogProvider, NNotificationProvider,
  NLayout, NLayoutSider, NLayoutContent, zhCN, dateZhCN 
} from 'naive-ui'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'

const route = useRoute()

// 登录页不显示侧边栏
const showSidebar = computed(() => route.name !== 'login')
</script>

<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-layout class="app-layout" has-sider>
            <!-- 侧边栏 -->
            <n-layout-sider
              v-if="showSidebar"
              bordered
              :width="220"
              :collapsed-width="64"
              collapse-mode="width"
              show-trigger
              :native-scrollbar="false"
            >
              <AppSidebar />
            </n-layout-sider>
            
            <!-- 主内容区 -->
            <n-layout>
              <AppHeader v-if="showSidebar" />
              <n-layout-content class="main-content">
                <router-view />
              </n-layout-content>
            </n-layout>
          </n-layout>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
}

.app-layout {
  height: 100vh;
}

.main-content {
  padding: 24px;
  background-color: #f5f7f9;
  min-height: calc(100vh - 64px);
}
</style>
