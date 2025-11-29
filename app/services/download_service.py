"""
下载服务模块

提供下载相关的业务逻辑，包括：
- 创建下载任务
- 下载章节内容（支持并发控制）
- 任务进度跟踪
- 失败重试
- 更新检测
"""

import uuid
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable, Union

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.api.base import (
    Platform,
    APIError,
    QuotaExceededError,
    ChapterNotFoundError,
    NetworkError,
)
from app.services.storage_service import StorageService
from app.utils.rate_limiter import RateLimiter
from app.config import settings

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """下载错误基类"""
    pass


class QuotaReachedError(DownloadError):
    """配额已用尽错误"""
    def __init__(self, platform: str, remaining: int = 0):
        self.platform = platform
        self.remaining = remaining
        super().__init__(f"今日{platform}平台配额已用尽，剩余{remaining}字")


class TaskCancelledError(DownloadError):
    """任务已取消错误"""
    pass


class DownloadService:
    """
    下载管理服务
    
    负责章节下载、任务管理、进度跟踪
    
    特性:
    - 支持并发下载（可配置并发数）
    - 自动速率限制检查
    - 任务进度实时更新
    - 失败重试机制
    - 支持任务取消
    """
    
    # 类级别的回调字典，所有实例共享
    # 这样不同实例可以访问同一个回调注册表
    _shared_progress_callbacks: Dict[str, Callable] = {}
    _shared_cancelled_tasks: set = set()
    
    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
        rate_limiter: Optional[RateLimiter] = None,
        concurrent_downloads: Optional[int] = None,
        download_delay: Optional[float] = None,
    ):
        """
        初始化下载服务
        
        Args:
            db: 数据库会话
            storage: 存储服务实例
            rate_limiter: 速率限制器实例
            concurrent_downloads: 并发下载数，默认从配置读取
            download_delay: 下载间隔(秒)，默认从配置读取
        """
        self.db = db
        self.storage = storage or StorageService()
        self.rate_limiter = rate_limiter or RateLimiter(db)
        self.concurrent_downloads = concurrent_downloads or settings.concurrent_downloads
        self.download_delay = download_delay or settings.download_delay
        
        # 使用类级别的共享字典
        self._cancelled_tasks = DownloadService._shared_cancelled_tasks
        self._progress_callbacks = DownloadService._shared_progress_callbacks
    
    def _get_api_client(self, platform: str) -> Union[FanqieAPI, QimaoAPI]:
        """根据平台获取API客户端"""
        if platform == Platform.FANQIE.value or platform == "fanqie":
            return FanqieAPI()
        elif platform == Platform.QIMAO.value or platform == "qimao":
            return QimaoAPI()
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    # ============ 任务管理 ============
    
    def create_task(
        self,
        book_uuid: str,
        task_type: str = "full_download",
    ) -> DownloadTask:
        """
        创建下载任务
        
        Args:
            book_uuid: 书籍UUID
            task_type: 任务类型 (full_download/update)
        
        Returns:
            新创建的DownloadTask对象
        """
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            raise ValueError(f"Book not found: {book_uuid}")
        
        # 统计待下载章节数
        if task_type == "full_download":
            # 完整下载：所有未完成的章节
            pending_count = self.db.query(func.count(Chapter.id)).filter(
                Chapter.book_id == book_uuid,
                Chapter.download_status != "completed"
            ).scalar() or 0
        else:
            # 更新：只下载pending状态的章节
            pending_count = self.db.query(func.count(Chapter.id)).filter(
                Chapter.book_id == book_uuid,
                Chapter.download_status == "pending"
            ).scalar() or 0
        
        task = DownloadTask(
            id=str(uuid.uuid4()),
            book_id=book_uuid,
            task_type=task_type,
            status="pending",
            total_chapters=pending_count,
            downloaded_chapters=0,
            failed_chapters=0,
            progress=0.0,
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(f"Created download task: {task.id}, type={task_type}, chapters={pending_count}")
        
        return task
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取任务详情"""
        return self.db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
    
    def list_tasks(
        self,
        book_uuid: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取任务列表
        
        Args:
            book_uuid: 按书籍筛选
            status: 按状态筛选
            page: 页码
            limit: 每页数量
        
        Returns:
            {"tasks": [...], "total": int, "page": int, "limit": int}
        """
        query = self.db.query(DownloadTask)
        
        if book_uuid:
            query = query.filter(DownloadTask.book_id == book_uuid)
        
        if status:
            query = query.filter(DownloadTask.status == status)
        
        total = query.count()
        
        query = query.order_by(DownloadTask.created_at.desc())
        query = query.offset(page * limit).limit(limit)
        
        tasks = query.all()
        
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "limit": limit,
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功取消
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        if task.status not in ("pending", "running"):
            return False
        
        self._cancelled_tasks.add(task_id)
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()
        
        # 同时更新书籍状态，使其可以重新下载
        book = self.db.query(Book).filter(Book.id == task.book_id).first()
        if book and book.download_status == "downloading":
            # 根据已下载章节数决定书籍状态
            if book.downloaded_chapters > 0:
                # 有已下载章节，标记为部分完成
                book.download_status = "partial"
            else:
                # 没有已下载章节，回退为待下载
                book.download_status = "pending"
            logger.info(f"Updated book status to '{book.download_status}' after task cancellation")
        
        self.db.commit()
        
        logger.info(f"Cancelled task: {task_id}")
        
        return True
    
    def _update_task_progress(
        self,
        task: DownloadTask,
        downloaded: int = 0,
        failed: int = 0,
    ):
        """更新任务进度和书籍下载章节数"""
        task.downloaded_chapters += downloaded
        task.failed_chapters += failed
        
        total = task.total_chapters
        if total > 0:
            completed = task.downloaded_chapters + task.failed_chapters
            task.progress = round(completed / total * 100, 2)
        
        # 同时更新书籍的已下载章节数，以便前端能实时显示进度
        if downloaded > 0:
            book = self.db.query(Book).filter(Book.id == task.book_id).first()
            if book:
                # 统计实际已完成的章节数
                completed_count = self.db.query(func.count(Chapter.id)).filter(
                    Chapter.book_id == task.book_id,
                    Chapter.download_status == "completed"
                ).scalar() or 0
                book.downloaded_chapters = completed_count
        
        self.db.commit()
        
        # 触发进度回调
        callback = self._progress_callbacks.get(task.id)
        if callback:
            logger.debug(f"Triggering progress callback for task {task.id}: {task.downloaded_chapters}/{task.total_chapters} ({task.progress}%)")
            callback(task)
        else:
            logger.warning(f"No progress callback registered for task {task.id}")
    
    def register_progress_callback(
        self,
        task_id: str,
        callback: Callable[[DownloadTask], None],
    ):
        """注册进度回调"""
        self._progress_callbacks[task_id] = callback
    
    def unregister_progress_callback(self, task_id: str):
        """注销进度回调"""
        self._progress_callbacks.pop(task_id, None)
    
    # ============ 下载操作 ============
    
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
            skip_completed: 是否跳过已完成章节（True=只下载未完成，False=重新下载所有）
        
        Returns:
            下载任务对象
        """
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            raise ValueError(f"Book not found: {book_uuid}")
        
        # 复用已有任务或创建新任务
        if task_id:
            task = self.get_task(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
        else:
            task = self.create_task(book_uuid, task_type)
        
        try:
            # 对于完整下载，根据 skip_completed 参数决定是否重置章节状态
            # skip_completed=False 时才重置已完成章节，用于强制重新下载
            if task_type == "full_download" and not skip_completed:
                self._reset_chapters_for_full_download(book_uuid, start_chapter, end_chapter)
            
            # 更新书籍和任务状态
            book.download_status = "downloading"
            task.status = "running"
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            # 获取待下载章节
            chapters = self._get_pending_chapters(book_uuid, task_type, start_chapter, end_chapter, skip_completed)
            
            if not chapters:
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                self.db.commit()
                return task
            
            # 执行下载
            await self._download_chapters_concurrent(book, chapters, task)
            
            # 更新最终状态
            if task.id in self._cancelled_tasks:
                task.status = "cancelled"
                self._cancelled_tasks.discard(task.id)
                # 更新书籍状态，使其可以重新下载
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
            
            task.completed_at = datetime.utcnow()
            
            # 更新书籍已下载章节数
            completed_count = self.db.query(func.count(Chapter.id)).filter(
                Chapter.book_id == book_uuid,
                Chapter.download_status == "completed"
            ).scalar() or 0
            book.downloaded_chapters = completed_count
            
            self.db.commit()
            
            # 触发最终进度回调，通知前端任务已完成
            callback = self._progress_callbacks.get(task.id)
            if callback:
                logger.debug(f"Triggering final progress callback for task {task.id}, status={task.status}")
                callback(task)
            
            logger.info(
                f"Download completed: book={book.title}, "
                f"downloaded={task.downloaded_chapters}, failed={task.failed_chapters}"
            )
            
            return task
            
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            book.download_status = "failed"
            self.db.commit()
            
            # 触发失败回调，通知前端任务失败
            callback = self._progress_callbacks.get(task.id)
            if callback:
                logger.debug(f"Triggering failure callback for task {task.id}")
                callback(task)
            
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
        """
        获取待下载的章节列表
        
        Args:
            book_uuid: 书籍UUID
            task_type: 任务类型
            start_chapter: 起始章节索引
            end_chapter: 结束章节索引
            skip_completed: 是否跳过已完成章节
        """
        query = self.db.query(Chapter).filter(
            Chapter.book_id == book_uuid,
            Chapter.chapter_index >= start_chapter
        )
        
        # 如果指定了结束章节，限制范围
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)
        
        if task_type == "full_download":
            if skip_completed:
                # 只下载未完成的章节（跳过已完成）
                query = query.filter(Chapter.download_status != "completed")
            # 否则下载所有章节（包括已完成的，因为它们已经被重置为pending）
        else:
            # 更新任务只下载pending状态的章节
            query = query.filter(Chapter.download_status == "pending")
        
        return query.order_by(Chapter.chapter_index).all()
    
    def _reset_chapters_for_full_download(
        self,
        book_uuid: str,
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
    ):
        """
        重置章节状态为pending，用于完整下载重新开始
        
        当用户再次下载已完成的书籍时，需要重置章节状态
        以支持重新下载
        
        Args:
            book_uuid: 书籍UUID
            start_chapter: 起始章节索引
            end_chapter: 结束章节索引（包含），None表示到最后一章
        """
        query = self.db.query(Chapter).filter(
            Chapter.book_id == book_uuid,
            Chapter.chapter_index >= start_chapter
        )
        
        # 如果指定了结束章节，限制范围
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)
        
        chapters = query.all()
        
        for chapter in chapters:
            if chapter.download_status in ("failed", "pending"):
                # 失败和待下载状态保持不变
                continue
            elif chapter.download_status == "completed":
                # 将已完成的章节重置为待下载
                chapter.download_status = "pending"
                chapter.content_path = None  # 清除路径，重新下载
                logger.debug(f"Reset chapter for re-download: {chapter.title}")
        
        self.db.commit()
        logger.info(f"Reset chapters for full download: book_id={book_uuid}, start={start_chapter}, end={end_chapter}")
    
    async def _download_chapters_concurrent(
        self,
        book: Book,
        chapters: List[Chapter],
        task: DownloadTask,
    ):
        """
        并发下载多个章节
        
        使用单个 API 客户端连接复用，提高下载效率。
        
        Args:
            book: 书籍对象
            chapters: 章节列表
            task: 下载任务
        """
        semaphore = asyncio.Semaphore(self.concurrent_downloads)
        
        # 复用单个 API 客户端连接
        async with self._get_api_client(book.platform) as api:
            # 七猫需要设置当前书籍ID（只需设置一次）
            if book.platform == "qimao":
                api.set_current_book_id(book.book_id)
            
            async def download_with_limit(chapter: Chapter):
                async with semaphore:
                    # 检查取消标志
                    if task.id in self._cancelled_tasks:
                        return False
                    
                    # 检查配额
                    if not self.rate_limiter.can_download(book.platform):
                        logger.warning(f"Daily quota exceeded for {book.platform}")
                        return False
                    
                    # 下载章节，返回字数 (-1 表示失败)
                    word_count = await self._download_single_chapter_with_api(api, book, chapter)
                    
                    if word_count >= 0:
                        self.rate_limiter.record_download(book.platform, word_count=word_count)
                        self._update_task_progress(task, downloaded=1)
                    else:
                        self._update_task_progress(task, failed=1)
                    
                    # 添加延迟
                    if self.download_delay > 0:
                        await asyncio.sleep(self.download_delay)
                    
                    return word_count >= 0
            
            # 创建所有下载任务
            tasks = [download_with_limit(ch) for ch in chapters]
            
            # 并发执行
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _download_single_chapter_with_api(
        self,
        api: Union[FanqieAPI, QimaoAPI],
        book: Book,
        chapter: Chapter,
    ) -> int:
        """
        使用指定的 API 客户端下载单个章节
        
        Args:
            api: API 客户端实例
            book: 书籍对象
            chapter: 章节对象
        
        Returns:
            下载成功返回章节字数，失败返回 -1
        """
        try:
            # 获取章节内容
            result = await api.get_chapter_content(chapter.item_id)
            
            if result.get("type") == "text":
                content = result.get("content", "")
                word_count = len(content)
                
                # 保存到文件
                content_path = await self.storage.save_chapter_content_async(
                    book.id,
                    chapter.chapter_index,
                    content
                )
                
                # 更新章节状态
                chapter.content_path = content_path
                chapter.download_status = "completed"
                chapter.downloaded_at = datetime.utcnow()
                self.db.commit()
                
                logger.debug(f"Downloaded chapter: {chapter.title} ({word_count} words)")
                return word_count
            else:
                # 音频内容暂不支持
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
        """
        下载单个章节（独立创建 API 连接）
        
        用于单章节下载或重试场景。对于批量下载，
        推荐使用 _download_single_chapter_with_api 复用连接。
        
        Args:
            book: 书籍对象
            chapter: 章节对象
        
        Returns:
            下载成功返回章节字数，失败返回 -1
        """
        async with self._get_api_client(book.platform) as api:
            # 七猫需要设置当前书籍ID
            if book.platform == "qimao":
                api.set_current_book_id(book.book_id)
            
            return await self._download_single_chapter_with_api(api, book, chapter)
    
    # ============ 更新和重试 ============
    
    async def update_book(
        self,
        book_uuid: str,
        task_id: Optional[str] = None,
    ) -> DownloadTask:
        """
        更新书籍（下载新章节）
        
        Args:
            book_uuid: 书籍UUID
            task_id: 已有的任务ID，如果提供则复用该任务
        
        Returns:
            下载任务对象
        """
        return await self.download_book(book_uuid, task_type="update", task_id=task_id)
    
    async def retry_failed_chapters(self, book_uuid: str) -> int:
        """
        重试失败的章节
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            重试的章节数量
        """
        # 将失败的章节状态重置为pending
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
    
    def get_download_progress(self, book_uuid: str) -> Dict[str, Any]:
        """
        获取书籍下载进度
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            {
                "total": int,
                "completed": int,
                "failed": int,
                "pending": int,
                "progress": float
            }
        """
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            return {}
        
        # 统计各状态章节数
        status_counts = self.db.query(
            Chapter.download_status,
            func.count(Chapter.id)
        ).filter(
            Chapter.book_id == book_uuid
        ).group_by(Chapter.download_status).all()
        
        counts = {status: count for status, count in status_counts}
        
        total = sum(counts.values())
        completed = counts.get("completed", 0)
        failed = counts.get("failed", 0)
        pending = counts.get("pending", 0)
        
        progress = round(completed / total * 100, 2) if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress": progress,
        }
    
    # ============ 配额管理 ============
    
    def get_quota_usage(self, platform: str) -> Dict[str, Any]:
        """获取平台配额使用情况"""
        return self.rate_limiter.get_usage(platform)
    
    def get_all_quota_usage(self) -> Dict[str, Dict[str, Any]]:
        """获取所有平台配额使用情况"""
        return {
            "fanqie": self.rate_limiter.get_usage("fanqie"),
            "qimao": self.rate_limiter.get_usage("qimao"),
        }
