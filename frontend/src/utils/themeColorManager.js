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
    
    // 直接使用背景色，实现沉浸式体验
    readerMeta.setAttribute('content', backgroundColor);
    
    document.head.appendChild(readerMeta);
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