"""
书籍管理服务

整合了书籍的搜索、添加、查询、更新、删除等功能。
本地上传功能分离到 BookUploadService。
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_

from app.api.base import Platform
from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.api.biquge import BiqugeAPI
from app.models.book import Book
from app.models.chapter import Chapter
from app.services.storage_service import StorageService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BookService:
    """
    书籍管理服务

    整合了以下功能:
    - 平台书籍搜索与添加
    - 书籍查询与统计
    - 元数据刷新与增量更新
    - 书籍删除
    """

    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
    ):
        self.db = db
        self.storage = storage or StorageService()

    def _get_api_client(self, platform: str) -> FanqieAPI | QimaoAPI | BiqugeAPI:
        """根据平台获取API客户端"""
        if platform == Platform.FANQIE.value or platform == "fanqie":
            return FanqieAPI()
        if platform == Platform.QIMAO.value or platform == "qimao":
            return QimaoAPI()
        if platform == Platform.BIQUGE.value or platform == "biquge":
            return BiqugeAPI()
        raise ValueError(f"Unsupported platform: {platform}")

    # ============ 搜索与添加 ============

    async def search_books(
        self,
        platform: str,
        keyword: str,
        page: int = 0,
    ) -> Dict[str, Any]:
        """搜索平台书籍"""
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
        """从平台添加书籍"""
        existing = self.get_book_by_platform_id(platform, book_id)
        if existing:
            raise ValueError(f"Book already exists: {existing.title} ({existing.id})")

        async with self._get_api_client(platform) as api:
            logger.info(f"Fetching book detail: platform={platform}, book_id={book_id}")
            detail = await api.get_book_detail(book_id)
            platform_book_id = detail.get("book_id", book_id)
            source_book_id = detail.get("source_book_id", book_id)

            book_uuid = str(uuid.uuid4())
            cover_url = detail.get("cover_url", "")
            book = Book(
                id=book_uuid,
                platform=platform,
                book_id=platform_book_id,
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
                chapter_list = await api.get_chapter_list(source_book_id)

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

    # ============ 查询 ============

    def get_book(self, book_uuid: str) -> Optional[Book]:
        """根据UUID获取书籍"""
        return self.db.query(Book).filter(Book.id == book_uuid).first()

    def get_book_by_platform_id(
        self,
        platform: str,
        book_id: str,
    ) -> Optional[Book]:
        """根据平台ID获取书籍"""
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
        """列出书籍"""
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
        """获取书籍概览（仅基本信息和统计）"""
        book = self.get_book(book_uuid)
        if not book:
            return None

        statistics = self.get_book_statistics(book_uuid)
        return {
            "book": book,
            "statistics": statistics,
        }

    def get_book_with_chapters(self, book_uuid: str) -> Optional[Dict[str, Any]]:
        """获取书籍详情（包含章节列表）"""
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
        """获取书籍统计信息"""
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
        """获取全局统计信息"""
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

    # ============ 更新 ============

    async def refresh_book_metadata(self, book_uuid: str) -> Optional[Book]:
        """刷新书籍元数据"""
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
        """手动更新书籍元数据"""
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
        """检查新章节"""
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
        """添加新章节"""
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
        """更新书籍状态"""
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
        """更新下载进度"""
        book = self.get_book(book_uuid)
        if not book:
            return None

        book.downloaded_chapters = downloaded_chapters

        if downloaded_chapters >= book.total_chapters:
            book.download_status = "completed"

        self.db.commit()
        self.db.refresh(book)
        return book

    # ============ 删除 ============

    def delete_book(
        self,
        book_uuid: str,
        delete_files: bool = True,
    ) -> bool:
        """删除书籍"""
        book = self.get_book(book_uuid)
        if not book:
            return False

        book_title = book.title

        if delete_files:
            self.storage.delete_book_files(book_uuid)
            self.storage.delete_epub(book.title, book_uuid)

        self.db.delete(book)
        self.db.commit()

        logger.info(f"Deleted book: {book_title} ({book_uuid})")
        return True


__all__ = [
    "BookService",
    "FanqieAPI",
    "QimaoAPI",
    "BiqugeAPI",
]
