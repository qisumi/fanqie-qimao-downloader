"""Repository for export task persistence."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.export_task import ExportTask


class ExportTaskRepository:
    """Encapsulates ExportTask ORM access."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_book_and_type(self, book_id: str, export_type: str) -> Optional[ExportTask]:
        return self.db.query(ExportTask).filter(
            ExportTask.book_id == book_id,
            ExportTask.export_type == export_type,
        ).first()
