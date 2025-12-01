import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from app.models.book import Book
from app.models.chapter import Chapter
from app.services.book_service_base import BookServiceBase

logger = logging.getLogger(__name__)


class BookServiceAddMixin(BookServiceBase):
    """搜索与添加书籍相关逻辑"""
    
    async def search_books(
        self,
        platform: str,
        keyword: str,
        page: int = 0,
    ) -> Dict[str, Any]:
        async with self._get_api_client(platform) as api:
            result = await api.search(keyword, page)
            result["platform"] = platform
            return result
    
    async def add_book(
        self,
        platform: str,
        book_id: str,
        download_cover: bool = True,
        fetch_chapters: bool = True,
    ) -> Book:
        existing = self.get_book_by_platform_id(platform, book_id)
        if existing:
            raise ValueError(f"Book already exists: {existing.title} ({existing.id})")
        
        async with self._get_api_client(platform) as api:
            logger.info(f"Fetching book detail: platform={platform}, book_id={book_id}")
            detail = await api.get_book_detail(book_id)
            
            book_uuid = str(uuid.uuid4())
            cover_url = detail.get("cover_url", "")
            book = Book(
                id=book_uuid,
                platform=platform,
                book_id=book_id,
                title=detail.get("book_name", ""),
                author=detail.get("author", ""),
                cover_url=cover_url,
                word_count=detail.get("word_count", 0),
                creation_status=detail.get("creation_status", ""),
                last_chapter_title=detail.get("last_chapter_title", ""),
                download_status="pending",
            )
            
            update_timestamp = detail.get("last_update_timestamp", 0)
            if update_timestamp:
                try:
                    ts = int(update_timestamp) if isinstance(update_timestamp, str) else update_timestamp
                    book.last_update_time = datetime.fromtimestamp(ts)
                except (ValueError, OSError, TypeError):
                    pass
            
            if download_cover and cover_url:
                cover_path = await self.storage.download_and_save_cover(book_uuid, cover_url)
                if cover_path:
                    book.cover_path = cover_path
            
            if fetch_chapters:
                logger.info(f"Fetching chapter list for book: {book.title}")
                chapter_list = await api.get_chapter_list(book_id)
                
                book.total_chapters = chapter_list.get("total_chapters", 0)
                
                chapters_data = chapter_list.get("chapters", [])
                for ch_data in chapters_data:
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
            
            self.db.add(book)
            self.db.commit()
            self.db.refresh(book)
            
            logger.info(f"Added book: {book.title} ({book.id}), {book.total_chapters} chapters")
            
            return book


__all__ = ["BookServiceAddMixin"]
