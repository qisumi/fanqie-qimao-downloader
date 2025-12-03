# Changelog

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [1.6.2] - 2025-12-04

### 🛠 修复

- **翻页模式稳定性改进**
  - 优化Flicking组件的数据更新机制，避免动画期间的数据冲突
  - 添加内部缓存和延迟更新策略，提升翻页流畅性
  - 改进页面数据过滤逻辑，确保渲染数据的完整性
  - 优化组件重建策略，仅在必要时重建Flicking实例

- **分页算法优化**
  - 实现精确的行边界切割，避免在行中间截断文本
  - 添加行数测量功能，确保分页准确性
  - 优化文本切割算法，使用二分查找确定最佳切割点

- **阅读体验改进**
  - 优化章节预取逻辑，确保新章节正确包含在分页窗口内
  - 改进边界事件处理，增强多章节模式下的稳定性
  - 调整消息提示持续时间，提升用户体验

### 📝 文档

- 更新版本号至 1.6.2

## [1.6.1] - 2025-12-04

### 🛠 修复

- 移动端翻页模式底部章节/页码栏被安全区截断：面板使用 100dvh 并为正文和底栏预留安全区内边距，同时调整分页可用高度，确保页脚完整显示
- 滚动模式容器改为占满可用高度并去除多余预留，避免工具栏和底栏空间占用导致章节被遮挡
- 精简章节头部信息，移除冗余的字数徽标

### 📝 文档

- 更新版本号至 1.6.1，并同步 ROADMAP

## [1.6.0] - 2025-12-03

### ✨ 新增

- **在线阅读器功能**
  - 实现在线阅读器界面，支持翻页和滚动模式
  - 集成 vue-book-reader 组件，提供流畅的阅读体验
  - 阅读进度自动保存与同步
  - 书签功能，支持添加/删除书签
  - 阅读设置：字体大小、主题（浅色/深色）、行距、页边距
  - 章节跳转与目录导航

### 🛠 改进

- 优化阅读器性能，减少页面跳动
- 修复翻页模式预取导致的页面跳动问题
- 添加缓存清理机制，提升内存使用效率
- 移除调试日志，减少控制台输出

### 📝 文档

- 更新版本号至1.6.0
- 更新ROADMAP.md，标记阅读器功能为已完成
- 删除过时的文档文件（PWA_FEATURES.md, READER_DEV_PLAN.md）

## [1.5.1] - 2025-12-03

### 🛠 改进

- 书架页和书籍卡片移动端布局优化：操作按钮换行铺满，标题/元信息双行显示，提升小屏可读性
- 设置页用户列表移动端操作区铺满并单列排列，日期信息独立换行
- 首页“今日配额”卡改为显示剩余额度 + 进度条，移除分式/百分比，保证与其他卡片对齐

### 📝 文档

- 更新版本号与路线图，记录 v1.5.1 变更

## [1.5.0] - 2025-12-03

### ✨ 新增

- 公共/私人书架并存：所有人共享公共书架与任务状态，按用户名切换私人书架（共用 .env 密码，无额外认证）
- 设置页用户管理：列表/新增/重命名/删除用户，切换时自动加载对应私人书架；移动端排版优化
- 书架页收藏操作：支持从公共书架一键加入或移出私人书架，状态实时更新
- 发布辅助脚本：`scripts/build_frontend_and_migrate.py` 一键构建前端并执行 `alembic upgrade head`

### 🛠 改进

- 设置页在移动端的按钮和操作区自适应换行，提升小屏可读性

## [1.4.3] - 2025-12-02

### ♻️ 重构

- 后端服务拆分为可组合的 mixin：`BookService` 拆出搜索/查询/更新/删除模块，`DownloadService` 拆出任务管理、并发下载、配额/取消等模块，降低单文件复杂度
- API 路由按职责拆分为子模块（books_search/books_crud/books_status/...、tasks_list/tasks_quota/tasks_start/tasks_control），由聚合路由集中注册

### ✨ 新增

- PWA 体验提升：新增安装/离线/更新三类横幅组件与 `usePwaManager` 组合式 API，支持延迟弹出、跳过版本、离线提示与 Service Worker 版本控制
- 任务 WebSocket 更健壮：心跳、指数回退重连与轮询兜底并存，自动为活跃任务建立连接，确保下载进度实时可见
- EPUB 默认样式：内置 `epub_default.css`，统一封面、章节标题与段落排版

### 🧪 测试

- 端到端测试拆分为独立用例集，覆盖完整下载流程、增量更新、API 错误响应、并发下载与 EPUB 生成；新增 pytest fixtures（`conftest.py`、结构化测试数据）并移除旧版单文件 E2E 用例

## [1.4.2] - 2025-11-30

### ✨ 新增

- **深色模式支持**
  - 新增主题 Store (`theme.js`)：支持浅色/深色/跟随系统三种模式
  - CSS 变量系统扩展：添加 `:root.dark` 深色配色方案
  - Naive UI 深色主题集成：动态切换 `darkTheme`
  - 顶部导航栏添加主题切换按钮：点击循环切换三种模式

- **PWA 功能完善**
  - 新增 `PWAManager.vue` 组件：整合安装提示、更新通知、离线状态管理
  - 新增 `offline.html` 离线回退页面：美观的离线提示，支持深色模式
  - 完善 `manifest.json`：添加 PNG 图标、shortcuts 快捷方式、screenshots 截图
  - Service Worker 重构：基于 Workbox 的多层缓存策略、版本管理、自动更新

### 🔧 改进

- **缓存策略优化**
  - 静态资源：CacheFirst 策略，7天过期
  - 图片资源：CacheFirst 策略，30天过期
  - API 数据：NetworkFirst 策略，支持离线回退
  - 导航请求：NetworkFirst 策略，超时后返回离线页面

- **主题系统**
  - localStorage 持久化用户主题偏好
  - 监听 `prefers-color-scheme` 媒体查询自动适配
  - 平滑的主题过渡动画

### 📝 文档

- 更新 `PWA_FEATURES.md`：完整的 PWA 和深色模式功能文档
- 更新 `ROADMAP.md`：标记 PWA 和深色模式任务完成

## [1.4.1] - 2025-11-30

### ✨ 新增

- **全新设计系统**
  - 新增 CSS 变量定义 (`variables.css`)：统一颜色、间距、阴影、动画等
  - 新增响应式布局样式 (`responsive.css`)：移动端适配、工具类、动画效果

- **组件化重构**
  - 新增 `BookInfoCard.vue` - 书籍信息卡片组件
  - 新增 `ChapterHeatmap.vue` - 章节下载状态热力图组件
  - 新增 `ChapterRangeSelector.vue` - 章节范围选择器组件
  - 新增 `WelcomeCard.vue` - 首页欢迎卡片组件
  - 新增 `StatsGrid.vue` - 统计数据网格组件
  - 新增 `QuickActions.vue` - 快速操作入口组件
  - 新增 `SearchResultItem.vue` - 搜索结果项组件
  - 新增 `useBookWebSocket.js` - WebSocket 连接管理 Composable

### 💄 界面美化

- **登录页面全新设计**
  - 添加渐变背景和装饰动画
  - 卡片式登录表单，毛玻璃效果
  - 平滑的淡入动画和图标跳动效果

- **首页仪表盘优化**
  - 全新欢迎卡片设计，渐变背景
  - 统计卡片添加渐变色和悬停效果
  - 快速入口按钮美化

- **书库页面优化**
  - 新增页面标题和书籍计数
  - 筛选栏卡片化设计
  - 空状态优化，添加清除筛选按钮

- **书籍详情页面重构**
  - 全新书籍信息卡片布局
  - 封面添加阴影和平台角标
  - 进度条样式优化
  - 操作按钮渐变色和悬停动画

- **任务管理页面优化**
  - 任务进度卡片添加状态脉冲指示
  - 历史任务列表简化设计
  - 空状态图标优化

- **搜索页面优化**
  - 搜索头部渐变背景设计
  - 搜索结果项卡片化，悬停效果

### 📱 移动端适配

- **响应式布局**
  - 所有页面支持移动端自适应
  - 通过 `inject('isMobile')` 提供全局移动端检测
  - 筛选栏移动端可折叠

- **移动端交互优化**
  - 更大的点击区域
  - 简化的按钮布局
  - 优化的间距和字体大小

### ♻️ 重构

- **书籍详情页大幅重构**
  - 将 WebSocket 逻辑提取为 `useBookWebSocket` Composable
  - 将 UI 组件拆分为独立的子组件
  - 简化主组件代码结构

- **状态管理优化**
  - `bookStore` 新增 `refreshBook` 方法
  - `taskStore` 简化 `startDownload` 逻辑，移除 `startUpdate`

### 🐛 修复

- 修复首页活跃任务数显示为 0 的问题
- 优化 TypeScript/JavaScript 配置 (`jsconfig.json`)

## [1.4.0] - 2025-11-30

### 🚀 重大更新

- **前端框架迁移至 Vue 3 + Naive UI**
  - 完成从 Jinja2 + Alpine.js 到 Vue 3 SPA 的完整迁移
  - 使用 Naive UI 组件库重构所有页面
  - 使用 Pinia 进行状态管理
  - 使用 Vue Router 实现前端路由
  - 使用 Axios 封装 API 请求
  - 支持 Vite 开发服务器热更新

### ✨ 新增

- **Vue 3 单页应用**
  - `HomeView.vue` - 首页仪表盘
  - `SearchView.vue` - 书籍搜索
  - `BooksView.vue` - 书库管理
  - `BookDetailView.vue` - 书籍详情
  - `TasksView.vue` - 任务管理
  - `LoginView.vue` - 登录页面

- **Pinia 状态管理**
  - `userStore` - 用户认证状态
  - `taskStore` - 下载任务状态
  - `bookStore` - 书籍数据状态

- **API 封装**
  - 统一的 Axios 实例配置
  - 自动携带认证 Cookie
  - 401 响应自动跳转登录

- **PWA 支持**
  - 使用 vite-plugin-pwa 集成
  - 自动生成 Service Worker
  - 支持离线缓存和应用安装

### ♻️ 重构

- **后端适配 SPA 模式**
  - 移除 Jinja2 模板和 pages 路由
  - 添加 SPA catch-all 路由
  - 静态资源从 `frontend/dist` 提供服务

### 🗑️ 移除

- 移除 `app/web/templates/` 目录（Jinja2 模板）
- 移除 `app/web/static/main.js`（Alpine.js 逻辑）
- 移除 `app/web/static/manifest.json`（旧 PWA 清单）
- 移除 `app/web/static/sw.js`（旧 Service Worker）
- 移除 `app/web/static/assets/`（旧静态资源）
- 移除 `app/web/routes/pages.py`（页面路由）

### 📝 文档

- 更新 `README.md` 技术栈和项目结构
- 更新 `ROADMAP.md` 标记 Vue 3 迁移完成
- 更新 `.github/copilot-instructions.md` 开发指南
- 更新 `FRONTEND_MIGRATION.md` 迁移状态

## [1.3.3] - 2025-11-30

### ♻️ 重构

- **前端构建迁移至 Vite**
  - 引入 Vite 作为前端构建工具
  - 使用 Workbox 自动生成 Service Worker
  - 重构前端代码为模块化结构 (`frontend/src`)
  - 优化静态资源管理，自动清理过时文件
  - 更新 `.gitignore` 规则

## [1.3.2] - 2025-11-30

### ✨ 新增

- **PWA 支持（基础）**
  - 添加 `manifest.json` 与 `sw.js`，支持离线缓存与安装
  - 添加 `scripts/generate_icons.py` 脚本，用于生成常用 PNG 图标（64/192/512）
  - 在模板中注册 Service Worker，添加 favicon 链接

- **WebSocket 集成测试**
  - 新增 `tests/test_websocket_integration.py`，覆盖任务订阅、初始状态和进度广播

### 🐛 修复

- 修复测试断言与 `FanqieAPI` 状态映射相关的不一致（调整测试以匹配实现）

## [1.3.1] - 2025-11-30

### 🐛 修复

- **修复 WebSocket 进度回调系统**
  - 修复回调字典不共享导致进度不更新的问题：将 `_progress_callbacks` 和 `_cancelled_tasks` 改为类级别共享字典
  - 修复下载完成/失败时不触发回调的问题：在 `download_book()` 完成时显式调用回调
  - 增强日志记录：添加详细的回调注册、触发和 WebSocket 消息日志
  - 提前注册 WebSocket 回调：在启动下载/更新任务前注册回调，确保不遗漏进度更新
  - 延迟 WebSocket 连接：给服务器 100-200ms 时间注册回调后再连接

- **修复章节重复下载问题**
  - 新增 `skip_completed` 参数（默认 True）：控制是否跳过已完成章节
  - 修正 `_get_pending_chapters()` 逻辑：只在 `skip_completed=False` 时重置章节状态
  - "下载选中章节" 功能现在正确跳过已完成章节，只下载未完成的

- **修复书籍状态显示相反问题**
  - 修正 `fanqie.py` 中 `creation_status` 解析：根据实际测试，API 返回值与文档相反（0=完结, 1=连载中）
  - 更新 `reference/FANQIE_EXAMPLE.txt` 文档：添加实际规则说明
  - 搜索和详情接口均已修正状态判断逻辑

- **修复导入错误**
  - 添加缺失的 `DownloadTask` 导入到 `app/web/routes/tasks.py`

### ✨ 改进

- **UI/UX 优化**
  - 新增自定义确认对话框系统：替换浏览器原生 `confirm()` 对话框
  - 支持三种对话框类型：`danger`（红色）、`warning`（黄色）、`info`（蓝色）
  - 添加平滑动画：淡入/淡出、模态框滑入/滑出效果
  - 支持 ESC 键关闭和点击外部区域关闭
  - 删除书籍操作使用 `Confirm.danger()` 提供更好的用户体验

### 🧪 测试

- **新增测试用例**
  - 测试 `skip_completed` 参数功能：验证章节过滤逻辑
  - 增强 WebSocket 日志：便于调试进度更新问题

## [1.3.0] - 2025-11-30

### 🐛 修复

- **修复 WebSocket 进度显示异常问题**
  - 初始化 `chapterSummary` 为空对象而非 `null`，避免 `Cannot read properties of null (reading 'segments')` 错误
  - 在 `loadChapterSummary()` 失败时正确初始化 `{ segments: [] }`

- **修复完结/连载中状态显示相反问题**
  - 修正 `search.html` 中状态判断逻辑：将 `'完结'` 改为 `'已完结'` 以匹配 API 返回值
  - 确保番茄小说和七猫小说的状态标签正确显示

- **实现搜索书籍分页支持**
  - 新增分页状态：`currentPage`、`hasNextPage`、`totalResults`
  - 修改 `search()` 方法支持 `page` 参数（从 0 开始）
  - 实现预加载机制：通过 `checkNextPage()` 异步检测下一页是否有结果
  - 新增分页 UI：上一页/下一页按钮，支持禁用状态
  - 兼容番茄和七猫平台：番茄 `page=0`，七猫内部转换为 `page*10`
  - 点击分页按钮后自动滚动到页面顶部（平滑滚动）

### 🧪 测试

- **修复测试中的认证问题**
  - 修正 `client` fixture：自动为 TestClient 添加认证 Cookie
  - 新增 `unauthenticated_client` fixture：用于测试认证中间件
  - 新增 `TestAuthMiddleware` 测试类：验证认证中间件功能
  - 修复 E2E 测试的认证问题：在 `tests/test_e2e/test_e2e.py` 中应用相同修复
  - 所有测试现在能正常通过：114 个测试（Web 测试 40 个 + E2E 测试 11 个）

## [1.2.0] - 2025-11-30

### ✨ 新功能

- **WebSocket 实时进度推送**
  - 新增 `ConnectionManager` 连接管理器，支持多客户端订阅
  - 任务进度实时推送 (`/ws/tasks/{task_id}`)
  - 书籍下载进度实时推送 (`/ws/books/{book_id}`)
  - 支持心跳检测 (30秒间隔)
  - 完成/错误事件推送

- **章节范围选择下载**
  - 支持指定起始和结束章节进行下载
  - 新增快捷选择：全选、前100章、前500章、最新100章
  - API: `POST /api/tasks/{book_id}/download?start_chapter=0&end_chapter=99`

- **章节状态热力图**
  - 可视化展示各分段章节的下载状态
  - 支持点击选择分段进行下载
  - 颜色标识：绿色(完成)、黄色(部分)、灰色(未下载)、红色(有失败)

### 🔧 优化

- **前端 WebSocket 集成**
  - 任务列表页面：自动为运行中任务建立 WebSocket 连接
  - 书籍详情页面：下载时自动切换到 WebSocket 监听
  - 指数退避重连（最多5次）
  - 降级到 3 秒轮询（WebSocket 失败时）

- **认证优化**
  - WebSocket 路由独立处理 Cookie 认证
  - 认证中间件排除 `/ws` 路径

### 📝 文档

- 更新 `.github/copilot-instructions.md`，添加 WebSocket 使用说明
- 新增 `ROADMAP.md` 项目路线图

### 🧪 测试

- 新增 13 个 WebSocket 相关测试用例
- 测试覆盖：连接管理、消息广播、Schema 验证

## [1.1.1] - 2025-11-29

### 🐛 Bug 修复

- **修复添加书籍后重定向到未定义书籍详情的问题**
  - 细化新增书籍后页面跳转逻辑，避免 `None` 路径

## [1.1.0] - 2025-11-29

### 🐛 Bug 修复

- **修复取消下载任务后无法重新下载的问题**
  - 取消任务时正确更新书籍状态（`partial` 或 `pending`）
  - 修复 `download_book()` 中取消/失败后书籍状态未更新的问题
  - 处理 `asyncio.CancelledError` 时同步更新书籍和任务状态

### ✨ 新功能

- **新增轻量级书籍状态 API**
  - 添加 `GET /api/books/{book_id}/status` 端点
  - 仅返回书籍信息和统计数据，不包含章节列表
  - 优化前端轮询下载进度的性能

### 🔧 优化

- **API 客户端连接复用**
  - 批量下载时复用单个 API 客户端连接
  - 新增 `_download_single_chapter_with_api()` 方法支持连接复用
  - 保留 `_download_single_chapter()` 用于单章节下载场景

- **API 响应健壮性增强**
  - 添加空响应检查，避免 JSON 解析失败
  - 空响应和解析失败时支持自动重试

- **前端优化**
  - 书籍详情页面使用轻量级状态 API 进行进度轮询

- **移动端布局与图标优化**
  - 移动菜单为首页/搜索/书籍/任务项添加 FontAwesome 图标
  - 书籍详情、列表、任务卡片在小屏幕改为列式布局并优化按钮/文本换行
  - 修复首页书籍管理图标为 `fa-book`，避免无效 `fa-books`

## [1.0.0] - 2025-11-29

### 🎉 首个正式版本发布

这是 FanqieQimaoDownloader 的首个正式版本，实现了从番茄小说和七猫小说平台下载小说并导出为 EPUB 格式的完整功能。

### ✨ 新功能

#### API 客户端层 (Phase 2)
- 实现 `RainAPIClient` 基类，支持异步 HTTP 请求、自动重试、错误处理
- 实现 `FanqieAPI` 番茄小说客户端
  - 搜索书籍
  - 获取书籍详情
  - 获取章节列表
  - 获取章节内容（支持文本和音频）
  - 封面 URL 转换（高清封面）
- 实现 `QimaoAPI` 七猫小说客户端
- 实现 `RateLimiter` 速率限制器（每日 2000 万字配额）

#### 服务层 (Phase 3)
- 实现 `StorageService` 文件存储服务
  - 章节内容存储与读取
  - 封面图片下载与保存
  - 异步文件 I/O 支持
  - 存储统计功能
- 实现 `BookService` 书籍管理服务
  - 搜索书籍
  - 添加/删除书籍
  - 章节更新检测
  - 书籍列表查询
- 实现 `DownloadService` 下载管理服务
  - 全量下载
  - 增量更新
  - 失败重试
  - 并发控制
  - 任务管理
- 实现 `EPUBService` EPUB 生成服务
  - 生成符合 EPUB 3.0 标准的电子书
  - 支持封面图片
  - 支持目录导航
  - EPUB 验证功能

#### Web 层 (Phase 4)
- 实现 FastAPI RESTful API
  - `/api/books` - 书籍管理 API
  - `/api/tasks` - 任务管理 API
  - `/api/stats` - 统计信息 API
  - `/health` - 健康检查端点
- 实现 Web 页面
  - 首页仪表盘
  - 书籍搜索页面
  - 书籍列表页面
  - 书籍详情页面
  - 任务管理页面
- 前端技术栈
  - TailwindCSS (响应式设计)
  - Alpine.js (交互逻辑)
  - Font Awesome (图标)

#### 基础设施 (Phase 1)
- SQLAlchemy 2.0 ORM 模型
  - Book (书籍)
  - Chapter (章节)
  - DownloadTask (下载任务)
  - DailyQuota (每日配额)
- Alembic 数据库迁移
- Pydantic Settings 配置管理
- structlog 结构化日志系统

#### 测试 (Phase 5-6)
- API 客户端单元测试
- 服务层单元测试
- Web 路由测试
- 端到端集成测试
- 85 个测试用例全部通过

### 📦 依赖

- Python 3.8+
- FastAPI 0.104.0+
- SQLAlchemy 2.0.0+
- httpx 0.25.0+
- ebooklib 0.18+
- 完整依赖列表见 `requirements.txt`

### 📝 文档

- README.md - 项目说明
- DEPLOYMENT.md - 部署手册
- .env.example - 环境变量配置模板
- .github/copilot-instructions.md - AI 编程助手指南

### ⚠️ 已知限制

- 每日下载配额限制为 2000 万字（Rain API 限制）
- 仅支持文本内容下载，音频下载功能待完善
- 不支持批量操作（计划在 v1.1 版本添加）
