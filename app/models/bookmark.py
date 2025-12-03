"""
书签模型
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Index
from sqlalchemy.orm import relationship

from app.utils.database import Base


class Bookmark(Base):
    """阅读书签，按用户保存章节位置和备注"""

    __tablename__ = "bookmarks"
    __table_args__ = (
        Index("ix_bookmarks_user_book", "user_id", "book_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    offset_px = Column(Integer, default=0)
    percent = Column(Float, default=0.0)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    book = relationship("Book")
    user = relationship("User")
    chapter = relationship("Chapter")

    def __repr__(self):
        return f"<Bookmark(id={self.id}, book_id={self.book_id}, chapter_id={self.chapter_id})>"
