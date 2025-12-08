"""
速率限制器

基于 DailyQuota 模型实现每日下载配额管理
"""

import logging
import uuid
from datetime import date, datetime, timedelta
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
    - 每个平台 (fanqie/qimao/biquge) 每天有独立的配额
    - 默认每日限制 2000万字
    - 支持同步和异步两种使用方式
    
    使用示例:
        # 同步方式
        limiter = RateLimiter(db_session)
        if limiter.can_download("fanqie"):
            # 执行下载
            limiter.record_download("fanqie", word_count=5000)
        
        # 异步方式
        async with get_async_session() as session:
            limiter = RateLimiter(session)
            if await limiter.can_download_async("fanqie"):
                # 执行下载
                await limiter.record_download_async("fanqie", word_count=5000)
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
            limit: 每日字数限制，默认从配置读取 (2000万字)
        """
        self.db = db_session
        settings = get_settings()
        self.limit = limit or settings.daily_word_limit
    
    def set_session(self, db_session: Session | AsyncSession):
        """设置数据库会话"""
        self.db = db_session
    
    # ============ 同步方法 ============
    
    def can_download(self, platform: str) -> bool:
        """
        检查是否可以下载 (同步)
        
        Args:
            platform: 平台名称 (fanqie/qimao/biquge)
            
        Returns:
            True 如果今日字数配额未用尽
        """
        # 笔趣阁平台不受配额限制
        if platform == "biquge":
            return True
        
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        quota = self.db.query(DailyQuota).filter(
            DailyQuota.date == today,
            DailyQuota.platform == platform,
        ).first()
        
        if quota is None:
            return True
        
        return quota.words_downloaded < self.limit
    
    def record_download(self, platform: str, word_count: int = 0) -> int:
        """
        记录下载 (同步)
        
        Args:
            platform: 平台名称
            word_count: 下载的字数
            
        Returns:
            今日已下载总字数
        """
        # 笔趣阁平台不受配额限制，直接返回0（表示不记录）
        if platform == "biquge":
            logger.debug(f"笔趣阁平台下载不计入配额: {word_count} 字")
            return 0
        
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
                words_downloaded=0,
                limit=self.limit,
            )
            self.db.add(quota)
        
        quota.words_downloaded += word_count
        self.db.commit()
        
        logger.debug(f"记录下载: {platform} 今日已下载 {quota.words_downloaded}/{self.limit} 字")
        
        return quota.words_downloaded
    
    def get_remaining(self, platform: str) -> int:
        """
        获取今日剩余配额 (同步)
        
        Args:
            platform: 平台名称
            
        Returns:
            剩余可下载字数
        """
        # 笔趣阁平台不受配额限制，返回一个很大的数
        if platform == "biquge":
            return 1_000_000_000  # 10亿字
        
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        quota = self.db.query(DailyQuota).filter(
            DailyQuota.date == today,
            DailyQuota.platform == platform,
        ).first()
        
        if quota is None:
            return self.limit
        
        return max(0, self.limit - quota.words_downloaded)
    
    def get_usage(self, platform: str) -> dict:
        """
        获取今日使用情况 (同步)
        
        Args:
            platform: 平台名称
            
        Returns:
            {
                "date": "2024-01-15",
                "platform": "fanqie",
                "downloaded": 500000,  # 已下载字数
                "limit": 20000000,     # 每日限制字数
                "remaining": 19500000, # 剩余字数
                "percentage": 2.5
            }
        """
        # 笔趣阁平台不受配额限制，返回无限配额
        if platform == "biquge":
            today = date.today()
            return {
                "date": today.isoformat(),
                "platform": platform,
                "downloaded": 0,
                "limit": 1_000_000_000,  # 10亿字，表示无限
                "remaining": 1_000_000_000,
                "percentage": 0.0,
            }
        
        if self.db is None:
            raise RuntimeError("数据库会话未设置")
        
        today = date.today()
        quota = self.db.query(DailyQuota).filter(
            DailyQuota.date == today,
            DailyQuota.platform == platform,
        ).first()
        
        downloaded = quota.words_downloaded if quota else 0
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
            platform: 平台名称 (fanqie/qimao/biquge)
            
        Returns:
            True 如果今日字数配额未用尽
        """
        # 笔趣阁平台不受配额限制
        if platform == "biquge":
            return True
        
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
        
        return quota.words_downloaded < self.limit
    
    async def record_download_async(self, platform: str, word_count: int = 0) -> int:
        """
        记录下载 (异步)
        
        Args:
            platform: 平台名称
            word_count: 下载的字数
            
        Returns:
            今日已下载总字数
        """
        # 笔趣阁平台不受配额限制，直接返回0（表示不记录）
        if platform == "biquge":
            logger.debug(f"笔趣阁平台下载不计入配额: {word_count} 字")
            return 0
        
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
                words_downloaded=0,
                limit=self.limit,
            )
            self.db.add(quota)
        
        quota.words_downloaded += word_count
        await self.db.commit()
        
        logger.debug(f"记录下载: {platform} 今日已下载 {quota.words_downloaded}/{self.limit} 字")
        
        return quota.words_downloaded
    
    async def get_remaining_async(self, platform: str) -> int:
        """
        获取今日剩余配额 (异步)
        
        Args:
            platform: 平台名称
            
        Returns:
            剩余可下载字数
        """
        # 笔趣阁平台不受配额限制，返回一个很大的数
        if platform == "biquge":
            return 1_000_000_000  # 10亿字
        
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
        
        return max(0, self.limit - quota.words_downloaded)
    
    async def get_usage_async(self, platform: str) -> dict:
        """
        获取今日使用情况 (异步)
        
        Args:
            platform: 平台名称
            
        Returns:
             同 get_usage()
        """
        # 笔趣阁平台不受配额限制，返回无限配额
        if platform == "biquge":
            today = date.today()
            return {
                "date": today.isoformat(),
                "platform": platform,
                "downloaded": 0,
                "limit": 1_000_000_000,  # 10亿字，表示无限
                "remaining": 1_000_000_000,
                "percentage": 0.0,
            }
        
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
        
        downloaded = quota.words_downloaded if quota else 0
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
        tomorrow = today + timedelta(days=1)
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
