"""Repository for chapter read operations."""

from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chapter import Chapter


class ChapterRepository:
    """Encapsulates Chapter ORM queries used by services/usecases."""

    def __init__(self, db: Session):
        self.db = db

    def list_by_book(self, book_id: str) -> List[Chapter]:
        return self.db.query(Chapter).filter(
            Chapter.book_id == book_id
        ).order_by(Chapter.chapter_index).all()

    def count_by_book(self, book_id: str) -> int:
        return self.db.query(func.count(Chapter.id)).filter(
            Chapter.book_id == book_id
        ).scalar() or 0

    def list_by_book_paginated(self, book_id: str, page: int, limit: int) -> tuple[list[Chapter], int]:
        query = self.db.query(Chapter).filter(Chapter.book_id == book_id)
        total = query.count()
        offset = (page - 1) * limit
        chapters = query.order_by(Chapter.chapter_index).offset(offset).limit(limit).all()
        return chapters, total

    def get_by_id_and_book(self, chapter_id: str, book_id: str) -> Chapter | None:
        return self.db.query(Chapter).filter(
            Chapter.id == chapter_id,
            Chapter.book_id == book_id,
        ).first()

    def get_status_counts(self, book_id: str) -> List[Tuple[str, int]]:
        return self.db.query(
            Chapter.download_status,
            func.count(Chapter.id).label("count"),
        ).filter(
            Chapter.book_id == book_id
        ).group_by(Chapter.download_status).all()

    def get_max_chapter_index(self, book_id: str) -> int:
        return self.db.query(func.max(Chapter.chapter_index)).filter(
            Chapter.book_id == book_id
        ).scalar() or -1

    def get_adjacent_chapter_ids(self, book_id: str, chapter_index: int) -> tuple[str | None, str | None]:
        prev_id = self.db.query(Chapter.id).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index < chapter_index,
        ).order_by(Chapter.chapter_index.desc()).limit(1).scalar()
        next_id = self.db.query(Chapter.id).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index > chapter_index,
        ).order_by(Chapter.chapter_index.asc()).limit(1).scalar()
        return prev_id, next_id

    def _build_range_query(
        self,
        book_id: str,
        start_chapter: int = 0,
        end_chapter: int | None = None,
    ):
        query = self.db.query(func.count(Chapter.id)).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index >= start_chapter,
        )
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)
        return query

    def list_in_range(
        self,
        book_id: str,
        start_chapter: int = 0,
        end_chapter: int | None = None,
    ) -> List[Chapter]:
        query = self.db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index >= start_chapter,
        )
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)
        return query.order_by(Chapter.chapter_index).all()

    def count_for_full_download(
        self,
        book_id: str,
        start_chapter: int = 0,
        end_chapter: int | None = None,
        skip_completed: bool = True,
    ) -> int:
        query = self._build_range_query(
            book_id=book_id,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
        )
        if skip_completed:
            query = query.filter(Chapter.download_status != "completed")
        return query.scalar() or 0

    def count_for_update(
        self,
        book_id: str,
        start_chapter: int = 0,
        end_chapter: int | None = None,
    ) -> int:
        query = self._build_range_query(
            book_id=book_id,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
        )
        query = query.filter(Chapter.download_status == "pending")
        return query.scalar() or 0

    def list_pending_for_download(
        self,
        book_id: str,
        task_type: str,
        start_chapter: int = 0,
        end_chapter: int | None = None,
        skip_completed: bool = True,
    ) -> List[Chapter]:
        query = self.db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index >= start_chapter,
        )
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)

        if task_type == "full_download":
            if skip_completed:
                query = query.filter(Chapter.download_status != "completed")
        else:
            query = query.filter(Chapter.download_status == "pending")

        return query.order_by(Chapter.chapter_index).all()

    def count_failed_by_book(self, book_id: str) -> int:
        return self.db.query(func.count(Chapter.id)).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "failed",
        ).scalar() or 0

    def count_completed_by_book(self, book_id: str) -> int:
        return self.db.query(func.count(Chapter.id)).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "completed",
        ).scalar() or 0

    def reset_failed_to_pending(self, book_id: str) -> int:
        return self.db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "failed",
        ).update({"download_status": "pending"})

    def list_failed_by_book(self, book_id: str) -> List[Chapter]:
        return self.db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "failed",
        ).all()

    def list_completed_by_book(self, book_id: str) -> List[Chapter]:
        return self.db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "completed",
        ).order_by(Chapter.chapter_index).all()

    def list_completed_ids_by_book(self, book_id: str) -> list[str]:
        rows = self.db.query(Chapter.id).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "completed",
        ).all()
        return [row[0] for row in rows]

    def list_after_index(self, book_id: str, start_index: int, limit: int) -> List[Chapter]:
        return self.db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index > start_index,
        ).order_by(Chapter.chapter_index).limit(limit).all()

    def get_total_count(self) -> int:
        return self.db.query(func.count(Chapter.id)).scalar() or 0

    def get_downloaded_count(self) -> int:
        return self.db.query(func.count(Chapter.id)).filter(
            Chapter.download_status == "completed"
        ).scalar() or 0
