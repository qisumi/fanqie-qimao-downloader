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
    words_downloaded = Column(Integer, default=0)  # 已下载字数
    limit = Column(Integer, default=20000000)  # 每日限制: 2000万字

    def __repr__(self):
        return f"<DailyQuota(date={self.date}, platform={self.platform}, downloaded={self.words_downloaded}/{self.limit})>"