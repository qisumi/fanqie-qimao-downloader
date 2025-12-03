"""
阅读进度模型
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.utils.database import Base


class ReadingProgress(Base):
    """阅读进度表，按用户 + 设备维度保存单本书的当前位置"""

    __tablename__ = "reading_progress"
    __table_args__ = (
        UniqueConstraint("book_id", "user_id", "device_id", name="uq_reading_progress_book_user_device"),
        Index("ix_reading_progress_user_book", "user_id", "book_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    offset_px = Column(Integer, default=0)  # 像素偏移
    percent = Column(Float, default=0.0)    # 百分比 0-100
    device_id = Column(String, nullable=False)  # 前端传入的设备标识
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    book = relationship("Book")
    user = relationship("User")
    chapter = relationship("Chapter")

    def __repr__(self):
        return f"<ReadingProgress(book_id={self.book_id}, user_id={self.user_id}, chapter_id={self.chapter_id})>"
