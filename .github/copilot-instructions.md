# FanqieQimaoDownloader - AI Coding Agent Instructions

## Project Overview

基于 Rain API V3 的番茄小说和七猫小说下载工具，支持批量下载和 EPUB 导出。

- **技术栈**: Python + FastAPI + SQLAlchemy + SQLite + WebSocket
- **版本**: v1.2.0 (WebSocket 实时进度推送)
- **测试**: 98 个测试用例

## Architecture

```
┌─────────────────────────────────────┐
│   Web Layer (FastAPI)              │  ← 用户界面、RESTful API
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
app/
├── api/           # API客户端
│   ├── base.py    # RainAPIClient基类、异常定义
│   ├── fanqie.py  # FanqieAPI
│   └── qimao.py   # QimaoAPI
├── models/        # 数据模型 (SQLAlchemy ORM)
│   ├── book.py    # Book
│   ├── chapter.py # Chapter
│   ├── task.py    # DownloadTask
│   └── quota.py   # DailyQuota
├── schemas/       # Pydantic模型
│   ├── api_responses.py    # API响应模型
│   └── service_schemas.py  # 服务层模型
├── services/      # 业务逻辑
│   ├── storage_service.py  # 文件存储
│   ├── book_service.py     # 书籍管理
│   ├── download_service.py # 下载管理
│   └── epub_service.py     # EPUB生成
├── utils/         # 工具函数
│   ├── database.py    # 数据库连接
│   ├── logger.py      # 日志管理
│   └── rate_limiter.py # 速率限制
├── web/           # Web层
│   ├── routes/    # API路由
│   │   ├── books.py   # /api/books
│   │   ├── tasks.py   # /api/tasks
│   │   ├── stats.py   # /api/stats
│   │   ├── pages.py   # 页面路由
│   │   └── ws.py      # WebSocket路由
│   ├── middleware/
│   │   └── auth.py    # 认证中间件
│   ├── websocket.py   # WebSocket连接管理器
│   └── templates/ # Jinja2模板
├── main.py        # FastAPI应用入口
└── config.py      # 配置管理
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
    DownloadError,
    QuotaReachedError,
    TaskCancelledError,
)

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

# PWA 文件位置（已添加）
- `app/web/static/manifest.json` — Web 应用清单（manifest）
- `app/web/static/sw.js` — 基础 service worker（缓存策略在 `sw.js`）
- 图标目录：`app/web/static/images/`（包含 `icon-64.png`, `icon-192.png`, `icon-512.png`, `icon.svg`）
- 图标生成脚本：`scripts/generate_icons.py`（使用 `cairosvg` 或 Pillow）
```

## API Endpoints

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/books/search` | GET | 搜索书籍 |
| `/api/books/{platform}/{book_id}` | POST | 添加书籍 |
| `/api/books/` | GET | 书籍列表 |
| `/api/books/{id}` | GET/DELETE | 书籍详情/删除 |
| `/api/books/{id}/epub` | POST/GET | 生成/下载EPUB |
| `/api/tasks/{book_id}/download` | POST | 启动下载 |
| `/api/tasks/{book_id}/update` | POST | 更新书籍 |
| `/api/tasks/{id}` | GET | 任务状态 |
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

- **FastAPI** ≥0.104.0 - Web框架
- **SQLAlchemy** ≥2.0.0 - ORM
- **httpx** ≥0.25.0 - 异步HTTP客户端
- **ebooklib** ≥0.18 - EPUB生成
- **Pydantic** ≥2.0.0 - 数据验证
- **Alpine.js** + **TailwindCSS** - 前端

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