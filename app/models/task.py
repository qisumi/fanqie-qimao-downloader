"""
下载任务数据模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, ForeignKey

from app.utils.database import Base


class DownloadTask(Base):
    """下载任务模型"""
    __tablename__ = "download_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String, nullable=False)  # full_download 或 update
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    total_chapters = Column(Integer, default=0)
    downloaded_chapters = Column(Integer, default=0)
    failed_chapters = Column(Integer, default=0)
    progress = Column(Float, default=0.0)  # 0-100%
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DownloadTask(id={self.id}, book_id={self.book_id}, status={self.status})>"