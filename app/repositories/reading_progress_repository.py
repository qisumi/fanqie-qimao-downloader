"""Repository for reading progress operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.reading_progress import ReadingProgress


class ReadingProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_progress(
        self,
        user_id: str,
        book_id: str,
        device_id: Optional[str] = None,
    ) -> Optional[ReadingProgress]:
        query = self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id,
        )
        if device_id:
            query = query.filter(ReadingProgress.device_id == device_id)
        else:
            query = query.order_by(ReadingProgress.updated_at.desc())
        return query.first()

    def list_by_user_book(self, user_id: str, book_id: str) -> List[ReadingProgress]:
        return self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id,
        ).order_by(ReadingProgress.updated_at.desc()).all()
