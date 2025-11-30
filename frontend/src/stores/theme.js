import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

/**
 * 主题模式枚举
 */
export const ThemeMode = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system'
}

/**
 * 主题 Store
 * 管理应用主题状态，支持浅色/深色/跟随系统三种模式
 */
export const useThemeStore = defineStore('theme', () => {
  // 存储的主题模式 (light/dark/system)
  const mode = ref(ThemeMode.LIGHT)
  
  // 系统主题偏好
  const systemPrefersDark = ref(false)
  
  // 实际应用的主题 (只有 light 或 dark)
  const resolvedTheme = computed(() => {
    if (mode.value === ThemeMode.SYSTEM) {
      return systemPrefersDark.value ? ThemeMode.DARK : ThemeMode.LIGHT
    }
    return mode.value
  })
  
  // 是否为深色模式
  const isDark = computed(() => resolvedTheme.value === ThemeMode.DARK)
  
  // 主题图标
  const themeIcon = computed(() => {
    switch (mode.value) {
      case ThemeMode.LIGHT:
        return 'sunny'
      case ThemeMode.DARK:
        return 'moon'
      case ThemeMode.SYSTEM:
        return 'desktop'
      default:
        return 'sunny'
    }
  })
  
  // 主题标签
  const themeLabel = computed(() => {
    switch (mode.value) {
      case ThemeMode.LIGHT:
        return '浅色'
      case ThemeMode.DARK:
        return '深色'
      case ThemeMode.SYSTEM:
        return '跟随系统'
      default:
        return '浅色'
    }
  })
  
  /**
   * 初始化主题
   * 从 localStorage 读取保存的主题，并设置系统主题监听
   */
  function init() {
    // 读取保存的主题模式
    const savedMode = localStorage.getItem('theme-mode')
    if (savedMode && Object.values(ThemeMode).includes(savedMode)) {
      mode.value = savedMode
    }
    
    // 检测系统主题偏好
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemPrefersDark.value = mediaQuery.matches
    
    // 监听系统主题变化
    mediaQuery.addEventListener('change', (e) => {
      systemPrefersDark.value = e.matches
    })
    
    // 应用主题到 DOM
    applyTheme()
  }
  
  /**
   * 设置主题模式
   * @param {string} newMode - 新的主题模式 (light/dark/system)
   */
  function setMode(newMode) {
    if (Object.values(ThemeMode).includes(newMode)) {
      mode.value = newMode
      localStorage.setItem('theme-mode', newMode)
    }
  }
  
  /**
   * 切换到下一个主题模式
   * 循环顺序: light -> dark -> system -> light
   */
  function toggleMode() {
    const modes = [ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.SYSTEM]
    const currentIndex = modes.indexOf(mode.value)
    const nextIndex = (currentIndex + 1) % modes.length
    setMode(modes[nextIndex])
  }
  
  /**
   * 应用主题到 DOM
   * 在 <html> 元素上添加/移除 dark class
   */
  function applyTheme() {
    const html = document.documentElement
    
    if (isDark.value) {
      html.classList.add('dark')
      // 更新 meta theme-color
      updateThemeColor('#1e1e1e')
    } else {
      html.classList.remove('dark')
      updateThemeColor('#18a058')
    }
  }
  
  /**
   * 更新 meta theme-color
   * @param {string} color - 主题颜色
   */
  function updateThemeColor(color) {
    let metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta')
      metaThemeColor.name = 'theme-color'
      document.head.appendChild(metaThemeColor)
    }
    metaThemeColor.content = color
  }
  
  // 监听 resolvedTheme 变化，自动应用主题
  watch(resolvedTheme, () => {
    applyTheme()
  })
  
  return {
    // State
    mode,
    systemPrefersDark,
    
    // Computed
    resolvedTheme,
    isDark,
    themeIcon,
    themeLabel,
    
    // Actions
    init,
    setMode,
    toggleMode,
    applyTheme
  }
})
