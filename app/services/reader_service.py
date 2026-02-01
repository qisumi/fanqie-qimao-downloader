"""
阅读器服务协调器
负责协调各个子服务（目录、章节、进度、书签、历史）提供统一的阅读器功能接口
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Book, Bookmark, Chapter, ReadingHistory, ReadingProgress
from app.services.book_service import BookService
from app.services.download_service import DownloadService
from app.services.storage_service import StorageService
from app.services.txt_service import TXTService
from app.services.reader.toc_service import TocService
from app.services.reader.chapter_service import ChapterService
from app.services.reader.progress_service import ProgressService
from app.services.reader.bookmark_service import BookmarkService
from app.services.reader.history_service import HistoryService

logger = logging.getLogger(__name__)


class ReaderService:
    """阅读器服务协调器
    
    职责：
    - 初始化并管理所有阅读器子服务
    - 提供统一的公共接口
    - 将请求委托给相应的子服务处理
    - 保留缓存管理功能
    
    子服务：
    - TocService: 目录查询和管理
    - ChapterService: 章节内容读取和预取
    - ProgressService: 阅读进度管理
    - BookmarkService: 书签管理
    - HistoryService: 阅读历史管理
    """

    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
        book_service: Optional[BookService] = None,
        download_service: Optional[DownloadService] = None,
        txt_service: Optional[TXTService] = None,
        toc_service: Optional[TocService] = None,
        chapter_service: Optional[ChapterService] = None,
        progress_service: Optional[ProgressService] = None,
        bookmark_service: Optional[BookmarkService] = None,
        history_service: Optional[HistoryService] = None,
    ):
        """初始化阅读器服务协调器
        
        Args:
            db: 数据库会话
            storage: 存储服务实例（可选）
            book_service: 书籍服务实例（可选）
            download_service: 下载服务实例（可选）
            txt_service: TXT服务实例（可选）
            toc_service: 目录服务实例（可选）
            chapter_service: 章节服务实例（可选）
            progress_service: 进度服务实例（可选）
            bookmark_service: 书签服务实例（可选）
            history_service: 历史服务实例（可选）
        """
        self.db = db
        
        # 初始化基础服务
        self.storage = storage or StorageService()
        self.book_service = book_service or BookService(db=db, storage=self.storage)
        self.download_service = download_service or DownloadService(db=db, storage=self.storage)
        self.txt_service = txt_service or TXTService(db=db, storage=self.storage)
        
        # 初始化子服务
        self.toc_service = toc_service or TocService(db=db, book_service=self.book_service)
        self.chapter_service = chapter_service or ChapterService(
            db=db,
            storage=self.storage,
            download_service=self.download_service,
        )
        self.progress_service = progress_service or ProgressService(db=db)
        self.bookmark_service = bookmark_service or BookmarkService(db=db)
        self.history_service = history_service or HistoryService(db=db)

    # ========= 辅助方法（供路由使用） =========
    def _get_book(self, book_id: str) -> Optional[Book]:
        """获取书籍信息（供路由使用）
        
        Args:
            book_id: 书籍UUID
            
        Returns:
            书籍对象，不存在时返回None
        """
        return self.book_service.get_book(book_id)

    def _get_chapter(self, book_id: str, chapter_id: str) -> Optional[Chapter]:
        """获取指定章节信息（供路由使用）
        
        Args:
            book_id: 书籍UUID
            chapter_id: 章节UUID
            
        Returns:
            章节对象，不存在时返回None
        """
        try:
            return self.db.query(Chapter).filter(
                Chapter.id == chapter_id,
                Chapter.book_id == book_id,
            ).first()
        except Exception as e:
            logger.error(f"获取章节失败: book_id={book_id}, chapter_id={chapter_id}, error={e}")
            return None

    # ========= 目录相关 =========
    def get_toc(
        self,
        book_id: str,
        page: int = 1,
        limit: int = 50,
        anchor_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """获取书籍目录（轻量字段，支持分页和锚点定位）
        
        委托给 TocService 处理
        
        Args:
            book_id: 书籍UUID
            page: 页码（1-based）
            limit: 每页数量（最大500）
            anchor_id: 希望包含的章节ID（用于根据章节定位页码）
            
        Returns:
            包含目录信息的字典，结构如下：
            {
                "book": Book对象,
                "chapters": 章节列表,
                "total": 总章节数,
                "page": 当前页码,
                "limit": 每页数量,
                "pages": 总页数,
                "has_more": 是否有更多页
            }
            书籍不存在时返回None
        """
        return self.toc_service.get_toc(
            book_id=book_id,
            page=page,
            limit=limit,
            anchor_id=anchor_id,
        )

    # ========= 章节内容相关 =========
    async def get_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        fmt: str = "html",
        fetch_range: Optional[str] = None,
        prefetch: int = 3,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """读取章节内容，缺失时尝试下载并可选预取
        
        委托给 ChapterService 处理
        
        Args:
            book_id: 书籍UUID
            chapter_id: 章节UUID
            fmt: 返回格式，"html" 或 "text"
            fetch_range: 获取范围，"prev" 或 "next"
            prefetch: 预取后续章节数量
            retries: 下载重试次数
            
        Returns:
            包含章节内容和元数据的字典
            
        Raises:
            ValueError: 书籍或章节不存在
        """
        return await self.chapter_service.get_chapter_content(
            book_id=book_id,
            chapter_id=chapter_id,
            fmt=fmt,
            fetch_range=fetch_range,
            prefetch=prefetch,
            retries=retries,
        )

    # ========= 进度相关 =========
    def get_progress(
        self,
        user_id: str,
        book_id: str,
        device_id: Optional[str] = None,
    ) -> Optional[ReadingProgress]:
        """获取阅读进度
        
        当 device_id 为 None 时，获取跨设备同步进度（最新的进度记录）
        
        委托给 ProgressService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            device_id: 设备ID，可选。为None时获取跨设备同步进度
            
        Returns:
            ReadingProgress 对象，如果不存在则返回 None
        """
        return self.progress_service.get_progress(
            user_id=user_id,
            book_id=book_id,
            device_id=device_id,
        )

    def get_all_device_progress(
        self,
        user_id: str,
        book_id: str,
    ) -> List[ReadingProgress]:
        """获取用户在该书籍的所有设备进度记录
        
        委托给 ProgressService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            
        Returns:
            ReadingProgress 对象列表，按更新时间降序排列
        """
        return self.progress_service.get_all_device_progress(
            user_id=user_id,
            book_id=book_id,
        )

    def upsert_progress(
        self,
        user_id: str,
        book_id: str,
        chapter_id: str,
        device_id: str,
        offset_px: int,
        percent: float,
    ) -> ReadingProgress:
        """更新或插入阅读进度（支持跨设备同步）
        
        跨设备同步策略：
        - 更新统一的进度记录（不区分设备）
        - 同时记录到历史表（保留设备信息用于分析）
        
        委托给 ProgressService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            chapter_id: 章节ID
            device_id: 设备ID
            offset_px: 像素偏移量
            percent: 阅读进度百分比（0-100）
            
        Returns:
            更新或创建的 ReadingProgress 对象
        """
        return self.progress_service.upsert_progress(
            user_id=user_id,
            book_id=book_id,
            chapter_id=chapter_id,
            device_id=device_id,
            offset_px=offset_px,
            percent=percent,
        )

    def clear_progress(
        self,
        user_id: str,
        book_id: str,
        device_id: Optional[str] = None,
    ) -> bool:
        """清除阅读进度
        
        委托给 ProgressService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            device_id: 设备ID，可选。为None时清除跨设备同步进度
            
        Returns:
            True 表示成功清除，False 表示未找到进度记录
        """
        return self.progress_service.clear_progress(
            user_id=user_id,
            book_id=book_id,
            device_id=device_id,
        )

    # ========= 书签相关 =========
    def list_bookmarks(self, user_id: str, book_id: str) -> List[Bookmark]:
        """列出指定用户和书籍的所有书签
        
        委托给 BookmarkService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            
        Returns:
            书签列表，按创建时间倒序排列
        """
        return self.bookmark_service.list_bookmarks(
            user_id=user_id,
            book_id=book_id,
        )

    def add_bookmark(
        self,
        user_id: str,
        book_id: str,
        chapter_id: str,
        offset_px: int,
        percent: float,
        note: Optional[str] = None,
    ) -> Bookmark:
        """添加新书签
        
        委托给 BookmarkService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            chapter_id: 章节ID
            offset_px: 章节内偏移量（像素）
            percent: 阅读进度百分比（0-100）
            note: 书签备注（可选）
            
        Returns:
            创建的书签对象
        """
        return self.bookmark_service.add_bookmark(
            user_id=user_id,
            book_id=book_id,
            chapter_id=chapter_id,
            offset_px=offset_px,
            percent=percent,
            note=note,
        )

    def delete_bookmark(self, user_id: str, book_id: str, bookmark_id: str) -> bool:
        """删除指定书签
        
        委托给 BookmarkService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            bookmark_id: 书签ID
            
        Returns:
            删除成功返回 True，书签不存在返回 False
        """
        return self.bookmark_service.delete_bookmark(
            user_id=user_id,
            book_id=book_id,
            bookmark_id=bookmark_id,
        )

    # ========= 历史相关 =========
    def list_history(
        self,
        user_id: str,
        book_id: str,
        limit: int = 50,
    ) -> List[ReadingHistory]:
        """列出指定书籍的阅读历史记录
        
        委托给 HistoryService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            limit: 返回记录的最大数量，默认50条
            
        Returns:
            阅读历史记录列表，按更新时间倒序排列
        """
        return self.history_service.list_history(
            user_id=user_id,
            book_id=book_id,
            limit=limit,
        )

    def clear_history(self, user_id: str, book_id: str) -> int:
        """清除指定书籍的阅读历史记录
        
        委托给 HistoryService 处理
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            
        Returns:
            删除的记录数量
        """
        return self.history_service.clear_history(
            user_id=user_id,
            book_id=book_id,
        )

    # ========= 缓存管理 =========
    def get_cache_status(self, book: Book) -> Dict[str, Any]:
        """获取书籍的缓存状态
        
        Args:
            book: 书籍对象
            
        Returns:
            包含缓存状态的字典：
            {
                "cached_chapters": 已缓存章节ID列表,
                "cached_at": 缓存时间戳
            }
        """
        cached_chapters = self.db.query(Chapter.id).filter(
            Chapter.book_id == book.id,
            Chapter.download_status == "completed",
        ).all()
        
        return {
            "cached_chapters": [cid[0] for cid in cached_chapters],
            "cached_at": datetime.now(timezone.utc),
        }

    def ensure_txt_cached(self, book: Book) -> str:
        """生成或返回已有 TXT 路径
        
        如果 TXT 文件已存在则直接返回路径，否则根据已下载的章节生成 TXT 文件
        
        Args:
            book: 书籍对象
            
        Returns:
            TXT 文件的绝对路径
            
        Raises:
            ValueError: 没有已下载的章节可生成TXT
        """
        txt_path = self.storage.get_txt_path(book.title, book.id)
        if txt_path.exists():
            return str(txt_path)

        chapters = self.db.query(Chapter).filter(
            Chapter.book_id == book.id,
            Chapter.download_status == "completed",
        ).order_by(Chapter.chapter_index).all()
        
        if not chapters:
            raise ValueError("没有已下载的章节可生成TXT")

        return self.txt_service.generate_txt(book, chapters)