import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func

from app.models.book import Book
from app.models.chapter import Chapter
from app.services.book_service_base import BookServiceBase

logger = logging.getLogger(__name__)


class BookServiceUpdateMixin(BookServiceBase):
    """元数据刷新、新章节处理、下载状态更新"""
    
    async def refresh_book_metadata(self, book_uuid: str) -> Optional[Book]:
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        async with self._get_api_client(book.platform) as api:
            detail = await api.get_book_detail(book.book_id)
            
            book.title = detail.get("book_name", book.title)
            book.author = detail.get("author", book.author)
            book.word_count = detail.get("word_count", book.word_count)
            book.creation_status = detail.get("creation_status", book.creation_status)
            book.last_chapter_title = detail.get("last_chapter_title", book.last_chapter_title)
            
            api_total_chapters = detail.get("total_chapters")
            if api_total_chapters is not None:
                book.total_chapters = api_total_chapters
            
            update_timestamp = detail.get("last_update_timestamp", 0)
            if update_timestamp:
                try:
                    ts = int(update_timestamp) if isinstance(update_timestamp, str) else update_timestamp
                    book.last_update_time = datetime.fromtimestamp(ts)
                except (ValueError, OSError, TypeError):
                    pass
            
            self.db.commit()
            self.db.refresh(book)
            
            logger.info(f"Refreshed metadata for book: {book.title}, total_chapters: {book.total_chapters}")
            return book

    def update_book_metadata(
        self, 
        book_uuid: str, 
        title: Optional[str] = None,
        author: Optional[str] = None,
        creation_status: Optional[str] = None,
        cover_url: Optional[str] = None
    ) -> Optional[Book]:
        """更新书籍元数据（手动）"""
        book = self.get_book(book_uuid)
        if not book:
            return None
            
        if title is not None:
            book.title = title
        if author is not None:
            book.author = author
        if creation_status is not None:
            book.creation_status = creation_status
        if cover_url is not None:
            book.cover_url = cover_url
            
        book.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(book)
        return book
    
    async def check_new_chapters(self, book_uuid: str) -> List[Dict[str, Any]]:
        book = self.get_book(book_uuid)
        if not book:
            return []
        
        max_index = self.db.query(func.max(Chapter.chapter_index)).filter(
            Chapter.book_id == book_uuid
        ).scalar() or -1
        
        async with self._get_api_client(book.platform) as api:
            chapter_list = await api.get_chapter_list(book.book_id)
            chapters = chapter_list.get("chapters", [])
            
            return [
                ch for ch in chapters
                if ch.get("chapter_index", 0) > max_index
            ]
    
    async def add_new_chapters(self, book_uuid: str) -> int:
        new_chapters = await self.check_new_chapters(book_uuid)
        if not new_chapters:
            return 0
        
        book = self.get_book(book_uuid)
        
        for ch_data in new_chapters:
            chapter = Chapter(
                id=str(uuid.uuid4()),
                book_id=book_uuid,
                item_id=ch_data.get("item_id", ""),
                title=ch_data.get("title", ""),
                volume_name=ch_data.get("volume_name", ""),
                chapter_index=ch_data.get("chapter_index", 0),
                word_count=ch_data.get("word_count", 0),
                download_status="pending",
            )
            self.db.add(chapter)
        
        book.total_chapters += len(new_chapters)
        
        self.db.commit()
        logger.info(f"Added {len(new_chapters)} new chapters for book: {book.title}")
        
        return len(new_chapters)
    
    def update_book_status(
        self,
        book_uuid: str,
        status: str,
    ) -> Optional[Book]:
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        book.download_status = status
        self.db.commit()
        self.db.refresh(book)
        return book
    
    def update_download_progress(
        self,
        book_uuid: str,
        downloaded_chapters: int,
    ) -> Optional[Book]:
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        book.downloaded_chapters = downloaded_chapters
        
        if downloaded_chapters >= book.total_chapters:
            book.download_status = "completed"
        
        self.db.commit()
        self.db.refresh(book)
        return book


__all__ = ["BookServiceUpdateMixin"]
