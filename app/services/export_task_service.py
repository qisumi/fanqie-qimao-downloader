"""Export task persistence service."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.export_task import ExportTask
from app.repositories import ExportTaskRepository


class ExportTaskService:
    """CRUD-like operations for EPUB/TXT export task states."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ExportTaskRepository(db)

    def _get(self, book_id: str, export_type: str) -> Optional[ExportTask]:
        return self.repo.get_by_book_and_type(book_id=book_id, export_type=export_type)

    def get_status_dict(self, book_id: str, export_type: str) -> Dict[str, Any]:
        task = self._get(book_id, export_type)
        if not task:
            label = "EPUB" if export_type == "epub" else "TXT"
            return {
                "status": "not_started",
                "message": f"没有正在进行的{label}生成任务",
            }

        return {
            "status": task.status,
            "progress": task.progress or 0,
            "message": task.message or "",
            "file_path": task.file_path,
            "error": task.error_message,
        }

    def is_active(self, book_id: str, export_type: str) -> bool:
        task = self._get(book_id, export_type)
        return bool(task and task.status in ("running", "queued"))

    def set_status(
        self,
        book_id: str,
        export_type: str,
        status: str,
        progress: int = 0,
        message: str = "",
        file_path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> ExportTask:
        task = self._get(book_id, export_type)
        now = datetime.now(timezone.utc)
        if not task:
            task = ExportTask(
                book_id=book_id,
                export_type=export_type,
            )
            self.db.add(task)

        task.status = status
        task.progress = progress
        task.message = message
        task.file_path = file_path
        task.error_message = error
        if status == "running":
            task.started_at = now
        if status in ("completed", "failed"):
            task.completed_at = now

        self.db.commit()
        self.db.refresh(task)
        return task
