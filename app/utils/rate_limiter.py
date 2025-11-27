"""
速率限制器

基于 DailyQuota 模型实现每日下载配额管理
"""

import logging
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quota import DailyQuota
from app.config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    速率限制器
    
    基于数据库 DailyQuota 表实现每日下载配额管理:
    - 每个平台 (fanqie/qimao) 每天有独立的配额
    - 默认每日限制 200 章
    - 支持同步和异步两种使用方式
    
    使用示例:
        # 同步方式
        limiter = RateLimiter(db_session)
        if limiter.can_download("fanqie"):
            # 执行下载
            limiter.record_download("fanqie")
        
        # 异步方式
        async with get_async_session() as session:
            limiter = RateLimiter(session)
            if await limiter.can_download_async("fanqie"):
                # 执行下载
                await limiter.record_download_async("fanqie")
    """
    
    def __init__(
        self,
        db_session: Optional[Session | AsyncSession] = None,
        limit: Optional[int] = None,
    ):
        """
        初始化速率限制器
        
        Args:
            db_session: 数据库会话 (同步或异步)
            limit: 每日下载限制，默认从配置读取
        """
        self.db = db_session
        settings = get_settings()
        self.limit = limit or settings.daily_chapter_limit
    
    def set_session(self, db_session: Session | AsyncSession):
        """设置数据库会话"""
        self.db = db_session
    
    # ============ 同步方法 ============
    
    def can_download(self, platform: str) -> bool:
        """
        检查是否可以下载 (同步)
        
        Args:
            platform: 平台名称 (fanqie/qimao)
            
        Returns:
            True 如果今日配额未用尽
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        quota = self.db.query(DailyQuota).filter(
            DailyQuota.date == today,
            DailyQuota.platform == platform,
        ).first()
        
        if quota is None:
            return True
        
        return quota.chapters_downloaded < self.limit
    
    def record_download(self, platform: str, count: int = 1) -> int:
        """
        记录下载 (同步)
        
        Args:
            platform: 平台名称
            count: 下载章节数量
            
        Returns:
            今日已下载总数
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        quota = self.db.query(DailyQuota).filter(
            DailyQuota.date == today,
            DailyQuota.platform == platform,
        ).first()
        
        if quota is None:
            quota = DailyQuota(
                id=str(uuid.uuid4()),
                date=today,
                platform=platform,
                chapters_downloaded=0,
                limit=self.limit,
            )
            self.db.add(quota)
        
        quota.chapters_downloaded += count
        self.db.commit()
        
        logger.debug(f"记录下载: {platform} 今日已下载 {quota.chapters_downloaded}/{self.limit}")
        
        return quota.chapters_downloaded
    
    def get_remaining(self, platform: str) -> int:
        """
        获取今日剩余配额 (同步)
        
        Args:
            platform: 平台名称
            
        Returns:
            剩余可下载章节数
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        quota = self.db.query(DailyQuota).filter(
            DailyQuota.date == today,
            DailyQuota.platform == platform,
        ).first()
        
        if quota is None:
            return self.limit
        
        return max(0, self.limit - quota.chapters_downloaded)
    
    def get_usage(self, platform: str) -> dict:
        """
        获取今日使用情况 (同步)
        
        Args:
            platform: 平台名称
            
        Returns:
            {
                "date": "2024-01-15",
                "platform": "fanqie",
                "downloaded": 50,
                "limit": 200,
                "remaining": 150,
                "percentage": 25.0
            }
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        quota = self.db.query(DailyQuota).filter(
            DailyQuota.date == today,
            DailyQuota.platform == platform,
        ).first()
        
        downloaded = quota.chapters_downloaded if quota else 0
        remaining = max(0, self.limit - downloaded)
        percentage = (downloaded / self.limit) * 100 if self.limit > 0 else 0
        
        return {
            "date": today.isoformat(),
            "platform": platform,
            "downloaded": downloaded,
            "limit": self.limit,
            "remaining": remaining,
            "percentage": round(percentage, 2),
        }
    
    # ============ 异步方法 ============
    
    async def can_download_async(self, platform: str) -> bool:
        """
        检查是否可以下载 (异步)
        
        Args:
            platform: 平台名称 (fanqie/qimao)
            
        Returns:
            True 如果今日配额未用尽
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        
        result = await self.db.execute(
            select(DailyQuota).where(
                DailyQuota.date == today,
                DailyQuota.platform == platform,
            )
        )
        quota = result.scalar_one_or_none()
        
        if quota is None:
            return True
        
        return quota.chapters_downloaded < self.limit
    
    async def record_download_async(self, platform: str, count: int = 1) -> int:
        """
        记录下载 (异步)
        
        Args:
            platform: 平台名称
            count: 下载章节数量
            
        Returns:
            今日已下载总数
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        
        result = await self.db.execute(
            select(DailyQuota).where(
                DailyQuota.date == today,
                DailyQuota.platform == platform,
            )
        )
        quota = result.scalar_one_or_none()
        
        if quota is None:
            quota = DailyQuota(
                id=str(uuid.uuid4()),
                date=today,
                platform=platform,
                chapters_downloaded=0,
                limit=self.limit,
            )
            self.db.add(quota)
        
        quota.chapters_downloaded += count
        await self.db.commit()
        
        logger.debug(f"记录下载: {platform} 今日已下载 {quota.chapters_downloaded}/{self.limit}")
        
        return quota.chapters_downloaded
    
    async def get_remaining_async(self, platform: str) -> int:
        """
        获取今日剩余配额 (异步)
        
        Args:
            platform: 平台名称
            
        Returns:
            剩余可下载章节数
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        
        result = await self.db.execute(
            select(DailyQuota).where(
                DailyQuota.date == today,
                DailyQuota.platform == platform,
            )
        )
        quota = result.scalar_one_or_none()
        
        if quota is None:
            return self.limit
        
        return max(0, self.limit - quota.chapters_downloaded)
    
    async def get_usage_async(self, platform: str) -> dict:
        """
        获取今日使用情况 (异步)
        
        Args:
            platform: 平台名称
            
        Returns:
            同 get_usage()
        """
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        
        result = await self.db.execute(
            select(DailyQuota).where(
                DailyQuota.date == today,
                DailyQuota.platform == platform,
            )
        )
        quota = result.scalar_one_or_none()
        
        downloaded = quota.chapters_downloaded if quota else 0
        remaining = max(0, self.limit - downloaded)
        percentage = (downloaded / self.limit) * 100 if self.limit > 0 else 0
        
        return {
            "date": today.isoformat(),
            "platform": platform,
            "downloaded": downloaded,
            "limit": self.limit,
            "remaining": remaining,
            "percentage": round(percentage, 2),
        }
    
    # ============ 工具方法 ============
    
    @staticmethod
    def get_reset_time() -> datetime:
        """
        获取配额重置时间 (次日0点)
        
        Returns:
            下次配额重置的 datetime
        """
        today = date.today()
        tomorrow = date(today.year, today.month, today.day + 1) if today.day < 28 else today.replace(day=1, month=today.month + 1 if today.month < 12 else 1)
        return datetime.combine(tomorrow, datetime.min.time())
    
    @staticmethod
    def get_seconds_until_reset() -> int:
        """
        获取距离配额重置的秒数
        
        Returns:
            距离次日0点的秒数
        """
        now = datetime.now()
        reset_time = RateLimiter.get_reset_time()
        delta = reset_time - now
        return max(0, int(delta.total_seconds()))
