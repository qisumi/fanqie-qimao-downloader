"""Repository for book read operations."""

from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.user_book import UserBook


class BookRepository:
    """Encapsulates Book ORM queries used across routes/usecases."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, book_id: str) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_id).first()

    def get_by_platform_id(self, platform: str, platform_book_id: str) -> Optional[Book]:
        return self.db.query(Book).filter(
            Book.platform == platform,
            Book.book_id == platform_book_id,
        ).first()

    def list_books(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Book], int]:
        query = self.db.query(Book)

        if platform:
            query = query.filter(Book.platform == platform)
        if status:
            query = query.filter(Book.download_status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                )
            )

        total = query.count()
        books = query.order_by(Book.updated_at.desc()).offset(page * limit).limit(limit).all()
        return books, total

    def get_total_books(self) -> int:
        return self.db.query(func.count(Book.id)).scalar() or 0

    def get_books_by_platform(self) -> dict[str, int]:
        rows = self.db.query(
            Book.platform, func.count(Book.id)
        ).group_by(Book.platform).all()
        return {platform: count for platform, count in rows}

    def get_books_by_status(self) -> dict[str, int]:
        rows = self.db.query(
            Book.download_status, func.count(Book.id)
        ).group_by(Book.download_status).all()
        return {status: count for status, count in rows}

    def get_total_chapters_sum(self) -> int:
        return self.db.query(func.sum(Book.total_chapters)).scalar() or 0

    def get_downloaded_chapters_sum(self) -> int:
        return self.db.query(func.sum(Book.downloaded_chapters)).scalar() or 0

    def list_recent(self, limit: int = 5) -> List[Book]:
        return self.db.query(Book).order_by(Book.created_at.desc()).limit(limit).all()

    def list_by_user(
        self,
        user_id: str,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Book], int]:
        query = (
            self.db.query(Book)
            .join(UserBook, UserBook.book_id == Book.id)
            .filter(UserBook.user_id == user_id)
        )
        if platform:
            query = query.filter(Book.platform == platform)
        if status:
            query = query.filter(Book.download_status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                )
            )

        total = query.count()
        books = query.order_by(Book.updated_at.desc()).offset(page * limit).limit(limit).all()
        return books, total
