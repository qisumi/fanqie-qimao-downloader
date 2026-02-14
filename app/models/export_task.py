"""Export task persistence model for EPUB/TXT generation."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.utils.database import Base


class ExportTask(Base):
    """EPUB/TXT export task status model."""

    __tablename__ = "export_tasks"
    __table_args__ = (
        UniqueConstraint("book_id", "export_type", name="uq_export_task_book_type"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    export_type = Column(String, nullable=False, index=True)  # epub, txt
    status = Column(String, default="not_started")  # not_started, queued, running, completed, failed
    progress = Column(Integer, default=0)
    message = Column(Text)
    file_path = Column(String)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ExportTask(book_id={self.book_id}, type={self.export_type}, status={self.status})>"
