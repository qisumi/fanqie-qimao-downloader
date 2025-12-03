<script setup>
/**
 * 阅读设置抽屉组件
 */
import {
  NDrawer,
  NDrawerContent,
  NButton,
  NIcon,
  NSlider,
  NSelect,
  NInputNumber,
  NSwitch,
  NColorPicker,
  NDivider,
  NSpace
} from 'naive-ui'
import {
  ContrastOutline,
  DocumentTextOutline,
  SwapHorizontalOutline
} from '@vicons/ionicons5'

const props = defineProps({
  visible: { type: Boolean, default: false },
  isMobile: { type: Boolean, default: false },
  settings: { type: Object, default: () => ({}) },
  isScrollMode: { type: Boolean, default: true },
  isPageMode: { type: Boolean, default: false },
  isEpubMode: { type: Boolean, default: false },
  isFullscreen: { type: Boolean, default: false },
  backgroundColor: { type: String, default: '#f7f3e8' },
  textColor: { type: String, default: '#333333' }
})

const emit = defineEmits([
  'update:visible',
  'update-setting',
  'change-mode',
  'toggle-fullscreen',
  'reset-settings'
])

const fontOptions = [
  { label: '衬线（Serif）', value: 'serif' },
  { label: '无衬线（Sans）', value: 'sans-serif' },
  { label: '等宽（Mono）', value: 'monospace' }
]

const themePresets = [
  { label: '米黄纸', background: 'paper', textColor: '#3a3327' },
  { label: '护眼绿', background: 'green', textColor: '#2a4a33' },
  { label: '夜间', background: 'dark', textColor: '#e9e9e9' }
]

const backgroundOptions = [
  { label: '米黄纸', value: 'paper' },
  { label: '护眼绿', value: 'green' },
  { label: '夜间', value: 'dark' }
]

function applyThemePreset(preset) {
  emit('update-setting', 'background', preset.background)
  emit('update-setting', 'textColor', preset.textColor)
}

function handleFontFamilyChange(val) {
  emit('update-setting', 'fontFamily', val)
}

function handleFontSizeChange(value) {
  emit('update-setting', 'fontSize', value)
}

function handleLineHeightChange(value) {
  emit('update-setting', 'lineHeight', value)
}

function handleParagraphChange(value) {
  emit('update-setting', 'paragraphSpacing', value)
}

function toggleIndent(val) {
  emit('update-setting', 'firstLineIndent', val)
}

function handleBackgroundChange(value) {
  emit('update-setting', 'background', value)
}

function handleTextColorChange(value) {
  emit('update-setting', 'textColor', value)
}
</script>

<template>
  <n-drawer
    :show="visible"
    :width="isMobile ? 320 : 420"
    placement="right"
    :native-scrollbar="false"
    @update:show="$emit('update:visible', $event)"
  >
    <n-drawer-content title="阅读设置">
      <div class="setting-block">
        <div class="setting-title">
          <n-icon :size="16"><ContrastOutline /></n-icon>
          字体与排版
        </div>
        <div class="setting-row">
          <span>字体</span>
          <n-select
            :value="settings.fontFamily"
            :options="fontOptions"
            size="small"
            style="width: 180px"
            @update:value="handleFontFamilyChange"
          />
        </div>
        <div class="setting-row">
          <span>字号</span>
          <div class="control-line">
            <n-slider :value="settings.fontSize" :min="14" :max="26" :step="1" style="flex:1" @update:value="handleFontSizeChange" />
            <n-input-number :value="settings.fontSize" size="small" :min="14" :max="32" style="width:80px" @update:value="handleFontSizeChange" />
          </div>
        </div>
        <div class="setting-row">
          <span>行距</span>
          <div class="control-line">
            <n-slider :value="settings.lineHeight" :min="1.2" :max="2.4" :step="0.05" style="flex:1" @update:value="handleLineHeightChange" />
            <n-input-number :value="settings.lineHeight" size="small" :min="1.2" :max="2.6" :step="0.05" style="width:80px" @update:value="handleLineHeightChange" />
          </div>
        </div>
        <div class="setting-row">
          <span>段间距</span>
          <div class="control-line">
            <n-slider :value="settings.paragraphSpacing" :min="0" :max="32" :step="2" style="flex:1" @update:value="handleParagraphChange" />
            <n-input-number :value="settings.paragraphSpacing" size="small" :min="0" :max="48" :step="2" style="width:80px" @update:value="handleParagraphChange" />
          </div>
        </div>
        <div class="setting-row">
          <span>首行缩进</span>
          <n-switch :value="settings.firstLineIndent !== false" @update:value="toggleIndent" />
        </div>
      </div>

      <n-divider />

      <div class="setting-block">
        <div class="setting-title">
          <n-icon :size="16"><DocumentTextOutline /></n-icon>
          主题与颜色
        </div>
        <div class="preset-row">
          <n-button
            v-for="preset in themePresets"
            :key="preset.label"
            size="small"
            :type="settings.background === preset.background ? 'primary' : 'default'"
            @click="applyThemePreset(preset)"
          >
            {{ preset.label }}
          </n-button>
        </div>
        <div class="setting-row">
          <span>背景</span>
          <div class="control-line">
            <n-select
              :value="settings.background"
              :options="backgroundOptions"
              size="small"
              style="flex:1"
              @update:value="handleBackgroundChange"
            />
            <n-color-picker :value="backgroundColor" size="small" :modes="['hex']" @update:value="handleBackgroundChange" />
          </div>
        </div>
        <div class="setting-row">
          <span>文字颜色</span>
          <div class="control-line">
            <n-color-picker :value="textColor" size="small" :modes="['hex']" @update:value="handleTextColorChange" />
          </div>
        </div>
      </div>

      <n-divider />

      <div class="setting-block">
        <div class="setting-title">
          <n-icon :size="16"><SwapHorizontalOutline /></n-icon>
          模式与控制
        </div>
        <div class="setting-row">
          <span>阅读模式</span>
          <n-space :wrap="true">
            <n-button size="small" :type="isScrollMode ? 'primary' : 'default'" @click="$emit('change-mode', 'scroll')">滚动</n-button>
            <n-button size="small" :type="isPageMode ? 'primary' : 'default'" :disabled="!isMobile" @click="$emit('change-mode', 'page')">翻页</n-button>
            <n-button size="small" :type="isEpubMode ? 'primary' : 'default'" @click="$emit('change-mode', 'epub')">EPUB</n-button>
          </n-space>
        </div>
        <div class="setting-row">
          <span>全屏</span>
          <n-button size="small" ghost @click="$emit('toggle-fullscreen')">
            {{ isFullscreen ? '退出全屏' : '进入全屏' }}
          </n-button>
        </div>
        <div class="setting-row">
          <span>重置</span>
          <n-button size="small" tertiary @click="$emit('reset-settings')">恢复默认</n-button>
        </div>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<style scoped>
.setting-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 8px;
}

.setting-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  color: var(--text-color-primary, #333);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.control-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.preset-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
