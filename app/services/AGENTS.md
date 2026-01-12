# SERVICES LAYER

## OVERVIEW

Business logic layer using **mixin-based composition** for complex services and **coordinator pattern** for the reader domain.

## STRUCTURE

```
services/
├── book_service.py         # Book lifecycle, metadata, stats
├── book_upload_service.py  # Local TXT/EPUB ingestion
├── download_service.py     # Mixin composition point
│   └── download/           # Mixins: tasks, operations, quota
├── storage_service.py      # Mixin composition point
│   └── storage/            # Mixins: chapters, cover, files, stats
├── reader_service.py       # Coordinator (delegates to reader/*)
│   └── reader/             # Sub-services: toc, chapter, progress, bookmark, history
├── epub_service.py         # EPUB3 generation
├── txt_service.py          # TXT export
└── user_service.py         # User management
```

## MIXIN PATTERN

For `DownloadService` and `StorageService`:

```python
# 1. Base class defines shared state
class StorageServiceBase:
    def __init__(self):
        self.books_path = settings.books_path
    
    def _sanitize_filename(self, name): ...

# 2. Mixins add specific functionality
class StorageServiceChapters(StorageServiceBase):
    def save_chapter(self, book_id, idx, content): ...

class StorageServiceStats(StorageServiceBase):
    def get_storage_stats(self): ...

# 3. Final service inherits all mixins
class StorageService(
    StorageServiceChapters,
    StorageServiceCover,
    StorageServiceFiles,
    StorageServiceStats
):
    pass  # All methods available on self
```

## COORDINATOR PATTERN

For `ReaderService` (distinct sub-domains):

```python
class ReaderService:
    def __init__(self, db: Session, storage: StorageService):
        self.toc = TocService(db, storage)
        self.chapter = ChapterService(db, storage)
        self.progress = ProgressService(db)
        self.bookmark = BookmarkService(db)
    
    # Delegates to sub-services
    def get_chapter_content(self, ...):
        return self.chapter.get_content(...)
```

## DEPENDENCY INJECTION

Services require dependencies via constructor:

```python
# In routes (app/web/routes/*.py):
def get_book(id: str, db: Session = Depends(get_db)):
    storage = StorageService()
    book_service = BookService(db=db, storage=storage)
    return book_service.get_book(id)
```

## CONVENTIONS

| Pattern | When to Use |
|---------|-------------|
| Mixin composition | Slicing a large service by functionality |
| Coordinator delegation | Multiple distinct sub-domains |
| Direct service | Simple, focused logic (TxtService, EpubService) |

## ADDING NEW SERVICES

1. **Simple service**: Create `{name}_service.py` with constructor DI
2. **Complex service**: Create subdirectory with `*_base.py` + mixins
3. **Reader-related**: Add sub-service in `reader/`, wire in `reader_service.py`

## ANTI-PATTERNS

- Direct DB queries outside services (use service methods)
- Calling external APIs from services (use `app/api/` clients)
- Shared mutable state (except `DownloadService._shared_progress_callbacks`)
