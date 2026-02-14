"""Repository for download task read/write operations."""

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.task import DownloadTask


class DownloadTaskRepository:
    """Encapsulates DownloadTask ORM access."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, task_id: str) -> Optional[DownloadTask]:
        return self.db.query(DownloadTask).filter(DownloadTask.id == task_id).first()

    def get_latest_running_by_book(self, book_id: str) -> Optional[DownloadTask]:
        return self.db.query(DownloadTask).filter(
            DownloadTask.book_id == book_id,
            DownloadTask.status.in_(["pending", "running"]),
        ).order_by(DownloadTask.created_at.desc()).first()

    def list_tasks(
        self,
        book_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Tuple[List[DownloadTask], int]:
        query = self.db.query(DownloadTask)
        if book_id:
            query = query.filter(DownloadTask.book_id == book_id)
        if status:
            query = query.filter(DownloadTask.status == status)

        total = query.count()
        tasks = query.order_by(DownloadTask.created_at.desc()).offset(page * limit).limit(limit).all()
        return tasks, total
