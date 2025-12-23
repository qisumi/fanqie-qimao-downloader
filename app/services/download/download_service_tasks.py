import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from sqlalchemy import func

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.services.download.download_service_base import DownloadServiceBase

logger = logging.getLogger(__name__)


class DownloadTaskMixin(DownloadServiceBase):
    """任务管理相关的逻辑拆分到独立 mixin 中。"""
    
    def _calculate_task_total(
        self,
        book_uuid: str,
        task_type: str = "full_download",
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
        skip_completed: bool = True,
    ) -> int:
        """
        计算任务实际需要处理的章节数，保证任务进度的分母准确。
        """
        query = self.db.query(func.count(Chapter.id)).filter(
            Chapter.book_id == book_uuid,
            Chapter.chapter_index >= start_chapter,
        )
        
        if end_chapter is not None:
            query = query.filter(Chapter.chapter_index <= end_chapter)
        
        if task_type == "full_download":
            if skip_completed:
                query = query.filter(Chapter.download_status != "completed")
        else:
            query = query.filter(Chapter.download_status == "pending")
        
        return query.scalar() or 0
    
    def create_task(
        self,
        book_uuid: str,
        task_type: str = "full_download",
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
        skip_completed: bool = True,
    ) -> DownloadTask:
        """
        创建下载任务
        
        Args:
            book_uuid: 书籍UUID
            task_type: 任务类型 (full_download/update)
            start_chapter: 起始章节索引
            end_chapter: 结束章节索引（包含）
            skip_completed: 是否跳过已完成章节（仅 full_download 有效）
        """
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            raise ValueError(f"Book not found: {book_uuid}")
        
        pending_count = self._calculate_task_total(
            book_uuid=book_uuid,
            task_type=task_type,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            skip_completed=skip_completed,
        )
        
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
        """获取任务列表"""
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
        """取消任务"""
        task = self.get_task(task_id)
        if not task:
            return False
        
        if task.status not in ("pending", "running"):
            return False
        
        self._cancelled_tasks.add(task_id)
        task.status = "cancelled"
        task.completed_at = datetime.now(timezone.utc)
        
        book = self.db.query(Book).filter(Book.id == task.book_id).first()
        if book and book.download_status == "downloading":
            if book.downloaded_chapters > 0:
                book.download_status = "partial"
            else:
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
        
        if downloaded > 0:
            book = self.db.query(Book).filter(Book.id == task.book_id).first()
            if book:
                completed_count = self.db.query(func.count(Chapter.id)).filter(
                    Chapter.book_id == task.book_id,
                    Chapter.download_status == "completed"
                ).scalar() or 0
                book.downloaded_chapters = completed_count
        
        self.db.commit()
        
        callbacks = self._progress_callbacks.get(task.id, set())
        if callbacks:
            logger.debug(
                f"Triggering {len(callbacks)} progress callback(s) for task {task.id}: "
                f"{task.downloaded_chapters}/{task.total_chapters} ({task.progress}%)"
            )
            # 复制列表，防止回调中修改集合导致迭代报错
            for callback in list(callbacks):
                try:
                    callback(task)
                except Exception:
                    logger.exception(f"Progress callback failed for task {task.id}")
        else:
            logger.warning(f"No progress callback registered for task {task.id}")
    
    def register_progress_callback(
        self,
        task_id: str,
        callback: Callable[[DownloadTask], None],
    ):
        """注册进度回调，支持多个订阅者并发存在"""
        callbacks = self._progress_callbacks.setdefault(task_id, set())
        callbacks.add(callback)
    
    def unregister_progress_callback(
        self,
        task_id: str,
        callback: Optional[Callable[[DownloadTask], None]] = None,
    ):
        """
        注销进度回调
        
        Args:
            task_id: 任务ID
            callback: 指定要移除的回调，不传则移除该任务的所有回调
        """
        callbacks = self._progress_callbacks.get(task_id)
        if not callbacks:
            return
        
        if callback is None:
            self._progress_callbacks.pop(task_id, None)
            return
        
        callbacks.discard(callback)
        if not callbacks:
            self._progress_callbacks.pop(task_id, None)


__all__ = ["DownloadTaskMixin"]
