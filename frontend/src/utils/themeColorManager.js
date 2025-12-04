/**
 * 状态栏颜色管理器
 * 智能管理不同页面的状态栏颜色
 */

class ThemeColorManager {
  constructor() {
    this.originalThemeColor = '#18a058';
    this.isInReaderMode = false;
    this.readerModeListener = null;
  }

  /**
   * 初始化状态栏颜色管理器
   */
  init() {
    // 存储原始的theme-color meta标签
    const themeMeta = document.querySelector('meta[name="theme-color"]');
    if (themeMeta) {
      this.originalThemeColor = themeMeta.getAttribute('content') || '#18a058';
    }

    // 监听路由变化，在离开阅读页面时恢复默认状态栏颜色
    this.setupRouteListener();
  }

  /**
   * 设置非阅读页面的状态栏颜色（根据系统主题）
   */
  setPageThemeColor() {
    this.isInReaderMode = false;
    
    // 移除所有现有的theme-color meta标签
    this.removeAllThemeColorMeta();
    
    // 添加基于系统主题的状态栏颜色
    const lightMeta = document.createElement('meta');
    lightMeta.name = 'theme-color';
    lightMeta.setAttribute('content', '#18a058');
    lightMeta.setAttribute('media', '(prefers-color-scheme: light)');
    
    const darkMeta = document.createElement('meta');
    darkMeta.name = 'theme-color';
    darkMeta.setAttribute('content', '#36ad6a');
    darkMeta.setAttribute('media', '(prefers-color-scheme: dark)');
    
    document.head.appendChild(lightMeta);
    document.head.appendChild(darkMeta);
  }

  /**
   * 设置阅读页面的状态栏颜色
   * @param {Object} options - 阅读设置选项
   * @param {string} options.backgroundColor - 阅读背景颜色
   * @param {boolean} options.isDark - 是否为深色模式
   */
  setReaderThemeColor(options = {}) {
    this.isInReaderMode = true;
    
    const {
      backgroundColor = '#ffffff',
      isDark = false
    } = options;

    // 移除所有现有的theme-color meta标签
    this.removeAllThemeColorMeta();

    // 根据阅读背景设置状态栏颜色
    const readerMeta = document.createElement('meta');
    readerMeta.name = 'theme-color';
    
    // 如果是深色背景，使用深色状态栏；浅色背景使用浅色状态栏
    if (isDark) {
      // 深色阅读模式状态栏颜色 - 使用稍深的颜色以确保对比度
      readerMeta.setAttribute('content', this.adjustColorForStatusBar(backgroundColor, -0.1));
    } else {
      // 浅色阅读模式状态栏颜色 - 使用稍浅的颜色
      readerMeta.setAttribute('content', this.adjustColorForStatusBar(backgroundColor, 0.1));
    }
    
    document.head.appendChild(readerMeta);
  }

  /**
   * 调整颜色以适应状态栏显示
   * @param {string} color - 原始颜色
   * @param {number} adjustment - 调整强度 (-1到1)
   * @returns {string} 调整后的颜色
   */
  adjustColorForStatusBar(color, adjustment) {
    // 将颜色转换为RGB
    const rgb = this.hexToRgb(color);
    if (!rgb) return color;

    // 根据调整强度修改亮度
    const adjusted = {
      r: Math.max(0, Math.min(255, rgb.r + (255 * adjustment))),
      g: Math.max(0, Math.min(255, rgb.g + (255 * adjustment))),
      b: Math.max(0, Math.min(255, rgb.b + (255 * adjustment)))
    };

    return this.rgbToHex(adjusted.r, adjusted.g, adjusted.b);
  }

  /**
   * 将十六进制颜色转换为RGB
   * @param {string} hex - 十六进制颜色
   * @returns {Object|null} RGB对象或null
   */
  hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }

  /**
   * 将RGB转换为十六进制颜色
   * @param {number} r - 红色值
   * @param {number} g - 绿色值
   * @param {number} b - 蓝色值
   * @returns {string} 十六进制颜色
   */
  rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  }

  /**
   * 移除所有theme-color meta标签
   */
  removeAllThemeColorMeta() {
    const metas = document.querySelectorAll('meta[name="theme-color"]');
    metas.forEach(meta => meta.remove());
  }

  /**
   * 监听路由变化
   */
  setupRouteListener() {
    // 使用Vue Router的afterEach hook（需要从组件中调用）
    if (typeof window !== 'undefined' && window.Vue && window.Vue.router) {
      window.Vue.router.afterEach((to, from) => {
        // 如果离开阅读页面，恢复默认状态栏颜色
        if (from.name === 'Reader' && to.name !== 'Reader') {
          this.restoreDefaultThemeColor();
        }
      });
    }
  }

  /**
   * 恢复默认状态栏颜色
   */
  restoreDefaultThemeColor() {
    this.isInReaderMode = false;
    this.setPageThemeColor();
  }

  /**
   * 获取当前状态栏颜色
   * @returns {string} 当前状态栏颜色
   */
  getCurrentThemeColor() {
    const meta = document.querySelector('meta[name="theme-color"]');
    return meta ? meta.getAttribute('content') : this.originalThemeColor;
  }

  /**
   * 检查是否在阅读模式
   * @returns {boolean} 是否在阅读模式
   */
  isInReader() {
    return this.isInReaderMode;
  }
}

// 创建单例实例
const themeColorManager = new ThemeColorManager();

// 自动初始化
if (typeof window !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    themeColorManager.init();
  });
}

export default themeColorManager;