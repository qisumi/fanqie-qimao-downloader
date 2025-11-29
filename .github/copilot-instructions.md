# FanqieQimaoDownloader - AI Coding Agent Instructions

## Project Overview
This is a novel downloader project for Chinese reading platforms **番茄小说 (Fanqie)** and **七猫小说 (Qimao)** using Rain API V3. The project is a **Python Web application** built with FastAPI that downloads novels and exports them as EPUB files.

### Current State
- **Phase 1 完成**: 基础架构搭建 (数据库模型、配置管理、目录结构)
- **Phase 2 完成**: API客户端实现 (FanqieAPI, QimaoAPI, RateLimiter)
- **Phase 3 完成**: 服务层实现 (StorageService, BookService, DownloadService, EPUBService)
- **Phase 4 完成**: Web层实现 (FastAPI路由、页面模板、API端点)
- **Phase 5-7 待开发**: 功能完善、测试优化、部署

### Project Architecture
```
┌─────────────────────────────────────┐
│   Web Layer (FastAPI)              │  ← 用户界面、RESTful API ✅ 已实现
├─────────────────────────────────────┤
│   Service Layer (业务逻辑)          │  ← 下载管理、更新检测、EPUB生成 ✅ 已实现
├─────────────────────────────────────┤
│   Data Access Layer (SQLAlchemy)   │  ← ORM、数据库操作 ✅ 已实现
├─────────────────────────────────────┤
│   API Client Layer (Rain API)      │  ← 番茄/七猫API封装 ✅ 已实现
├─────────────────────────────────────┤
│   Storage Layer (文件系统/数据库)    │  ← 章节内容、封面、EPUB存储 ✅ 已实现
└─────────────────────────────────────┘
```

## Implemented Modules

### Service Layer (`app/services/`) ✅ Phase 3

**已实现的服务:**

```python
from app.services import (
    StorageService,     # 文件存储服务
    BookService,        # 书籍管理服务
    DownloadService,    # 下载管理服务
    EPUBService,        # EPUB生成服务
    # 异常类
    DownloadError,      # 下载错误基类
    QuotaReachedError,  # 配额已用尽
    TaskCancelledError, # 任务已取消
)
```

**StorageService 使用示例:**
```python
storage = StorageService()

# 保存章节内容
path = storage.save_chapter_content(book_uuid, chapter_index, content)
path = await storage.save_chapter_content_async(book_uuid, chapter_index, content)

# 读取章节内容
content = storage.get_chapter_content(content_path)
content = storage.get_chapter_content_by_index(book_uuid, chapter_index)

# 下载保存封面
cover_path = await storage.download_and_save_cover(book_uuid, cover_url)

# 删除书籍文件
storage.delete_book_files(book_uuid)

# 存储统计
stats = storage.get_storage_stats()
# {"books_count": 10, "total_chapters": 1500, "total_size_mb": 50.0, ...}
```

**BookService 使用示例:**
```python
book_service = BookService(db=session, storage=storage)

# 搜索书籍 (调用API)
result = await book_service.search_books("fanqie", "禁神之下", page=0)

# 添加书籍 (获取详情+封面+章节列表)
book = await book_service.add_book("fanqie", "7123456789")

# 查询书籍
books = book_service.list_books(platform="fanqie", status="completed", page=0)
book = book_service.get_book(book_uuid)
detail = book_service.get_book_with_chapters(book_uuid)

# 检测和添加新章节
new_chapters = await book_service.check_new_chapters(book_uuid)
count = await book_service.add_new_chapters(book_uuid)

# 删除书籍
book_service.delete_book(book_uuid, delete_files=True)
```

**DownloadService 使用示例:**
```python
download_service = DownloadService(db=session, storage=storage)

# 下载书籍 (创建任务+并发下载)
task = await download_service.download_book(book_uuid, task_type="full_download")

# 更新书籍 (下载新章节)
task = await download_service.update_book(book_uuid)

# 重试失败章节
count = await download_service.retry_failed_chapters(book_uuid)

# 任务管理
task = download_service.get_task(task_id)
tasks = download_service.list_tasks(book_uuid=book_uuid, status="running")
download_service.cancel_task(task_id)

# 配额查询
usage = download_service.get_quota_usage("fanqie")
all_usage = download_service.get_all_quota_usage()
```

**EPUBService 使用示例:**
```python
epub_service = EPUBService(db=session, storage=storage)

# 生成EPUB
epub_path = epub_service.generate_epub(book, chapters)

# 验证EPUB
is_valid = epub_service.validate_epub(epub_path)

# 获取EPUB信息
info = epub_service.get_epub_info(epub_path)
# {"title": "...", "author": "...", "chapter_count": 125, "file_size_mb": 1.5}
```

### Web Layer (`app/web/`) ✅ Phase 4

**FastAPI 应用入口 (`app/main.py`):**
```python
from fastapi import FastAPI
from app.web.routes import pages, books, tasks, stats

app = FastAPI(title="FanqieQimaoDownloader", version="1.0.0")
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# 路由注册
app.include_router(pages.router, prefix="", tags=["pages"])
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
```

**API端点概览:**

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/books/search` | GET | 搜索书籍 |
| `/api/books/{platform}/{book_id}` | POST | 添加书籍 |
| `/api/books/` | GET | 获取书籍列表 |
| `/api/books/{id}` | GET | 获取书籍详情 |
| `/api/books/{id}` | DELETE | 删除书籍 |
| `/api/books/{id}/epub` | POST | 生成EPUB |
| `/api/books/{id}/epub` | GET | 下载EPUB |
| `/api/tasks/` | GET | 获取任务列表 |
| `/api/tasks/{id}` | GET | 获取任务详情 |
| `/api/tasks/{book_id}/download` | POST | 启动下载任务 |
| `/api/tasks/{book_id}/update` | POST | 启动更新任务 |
| `/api/tasks/{id}/cancel` | POST | 取消任务 |
| `/api/tasks/quota` | GET | 获取所有配额 |
| `/api/tasks/quota/{platform}` | GET | 获取平台配额 |
| `/api/stats/` | GET | 系统统计概览 |
| `/api/stats/storage` | GET | 存储统计 |
| `/api/stats/quota` | GET | 配额统计 |
| `/api/stats/books/summary` | GET | 书籍摘要 |
| `/health` | GET | 健康检查 |

**页面路由:**
| 路由 | 页面 | 模板 |
|------|------|------|
| `/` | 首页 | `index.html` |
| `/login` | 登录页面 | `login.html` |
| `/logout` | 登出 | (重定向) |
| `/search` | 搜索页面 | `search.html` |
| `/books` | 书籍列表 | `books.html` |
| `/book/{id}` | 书籍详情 | `book_detail.html` |
| `/tasks` | 任务管理 | `tasks.html` |

**前端技术栈:**
- TailwindCSS (CDN) - 样式框架
- Alpine.js (CDN) - 轻量级响应式框架
- Font Awesome - 图标库

### Service Layer Schemas (`app/schemas/service_schemas.py`)

```python
from app.schemas import (
    # 书籍相关
    BookCreate, BookUpdate, BookResponse, BookListResponse, BookDetailResponse, BookStatistics,
    # 章节相关
    ChapterResponse,
    # 任务相关
    TaskCreate, TaskResponse, TaskListResponse, DownloadProgress,
    # 存储相关
    StorageStats,
    # 配额相关
    QuotaResponse, AllQuotaResponse,
    # 统计相关
    SystemStats,
    # 搜索相关
    SearchRequest,
    # 通用响应
    SuccessResponse, ErrorResponseModel,
)
```

### API Client Layer (`app/api/`)

**已实现的类:**

```python
# 基类和异常
from app.api import (
    RainAPIClient,      # 基类: 异步HTTP请求、重试、错误处理
    FanqieAPI,          # 番茄小说客户端
    QimaoAPI,           # 七猫小说客户端
    # 异常类
    APIError,           # API错误基类
    QuotaExceededError, # 配额超限 (2000万字/天)
    NetworkError,       # 网络错误
    BookNotFoundError,  # 书籍不存在
    ChapterNotFoundError, # 章节不存在
    # 枚举
    Platform,           # fanqie / qimao
    AudioMode,          # NONE / AI (@) / REAL_PERSON (!)
)
```

**FanqieAPI 使用示例:**
```python
async with FanqieAPI() as api:
    # 搜索书籍
    result = await api.search("禁神之下", page=0)
    books = result["books"]  # List[dict]
    
    # 获取书籍详情
    detail = await api.get_book_detail(book_id="7123456789")
    
    # 获取章节列表
    chapters = await api.get_chapter_list(book_id="7123456789")
    
    # 获取章节内容
    content = await api.get_chapter_content(item_id="111111")
    # content["type"] == "text" or "audio"
    # content["content"] 或 content["audio_url"]
```

**QimaoAPI 差异:**
- 搜索参数: `wd` (非 `keywords`)
- 页码: `(page-1)*10`
- 章节内容需同时传 `book_id` 和 `chapter_id`

### Rate Limiter (`app/utils/rate_limiter.py`)

```python
from app.utils import RateLimiter

# 同步使用
limiter = RateLimiter(db_session=session, limit=20000000)  # 2000万字
if limiter.can_download("fanqie"):
    # 执行下载
    limiter.record_download("fanqie", word_count=5000)

# 异步使用
if await limiter.can_download_async("fanqie"):
    await limiter.record_download_async("fanqie", word_count=5000)

# 获取配额信息
remaining = limiter.get_remaining("fanqie")
usage = limiter.get_usage("fanqie")
# usage = {"date": "2024-01-15", "downloaded": 500000, "limit": 20000000, "remaining": 19500000, "percentage": 2.5}
```

### Response Models (`app/schemas/api_responses.py`)

```python
from app.schemas import (
    BookSearchResult,   # 搜索结果中的书籍
    SearchResponse,     # 搜索响应
    BookDetail,         # 书籍详情
    ChapterInfo,        # 章节信息
    ChapterListResponse,# 章节列表响应
    TextContent,        # 文本内容
    AudioContent,       # 音频内容
    QuotaUsage,         # 配额使用情况
)
```

### Database Models (`app/models/`)

```python
from app.models import Book, Chapter, DownloadTask, DailyQuota
```

### Configuration (`app/config.py`)

```python
from app.config import get_settings, settings

# 主要配置项
settings.rain_api_key       # API密钥
settings.rain_api_base_url  # http://v3.rain.ink
settings.daily_word_limit   # 20000000 (2000万字)
settings.api_timeout        # 30秒
settings.api_retry_times    # 3次

# 密码保护配置
settings.app_password       # 应用密码，为空则不启用保护
settings.secret_key         # Cookie签名密钥
settings.session_expire_hours  # 登录有效期 (168小时=7天)
```

## Rain API V3 Endpoints

Base URL: `http://v3.rain.ink/fanqie/` 或 `http://v3.rain.ink/qimao/`

| type | 功能 | 番茄参数 | 七猫参数 |
|------|------|---------|---------|
| `1` | 搜索书籍 | `keywords`, `page` | `wd`, `page*10` |
| `2` | 书籍详情 | `bookid` | `id` |
| `3` | 章节列表 | `bookid` | `id` |
| `4` | 章节内容 | `itemid` | `id`, `chapterid` |

**特殊功能:**
- AI朗读: 搜索关键词前加 `@`
- 真人朗读: 搜索关键词前加 `!`
- 音色选择: `tone_id` 参数 (74=成熟大叔升级版, 0=甜美少女 等)

## Reference Files

| 文件 | 内容 |
|------|------|
| `reference/FANQIE_RULES.md` | API参数说明、音频模式 |
| `reference/FANQIE_EXAMPLE.txt` | 完整API响应示例 |
| `reference/QIMAO_RULES.json` | 七猫平台规则 |

## Project Conventions

### Tech Stack
- **Web框架**: FastAPI >=0.104.0
- **ORM**: SQLAlchemy >=2.0.0
- **数据库**: SQLite
- **HTTP客户端**: httpx >=0.25.0 (异步)
- **异步文件IO**: aiofiles >=23.0.0
- **EPUB生成**: ebooklib >=0.18
- **数据验证**: Pydantic >=2.0.0
- **Cookie签名**: itsdangerous >=2.1.0
- **表单处理**: python-multipart >=0.0.5

### Directory Structure
```
app/
├── api/           # ✅ API客户端 (已实现)
│   ├── base.py    # RainAPIClient基类
│   ├── fanqie.py  # FanqieAPI
│   └── qimao.py   # QimaoAPI
├── models/        # ✅ 数据模型 (已实现)
├── schemas/       # ✅ Pydantic模型 (已实现)
│   ├── api_responses.py    # API响应模型
│   └── service_schemas.py  # 服务层模型
├── services/      # ✅ 业务逻辑 (已实现)
│   ├── storage_service.py  # 文件存储
│   ├── book_service.py     # 书籍管理
│   ├── download_service.py # 下载管理
│   └── epub_service.py     # EPUB生成
├── utils/         # ✅ 工具函数 (已实现)
│   ├── database.py    # 数据库连接
│   ├── logger.py      # 日志管理
│   └── rate_limiter.py # 速率限制
├── web/           # ✅ Web层 (已实现)
│   ├── routes/    # API路由
│   │   ├── books.py   # 书籍API (/api/books)
│   │   ├── tasks.py   # 任务API (/api/tasks)
│   │   ├── stats.py   # 统计API (/api/stats)
│   │   └── pages.py   # 页面路由 (包含 /login, /logout)
│   ├── middleware/ # 中间件
│   │   └── auth.py    # 认证中间件 (AuthMiddleware)
│   ├── templates/ # Jinja2模板
│   │   ├── base.html        # 基础模板
│   │   ├── index.html       # 首页
│   │   ├── login.html       # 登录页面
│   │   ├── search.html      # 搜索页面
│   │   ├── books.html       # 书籍列表
│   │   ├── book_detail.html # 书籍详情
│   │   └── tasks.html       # 任务管理
│   └── static/    # 静态资源 (TailwindCSS CDN)
├── main.py        # ✅ FastAPI应用入口 (已实现)
└── config.py      # ✅ 配置管理 (已实现)
```

### Testing
```bash
# 运行所有测试
pytest tests/ -v

# 运行API客户端测试
pytest tests/test_api/test_api_client.py -v

# 运行服务层测试
pytest tests/test_services/test_services.py -v

# 运行Web层测试
pytest tests/test_web/test_web_routes.py -v
```

## Common Pitfalls
- **book_id vs item_id**: 前者用于书籍，后者用于章节
- **七猫需要持久化book_id**: 获取章节内容时需同时传递
- **配额限制**: 每天2000万字，使用RateLimiter检查
- **封面URL转换**: 使用 `FanqieAPI.replace_cover_url()` 获取高质量封面
- **EPUB内容编码**: 使用 `set_content(html.encode('utf-8'))` 设置章节内容