# Changelog

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

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

---

## [未发布]

### 计划中的功能

- [ ] 批量操作支持
- [ ] 音频下载功能
- [ ] WebSocket 实时进度推送
- [ ] Docker 容器化部署
- [ ] 更多平台支持
