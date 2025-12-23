import logging
from typing import Any, Dict, Optional

from sqlalchemy import or_, func

from app.models.book import Book
from app.models.chapter import Chapter
from app.services.book.book_service_base import BookServiceBase

logger = logging.getLogger(__name__)


class BookServiceQueryMixin(BookServiceBase):
    """查询和统计相关逻辑"""
    
    def get_book(self, book_uuid: str) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_uuid).first()
    
    def get_book_by_platform_id(
        self,
        platform: str,
        book_id: str,
    ) -> Optional[Book]:
        return self.db.query(Book).filter(
            Book.platform == platform,
            Book.book_id == book_id
        ).first()
    
    def list_books(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
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
                    Book.author.ilike(search_pattern)
                )
            )
        
        total = query.count()
        query = query.order_by(Book.updated_at.desc())
        query = query.offset(page * limit).limit(limit)
        
        books = query.all()
        pages = (total + limit - 1) // limit
        
        return {
            "books": books,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }
    
    def get_book_overview(self, book_uuid: str) -> Optional[Dict[str, Any]]:
        """仅返回书籍信息和统计数据的轻量级详情。"""
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        statistics = self.get_book_statistics(book_uuid)
        return {
            "book": book,
            "statistics": statistics,
        }
    
    def get_book_with_chapters(self, book_uuid: str) -> Optional[Dict[str, Any]]:
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        chapters = self.db.query(Chapter).filter(
            Chapter.book_id == book_uuid
        ).order_by(Chapter.chapter_index).all()
        
        completed_count = sum(1 for c in chapters if c.download_status == "completed")
        failed_count = sum(1 for c in chapters if c.download_status == "failed")
        pending_count = sum(1 for c in chapters if c.download_status == "pending")
        
        statistics = {
            "total_chapters": len(chapters),
            "completed_chapters": completed_count,
            "failed_chapters": failed_count,
            "pending_chapters": pending_count,
            "progress": round(completed_count / len(chapters) * 100, 2) if chapters else 0,
        }
        
        storage_stats = self.storage.get_book_stats(book_uuid)
        statistics.update(storage_stats)
        
        return {
            "book": book,
            "chapters": chapters,
            "statistics": statistics,
        }
    
    def get_book_statistics(self, book_uuid: str) -> Dict[str, Any]:
        status_counts = self.db.query(
            Chapter.download_status,
            func.count(Chapter.id).label('count')
        ).filter(
            Chapter.book_id == book_uuid
        ).group_by(Chapter.download_status).all()
        
        completed_count = 0
        failed_count = 0
        pending_count = 0
        total_count = 0
        
        for status, count in status_counts:
            total_count += count
            if status == "completed":
                completed_count = count
            elif status == "failed":
                failed_count = count
            elif status == "pending":
                pending_count = count
        
        statistics = {
            "total_chapters": total_count,
            "completed_chapters": completed_count,
            "failed_chapters": failed_count,
            "pending_chapters": pending_count,
            "progress": round(completed_count / total_count * 100, 2) if total_count > 0 else 0,
        }
        
        storage_stats = self.storage.get_book_stats(book_uuid)
        statistics.update(storage_stats)
        
        return statistics
    
    def get_statistics(self) -> Dict[str, Any]:
        total_books = self.db.query(func.count(Book.id)).scalar()
        
        platform_counts = self.db.query(
            Book.platform, func.count(Book.id)
        ).group_by(Book.platform).all()
        books_by_platform = {p: c for p, c in platform_counts}
        
        status_counts = self.db.query(
            Book.download_status, func.count(Book.id)
        ).group_by(Book.download_status).all()
        books_by_status = {s: c for s, c in status_counts}
        
        total_chapters = self.db.query(func.sum(Book.total_chapters)).scalar() or 0
        downloaded_chapters = self.db.query(func.sum(Book.downloaded_chapters)).scalar() or 0
        
        return {
            "total_books": total_books or 0,
            "books_by_platform": books_by_platform,
            "books_by_status": books_by_status,
            "total_chapters": total_chapters,
            "downloaded_chapters": downloaded_chapters,
        }


__all__ = ["BookServiceQueryMixin"]
