"""
章节数据模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.utils.database import Base


class Chapter(Base):
    """章节模型"""
    __tablename__ = "chapters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String, nullable=False)  # 平台章节ID
    title = Column(String, nullable=False)
    volume_name = Column(String)  # 卷名
    chapter_index = Column(Integer, nullable=False)  # 顺序编号
    word_count = Column(Integer)
    content_path = Column(String)  # 存储路径
    download_status = Column(String, default="pending")  # pending, completed, failed
    downloaded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    book = relationship("Book", back_populates="chapters")

    def __repr__(self):
        return f"<Chapter(id={self.id}, title={self.title}, index={self.chapter_index})>"


# 为Book模型添加反向关系
from app.models.book import Book
Book.chapters = relationship("Chapter", order_by=Chapter.chapter_index, back_populates="book")