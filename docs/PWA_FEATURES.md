# PWA 功能说明（番茄七猫下载器）

本文档详细说明本仓库中实现的 PWA（Progressive Web App）功能、实现方式、调试建议以及注意事项。

## 概述

项目包含一套完整的 PWA 支持：manifest、Service Worker（基于 Workbox）、多层缓存策略、离线回退、安装提示、更新流程以及深色模式支持。

## 核心功能

- **智能安装提示**：通过 `beforeinstallprompt` 事件捕获，使用 Naive UI 组件展示美观的安装横幅
- **自动更新系统**：Service Worker 版本管理、跳过等待、更新提示与自动重载
- **离线支持**：离线回退页面、缓存优先/网络优先策略、网络状态实时监测
- **深色模式**：支持浅色/深色/跟随系统三种模式，与 Naive UI 深色主题完美集成
- **快捷方式**：PWA 安装后支持快捷入口（搜索、书架、任务）

## 代码结构（关键文件）

### 前端（Vue 3）

```
frontend/
├── public/
│   ├── manifest.json          # PWA 应用清单
│   └── offline.html           # 离线回退页面
├── src/
│   ├── sw.js                  # Service Worker (Workbox)
│   ├── stores/
│   │   └── theme.js           # 主题状态管理 (Pinia)
│   ├── components/
│   │   ├── PWAManager.vue     # PWA 管理组件（安装/更新/离线提示）
│   │   └── AppHeader.vue      # 顶部导航（含主题切换按钮）
│   ├── styles/
│   │   └── variables.css      # CSS 变量（含深色模式）
│   └── pwa/                   # PWA 原生模块（备用）
│       ├── install.js
│       ├── update.js
│       ├── offline.js
│       └── skeleton.js
└── vite.config.js             # Vite PWA 插件配置
```

### 后端静态资源

```
app/web/static/images/
├── icon-64.png
├── icon-192.png
├── icon-512.png
└── icon.svg
```

## Service Worker 设计要点

基于 **Workbox** 实现，使用 `injectManifest` 策略：

### 缓存策略

| 资源类型 | 策略 | 缓存名称 | 过期时间 |
|---------|------|---------|---------|
| 静态资源 (CSS/JS/Font) | CacheFirst | static-resources-v1 | 7 天 |
| 图片资源 | CacheFirst | images-v1 | 30 天 |
| API 数据 (/api/books, /api/stats) | NetworkFirst | api-data-v1 | 1 小时 |
| 其他 API | StaleWhileRevalidate | api-cache-v1 | 5 分钟 |
| HTML 页面 | NetworkFirst | pages-v1 | 1 天 |

### 离线回退

```javascript
// 导航请求失败时返回离线页面
setCatchHandler(async ({request}) => {
  if (request.destination === 'document') {
    return matchPrecache('/offline.html');
  }
  return Response.error();
});
```

### 更新机制

1. 新 Service Worker 安装后进入 `waiting` 状态
2. PWAManager 组件检测到更新，显示通知
3. 用户点击"立即更新"发送 `SKIP_WAITING` 消息
4. 新 SW 激活后触发 `controllerchange` 事件
5. 页面自动刷新以加载新版本

## 深色模式

### 主题切换

支持三种模式：
- **浅色**：固定使用浅色主题
- **深色**：固定使用深色主题
- **跟随系统**：根据 `prefers-color-scheme` 媒体查询自动切换

### 实现方式

1. **Pinia Store** (`stores/theme.js`)：管理主题状态和持久化
2. **CSS 变量** (`styles/variables.css`)：`:root.dark` 选择器定义深色配色
3. **Naive UI**：动态传入 `darkTheme` 到 `n-config-provider`
4. **DOM class**：在 `<html>` 元素上切换 `dark` class

```javascript
// 主题切换 API
import { useThemeStore, ThemeMode } from '@/stores/theme'

const themeStore = useThemeStore()
themeStore.setMode(ThemeMode.DARK)    // 设置深色
themeStore.toggleMode()                // 循环切换
themeStore.isDark                      // 是否为深色模式
```

## 测试与调试

### 本地调试

1. 启动开发服务器：
   ```bash
   cd frontend
   npm run dev
   ```

2. 打开 Chrome DevTools → Application 面板：
   - **Service Workers**：查看注册状态、更新、调试
   - **Cache Storage**：查看缓存内容
   - **Manifest**：检查应用清单

3. 模拟离线：勾选 "Offline" 复选框

### Lighthouse 审计

```bash
# 构建生产版本
npm run build

# 使用 Lighthouse 检查 PWA 评分
npx lighthouse http://localhost:4568 --view
```

## PWA 安装要求

浏览器显示安装提示需满足以下条件：

1. ✅ HTTPS 或 localhost
2. ✅ 有效的 Web App Manifest
3. ✅ 注册了 Service Worker
4. ✅ 用户与页面有一定交互

## 配置说明

### manifest.json 关键配置

```json
{
  "name": "番茄七猫小说下载器",
  "short_name": "番茄七猫",
  "display": "standalone",
  "theme_color": "#18a058",
  "icons": [...],
  "shortcuts": [
    {"name": "搜索书籍", "url": "/search"},
    {"name": "我的书架", "url": "/books"},
    {"name": "下载任务", "url": "/tasks"}
  ]
}
```

### Vite PWA 插件配置

```javascript
// vite.config.js
VitePWA({
  strategies: 'injectManifest',
  srcDir: 'src',
  filename: 'sw.js',
  devOptions: {
    enabled: true,
    type: 'module'
  }
})
```

## 常见问题

### Service Worker 不触发更新？

1. 确保新 SW 文件有变化（构建时自动更新预缓存列表）
2. 检查是否正确处理了 `SKIP_WAITING` 消息
3. 在 DevTools 中手动点击 "Update" 按钮测试

### 深色模式样式不生效？

1. 确保使用 CSS 变量而非硬编码颜色
2. 检查 `<html>` 元素上是否有 `dark` class
3. 确认 Naive UI 组件正确接收了 `darkTheme` prop

### 离线页面不显示？

1. 确保 `offline.html` 在预缓存列表中
2. 检查 `setCatchHandler` 配置
3. 清除所有缓存后重新测试

## 参考资源

- [Workbox 文档](https://developer.chrome.com/docs/workbox/)
- [PWA 基本指南](https://web.dev/progressive-web-apps/)
- [Naive UI 深色模式](https://www.naiveui.com/zh-CN/os-theme/docs/customize-theme)
- [Vite Plugin PWA](https://vite-pwa-org.netlify.app/)

---

*文档更新于 v1.5.1，包含 PWA 功能完善、深色模式与移动端细节优化。*
