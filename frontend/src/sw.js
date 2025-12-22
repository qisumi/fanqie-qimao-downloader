import { precacheAndRoute, matchPrecache } from 'workbox-precaching';
import { registerRoute, NavigationRoute, setCatchHandler } from 'workbox-routing';
import { CacheFirst, NetworkFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// Service Worker 版本 (用于更新检测)
const SW_VERSION = '1.7.1';

// 缓存配置常量
const CACHE_CONFIG = {
  // 静态资源缓存配置
  static: {
    maxEntries: 100,
    maxAgeSeconds: 7 * 24 * 60 * 60, // 7天
    strategy: 'CacheFirst'
  },
  
  // 图片缓存配置
  images: {
    maxEntries: 200,
    maxAgeSeconds: 30 * 24 * 60 * 60, // 30天
    strategy: 'CacheFirst'
  },
  
  // 字体缓存配置
  fonts: {
    maxEntries: 20,
    maxAgeSeconds: 365 * 24 * 60 * 60, // 1年
    strategy: 'CacheFirst'
  },
  
  // API数据缓存配置
  api: {
    maxEntries: 100,
    maxAgeSeconds: 60 * 60, // 1小时
    networkTimeoutSeconds: 10,
    strategy: 'NetworkFirst'
  },
  
  // 页面缓存配置
  pages: {
    maxEntries: 20,
    maxAgeSeconds: 24 * 60 * 60, // 1天
    networkTimeoutSeconds: 5,
    strategy: 'NetworkFirst'
  }
};

// 缓存文件类型映射
const CACHE_FILE_TYPES = {
  // 核心应用文件
  core: ['index.html', 'manifest.json'],
  
  // 静态资源文件
  static: ['.js', '.css', '.woff', '.woff2', '.ttf'],
  
  // 图片资源文件
  images: ['.png', '.jpg', '.jpeg', '.svg', '.ico'],
  
  // 离线资源文件
  offline: ['offline.html'],
  
  // 字体文件
  fonts: ['.ttf', '.woff', '.woff2'],
  
  // API端点
  apiEndpoints: ['/api/books', '/api/stats', '/api/tasks', '/api/users']
};

// 自动注入预缓存列表 (构建时替换)
precacheAndRoute(self.__WB_MANIFEST);

// 缓存文件类型检测工具函数
function getFileCategory(url) {
  const pathname = url.pathname;
  
  // 检测核心应用文件
  if (CACHE_FILE_TYPES.core.some(file => pathname.endsWith(file))) {
    return 'core';
  }
  
  // 检测字体文件
  if (CACHE_FILE_TYPES.fonts.some(ext => pathname.endsWith(ext))) {
    return 'fonts';
  }
  
  // 检测图片文件
  if (CACHE_FILE_TYPES.images.some(ext => pathname.endsWith(ext))) {
    return 'images';
  }
  
  // 检测离线资源
  if (CACHE_FILE_TYPES.offline.some(file => pathname.endsWith(file))) {
    return 'offline';
  }
  
  // 检测静态资源
  if (CACHE_FILE_TYPES.static.some(ext => pathname.endsWith(ext))) {
    return 'static';
  }
  
  // 检测API端点
  if (CACHE_FILE_TYPES.apiEndpoints.some(endpoint => pathname.startsWith(endpoint))) {
    return 'api';
  }
  
  return 'other';
}

// 字体文件 - 缓存优先策略 (最长缓存时间，支持大字体文件)
registerRoute(
  ({request}) => request.destination === 'font' || request.url.includes('.ttf'),
  new CacheFirst({
    cacheName: 'fonts-cache-v2',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: CACHE_CONFIG.fonts.maxEntries,
        maxAgeSeconds: CACHE_CONFIG.fonts.maxAgeSeconds,
      }),
    ],
  })
);

// 静态资源 - 缓存优先策略 (JS, CSS)
registerRoute(
  ({request}) => request.destination === 'style' || request.destination === 'script',
  new CacheFirst({
    cacheName: 'static-resources-v2',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: CACHE_CONFIG.static.maxEntries,
        maxAgeSeconds: CACHE_CONFIG.static.maxAgeSeconds,
      }),
    ],
  })
);

// 图片资源 - 缓存优先策略
registerRoute(
  ({request}) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images-cache-v2',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: CACHE_CONFIG.images.maxEntries,
        maxAgeSeconds: CACHE_CONFIG.images.maxAgeSeconds,
      }),
    ],
  })
);

// API请求 - 网络优先策略 (重要数据: 书籍、统计信息)
registerRoute(
  ({url}) => url.pathname.startsWith('/api/books') || url.pathname.startsWith('/api/stats'),
  new NetworkFirst({
    cacheName: 'api-critical-data-v2',
    networkTimeoutSeconds: CACHE_CONFIG.api.networkTimeoutSeconds,
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: CACHE_CONFIG.api.maxEntries,
        maxAgeSeconds: CACHE_CONFIG.api.maxAgeSeconds,
      }),
    ],
  })
);

// 用户相关API - 网络优先策略 (较短缓存)
registerRoute(
  ({url}) => url.pathname.startsWith('/api/users') || url.pathname.startsWith('/api/tasks'),
  new NetworkFirst({
    cacheName: 'api-user-data-v2',
    networkTimeoutSeconds: 5,
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 30 * 60, // 30分钟
      }),
    ],
  })
);

// 其他 API 请求 - StaleWhileRevalidate 策略 (非关键数据)
registerRoute(
  ({url}) => url.pathname.startsWith('/api/') && !url.pathname.startsWith('/api/books') && !url.pathname.startsWith('/api/stats') && !url.pathname.startsWith('/api/users') && !url.pathname.startsWith('/api/tasks'),
  new StaleWhileRevalidate({
    cacheName: 'api-general-cache-v2',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 30,
        maxAgeSeconds: 10 * 60, // 10分钟
      }),
    ],
  })
);

// HTML 页面导航 - 网络优先策略
const navigationHandler = new NetworkFirst({
  cacheName: 'pages-cache-v2',
  networkTimeoutSeconds: CACHE_CONFIG.pages.networkTimeoutSeconds,
  plugins: [
    new CacheableResponsePlugin({
      statuses: [0, 200]
    }),
    new ExpirationPlugin({
      maxEntries: CACHE_CONFIG.pages.maxEntries,
      maxAgeSeconds: CACHE_CONFIG.pages.maxAgeSeconds,
    }),
  ],
});

// 注册导航路由
registerRoute(
  new NavigationRoute(navigationHandler, {
    // 排除 API 路由和静态资源
    denylist: [/^\/api\//, /^\/static\//]
  })
);

// 设置全局 catch handler - 离线回退
setCatchHandler(async ({event, request}) => {
  // 如果是导航请求，返回离线页面
  if (request.destination === 'document') {
    return matchPrecache('/offline.html');
  }
  
  // 对于其他请求，返回一个基本的错误响应
  return Response.error();
});

// Handle skip waiting - 接收来自客户端的消息
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  // 响应版本查询
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: SW_VERSION });
  }
  
  // 缓存统计查询
  if (event.data && event.data.type === 'GET_CACHE_STATS') {
    getCacheStats().then(stats => {
      event.ports[0].postMessage({ stats });
    });
  }
  
  // 清理指定缓存
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    const { cacheName } = event.data;
    clearCache(cacheName).then(result => {
      event.ports[0].postMessage({ result });
    });
  }
  
  // 清理所有缓存
  if (event.data && event.data.type === 'CLEAR_ALL_CACHES') {
    clearAllCaches().then(result => {
      event.ports[0].postMessage({ result });
    });
  }
});

// 安装事件 - 预缓存关键资源
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker v' + SW_VERSION);
  // 不自动 skipWaiting，等待用户确认更新
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker v' + SW_VERSION);
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => {
            // 删除不再使用的旧缓存
            return !cacheName.endsWith('-v1') && cacheName !== 'workbox-precache-v2';
          })
          .map((cacheName) => {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    })
  );
  
  // 立即控制所有页面
  event.waitUntil(self.clients.claim());
});

/**
 * 缓存管理工具函数
 */

// 获取缓存统计信息
async function getCacheStats() {
  const cacheNames = await caches.keys();
  const stats = {};
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    stats[cacheName] = {
      entries: keys.length,
      cacheName,
      type: getCacheType(cacheName)
    };
  }
  
  return stats;
}

// 获取缓存类型
function getCacheType(cacheName) {
  if (cacheName.includes('fonts')) return 'fonts';
  if (cacheName.includes('static')) return 'static';
  if (cacheName.includes('images')) return 'images';
  if (cacheName.includes('api')) return 'api';
  if (cacheName.includes('pages')) return 'pages';
  return 'other';
}

// 清理指定缓存
async function clearCache(cacheName) {
  try {
    const cache = await caches.open(cacheName);
    await cache.clear();
    return { success: true, cacheName };
  } catch (error) {
    console.error('清理缓存失败:', error);
    return { success: false, error: error.message };
  }
}

// 清理所有缓存
async function clearAllCaches() {
  try {
    const cacheNames = await caches.keys();
    const results = [];
    
    for (const cacheName of cacheNames) {
      await caches.delete(cacheName);
      results.push(cacheName);
    }
    
    return { success: true, cleared: results };
  } catch (error) {
    console.error('清理所有缓存失败:', error);
    return { success: false, error: error.message };
  }
}

// 缓存文件标注和说明
const CACHE_DOCUMENTATION = {
  version: SW_VERSION,
  description: '番茄·七猫·笔趣阁小说下载器 PWA 缓存配置',
  caches: {
    'fonts-cache-v2': {
      description: '字体文件缓存',
      files: ['.ttf', '.woff', '.woff2'],
      strategy: 'CacheFirst',
      maxAge: '1年',
      purpose: '提升字体加载速度'
    },
    'static-resources-v2': {
      description: '静态资源缓存 (JS/CSS)',
      files: ['.js', '.css'],
      strategy: 'CacheFirst',
      maxAge: '7天',
      purpose: '提升页面加载速度'
    },
    'images-cache-v2': {
      description: '图片资源缓存',
      files: ['.png', '.jpg', '.svg', '.ico'],
      strategy: 'CacheFirst',
      maxAge: '30天',
      purpose: '节省网络流量，提升加载速度'
    },
    'api-critical-data-v2': {
      description: '关键API数据缓存 (书籍、统计)',
      files: ['/api/books/*', '/api/stats/*'],
      strategy: 'NetworkFirst',
      maxAge: '1小时',
      purpose: '离线时提供关键数据支持'
    },
    'api-user-data-v2': {
      description: '用户相关API缓存',
      files: ['/api/users/*', '/api/tasks/*'],
      strategy: 'NetworkFirst',
      maxAge: '30分钟',
      purpose: '提供用户状态和任务数据'
    },
    'api-general-cache-v2': {
      description: '通用API数据缓存',
      files: ['/api/*'],
      strategy: 'StaleWhileRevalidate',
      maxAge: '10分钟',
      purpose: '提升API响应速度'
    },
    'pages-cache-v2': {
      description: '页面缓存',
      files: ['HTML pages'],
      strategy: 'NetworkFirst',
      maxAge: '1天',
      purpose: '离线时提供页面访问'
    }
  },
  offlineFeatures: [
    '查看已缓存的书籍列表',
    '阅读已下载的章节内容', 
    '浏览应用界面和设置',
    '离线状态检测和提示'
  ]
};

// 导出缓存配置供调试使用
if (typeof globalThis !== 'undefined') {
  globalThis.CACHE_DOCUMENTATION = CACHE_DOCUMENTATION;
}
