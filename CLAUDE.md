# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Qisumi的书库** - A novel downloader for Fanqie (番茄小说), Qimao (七猫小说), and Biquge (笔趣阁) platforms, built on Rain API V3. Features batch downloading, EPUB/TXT export, and an online reader with multi-user support.

**Tech Stack:**
- **Backend**: FastAPI + SQLAlchemy 2.0 (SQLite) + httpx (async)
- **Frontend**: Vue 3 (Composition API) + Naive UI + Vite 5 + Pinia
- **Architecture**: Async-first, service layer with mixin pattern, WebSocket for real-time updates

## Common Development Commands

### Backend

```bash
# Initialize database
python init_db.py

# Start development server (auto-checks dependencies and DB)
python start.py

# Or use uvicorn directly
uvicorn app.main:app --host 127.0.0.1 --port 4568 --reload

# Run tests
pytest                           # All tests
pytest tests/test_api/          # API client tests
pytest tests/test_services/     # Service layer tests
pytest tests/test_web/          # Web layer tests
pytest tests/test_e2e/          # End-to-end tests
pytest --cov=app --cov-report=html  # Coverage report

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend

```bash
cd frontend
npm install           # Install dependencies
npm run dev          # Dev server (http://localhost:3000, proxies API to backend)
npm run build        # Build for production
```

### Docker

```bash
docker-compose up -d    # Start all services
docker-compose logs -f  # View logs
docker-compose down     # Stop services
```

## Architecture

### Backend Service Layer (Mixin Pattern)

The service layer uses a **mixin composition pattern** to organize functionality by responsibility:

- **`BookService`** (`app/services/book_service.py`): Composed of mixins for book operations
  - `BookServiceAddMixin`: Search and add books from platforms
  - `BookServiceQueryMixin`: List, detail, statistics
  - `BookServiceUpdateMixin`: Metadata refresh, incremental updates, status changes
  - `BookServiceDeleteMixin`: Book deletion
  - `BookServiceUploadMixin`: Local TXT/EPUB upload and chapter parsing

- **`DownloadService`** (`app/services/download_service.py`): Orchestrates chapter downloads
  - `DownloadTaskMixin`: Task CRUD operations, task state management
  - `DownloadOperationMixin`: Core download logic with retry and concurrency control
  - `DownloadQuotaMixin`: Daily quota tracking (20M words default, Biquge exempt)

- **`StorageService`** (`app/services/storage_service.py`): File system operations
  - `StorageServiceChapters`: Read/write chapter content files
  - `StorageServiceCover`: Download/save cover images
  - `StorageServiceFiles`: Delete book files, manage storage
  - `StorageServiceStats`: Calculate storage usage

- **`ReaderService`** (`app/services/reader_service.py`): Coordinates reader sub-services
  - `TocService`: Table of contents queries
  - `ChapterService`: Chapter content retrieval with prefetch
  - `ProgressService`: Reading progress (per-user)
  - `BookmarkService`: Bookmarks
  - `HistoryService`: Reading history

### API Client Layer

Platform-specific API clients in `app/api/`:
- **`fanqie.py`**: Fanqie Novel API client
- **`qimao.py`**: Qimao Novel API client
- **`biquge.py`**: Biquge API client
- **`base.py`**: Base classes and exceptions

All clients inherit from `BaseAPIClient` and implement `search()`, `get_book_info()`, `get_chapters()`, `get_chapter_content()` methods.

### Data Layer

- **Models** (`app/models/`): SQLAlchemy ORM models (Book, Chapter, Task, User, Quota, Bookmark, ReadingProgress, ReadingHistory, UserBook)
- **Database**: SQLite with SQLAlchemy 2.0 async-compatible syntax
- Use `select()` statements: `stmt = select(Book).where(Book.id == book_id)`

### Web Layer

- **Routes** (`app/web/routes/`): Organized by domain (books, tasks, stats, auth, users, ws)
- **Middleware** (`app/web/middleware.py`): `AuthMiddleware` for password protection
- **WebSocket** (`app/web/routes/ws.py`): Real-time download progress push to clients

### Frontend Architecture

- **Views** (`frontend/src/views/`): Page-level components (Home, Search, Books, BookDetail, Reader, Tasks, Settings, Login)
- **Components** (`frontend/src/components/`): Reusable components
- **Stores** (`frontend/src/stores/`): Pinia stores for global state
- **API** (`frontend/src/api/`): Axios wrappers for backend endpoints
- **Router** (`frontend/src/router/`): Vue Router configuration
- **PWA** (`frontend/src/pwa/`, `frontend/src/sw.js`): Service Worker for offline support

## Configuration

Configuration via `.env` file (see `.env.example`):

```ini
# Required
RAIN_API_KEY=your_api_key_here

# Optional (with defaults)
HOST=127.0.0.1
PORT=4568
DATABASE_URL=sqlite:///./data/database.db
DAILY_WORD_LIMIT=20000000
APP_PASSWORD=                    # Set to enable password protection
DEBUG=false
LOG_LEVEL=INFO
```

Access via `from app.config import settings` (singleton pattern).

## Important Patterns

### Backend

1. **Use async/await for all I/O operations** with httpx and aiofiles
2. **Type hints required** on all functions
3. **Pydantic v2 syntax**: `model_config = ConfigDict(from_attributes=True)`
4. **SQLAlchemy 2.0**: Use `select()` instead of `query()`
5. **Logging**: Use `from app.utils.logger import get_logger; logger = get_logger(__name__)`
6. **Service initialization**: Services typically require `db: Session` and optional `storage: StorageService`

### Frontend

1. **Composition API with `<script setup>`** syntax
2. **Naive UI components** follow `<n-ComponentName>` pattern
3. **API calls** through wrappers in `frontend/src/api/`
4. **Pinia stores** in `frontend/src/stores/` for shared state

### Data Storage

- **Chapter content**: `data/books/{book_uuid}/chapters/{idx:04d}.txt`
- **Covers**: `data/books/{book_uuid}/cover.jpg`
- **EPUBs**: `data/epubs/{book_title}_{book_id}.epub`
- **Database**: `data/database.db` (SQLite)

### Multi-User System

- **Public bookshelf**: Shared across all users
- **Private bookshelf**: Per-user, via `UserBook` association model
- **Reading progress**: Per-user, via `ReadingProgress` model
- **Bookmarks**: Per-user, via `Bookmark` model

## API Endpoints Reference

- **Books**: `/api/books/search`, `/api/books/{platform}/{book_id}` (POST), `/api/books/`
- **Tasks**: `/api/tasks/{book_id}/download`, `/api/tasks/{id}`
- **Reader**: `/api/books/{id}/reader/chapters`, `/api/books/{id}/reader/progress`
- **Users**: `/api/users/`, `/api/users/{id}/books`
- **WebSocket**: `/ws/tasks/{task_id}`, `/ws/books/{book_id}`
- **Health**: `/health`
- **Swagger docs**: `/docs` (when server is running)

## Adding New Features

### New API Route

1. Create route handler in `app/web/routes/`
2. Register in `app/main.py` with `app.include_router()`
3. Add Pydantic schemas in `app/schemas/` if needed

### New Service

1. Create mixin class in `app/services/{domain}/`
2. Compose into main service class
3. Inject via `__init__` into coordinator services if needed

### Database Migration

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend Page

1. Create view in `frontend/src/views/`
2. Add route in `frontend/src/router/`
3. Add navigation entry if needed
