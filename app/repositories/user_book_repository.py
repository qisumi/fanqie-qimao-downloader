"""Repository for user shelf link operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user_book import UserBook


class UserBookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_link(self, user_id: str, book_id: str) -> Optional[UserBook]:
        return self.db.query(UserBook).filter(
            UserBook.user_id == user_id,
            UserBook.book_id == book_id,
        ).first()

    def list_book_ids(self, user_id: str) -> List[str]:
        rows = self.db.query(UserBook.book_id).filter(UserBook.user_id == user_id).all()
        return [row.book_id for row in rows]
