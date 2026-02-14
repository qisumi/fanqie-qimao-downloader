"""Book response mappers used by route handlers."""

from typing import Any, Dict

from app.schemas import BookDetailResponse, BookResponse, BookStatistics
from app.services import StorageService


def to_book_response(
    book,
    storage: StorageService | None = None,
    include_export_paths: bool = False,
) -> BookResponse:
    epub_path = None
    txt_path = None

    if include_export_paths and storage is not None:
        epub = storage.get_epub_path(book.title, book.id)
        txt = storage.get_txt_path(book.title, book.id)
        epub_path = str(epub) if epub.exists() else None
        txt_path = str(txt) if txt.exists() else None

    return BookResponse(
        id=book.id,
        platform=book.platform,
        book_id=book.book_id,
        title=book.title,
        author=book.author or "",
        cover_url=book.cover_url,
        cover_path=book.cover_path,
        epub_path=epub_path,
        txt_path=txt_path,
        total_chapters=book.total_chapters or 0,
        downloaded_chapters=book.downloaded_chapters or 0,
        word_count=book.word_count,
        creation_status=book.creation_status,
        last_chapter_title=book.last_chapter_title,
        last_update_time=book.last_update_time,
        download_status=book.download_status or "pending",
        created_at=book.created_at,
        updated_at=book.updated_at,
    )


def to_book_statistics(statistics: Dict[str, Any]) -> BookStatistics:
    return BookStatistics(
        total_chapters=statistics.get("total_chapters", 0),
        completed_chapters=statistics.get("completed_chapters", 0),
        failed_chapters=statistics.get("failed_chapters", 0),
        pending_chapters=statistics.get("pending_chapters", 0),
        progress=statistics.get("progress", 0.0),
        exists=statistics.get("exists", False),
        has_cover=statistics.get("has_cover", False),
        chapter_count=statistics.get("chapter_count", 0),
        size_bytes=statistics.get("size_bytes", 0),
        size_mb=statistics.get("size_mb", 0.0),
    )


def to_book_detail_response(
    book,
    statistics: Dict[str, Any],
    storage: StorageService,
) -> BookDetailResponse:
    return BookDetailResponse(
        book=to_book_response(book, storage=storage, include_export_paths=True),
        chapters=[],
        statistics=to_book_statistics(statistics),
    )
