# PWA缓存配置说明

## 概述

番茄七猫小说下载器PWA缓存系统提供了完整的离线支持，包括静态资源缓存、API数据缓存和离线回退功能。

## 缓存策略

### 1. 字体文件缓存 (fonts-cache-v2)
- **文件类型**: `.ttf`, `.woff`, `.woff2`
- **策略**: CacheFirst (缓存优先)
- **缓存时间**: 1年
- **目的**: 提升字体加载速度，减少网络请求
- **最大条目**: 20个文件

### 2. 静态资源缓存 (static-resources-v2)
- **文件类型**: `.js`, `.css`
- **策略**: CacheFirst (缓存优先)
- **缓存时间**: 7天
- **目的**: 提升页面加载速度
- **最大条目**: 100个文件

### 3. 图片资源缓存 (images-cache-v2)
- **文件类型**: `.png`, `.jpg`, `.svg`, `.ico`
- **策略**: CacheFirst (缓存优先)
- **缓存时间**: 30天
- **目的**: 节省网络流量，提升加载速度
- **最大条目**: 200个文件

### 4. 关键API数据缓存 (api-critical-data-v2)
- **端点**: `/api/books/*`, `/api/stats/*`
- **策略**: NetworkFirst (网络优先)
- **缓存时间**: 1小时
- **目的**: 离线时提供关键数据支持
- **网络超时**: 10秒

### 5. 用户相关API缓存 (api-user-data-v2)
- **端点**: `/api/users/*`, `/api/tasks/*`
- **策略**: NetworkFirst (网络优先)
- **缓存时间**: 30分钟
- **目的**: 提供用户状态和任务数据
- **网络超时**: 5秒

### 6. 通用API缓存 (api-general-cache-v2)
- **端点**: `/api/*`
- **策略**: StaleWhileRevalidate (过期数据回源)
- **缓存时间**: 10分钟
- **目的**: 提升API响应速度
- **最大条目**: 30个文件

### 7. 页面缓存 (pages-cache-v2)
- **文件类型**: HTML页面
- **策略**: NetworkFirst (网络优先)
- **缓存时间**: 1天
- **目的**: 离线时提供页面访问
- **最大条目**: 20个文件

## 离线功能

### 支持的离线功能
1. 查看已缓存的书籍列表
2. 阅读已下载的章节内容
3. 浏览应用界面和设置
4. 离线状态检测和提示

### 离线页面 (offline.html)
- 自动检测网络状态
- 提供重试功能
- 显示离线可用功能列表
- 自动恢复网络后重定向

## 预缓存资源

以下资源在Service Worker安装时自动缓存：

1. **核心应用文件**
   - `/` - 应用首页
   - `/manifest.json` - PWA配置
   - `/offline.html` - 离线页面

2. **应用资源**
   - `/favicon.svg` - 应用图标
   - `/static/images/icon-192.png` - 192x192图标
   - `/static/images/icon-512.png` - 512x512图标

3. **字体文件**
   - `/寒蝉半圆体.ttf` - 中文字体

## 缓存管理

### API接口
Service Worker提供以下管理接口：

```javascript
// 获取缓存统计
navigator.serviceWorker.controller.postMessage({
  type: 'GET_CACHE_STATS'
});

// 清理指定缓存
navigator.serviceWorker.controller.postMessage({
  type: 'CLEAR_CACHE',
  cacheName: 'images-cache-v2'
});

// 清理所有缓存
navigator.serviceWorker.controller.postMessage({
  type: 'CLEAR_ALL_CACHES'
});
```

### 缓存清理策略
- Service Worker激活时会自动清理旧版本的缓存
- 根据配置的时间限制自动过期缓存
- 手动清理功能支持

## 配置参数

### Vite PWA配置
```javascript
// 文件大小限制
maximumFileSizeToCacheInBytes: 3 * 1024 * 1024 // 3MB

// 预缓存条目
additionalPrecacheEntries: [
  { url: '/', revision: null },
  { url: '/manifest.json', revision: null },
  { url: '/offline.html', revision: null },
  { url: '/favicon.svg', revision: null },
  { url: '/寒蝉半圆体.ttf', revision: null }
]
```

### 缓存大小限制
- **字体文件**: 20MB
- **静态资源**: 50MB
- **图片文件**: 200MB
- **API数据**: 100MB

## 版本更新

### 版本号: 1.7.0
- 优化缓存策略分类
- 添加缓存管理功能
- 增强离线支持
- 改进缓存文档

### 更新机制
- Service Worker版本检测
- 用户确认更新
- 自动清理旧缓存
- 版本号: `SW_VERSION`

## 调试信息

在浏览器控制台中可以通过以下方式查看缓存信息：

```javascript
// 查看缓存配置
console.log(CACHE_DOCUMENTATION);

// 获取当前缓存状态
navigator.serviceWorker.controller.postMessage({
  type: 'GET_CACHE_STATS'
}, [port]);
```

## 注意事项

1. **存储限制**: 浏览器对PWA存储有配额限制，建议定期清理
2. **网络策略**: API数据使用NetworkFirst策略确保数据新鲜度
3. **离线体验**: 离线时优先显示缓存内容，确保基本功能可用
4. **更新策略**: 采用用户确认更新模式，避免强制更新

## 性能优化

1. **字体缓存**: 永久缓存字体文件，首次加载后无需重新下载
2. **图片优化**: 30天缓存时间，平衡存储和新鲜度
3. **API缓存**: 分类缓存不同重要级别的API数据
4. **预缓存**: 关键资源预缓存，提升首屏加载速度