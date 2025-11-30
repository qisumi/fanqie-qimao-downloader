<script setup>
import { ref, computed } from 'vue'
import { NInput, NInputGroup, NButton, NSelect, NIcon } from 'naive-ui'
import { SearchOutline } from '@vicons/ionicons5'

const props = defineProps({
  platform: {
    type: String,
    default: 'fanqie'
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['search', 'update:platform'])

const keyword = ref('')
const localPlatform = computed({
  get: () => props.platform,
  set: (val) => emit('update:platform', val)
})

const platformOptions = [
  { label: '番茄小说', value: 'fanqie' },
  { label: '七猫小说', value: 'qimao' }
]

function handleSearch() {
  if (keyword.value.trim()) {
    emit('search', keyword.value.trim())
  }
}

function clear() {
  keyword.value = ''
}

defineExpose({ clear })
</script>

<template>
  <n-input-group>
    <n-select 
      v-model:value="localPlatform" 
      :options="platformOptions" 
      :style="{ width: '140px' }"
    />
    <n-input 
      v-model:value="keyword" 
      placeholder="输入书名或作者"
      @keyup.enter="handleSearch"
      clearable
    />
    <n-button type="primary" @click="handleSearch" :loading="loading">
      <template #icon>
        <n-icon><SearchOutline /></n-icon>
      </template>
      搜索
    </n-button>
  </n-input-group>
</template>
