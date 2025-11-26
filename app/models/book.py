"""
书籍数据模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float
from sqlalchemy.dialects.sqlite import JSON

from app.utils.database import Base


class Book(Base):
    """书籍模型"""
    __tablename__ = "books"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String, nullable=False, index=True)  # fanqie 或 qimao
    book_id = Column(String, nullable=False)  # 平台书籍ID
    title = Column(String, nullable=False)
    author = Column(String)
    cover_path = Column(String)  # 本地封面路径
    total_chapters = Column(Integer, default=0)
    downloaded_chapters = Column(Integer, default=0)
    word_count = Column(Integer)
    creation_status = Column(String)  # 连载/完结
    last_chapter_title = Column(String)
    last_update_time = Column(DateTime)
    download_status = Column(String, default="pending")  # pending, downloading, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Book(id={self.id}, title={self.title}, platform={self.platform})>"