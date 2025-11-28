"""
书籍管理服务模块

提供书籍相关的业务逻辑，包括：
- 搜索书籍
- 添加书籍（获取详情、下载封面、创建章节记录）
- 书籍列表查询
- 书籍元数据刷新
- 删除书籍
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.api.base import Platform, BookNotFoundError, APIError
from app.services.storage_service import StorageService
from app.config import settings

logger = logging.getLogger(__name__)


class BookService:
    """
    书籍管理服务
    
    负责书籍的增删改查以及与外部API的交互
    """
    
    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
    ):
        """
        初始化书籍服务
        
        Args:
            db: 数据库会话
            storage: 存储服务实例，默认创建新实例
        """
        self.db = db
        self.storage = storage or StorageService()
    
    def _get_api_client(self, platform: str) -> Union[FanqieAPI, QimaoAPI]:
        """
        根据平台获取API客户端
        
        Args:
            platform: 平台名称 (fanqie/qimao)
        
        Returns:
            对应的API客户端实例
        """
        if platform == Platform.FANQIE.value or platform == "fanqie":
            return FanqieAPI()
        elif platform == Platform.QIMAO.value or platform == "qimao":
            return QimaoAPI()
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    # ============ 搜索书籍 ============
    
    async def search_books(
        self,
        platform: str,
        keyword: str,
        page: int = 0,
    ) -> Dict[str, Any]:
        """
        搜索书籍
        
        Args:
            platform: 平台名称 (fanqie/qimao)
            keyword: 搜索关键词
            page: 页码 (番茄从0开始，七猫从1开始)
        
        Returns:
            {
                "books": [...],
                "total": int,
                "page": int,
                "platform": str
            }
        """
        async with self._get_api_client(platform) as api:
            result = await api.search(keyword, page)
            result["platform"] = platform
            return result
    
    # ============ 添加书籍 ============
    
    async def add_book(
        self,
        platform: str,
        book_id: str,
        download_cover: bool = True,
        fetch_chapters: bool = True,
    ) -> Book:
        """
        添加书籍到数据库
        
        流程:
        1. 检查书籍是否已存在
        2. 从API获取书籍详情
        3. 下载封面（可选）
        4. 获取章节列表并创建章节记录（可选）
        5. 保存书籍到数据库
        
        Args:
            platform: 平台名称 (fanqie/qimao)
            book_id: 平台书籍ID
            download_cover: 是否下载封面
            fetch_chapters: 是否获取章节列表
        
        Returns:
            新创建的Book对象
        
        Raises:
            ValueError: 书籍已存在
            BookNotFoundError: 书籍在平台上不存在
        """
        # 检查是否已存在
        existing = self.get_book_by_platform_id(platform, book_id)
        if existing:
            raise ValueError(f"Book already exists: {existing.title} ({existing.id})")
        
        async with self._get_api_client(platform) as api:
            # 获取书籍详情
            logger.info(f"Fetching book detail: platform={platform}, book_id={book_id}")
            detail = await api.get_book_detail(book_id)
            
            # 创建Book对象
            book_uuid = str(uuid.uuid4())
            cover_url = detail.get("cover_url", "")
            book = Book(
                id=book_uuid,
                platform=platform,
                book_id=book_id,
                title=detail.get("book_name", ""),
                author=detail.get("author", ""),
                cover_url=cover_url,  # 保存原始封面URL
                word_count=detail.get("word_count", 0),
                creation_status=detail.get("creation_status", ""),
                last_chapter_title=detail.get("last_chapter_title", ""),
                download_status="pending",
            )
            
            # 解析更新时间
            update_timestamp = detail.get("last_update_timestamp", 0)
            if update_timestamp:
                try:
                    # API 可能返回字符串或整数，统一转换为整数
                    ts = int(update_timestamp) if isinstance(update_timestamp, str) else update_timestamp
                    book.last_update_time = datetime.fromtimestamp(ts)
                except (ValueError, OSError, TypeError):
                    pass
            
            # 下载封面
            if download_cover:
                if cover_url:
                    cover_path = await self.storage.download_and_save_cover(
                        book_uuid, cover_url
                    )
                    if cover_path:
                        book.cover_path = cover_path
            
            # 获取章节列表
            if fetch_chapters:
                logger.info(f"Fetching chapter list for book: {book.title}")
                chapter_list = await api.get_chapter_list(book_id)
                
                book.total_chapters = chapter_list.get("total_chapters", 0)
                
                # 创建章节记录
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
            
            # 保存到数据库
            self.db.add(book)
            self.db.commit()
            self.db.refresh(book)
            
            logger.info(f"Added book: {book.title} ({book.id}), {book.total_chapters} chapters")
            
            return book
    
    # ============ 查询书籍 ============
    
    def get_book(self, book_uuid: str) -> Optional[Book]:
        """
        根据UUID获取书籍
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            Book对象，如果不存在返回None
        """
        return self.db.query(Book).filter(Book.id == book_uuid).first()
    
    def get_book_by_platform_id(
        self,
        platform: str,
        book_id: str,
    ) -> Optional[Book]:
        """
        根据平台和平台书籍ID获取书籍
        
        Args:
            platform: 平台名称
            book_id: 平台书籍ID
        
        Returns:
            Book对象，如果不存在返回None
        """
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
        """
        获取书籍列表
        
        Args:
            platform: 按平台筛选
            status: 按下载状态筛选
            search: 搜索书名或作者
            page: 页码 (从0开始)
            limit: 每页数量
        
        Returns:
            {
                "books": [Book...],
                "total": int,
                "page": int,
                "limit": int,
                "pages": int
            }
        """
        query = self.db.query(Book)
        
        # 筛选条件
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
        
        # 计算总数
        total = query.count()
        
        # 排序和分页
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
    
    def get_book_with_chapters(self, book_uuid: str) -> Optional[Dict[str, Any]]:
        """
        获取书籍及其章节信息
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            {
                "book": Book,
                "chapters": [Chapter...],
                "statistics": {...}
            }
        """
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        chapters = self.db.query(Chapter).filter(
            Chapter.book_id == book_uuid
        ).order_by(Chapter.chapter_index).all()
        
        # 统计信息
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
        
        # 获取存储统计
        storage_stats = self.storage.get_book_stats(book_uuid)
        statistics.update(storage_stats)
        
        return {
            "book": book,
            "chapters": chapters,
            "statistics": statistics,
        }
    
    # ============ 更新书籍 ============
    
    async def refresh_book_metadata(self, book_uuid: str) -> Optional[Book]:
        """
        从API刷新书籍元数据
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            更新后的Book对象
        """
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        async with self._get_api_client(book.platform) as api:
            detail = await api.get_book_detail(book.book_id)
            
            # 更新元数据
            book.title = detail.get("book_name", book.title)
            book.author = detail.get("author", book.author)
            book.word_count = detail.get("word_count", book.word_count)
            book.creation_status = detail.get("creation_status", book.creation_status)
            book.last_chapter_title = detail.get("last_chapter_title", book.last_chapter_title)
            
            # 更新时间
            update_timestamp = detail.get("last_update_timestamp", 0)
            if update_timestamp:
                try:
                    # API 可能返回字符串或整数，统一转换为整数
                    ts = int(update_timestamp) if isinstance(update_timestamp, str) else update_timestamp
                    book.last_update_time = datetime.fromtimestamp(ts)
                except (ValueError, OSError, TypeError):
                    pass
            
            self.db.commit()
            self.db.refresh(book)
            
            logger.info(f"Refreshed metadata for book: {book.title}")
            
            return book
    
    async def check_new_chapters(self, book_uuid: str) -> List[Dict[str, Any]]:
        """
        检查新章节
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            新章节列表 [{"item_id": "...", "title": "...", ...}]
        """
        book = self.get_book(book_uuid)
        if not book:
            return []
        
        # 获取现有章节的最大索引
        max_index = self.db.query(func.max(Chapter.chapter_index)).filter(
            Chapter.book_id == book_uuid
        ).scalar() or -1
        
        async with self._get_api_client(book.platform) as api:
            chapter_list = await api.get_chapter_list(book.book_id)
            chapters = chapter_list.get("chapters", [])
            
            # 筛选新章节
            new_chapters = [
                ch for ch in chapters
                if ch.get("chapter_index", 0) > max_index
            ]
            
            return new_chapters
    
    async def add_new_chapters(self, book_uuid: str) -> int:
        """
        添加新章节记录到数据库
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            新增的章节数量
        """
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
        
        # 更新书籍总章节数
        book.total_chapters += len(new_chapters)
        
        self.db.commit()
        
        logger.info(f"Added {len(new_chapters)} new chapters for book: {book.title}")
        
        return len(new_chapters)
    
    def update_book_status(
        self,
        book_uuid: str,
        status: str,
    ) -> Optional[Book]:
        """
        更新书籍下载状态
        
        Args:
            book_uuid: 书籍UUID
            status: 新状态 (pending/downloading/completed/failed)
        
        Returns:
            更新后的Book对象
        """
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
        """
        更新书籍下载进度
        
        Args:
            book_uuid: 书籍UUID
            downloaded_chapters: 已下载章节数
        
        Returns:
            更新后的Book对象
        """
        book = self.get_book(book_uuid)
        if not book:
            return None
        
        book.downloaded_chapters = downloaded_chapters
        
        # 如果下载完成，更新状态
        if downloaded_chapters >= book.total_chapters:
            book.download_status = "completed"
        
        self.db.commit()
        self.db.refresh(book)
        
        return book
    
    # ============ 删除书籍 ============
    
    def delete_book(
        self,
        book_uuid: str,
        delete_files: bool = True,
    ) -> bool:
        """
        删除书籍
        
        Args:
            book_uuid: 书籍UUID
            delete_files: 是否删除本地文件
        
        Returns:
            是否成功删除
        """
        book = self.get_book(book_uuid)
        if not book:
            return False
        
        book_title = book.title
        
        # 删除本地文件
        if delete_files:
            self.storage.delete_book_files(book_uuid)
            self.storage.delete_epub(book.title, book_uuid)
        
        # 删除数据库记录（章节和任务会级联删除）
        self.db.delete(book)
        self.db.commit()
        
        logger.info(f"Deleted book: {book_title} ({book_uuid})")
        
        return True
    
    # ============ 统计信息 ============
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取书籍统计信息
        
        Returns:
            {
                "total_books": int,
                "books_by_platform": {"fanqie": int, "qimao": int},
                "books_by_status": {"pending": int, "completed": int, ...},
                "total_chapters": int,
                "downloaded_chapters": int
            }
        """
        total_books = self.db.query(func.count(Book.id)).scalar()
        
        # 按平台统计
        platform_counts = self.db.query(
            Book.platform, func.count(Book.id)
        ).group_by(Book.platform).all()
        books_by_platform = {p: c for p, c in platform_counts}
        
        # 按状态统计
        status_counts = self.db.query(
            Book.download_status, func.count(Book.id)
        ).group_by(Book.download_status).all()
        books_by_status = {s: c for s, c in status_counts}
        
        # 章节统计
        total_chapters = self.db.query(func.sum(Book.total_chapters)).scalar() or 0
        downloaded_chapters = self.db.query(func.sum(Book.downloaded_chapters)).scalar() or 0
        
        return {
            "total_books": total_books or 0,
            "books_by_platform": books_by_platform,
            "books_by_status": books_by_status,
            "total_chapters": total_chapters,
            "downloaded_chapters": downloaded_chapters,
        }
