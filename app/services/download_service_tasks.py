import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from sqlalchemy import func

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.services.download_service_base import DownloadServiceBase

logger = logging.getLogger(__name__)


class DownloadTaskMixin(DownloadServiceBase):
    """任务管理相关的逻辑拆分到独立 mixin 中。"""
    
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
        """
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            raise ValueError(f"Book not found: {book_uuid}")
        
        if task_type == "full_download":
            pending_count = self.db.query(func.count(Chapter.id)).filter(
                Chapter.book_id == book_uuid,
                Chapter.download_status != "completed"
            ).scalar() or 0
        else:
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
        task.completed_at = datetime.utcnow()
        
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
        
        callback = self._progress_callbacks.get(task.id)
        if callback:
            logger.debug(
                f"Triggering progress callback for task {task.id}: "
                f"{task.downloaded_chapters}/{task.total_chapters} ({task.progress}%)"
            )
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


__all__ = ["DownloadTaskMixin"]
