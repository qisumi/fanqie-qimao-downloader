# PWA 功能说明（番茄七猫下载器）

本文档详细说明本仓库中实现的 PWA（Progressive Web App）功能、实现方式、调试建议以及注意事项。

## 概述

项目包含一套完整的 PWA 支持：manifest、Service Worker、多层缓存策略、离线回退、安装提示、更新流程以及骨架屏/性能优化。

## 核心功能

- 智能安装提示（`beforeinstallprompt` 事件捕获与自定义安装横幅）
- 自动更新系统（Service Worker 版本管理、跳过等待、更新提示与重启）
- 离线支持（离线页面、缓存优先/网络优先策略）
- 性能优化（关键资源预缓存、骨架屏、懒加载与后台缓存更新）
- 响应式与无障碍（针对不同设备和无障碍改进）

## 代码结构（关键文件）

- `app/web/static/manifest.json` — 应用清单（快捷方式、图标、分享目标等）
- `app/web/static/sw-enhanced.js` — 更完善的 Service Worker，实现多策略缓存、版本通知与离线页面
- `app/web/static/sw.js` — 较基础的 Service Worker，作为降级方案
- `app/web/static/js/pwa/install.js` — 安装横幅、安装逻辑与状态管理
- `app/web/static/js/pwa/update.js` — 更新检测、通知和应用更新逻辑
- `app/web/static/js/pwa/offline.js` — 网络状态检测、离线提示与离线功能说明
- `app/web/static/js/pwa/skeleton.js` — 骨架屏与页面加载过渡管理
- `app/web/static/css/pwa.css` — PWA 专用样式

## Service Worker 设计要点

- 使用版本号（`APP_VERSION`）进行缓存命名与更新比对。
- 根据请求类型使用不同策略：静态资源 cache-first、API network-first、图片 cache-first（并后台刷新）、页面 network-first 并提供离线页回退。
- 预缓存关键资源（`PRECACHE_URLS`），激活时清理旧缓存并通知客户端。
- 注意：不是所有响应都会带 `Date` header，因此不能完全依赖它判断缓存过期。可选策略是在缓存时保存自定义元数据（例如使用 IndexedDB 存储时间戳）。

## 测试与调试

- 提供了 `tests/test_pwa/test_pwa_features.py`，用于对静态资源、页面模板中 PWA 引用等进行服务端级检查。浏览器端行为（Service Worker 注册、安装提示、appinstalled 事件等）需要通过 e2e 测试（Playwright/Selenium）验证。
- 在本地调试 Service Worker：使用 Chrome 的 Application 面板可查看已注册的 SW、Cache Storage、发送消息和模拟离线。

## 性能与安全建议

- 添加适当的缓存控制头（`Cache-Control`, `Service-Worker-Allowed` 如需跨目录）以配合 SW 策略。
- 对敏感 API 使用 network-first，并避免把敏感响应长期缓存在客户端。
- 推荐在生产上通过 HTTPS 部署以支持 PWA 特性（Service Worker 需要安全上下文）。
- 为了防 XSS，建议逐步添加 Content-Security-Policy（CSP），并将内联脚本最小化。

## 开发者注意事项

- 这些大型静态文件（JS/CSS/Service Worker）可视为前端构建产物：如果你有前端源码或构建步骤（例如使用 Rollup、Webpack、esbuild），建议把源文件和构建脚本保留在 `frontend/` 或 `assets_src/`，并把生成产物加入 `.gitignore`，由 CI/CD 管道生成并发布。
- 如果保留在仓库中，建议维护简要生成说明（例如 `scripts/generate_pwa_assets.sh`）帮助未来维护者。

## 常见问题

- 为什么 Service Worker 不触发更新？
  - 需要在新 SW 安装完成后调用 `skipWaiting()` 并在 client 端通过 `postMessage` 触发 `skip-waiting` 或直接刷新页面。

- 缓存过期如何控制？
  - 可以在缓存时写入自定义 header 或把元数据存入 IndexedDB，用以判断是否需要后台刷新。

## 参考

- PWA 基本指南：https://web.dev/progressive-web-apps/
- Service Worker Cookbook: https://serviceworke.rs/

---

文档由仓库维护者生成，后续可根据实现演进补充细节与示例代码片段。
