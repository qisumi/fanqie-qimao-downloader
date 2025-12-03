"""
阅读历史模型
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Index
from sqlalchemy.orm import relationship

from app.utils.database import Base


class ReadingHistory(Base):
    """阅读历史记录，追加式用于最近阅读列表"""

    __tablename__ = "reading_history"
    __table_args__ = (
        Index("ix_reading_history_user_book", "user_id", "book_id"),
        Index("ix_reading_history_updated", "updated_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    percent = Column(Float, default=0.0)
    device_id = Column(String, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    book = relationship("Book")
    user = relationship("User")
    chapter = relationship("Chapter")

    def __repr__(self):
        return f"<ReadingHistory(book_id={self.book_id}, user_id={self.user_id}, chapter_id={self.chapter_id})>"
