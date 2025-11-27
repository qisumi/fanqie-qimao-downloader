# FanqieQimaoDownloader - AI Coding Agent Instructions

## Project Overview
This is a novel downloader project for Chinese reading platforms **番茄小说 (Fanqie)** and **七猫小说 (Qimao)** using Rain API V3. The project is a **Python Web application** built with FastAPI that downloads novels and exports them as EPUB files.

### Current State
- **Phase 1 完成**: 基础架构搭建 (数据库模型、配置管理、目录结构)
- **Phase 2 完成**: API客户端实现 (FanqieAPI, QimaoAPI, RateLimiter)
- **Phase 3 待开发**: 服务层实现 (BookService, DownloadService, EPUBService)
- **Phase 4-7 待开发**: Web层、功能完善、测试优化、部署

### Project Architecture
```
┌─────────────────────────────────────┐
│   Web Layer (FastAPI)              │  ← 用户界面、RESTful API
├─────────────────────────────────────┤
│   Service Layer (业务逻辑)          │  ← 下载管理、更新检测、EPUB生成
├─────────────────────────────────────┤
│   Data Access Layer (SQLAlchemy)   │  ← ORM、数据库操作
├─────────────────────────────────────┤
│   API Client Layer (Rain API)      │  ← 番茄/七猫API封装 ✅ 已实现
├─────────────────────────────────────┤
│   Storage Layer (文件系统/数据库)    │  ← 章节内容、封面、EPUB存储
└─────────────────────────────────────┘
```

## Implemented Modules

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
    QuotaExceededError, # 配额超限 (200章/天)
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
limiter = RateLimiter(db_session=session, limit=200)
if limiter.can_download("fanqie"):
    # 执行下载
    limiter.record_download("fanqie")

# 异步使用
if await limiter.can_download_async("fanqie"):
    await limiter.record_download_async("fanqie")

# 获取配额信息
remaining = limiter.get_remaining("fanqie")
usage = limiter.get_usage("fanqie")
# usage = {"date": "2024-01-15", "downloaded": 50, "limit": 200, "remaining": 150, "percentage": 25.0}
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
settings.daily_chapter_limit # 200
settings.api_timeout        # 30秒
settings.api_retry_times    # 3次
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
- **EPUB生成**: ebooklib >=0.18
- **数据验证**: Pydantic >=2.0.0

### Directory Structure
```
app/
├── api/           # ✅ API客户端 (已实现)
│   ├── base.py    # RainAPIClient基类
│   ├── fanqie.py  # FanqieAPI
│   └── qimao.py   # QimaoAPI
├── models/        # ✅ 数据模型 (已实现)
├── schemas/       # ✅ Pydantic模型 (已实现)
├── services/      # 🔄 业务逻辑 (待实现)
├── utils/         # ✅ 工具函数 (rate_limiter已实现)
├── web/           # 🔄 Web层 (待实现)
└── config.py      # ✅ 配置管理 (已实现)
```

### Testing
```bash
# 运行API客户端测试 (30个测试用例)
pytest tests/test_api/test_api_client.py -v
```

## Common Pitfalls
- **book_id vs item_id**: 前者用于书籍，后者用于章节
- **七猫需要持久化book_id**: 获取章节内容时需同时传递
- **配额限制**: 每天200章，使用RateLimiter检查
- **封面URL转换**: 使用 `FanqieAPI.replace_cover_url()` 获取高质量封面

## Next Steps (Phase 3)
待实现的服务层:
1. `StorageService` - 文件读写
2. `BookService` - 书籍管理
3. `DownloadService` - 下载逻辑
4. `EPUBService` - EPUB生成
