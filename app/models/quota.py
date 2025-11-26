"""
每日配额数据模型
"""

from datetime import date
from sqlalchemy import Column, String, Integer, Date

from app.utils.database import Base


class DailyQuota(Base):
    """每日下载配额模型"""
    __tablename__ = "daily_quota"

    id = Column(String, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    platform = Column(String, nullable=False, index=True)  # fanqie 或 qimao
    chapters_downloaded = Column(Integer, default=0)
    limit = Column(Integer, default=200)

    def __repr__(self):
        return f"<DailyQuota(date={self.date}, platform={self.platform}, downloaded={self.chapters_downloaded}/{self.limit})>"