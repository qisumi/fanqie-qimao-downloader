"""
阅读相关服务：章节内容读取、进度/书签/历史管理、EPUB 缓存状态
"""

import asyncio
import html
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import (
    Book,
    Bookmark,
    Chapter,
    ReadingHistory,
    ReadingProgress,
    User,
)
from app.services.book_service import BookService
from app.services.download_service import DownloadService, QuotaReachedError
from app.services.epub_service import EPUBService
from app.services.storage_service import StorageService
from app.utils.database import SessionLocal

logger = logging.getLogger(__name__)


class ReaderService:
    """阅读器后端服务"""

    # 进程内预取去重：跟踪正在预取的章节，避免重复下载
    _prefetch_inflight: Set[str] = set()
    _prefetch_lock: Optional[asyncio.Lock] = None

    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
        book_service: Optional[BookService] = None,
        download_service: Optional[DownloadService] = None,
        epub_service: Optional[EPUBService] = None,
    ):
        self.db = db
        self.storage = storage or StorageService()
        self.book_service = book_service or BookService(db=db, storage=self.storage)
        self.download_service = download_service or DownloadService(db=db, storage=self.storage)
        self.epub_service = epub_service or EPUBService(db=db, storage=self.storage)

    # ========= 基础查询 =========
    def _get_user(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def _get_book(self, book_id: str) -> Optional[Book]:
        return self.book_service.get_book(book_id)

    def _get_chapter(self, book_id: str, chapter_id: str) -> Optional[Chapter]:
        return self.db.query(Chapter).filter(
            Chapter.id == chapter_id,
            Chapter.book_id == book_id,
        ).first()

    def _get_adjacent_chapters(self, book_id: str, chapter_index: int) -> Tuple[Optional[str], Optional[str]]:
        prev_id = self.db.query(Chapter.id).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index < chapter_index
        ).order_by(Chapter.chapter_index.desc()).limit(1).scalar()

        next_id = self.db.query(Chapter.id).filter(
            Chapter.book_id == book_id,
            Chapter.chapter_index > chapter_index
        ).order_by(Chapter.chapter_index.asc()).limit(1).scalar()

        return prev_id, next_id

    def get_toc(self, book_id: str) -> Optional[Dict[str, Any]]:
        """获取书籍目录（轻量字段）"""
        book = self._get_book(book_id)
        if not book:
            return None

        chapters = self.db.query(Chapter).filter(
            Chapter.book_id == book_id
        ).order_by(Chapter.chapter_index).all()

        toc_items = [
            {
                "id": ch.id,
                "index": ch.chapter_index,
                "title": ch.title,
                "word_count": ch.word_count,
                "updated_at": ch.created_at,
                "download_status": ch.download_status,
            }
            for ch in chapters
        ]

        return {
            "book": book,
            "chapters": toc_items,
        }

    # ========= 章节内容 =========
    async def get_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        fmt: str = "html",
        fetch_range: Optional[str] = None,
        prefetch: int = 3,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """读取章节内容，缺失时尝试下载并可选预取"""
        book = self._get_book(book_id)
        if not book:
            raise ValueError("书籍不存在")

        target_chapter = self._get_chapter(book_id, chapter_id)
        if not target_chapter:
            raise ValueError("章节不存在")

        if fetch_range == "prev":
            prev_id, _ = self._get_adjacent_chapters(book_id, target_chapter.chapter_index)
            if not prev_id:
                raise ValueError("没有上一章")
            target_chapter = self._get_chapter(book_id, prev_id) or target_chapter
        elif fetch_range == "next":
            _, next_id = self._get_adjacent_chapters(book_id, target_chapter.chapter_index)
            if not next_id:
                raise ValueError("没有下一章")
            target_chapter = self._get_chapter(book_id, next_id) or target_chapter

        prev_id, next_id = self._get_adjacent_chapters(book_id, target_chapter.chapter_index)

        content_text = self._read_chapter_text(target_chapter)
        status = "ready" if content_text else "fetching"
        status_message = None

        if not content_text:
            try:
                downloaded = await self.download_service.download_chapter_with_retry(
                    book_id,
                    target_chapter.id,
                    retries=retries,
                )
                if downloaded:
                    self.db.refresh(target_chapter)
                    content_text = self._read_chapter_text(target_chapter)
                    status = "ready" if content_text else "fetching"
                    if prefetch > 0 and status == "ready":
                        self._schedule_prefetch(book_id, target_chapter.chapter_index, prefetch)
                else:
                    status = "fetching"
                    status_message = "章节拉取失败，可能是网络问题或配额限制"
            except QuotaReachedError as e:
                status = "fetching"
                status_message = str(e)
            except Exception as e:
                logger.exception("Download chapter failed")
                status = "fetching"
                status_message = str(e)

        payload: Dict[str, Any] = {
            "title": target_chapter.title,
            "index": target_chapter.chapter_index,
            "prev_id": prev_id,
            "next_id": next_id,
            "word_count": target_chapter.word_count or (len(content_text) if content_text else 0),
            "updated_at": target_chapter.created_at,
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

    def _read_chapter_text(self, chapter: Chapter) -> Optional[str]:
        """读取章节文本，如果文件缺失则返回None"""
        if not chapter.content_path:
            return None
        return self.storage.get_chapter_content(chapter.content_path)

    def _format_content_to_html(self, content: str) -> str:
        """将纯文本格式化为简单 HTML 段落"""
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

    def _schedule_prefetch(self, book_id: str, start_index: int, count: int = 3):
        """后台预取后续章节，使用独立会话避免当前请求会话关闭"""
        if count <= 0:
            return

        async def _prefetch():
            db = SessionLocal()
            try:
                storage = StorageService()
                downloader = DownloadService(db=db, storage=storage)
                cls = self.__class__
                if cls._prefetch_lock is None:
                    cls._prefetch_lock = asyncio.Lock()
                lock = cls._prefetch_lock
                inflight = cls._prefetch_inflight

                chapters = db.query(Chapter).filter(
                    Chapter.book_id == book_id,
                    Chapter.chapter_index > start_index,
                ).order_by(Chapter.chapter_index).limit(count).all()

                for ch in chapters:
                    cache_key = f"{book_id}:{ch.id}"
                    async with lock:
                        if cache_key in inflight or ch.download_status in ("completed", "downloading"):
                            continue
                        inflight.add(cache_key)
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
                        logger.warning("Prefetch stopped: quota exceeded")
                        break
                    except Exception:
                        logger.exception("Prefetch chapter failed")
                        break
                    finally:
                        async with lock:
                            inflight.discard(cache_key)
            finally:
                db.close()

        try:
            asyncio.create_task(_prefetch())
        except RuntimeError:
            # 在无事件循环环境下跳过预取，避免阻断主流程
            logger.debug("Event loop unavailable, skip prefetch")

    # ========= 进度 =========
    def get_progress(self, user_id: str, book_id: str, device_id: str) -> Optional[ReadingProgress]:
        return self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id,
            ReadingProgress.device_id == device_id,
        ).first()

    def upsert_progress(
        self,
        user_id: str,
        book_id: str,
        chapter_id: str,
        device_id: str,
        offset_px: int,
        percent: float,
    ) -> ReadingProgress:
        if percent < 0:
            percent = 0.0
        if percent > 100:
            percent = 100.0

        progress = self.get_progress(user_id, book_id, device_id)
        now = datetime.now(timezone.utc)

        if progress:
            progress.chapter_id = chapter_id
            progress.offset_px = offset_px
            progress.percent = percent
            progress.updated_at = now
        else:
            progress = ReadingProgress(
                user_id=user_id,
                book_id=book_id,
                chapter_id=chapter_id,
                device_id=device_id,
                offset_px=offset_px,
                percent=percent,
                updated_at=now,
            )
            self.db.add(progress)

        history = ReadingHistory(
            user_id=user_id,
            book_id=book_id,
            chapter_id=chapter_id,
            percent=percent,
            device_id=device_id,
            updated_at=now,
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(progress)
        return progress

    def clear_progress(self, user_id: str, book_id: str, device_id: str) -> bool:
        progress = self.get_progress(user_id, book_id, device_id)
        if not progress:
            return False
        self.db.delete(progress)
        self.db.commit()
        return True

    # ========= 书签 =========
    def list_bookmarks(self, user_id: str, book_id: str) -> List[Bookmark]:
        return self.db.query(Bookmark).filter(
            Bookmark.user_id == user_id,
            Bookmark.book_id == book_id,
        ).order_by(Bookmark.created_at.desc()).all()

    def add_bookmark(
        self,
        user_id: str,
        book_id: str,
        chapter_id: str,
        offset_px: int,
        percent: float,
        note: Optional[str] = None,
    ) -> Bookmark:
        bookmark = Bookmark(
            user_id=user_id,
            book_id=book_id,
            chapter_id=chapter_id,
            offset_px=offset_px,
            percent=max(0.0, min(percent, 100.0)),
            note=note,
        )
        self.db.add(bookmark)
        self.db.commit()
        self.db.refresh(bookmark)
        return bookmark

    def delete_bookmark(self, user_id: str, book_id: str, bookmark_id: str) -> bool:
        bookmark = self.db.query(Bookmark).filter(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == user_id,
            Bookmark.book_id == book_id,
        ).first()
        if not bookmark:
            return False
        self.db.delete(bookmark)
        self.db.commit()
        return True

    # ========= 历史 =========
    def list_history(self, user_id: str, book_id: str, limit: int = 50) -> List[ReadingHistory]:
        return self.db.query(ReadingHistory).filter(
            ReadingHistory.user_id == user_id,
            ReadingHistory.book_id == book_id,
        ).order_by(ReadingHistory.updated_at.desc()).limit(limit).all()

    def clear_history(self, user_id: str, book_id: str) -> int:
        rows = self.db.query(ReadingHistory).filter(
            ReadingHistory.user_id == user_id,
            ReadingHistory.book_id == book_id,
        ).delete()
        self.db.commit()
        return rows

    # ========= 缓存 =========
    def get_cache_status(self, book: Book) -> Dict[str, Any]:
        cached_chapters = self.db.query(Chapter.id).filter(
            Chapter.book_id == book.id,
            Chapter.download_status == "completed",
        ).all()
        epub_cached = self.storage.epub_exists(book.title, book.id)
        return {
            "epub_cached": epub_cached,
            "cached_chapters": [cid[0] for cid in cached_chapters],
            "cached_at": datetime.now(timezone.utc),
        }

    def ensure_epub_cached(self, book: Book) -> str:
        """生成或返回已有 EPUB 路径"""
        epub_path = self.storage.get_epub_path(book.title, book.id)
        if epub_path.exists():
            return str(epub_path)

        chapters = self.db.query(Chapter).filter(
            Chapter.book_id == book.id,
            Chapter.download_status == "completed",
        ).order_by(Chapter.chapter_index).all()
        if not chapters:
            raise ValueError("没有已下载的章节可生成EPUB")

        return self.epub_service.generate_epub(book, chapters)
