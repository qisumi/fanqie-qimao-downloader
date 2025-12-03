import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import func

from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.api.base import ChapterNotFoundError, NetworkError
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.services.download_service_base import DownloadServiceBase, QuotaReachedError

logger = logging.getLogger(__name__)


class DownloadOperationMixin(DownloadServiceBase):
    """章节下载、更新和重试相关的逻辑。"""
    
    async def download_book(
        self,
        book_uuid: str,
        task_type: str = "full_download",
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
        task_id: Optional[str] = None,
        skip_completed: bool = True,
    ) -> DownloadTask:
        """
        下载书籍
        
        Args:
            book_uuid: 书籍UUID
            task_type: 任务类型
            start_chapter: 起始章节索引
            end_chapter: 结束章节索引（包含），None表示到最后一章
            task_id: 已有的任务ID，如果提供则复用该任务
            skip_completed: 是否跳过已完成章节
        """
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            raise ValueError(f"Book not found: {book_uuid}")
        
        if task_id:
            task = self.get_task(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
        else:
            task = self.create_task(
                book_uuid,
                task_type,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                skip_completed=skip_completed,
            )
        
        try:
            if task_type == "full_download" and not skip_completed:
                self._reset_chapters_for_full_download(book_uuid, start_chapter, end_chapter)
            
            book.download_status = "downloading"
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            
            chapters = self._get_pending_chapters(book_uuid, task_type, start_chapter, end_chapter, skip_completed)
            task.total_chapters = len(chapters)
            task.downloaded_chapters = 0
            task.failed_chapters = 0
            task.progress = 0.0
            self.db.commit()
            
            if not chapters:
                task.status = "completed"
                task.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                return task
            
            await self._download_chapters_concurrent(book, chapters, task)
            
            if task.id in self._cancelled_tasks:
                task.status = "cancelled"
                self._cancelled_tasks.discard(task.id)
                if book.downloaded_chapters > 0:
                    book.download_status = "partial"
                else:
                    book.download_status = "pending"
            elif task.failed_chapters > 0:
                task.status = "failed"
                task.error_message = f"{task.failed_chapters}个章节下载失败"
                book.download_status = "failed"
            else:
                task.status = "completed"
                book.download_status = "completed"
            
            task.completed_at = datetime.now(timezone.utc)
            
            completed_count = self.db.query(func.count(Chapter.id)).filter(
                Chapter.book_id == book_uuid,
                Chapter.download_status == "completed"
            ).scalar() or 0
            book.downloaded_chapters = completed_count
            
            self.db.commit()
            
            callbacks = self._progress_callbacks.get(task.id, set())
            if callbacks:
                logger.debug(f"Triggering {len(callbacks)} final progress callback(s) for task {task.id}, status={task.status}")
                for callback in list(callbacks):
                    try:
                        callback(task)
                    except Exception:
                        logger.exception(f"Final progress callback failed for task {task.id}")
            
            logger.info(
                f"Download completed: book={book.title}, "
                f"downloaded={task.downloaded_chapters}, failed={task.failed_chapters}"
            )
            
            return task
            
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            book.download_status = "failed"
            self.db.commit()
            
            callbacks = self._progress_callbacks.get(task.id, set())
            if callbacks:
                logger.debug(f"Triggering {len(callbacks)} failure callback(s) for task {task.id}")
                for callback in list(callbacks):
                    try:
                        callback(task)
                    except Exception:
                        logger.exception(f"Failure progress callback failed for task {task.id}")
            
            logger.error(f"Download failed: {e}")
            raise
    
    def _get_pending_chapters(
        self,
        book_uuid: str,
        task_type: str,
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
        skip_completed: bool = True,
    ) -> List[Chapter]:
        """获取待下载的章节列表"""
        query = self.db.query(Chapter).filter(
            Chapter.book_id == book_uuid,
            Chapter.chapter_index >= start_chapter
        )
        
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)
        
        if task_type == "full_download":
            if skip_completed:
                query = query.filter(Chapter.download_status != "completed")
        else:
            query = query.filter(Chapter.download_status == "pending")
        
        return query.order_by(Chapter.chapter_index).all()
    
    def _reset_chapters_for_full_download(
        self,
        book_uuid: str,
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
    ):
        """重置章节状态为pending，用于完整下载重新开始"""
        query = self.db.query(Chapter).filter(
            Chapter.book_id == book_uuid,
            Chapter.chapter_index >= start_chapter
        )
        
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)
        
        chapters = query.all()
        
        for chapter in chapters:
            if chapter.download_status in ("failed", "pending"):
                continue
            if chapter.download_status == "completed":
                chapter.download_status = "pending"
                chapter.content_path = None
                logger.debug(f"Reset chapter for re-download: {chapter.title}")
        
        self.db.commit()
        logger.info(f"Reset chapters for full download: book_id={book_uuid}, start={start_chapter}, end={end_chapter}")
    
    async def _download_chapters_concurrent(
        self,
        book: Book,
        chapters: List[Chapter],
        task: DownloadTask,
    ):
        """并发下载多个章节"""
        semaphore = asyncio.Semaphore(self.concurrent_downloads)
        
        async with self._get_api_client(book.platform) as api:
            if book.platform == "qimao":
                api.set_current_book_id(book.book_id)
            
            async def download_with_limit(chapter: Chapter):
                async with semaphore:
                    if task.id in self._cancelled_tasks:
                        return False
                    
                    if not self.rate_limiter.can_download(book.platform):
                        logger.warning(f"Daily quota exceeded for {book.platform}")
                        return False
                    
                    word_count = await self._download_single_chapter_with_api(api, book, chapter)
                    
                    if word_count >= 0:
                        self.rate_limiter.record_download(book.platform, word_count=word_count)
                        self._update_task_progress(task, downloaded=1)
                    else:
                        self._update_task_progress(task, failed=1)
                    
                    if self.download_delay > 0:
                        await asyncio.sleep(self.download_delay)
                    
                    return word_count >= 0
            
            tasks = [download_with_limit(ch) for ch in chapters]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _download_single_chapter_with_api(
        self,
        api: Union[FanqieAPI, QimaoAPI],
        book: Book,
        chapter: Chapter,
    ) -> int:
        """使用指定的 API 客户端下载单个章节"""
        try:
            result = await api.get_chapter_content(chapter.item_id)
            
            if result.get("type") == "text":
                content = result.get("content", "")
                word_count = len(content)
                
                content_path = await self.storage.save_chapter_content_async(
                    book.id,
                    chapter.chapter_index,
                    content
                )
                
                chapter.content_path = content_path
                chapter.download_status = "completed"
                chapter.downloaded_at = datetime.now(timezone.utc)
                self.db.commit()
                
                logger.debug(f"Downloaded chapter: {chapter.title} ({word_count} words)")
                return word_count
            
            logger.warning(f"Audio content not supported: {chapter.title}")
            chapter.download_status = "failed"
            self.db.commit()
            return -1
                
        except ChapterNotFoundError:
            logger.error(f"Chapter not found: {chapter.item_id}")
            chapter.download_status = "failed"
            self.db.commit()
            return -1
            
        except NetworkError as e:
            logger.error(f"Network error downloading chapter {chapter.title}: {e}")
            chapter.download_status = "failed"
            self.db.commit()
            return -1
            
        except Exception as e:
            logger.error(f"Error downloading chapter {chapter.title}: {e}")
            chapter.download_status = "failed"
            self.db.commit()
            return -1
    
    async def _download_single_chapter(
        self,
        book: Book,
        chapter: Chapter,
    ) -> int:
        """下载单个章节（独立创建 API 连接）"""
        async with self._get_api_client(book.platform) as api:
            if book.platform == "qimao":
                api.set_current_book_id(book.book_id)
            
            return await self._download_single_chapter_with_api(api, book, chapter)
    
    async def update_book(
        self,
        book_uuid: str,
        task_id: Optional[str] = None,
    ) -> DownloadTask:
        """更新书籍（下载新章节）"""
        return await self.download_book(book_uuid, task_type="update", task_id=task_id)
    
    async def retry_failed_chapters(self, book_uuid: str) -> int:
        """重试失败的章节"""
        failed_chapters = self.db.query(Chapter).filter(
            Chapter.book_id == book_uuid,
            Chapter.download_status == "failed"
        ).all()
        
        if not failed_chapters:
            return 0
        
        for chapter in failed_chapters:
            chapter.download_status = "pending"
        
        self.db.commit()
        
        count = len(failed_chapters)
        logger.info(f"Reset {count} failed chapters for retry")
        
        return count

    async def download_chapter_with_retry(
        self,
        book_uuid: str,
        chapter_uuid: str,
        retries: int = 3,
    ) -> bool:
        """
        下载单个章节（带重试）

        Args:
            book_uuid: 书籍UUID
            chapter_uuid: 章节UUID
            retries: 重试次数

        Returns:
            bool: 是否成功下载
        """
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            raise ValueError("书籍不存在")

        chapter = self.db.query(Chapter).filter(
            Chapter.id == chapter_uuid,
            Chapter.book_id == book_uuid,
        ).first()
        if not chapter:
            raise ValueError("章节不存在")

        # 若章节标记完成但缺文件，重置状态
        if chapter.download_status == "completed" and chapter.content_path:
            content = self.storage.get_chapter_content(chapter.content_path)
            if content:
                return True
            chapter.download_status = "pending"
            chapter.content_path = None
            self.db.commit()

        last_error: Optional[str] = None

        for attempt in range(1, retries + 1):
            if not self.rate_limiter.can_download(book.platform):
                remaining = self.rate_limiter.get_remaining(book.platform)
                raise QuotaReachedError(book.platform, remaining=remaining)

            result = await self._download_single_chapter(book, chapter)
            if result >= 0:
                try:
                    self.rate_limiter.record_download(book.platform, word_count=result)
                except Exception:
                    logger.exception("Record download words failed")

                completed_count = self.db.query(func.count(Chapter.id)).filter(
                    Chapter.book_id == book_uuid,
                    Chapter.download_status == "completed",
                ).scalar() or 0
                book.downloaded_chapters = completed_count
                self.db.commit()
                return True

            last_error = f"下载失败，已尝试 {attempt}/{retries}"
            chapter.download_status = "pending"
            self.db.commit()

        if last_error:
            logger.error(last_error)
        return False


__all__ = ["DownloadOperationMixin"]
