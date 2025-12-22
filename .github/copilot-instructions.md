# FanqieQimaoDownloader - AI Coding Agent Instructions

## Project Overview

基于 Rain API V3 的番茄小说和七猫小说下载工具，支持批量下载和 EPUB 导出。

- **技术栈**: Python + FastAPI + SQLAlchemy + SQLite + Vue 3 + Naive UI
- **版本**: v1.4.3（服务/路由拆分 + PWA 状态管理优化）
- **测试**: 单元 + 端到端（新增多文件 E2E 场景覆盖）

## Architecture

```
┌─────────────────────────────────────┐
│   Frontend (Vue 3 + Naive UI)      │  ← SPA 单页应用、Pinia 状态管理
├─────────────────────────────────────┤
│   Web Layer (FastAPI)              │  ← RESTful API、WebSocket
├─────────────────────────────────────┤
│   Service Layer (业务逻辑)          │  ← 下载管理、更新检测、EPUB生成
├─────────────────────────────────────┤
│   Data Access Layer (SQLAlchemy)   │  ← ORM、数据库操作
├─────────────────────────────────────┤
│   API Client Layer (Rain API)      │  ← 番茄/七猫API封装
├─────────────────────────────────────┤
│   Storage Layer (文件系统/数据库)    │  ← 章节内容、封面、EPUB存储
└─────────────────────────────────────┘
```

## Directory Structure

```
app/                    # 后端应用
├── api/                # API客户端
│   ├── base.py         # RainAPIClient基类、异常定义
│   ├── fanqie.py       # FanqieAPI
│   └── qimao.py        # QimaoAPI
├── models/             # 数据模型 (SQLAlchemy ORM)
│   ├── book.py         # Book
│   ├── chapter.py      # Chapter
│   ├── task.py         # DownloadTask
│   ├── quota.py        # DailyQuota
│   ├── user.py         # User (用户)
│   ├── user_book.py    # UserBook (书架关联)
│   ├── bookmark.py     # Bookmark (书签)
│   ├── reading_progress.py # ReadingProgress (阅读进度)
│   └── reading_history.py  # ReadingHistory (阅读历史)
├── schemas/            # Pydantic模型
│   ├── api_responses.py    # API响应模型
│   └── service_schemas.py  # 服务层模型
├── services/           # 业务逻辑（聚合类 + mixin 拆分）
│   ├── storage_service.py          # 文件存储
│   ├── book_service.py             # 书籍聚合
│   ├── book_service_base.py        # 平台客户端选择
│   ├── book_service_add.py         # 搜索/添加
│   ├── book_service_query.py       # 列表/统计
│   ├── book_service_update.py      # 增量更新/状态刷新
│   ├── book_service_delete.py      # 删除
│   ├── download_service.py         # 下载聚合
│   ├── download_service_base.py    # 公共初始化、配额
│   ├── download_service_tasks.py   # 任务管理
│   ├── download_service_operations.py # 并发章节下载/重试
│   ├── download_service_quota.py   # 配额查询与速率限制
│   ├── epub_service.py             # EPUB生成
│   ├── txt_service.py              # TXT生成
│   ├── reader_service.py           # 在线阅读与进度/书签管理
│   └── user_service.py             # 用户管理
├── utils/              # 工具函数
│   ├── database.py     # 数据库连接
│   ├── logger.py       # 日志管理
│   └── rate_limiter.py # 速率限制
├── web/                # Web层
│   ├── routes/         # API路由（聚合 + 子模块）
│   │   ├── books.py            # /api/books 聚合
│   │   ├── books_search.py     # 搜索
│   │   ├── books_crud.py       # 创建/列表/详情
│   │   ├── books_status.py     # 轻量状态与章节摘要
│   │   ├── books_maintenance.py # 刷新/增量/删除
│   │   ├── books_epub.py       # EPUB 生成/下载
│   │   ├── books_txt.py        # TXT 生成/下载
│   │   ├── books_reader.py     # 在线阅读 (TOC/内容/进度/书签)
│   │   ├── tasks.py            # /api/tasks 聚合
│   │   ├── tasks_list.py       # 列表/详情
│   │   ├── tasks_quota.py      # 配额查询
│   │   ├── tasks_start.py      # 下载/更新触发与后台执行
│   │   ├── tasks_control.py    # 取消/重试
│   │   ├── stats.py            # /api/stats
│   │   ├── auth.py             # /api/auth
│   │   ├── users.py            # /api/users
│   │   └── ws.py               # WebSocket路由
│   ├── middleware/
│   │   └── auth.py     # 认证中间件
│   ├── websocket.py    # WebSocket连接管理器
│   └── static/         # 静态资源（图标等）
├── main.py             # FastAPI应用入口
└── config.py           # 配置管理

frontend/               # Vue 3 前端项目
├── src/
│   ├── views/          # 页面组件
│   │   ├── HomeView.vue
│   │   ├── SearchView.vue
│   │   ├── BooksView.vue
│   │   ├── BookDetailView.vue
│   │   ├── ReaderView.vue    # 在线阅读器
│   │   ├── TasksView.vue
│   │   └── LoginView.vue
│   ├── components/     # 通用组件
│   ├── stores/         # Pinia 状态管理
│   ├── api/            # API 封装 (Axios)
│   ├── router/         # Vue Router 配置
│   └── App.vue         # 根组件
├── dist/               # 构建产物
├── package.json
└── vite.config.js
```

## Key Modules

### API Client (`app/api/`)

```python
from app.api import (
    RainAPIClient,       # 基类
    FanqieAPI,           # 番茄小说API
    QimaoAPI,            # 七猫小说API
    APIError,            # API错误基类
    QuotaExceededError,  # 配额超限
    BookNotFoundError,   # 书籍不存在
    Platform,            # fanqie / qimao
)

async with FanqieAPI() as api:
    result = await api.search("书名", page=0)
    detail = await api.get_book_detail(book_id="7123456789")
    chapters = await api.get_chapter_list(book_id="7123456789")
    content = await api.get_chapter_content(item_id="111111")
```

### Services (`app/services/`)

```python
from app.services import (
    StorageService,      # 文件存储
    BookService,         # 书籍管理
    DownloadService,     # 下载管理
    EPUBService,         # EPUB生成
    TXTService,          # TXT生成
    ReaderService,       # 在线阅读与进度
    UserService,         # 用户管理
    DownloadError,
    QuotaReachedError,
    TaskCancelledError,
)

# ReaderService
toc = reader_service.get_toc(book_id, page=1)
content = await reader_service.get_chapter_content(book_id, chapter_id)
reader_service.upsert_progress(user_id, book_id, chapter_id, device_id, offset_px, percent)

# BookService
book = await book_service.add_book("fanqie", "7123456789")
books = book_service.list_books(platform="fanqie", status="completed")

# DownloadService
task = await download_service.download_book(book_uuid)
task = await download_service.update_book(book_uuid)

# EPUBService
epub_path = epub_service.generate_epub(book, chapters)
```

### Configuration (`app/config.py`)

```python
from app.config import get_settings, settings

settings.rain_api_key        # API密钥
settings.rain_api_base_url   # http://v3.rain.ink
settings.daily_word_limit    # 20000000 (2000万字/天)
settings.app_password        # 应用密码 (可选)
```

# PWA 文件位置
- `frontend/public/manifest.json` — Web 应用清单（manifest）
- `frontend/src/sw.js` — Service Worker
- `frontend/src/components/pwa/` — 安装/更新/离线提示组件
- `frontend/src/composables/usePwaManager.js` — PWA 状态与提示管理
- `frontend/src/pwa/update.js` — 前端更新检测逻辑
- 图标目录：`app/web/static/images/`（包含 `icon-64.png`, `icon-192.png`, `icon-512.png`, `icon.svg`）
```

## API Endpoints

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/books/search` | GET | 搜索书籍 |
| `/api/books/{platform}/{book_id}` | POST | 添加书籍 |
| `/api/books/` | GET | 书籍列表 |
| `/api/books/{id}` | GET/DELETE | 书籍详情/删除 |
| `/api/books/{id}/epub` | POST/GET | 生成/下载EPUB |
| `/api/books/{id}/txt` | POST/GET | 生成/下载TXT |
| `/api/books/{id}/toc` | GET | 获取阅读目录 |
| `/api/books/{id}/chapters/{chapter_id}/content` | GET | 获取章节内容（缺失自动拉取） |
| `/api/books/{id}/reader/progress` | GET/POST/DELETE | 阅读进度同步 |
| `/api/books/{id}/reader/bookmarks` | GET/POST/DELETE | 书签管理 |
| `/api/tasks/{book_id}/download` | POST | 启动下载 |
| `/api/tasks/{book_id}/update` | POST | 更新书籍 |
| `/api/tasks/{id}` | GET | 任务状态 |
| `/api/users/` | GET/POST | 用户列表/创建 |
| `/api/stats/` | GET | 系统统计 |
| `/health` | GET | 健康检查 |
| `/ws/tasks/{task_id}` | WebSocket | 任务进度实时推送 |
| `/ws/books/{book_id}` | WebSocket | 书籍下载进度实时推送 |

## Rain API V3

Base URL: `http://v3.rain.ink/fanqie/` 或 `http://v3.rain.ink/qimao/`

| type | 功能 | 番茄参数 | 七猫参数 |
|------|------|---------|---------|
| `1` | 搜索 | `keywords`, `page` | `wd`, `page*10` |
| `2` | 详情 | `bookid` | `id` |
| `3` | 章节列表 | `bookid` | `id` |
| `4` | 章节内容 | `itemid` | `id`, `chapterid` |

## Tech Stack

### 后端
- **FastAPI** ≥0.104.0 - Web框架
- **SQLAlchemy** ≥2.0.0 - ORM
- **httpx** ≥0.25.0 - 异步HTTP客户端
- **ebooklib** ≥0.18 - EPUB生成
- **Pydantic** ≥2.0.0 - 数据验证

### 前端
- **Vue 3** ^3.4 - 组合式 API
- **Vite** ^5.0 - 构建工具
- **Vue Router** ^4.2 - 路由管理
- **Pinia** ^2.1 - 状态管理
- **Naive UI** ^2.38 - UI 组件库
- **Axios** ^1.6 - HTTP 客户端

## Testing

```bash
pytest tests/ -v                    # 运行所有测试
pytest tests/test_api/ -v           # API测试
pytest tests/test_services/ -v      # 服务层测试
pytest tests/test_web/ -v           # Web层测试
pytest tests/test_e2e/ -v           # 端到端测试
```

## Reference Files

| 文件 | 内容 |
|------|------|
| `reference/FANQIE_RULES.md` | API参数说明 |
| `reference/FANQIE_EXAMPLE.txt` | API响应示例 |
| `reference/QIMAO_RULES.json` | 七猫平台规则 |

## Common Pitfalls

- **book_id vs item_id**: book_id用于书籍，item_id用于番茄章节
- **七猫章节内容**: 需同时传 `book_id` 和 `chapter_id`
- **配额限制**: 每天2000万字，使用 `RateLimiter` 检查
- **封面URL**: 使用 `FanqieAPI.replace_cover_url()` 获取高质量封面
- **EPUB编码**: 使用 `set_content(html.encode('utf-8'))`
- **阅读进度**: 区分 `device_id` 以支持多端独立进度或全局同步

## 最新修改摘要

下面是对仓库中近期可观察到修改点的简要总结（基于当前工作区文件结构）：
- **在线阅读与进度管理**: 新增 `ReaderService` 与相关路由，支持在线阅读章节内容（缺失自动拉取）、预取后续章节、跨设备阅读进度同步、书签管理及阅读历史记录。
- **服务/路由拆分**: 后端服务模块已按功能拆分到 `app/services/` 与 `app/web/routes/`，实现了更清晰的职责划分，便于维护与扩展。
- **PWA 与前端更新**: 前端包含 PWA 支持（`frontend/public/manifest.json`、`frontend/src/sw.js`）和相关前端组件/组合式 API，用于离线与更新提示。
- **端到端与单元测试覆盖**: 仓库包含 `tests/test_e2e/` 与 `tests/test_api/` 等测试目录，覆盖 API 路由与 E2E 场景。
- **构建与部署脚本**: 包含 `Dockerfile`、`docker-compose.yml` 与 `scripts/build_frontend_and_migrate.py`，方便容器化部署与前端构建 + 数据库迁移的自动化流程。
- **数据库迁移演进**: `alembic/versions/` 中包含多次迁移（例如添加阅读器相关表、封面 URL、调整配额模型），表明模型在迭代中已做多次架构变更。
- **启动与管理**: 项目根目录含 `start.py` （开发/启动入口脚本）以及 `init_db.py`，便于初始化和本地运行。

如果你希望我：
- 将这些修改点写入仓库的 `CHANGELOG.md` 或生成一份更正式的发布说明，我可以继续完成；
- 或者我可以直接为你创建一个 Git 提交并推送（需要你授权并提供分支/提交信息），也可以运行测试以验证改动。

（摘要基于当前工作区文件结构与显式文件；如果你需要更精确的“最近提交”级别变更摘要，请授权我查看 Git 日志或提供额外上下文。）

## WebSocket (`app/web/`)

### 连接管理器 (`websocket.py`)

```python
from app.web.websocket import get_connection_manager

manager = get_connection_manager()

# 广播进度更新
await manager.broadcast_progress(
    task_id="task-123",
    status="running",
    total_chapters=100,
    downloaded_chapters=50,
    failed_chapters=0,
    progress=50.0,
    book_title="书名"
)

# 广播完成通知
await manager.broadcast_completed(
    task_id="task-123",
    success=True,
    message="下载完成"
)
```

### 消息格式

```json
// 进度更新
{
  "type": "progress",
  "data": {
    "task_id": "...",
    "status": "running",
    "total_chapters": 100,
    "downloaded_chapters": 50,
    "failed_chapters": 0,
    "progress": 50.0,
    "book_title": "书名",
    "timestamp": "2024-01-01T12:00:00"
  }
}

// 任务完成
{
  "type": "completed",
  "data": {
    "task_id": "...",
    "success": true,
    "message": "下载完成",
    "book_title": "书名"
  }
}

// 心跳
{ "type": "ping" } -> { "type": "pong" }
```

### 进度回调集成

```python
# 在 DownloadService 中注册回调
def sync_callback(task: DownloadTask):
    asyncio.create_task(
        manager.broadcast_progress(
            task_id=task.id,
            status=task.status,
            total_chapters=task.total_chapters,
            downloaded_chapters=task.downloaded_chapters,
            failed_chapters=task.failed_chapters,
            progress=task.progress
        )
    )

download_service.register_progress_callback(task_id, sync_callback)
```
