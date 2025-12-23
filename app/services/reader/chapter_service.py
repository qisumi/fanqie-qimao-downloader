"""
章节内容服务：负责章节内容的读取、格式化和预取
"""

import asyncio
import html
import logging
from typing import Any, Dict, Optional, Set

from sqlalchemy.orm import Session

from app.models import Book, Chapter
from app.services.download_service import DownloadService, QuotaReachedError
from app.services.storage_service import StorageService
from app.utils.database import SessionLocal

logger = logging.getLogger(__name__)


class ChapterPrefetchManager:
    """章节预取管理器：独立管理预取状态，避免静态变量问题"""

    def __init__(self):
        self._inflight: Set[str] = set()
        self._lock: Optional[asyncio.Lock] = None

    @property
    def lock(self) -> asyncio.Lock:
        """获取或创建异步锁"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    def is_inflight(self, cache_key: str) -> bool:
        """检查章节是否正在预取中"""
        return cache_key in self._inflight

    def add_inflight(self, cache_key: str) -> None:
        """标记章节为正在预取"""
        self._inflight.add(cache_key)

    def remove_inflight(self, cache_key: str) -> None:
        """移除章节的预取标记"""
        self._inflight.discard(cache_key)


class ChapterService:
    """章节内容服务：负责章节内容的读取、格式化和预取"""

    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
        download_service: Optional[DownloadService] = None,
        prefetch_manager: Optional[ChapterPrefetchManager] = None,
    ):
        """初始化章节服务

        Args:
            db: 数据库会话
            storage: 存储服务实例
            download_service: 下载服务实例
            prefetch_manager: 预取管理器实例
        """
        self.db = db
        self.storage = storage or StorageService()
        self.download_service = download_service or DownloadService(db=db, storage=self.storage)
        self.prefetch_manager = prefetch_manager or ChapterPrefetchManager()

    # ========= 基础查询 =========
    def _get_book(self, book_id: str) -> Optional[Book]:
        """获取书籍

        Args:
            book_id: 书籍UUID

        Returns:
            书籍对象或None
        """
        return self.db.query(Book).filter(Book.id == book_id).first()

    def _get_chapter(self, book_id: str, chapter_id: str) -> Optional[Chapter]:
        """获取章节

        Args:
            book_id: 书籍UUID
            chapter_id: 章节UUID

        Returns:
            章节对象或None
        """
        return self.db.query(Chapter).filter(
            Chapter.id == chapter_id,
            Chapter.book_id == book_id,
        ).first()

    def _get_adjacent_chapters(self, book_id: str, chapter_index: int) -> tuple[Optional[str], Optional[str]]:
        """获取相邻章节ID

        Args:
            book_id: 书籍UUID
            chapter_index: 当前章节索引

        Returns:
            (上一章ID, 下一章ID) 元组
        """
        prev_id = self.db.query(Chapter.id).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index < chapter_index
        ).order_by(Chapter.chapter_index.desc()).limit(1).scalar()

        next_id = self.db.query(Chapter.id).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index > chapter_index
        ).order_by(Chapter.chapter_index.asc()).limit(1).scalar()

        return prev_id, next_id

    # ========= 章节内容读取 =========
    def _read_chapter_text(self, chapter: Chapter) -> Optional[str]:
        """读取章节文本内容

        Args:
            chapter: 章节对象

        Returns:
            章节文本内容，如果文件缺失则返回None
        """
        if not chapter.content_path:
            logger.debug(f"Chapter {chapter.id} has no content_path")
            return None
        return self.storage.get_chapter_content(chapter.content_path)

    def _format_content_to_html(self, content: str) -> str:
        """将纯文本格式化为HTML段落

        Args:
            content: 纯文本内容

        Returns:
            格式化后的HTML字符串
        """
        if not content:
            return ""
        paragraphs = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped:
                paragraphs.append(f"<p>{html.escape(stripped)}</p>")
            else:
                paragraphs.append("<p>&nbsp;</p>")
        return "\n".join(paragraphs)

    # ========= 章节内容获取 =========
    async def get_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        fmt: str = "html",
        fetch_range: Optional[str] = None,
        prefetch: int = 3,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """获取章节内容，缺失时尝试下载并可选预取

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
        # 验证书籍和章节存在
        book = self._get_book(book_id)
        if not book:
            raise ValueError("书籍不存在")

        target_chapter = self._get_chapter(book_id, chapter_id)
        if not target_chapter:
            raise ValueError("章节不存在")

        # 处理 fetch_range 参数
        target_chapter = self._resolve_fetch_range(book_id, target_chapter, fetch_range)

        # 获取相邻章节ID
        prev_id, next_id = self._get_adjacent_chapters(book_id, target_chapter.chapter_index)

        # 读取或下载章节内容
        content_text, status, status_message = await self._fetch_chapter_content(
            target_chapter, retries, prefetch
        )

        # 构建响应数据
        payload = self._build_chapter_payload(
            target_chapter, prev_id, next_id, content_text, status, status_message, fmt
        )

        return payload

    def _resolve_fetch_range(
        self,
        book_id: str,
        chapter: Chapter,
        fetch_range: Optional[str],
    ) -> Chapter:
        """解析 fetch_range 参数，返回目标章节

        Args:
            book_id: 书籍UUID
            chapter: 原始章节对象
            fetch_range: 获取范围，"prev" 或 "next"

        Returns:
            目标章节对象
        """
        if fetch_range == "prev":
            prev_id, _ = self._get_adjacent_chapters(book_id, chapter.chapter_index)
            if not prev_id:
                raise ValueError("没有上一章")
            return self._get_chapter(book_id, prev_id) or chapter
        elif fetch_range == "next":
            _, next_id = self._get_adjacent_chapters(book_id, chapter.chapter_index)
            if not next_id:
                raise ValueError("没有下一章")
            return self._get_chapter(book_id, next_id) or chapter
        return chapter

    async def _fetch_chapter_content(
        self,
        chapter: Chapter,
        retries: int,
        prefetch: int,
    ) -> tuple[Optional[str], str, Optional[str]]:
        """获取章节内容，如果缺失则尝试下载

        Args:
            chapter: 章节对象
            retries: 下载重试次数
            prefetch: 预取章节数量

        Returns:
            (内容文本, 状态, 状态消息) 元组
        """
        content_text = self._read_chapter_text(chapter)
        status = "ready" if content_text else "fetching"
        status_message = None

        if not content_text:
            content_text, status, status_message = await self._download_chapter_content(
                chapter, retries, prefetch
            )

        return content_text, status, status_message

    async def _download_chapter_content(
        self,
        chapter: Chapter,
        retries: int,
        prefetch: int,
    ) -> tuple[Optional[str], str, Optional[str]]:
        """下载章节内容

        Args:
            chapter: 章节对象
            retries: 下载重试次数
            prefetch: 预取章节数量

        Returns:
            (内容文本, 状态, 状态消息) 元组
        """
        try:
            downloaded = await self.download_service.download_chapter_with_retry(
                chapter.book_id,
                chapter.id,
                retries=retries,
            )
            if downloaded:
                self.db.refresh(chapter)
                content_text = self._read_chapter_text(chapter)
                status = "ready" if content_text else "fetching"
                status_message = None

                # 触发预取
                if prefetch > 0 and status == "ready":
                    self._schedule_prefetch(chapter.book_id, chapter.chapter_index, prefetch)

                return content_text, status, status_message
            else:
                return None, "fetching", "章节拉取失败，可能是网络问题或配额限制"
        except QuotaReachedError as e:
            logger.warning(f"Quota reached for chapter {chapter.id}: {e}")
            return None, "fetching", str(e)
        except Exception as e:
            logger.exception(f"Download chapter {chapter.id} failed")
            return None, "fetching", str(e)

    def _build_chapter_payload(
        self,
        chapter: Chapter,
        prev_id: Optional[str],
        next_id: Optional[str],
        content_text: Optional[str],
        status: str,
        status_message: Optional[str],
        fmt: str,
    ) -> Dict[str, Any]:
        """构建章节响应数据

        Args:
            chapter: 章节对象
            prev_id: 上一章ID
            next_id: 下一章ID
            content_text: 章节文本内容
            status: 章节状态
            status_message: 状态消息
            fmt: 返回格式

        Returns:
            响应数据字典
        """
        payload: Dict[str, Any] = {
            "title": chapter.title,
            "index": chapter.chapter_index,
            "prev_id": prev_id,
            "next_id": next_id,
            "word_count": chapter.word_count or (len(content_text) if content_text else 0),
            "updated_at": chapter.created_at,
            "status": status,
        }

        if status_message:
            payload["message"] = status_message

        if status == "ready" and content_text:
            if fmt == "text":
                payload["content_text"] = content_text
            else:
                payload["content_html"] = self._format_content_to_html(content_text)

        return payload

    # ========= 章节预取 =========
    def _schedule_prefetch(self, book_id: str, start_index: int, count: int = 3) -> None:
        """后台预取后续章节

        Args:
            book_id: 书籍UUID
            start_index: 起始章节索引
            count: 预取章节数量
        """
        if count <= 0:
            return

        async def _prefetch():
            db = SessionLocal()
            try:
                storage = StorageService()
                downloader = DownloadService(db=db, storage=storage)
                await self._prefetch_chapters(db, downloader, book_id, start_index, count)
            finally:
                db.close()

        try:
            asyncio.create_task(_prefetch())
        except RuntimeError:
            logger.debug("Event loop unavailable, skip prefetch")

    async def _prefetch_chapters(
        self,
        db: Session,
        downloader: DownloadService,
        book_id: str,
        start_index: int,
        count: int,
    ) -> None:
        """执行章节预取

        Args:
            db: 数据库会话
            downloader: 下载服务实例
            book_id: 书籍UUID
            start_index: 起始章节索引
            count: 预取章节数量
        """
        chapters = db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index > start_index,
        ).order_by(Chapter.chapter_index).limit(count).all()

        for ch in chapters:
            cache_key = f"{book_id}:{ch.id}"
            async with self.prefetch_manager.lock:
                if self.prefetch_manager.is_inflight(cache_key) or ch.download_status in ("completed", "downloading"):
                    continue
                self.prefetch_manager.add_inflight(cache_key)
                if ch.download_status != "completed":
                    ch.download_status = "downloading"
                    db.commit()

            try:
                success = await downloader.download_chapter_with_retry(
                    book_id,
                    ch.id,
                    retries=1,
                )
                if not success:
                    break
            except QuotaReachedError:
                logger.warning(f"Prefetch stopped for book {book_id}: quota exceeded")
                break
            except Exception:
                logger.exception(f"Prefetch chapter {ch.id} failed")
                break
            finally:
                async with self.prefetch_manager.lock:
                    self.prefetch_manager.remove_inflight(cache_key)