"""
用户书架关联模型
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.utils.database import Base


class UserBook(Base):
    """用户与书籍的关联关系，用于表示个人书架"""

    __tablename__ = "user_books"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_book"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="shelves")
    book = relationship("Book", back_populates="user_links")

    def __repr__(self):
        return f"<UserBook(user_id={self.user_id}, book_id={self.book_id})>"
