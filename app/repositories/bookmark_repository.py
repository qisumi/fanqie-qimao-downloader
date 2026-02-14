"""Repository for bookmark operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.bookmark import Bookmark


class BookmarkRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user_book(self, user_id: str, book_id: str) -> List[Bookmark]:
        return self.db.query(Bookmark).filter(
            Bookmark.user_id == user_id,
            Bookmark.book_id == book_id,
        ).order_by(Bookmark.created_at.desc()).all()

    def get_by_id(self, bookmark_id: str) -> Optional[Bookmark]:
        return self.db.query(Bookmark).filter(Bookmark.id == bookmark_id).first()

    def get_by_scope(self, user_id: str, book_id: str, bookmark_id: str) -> Optional[Bookmark]:
        return self.db.query(Bookmark).filter(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == user_id,
            Bookmark.book_id == book_id,
        ).first()
