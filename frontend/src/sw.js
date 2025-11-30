import { precacheAndRoute, matchPrecache } from 'workbox-precaching';
import { registerRoute, NavigationRoute, setCatchHandler } from 'workbox-routing';
import { CacheFirst, NetworkFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// Service Worker 版本 (用于更新检测)
const SW_VERSION = '1.5.0';

// 自动注入预缓存列表 (构建时替换)
precacheAndRoute(self.__WB_MANIFEST);

// 预缓存离线回退页面
precacheAndRoute([
  { url: '/offline.html', revision: SW_VERSION }
]);

// 静态资源 - 缓存优先策略
registerRoute(
  ({request}) => request.destination === 'style' || request.destination === 'script' || request.destination === 'font',
  new CacheFirst({
    cacheName: 'static-resources-v1',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 7 * 24 * 60 * 60, // 7 Days
      }),
    ],
  })
);

// 图片资源 - 缓存优先策略
registerRoute(
  ({request}) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images-v1',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 200,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
      }),
    ],
  })
);

// API请求 - 网络优先策略 (重要数据)
registerRoute(
  ({url}) => url.pathname.startsWith('/api/books') || url.pathname.startsWith('/api/stats'),
  new NetworkFirst({
    cacheName: 'api-data-v1',
    networkTimeoutSeconds: 10,
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 60, // 1 Hour
      }),
    ],
  })
);

// 其他 API 请求 - StaleWhileRevalidate 策略
registerRoute(
  ({url}) => url.pathname.startsWith('/api/'),
  new StaleWhileRevalidate({
    cacheName: 'api-cache-v1',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200]
      }),
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 5 * 60, // 5 Minutes
      }),
    ],
  })
);

// HTML 页面导航 - 网络优先策略
const navigationHandler = new NetworkFirst({
  cacheName: 'pages-v1',
  networkTimeoutSeconds: 5,
  plugins: [
    new CacheableResponsePlugin({
      statuses: [0, 200]
    }),
    new ExpirationPlugin({
      maxEntries: 20,
      maxAgeSeconds: 24 * 60 * 60, // 1 Day
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
