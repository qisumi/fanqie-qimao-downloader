"""Repository for reading history operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.reading_history import ReadingHistory


class ReadingHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_history(self, user_id: str, book_id: str, limit: int) -> List[ReadingHistory]:
        return self.db.query(ReadingHistory).filter(
            ReadingHistory.user_id == user_id,
            ReadingHistory.book_id == book_id,
        ).order_by(ReadingHistory.updated_at.desc()).limit(limit).all()

    def clear_history(self, user_id: str, book_id: str) -> int:
        return self.db.query(ReadingHistory).filter(
            ReadingHistory.user_id == user_id,
            ReadingHistory.book_id == book_id,
        ).delete()

    def get_latest(self, user_id: str, book_id: str) -> Optional[ReadingHistory]:
        return self.db.query(ReadingHistory).filter(
            ReadingHistory.user_id == user_id,
            ReadingHistory.book_id == book_id,
        ).order_by(ReadingHistory.updated_at.desc()).first()
