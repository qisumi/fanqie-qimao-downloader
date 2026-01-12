# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-13
**Commit:** c43e332
**Branch:** develop

## OVERVIEW

Novel downloader/reader for Fanqie, Qimao, Biquge platforms. FastAPI backend + Vue 3/Naive UI frontend with PWA support. Rain API V3 integration for content fetching.

## STRUCTURE

```
FanqieQimaoDownloader/
├── app/                    # FastAPI backend
│   ├── api/                # External platform API clients (NOT app routes)
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic validation schemas
│   ├── services/           # Business logic (mixin-based) [has AGENTS.md]
│   ├── utils/              # Logger, database, rate limiter
│   └── web/routes/         # API endpoints (granular: books_*, tasks_*)
├── frontend/               # Vue 3 SPA [has AGENTS.md]
├── tests/                  # Pytest suite (see TEST_COVERAGE_GUIDE.md)
├── alembic/                # DB migrations
├── data/                   # SQLite + downloaded content (gitignored)
└── scripts/                # Build/migration helpers
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `app/web/routes/` | Split by domain: `books_*.py`, `tasks_*.py` |
| External API integration | `app/api/` | Normalize response → internal dict format |
| Business logic | `app/services/` | See services/AGENTS.md for mixin pattern |
| Database models | `app/models/` | SQLAlchemy 2.0 async |
| Request/response validation | `app/schemas/` | `*Create`, `*Update`, `*Response` naming |
| Frontend features | `frontend/` | See frontend/AGENTS.md |
| Tests | `tests/` | See TEST_COVERAGE_GUIDE.md |

## CONVENTIONS

### Backend (Python)
- **Async everywhere**: All I/O uses `async/await` (httpx, SQLAlchemy async)
- **Config access**: `from app.config import get_settings` (singleton)
- **Logging**: `logger = logging.getLogger(__name__)` at module top
- **Errors**: Custom exceptions in `app/api/base.py` inherit from `APIError`
- **DI pattern**: Services instantiated in routes with `db` from `Depends(get_db)`

### Schemas
- Naming: `BookCreate`, `BookUpdate`, `BookResponse`, `BookStatistics`
- Common responses: `SuccessResponse`, `ErrorResponseModel` in `common_schemas.py`

### Routes
- Granular splitting: `books_crud.py`, `books_epub.py`, `books_reader.py`
- All return Pydantic models, not raw dicts

## ANTI-PATTERNS (THIS PROJECT)

| Forbidden | Reason |
|-----------|--------|
| Direct SQL queries | Use SQLAlchemy models |
| Sync I/O in async context | Blocks event loop |
| Hardcoded config values | Use `get_settings()` |
| `as any` / type suppression | Not applicable (Python) |
| Modifying `data/` structure | UUID-based book storage is fixed |

## COMMANDS

```bash
# Development
python start.py                          # Start with auto-init
uvicorn app.main:app --reload            # Manual start

# Database
python init_db.py                        # Initialize schema
alembic revision --autogenerate -m "msg" # New migration
alembic upgrade head                     # Apply migrations

# Testing
pytest tests/ -v                         # All tests
pytest tests/ --cov=app --cov-report=html # With coverage

# Frontend (in frontend/)
npm run dev                              # Dev server :3000
npm run build                            # Build to dist/
```

## NOTES

- **Quota limit**: 20M words/day via Rain API (Biquge exempt)
- **SPA serving**: Backend serves `frontend/dist/` with catch-all route
- **Auth**: Optional password protection via `APP_PASSWORD` env var
- **WebSocket**: `/ws/tasks/{id}` and `/ws/books/{id}` for progress
- **No CI**: Manual build/test; Docker is primary deployment
- **TEST_COVERAGE_GUIDE.md**: Detailed testing patterns and priorities
