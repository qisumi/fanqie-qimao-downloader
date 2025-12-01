import logging
from typing import Callable, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.api.base import Platform
from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.services.storage_service import StorageService
from app.utils.rate_limiter import RateLimiter
from app.config import settings

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """下载错误基类"""
    pass


class QuotaReachedError(DownloadError):
    """配额已用尽错误"""
    def __init__(self, platform: str, remaining: int = 0):
        self.platform = platform
        self.remaining = remaining
        super().__init__(f"今日{platform}平台配额已用尽，剩余{remaining}字")


class TaskCancelledError(DownloadError):
    """任务已取消错误"""
    pass


class DownloadServiceBase:
    """
    下载服务基础类，提供公共初始化和API客户端选择。
    其他功能通过 mixin 组合的方式拆分到独立模块中，降低单文件体积。
    """
    
    _shared_progress_callbacks: Dict[str, Callable] = {}
    _shared_cancelled_tasks: set = set()
    
    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
        rate_limiter: Optional[RateLimiter] = None,
        concurrent_downloads: Optional[int] = None,
        download_delay: Optional[float] = None,
    ):
        self.db = db
        self.storage = storage or StorageService()
        self.rate_limiter = rate_limiter or RateLimiter(db)
        self.concurrent_downloads = concurrent_downloads or settings.concurrent_downloads
        self.download_delay = download_delay or settings.download_delay
        
        self._cancelled_tasks = DownloadServiceBase._shared_cancelled_tasks
        self._progress_callbacks = DownloadServiceBase._shared_progress_callbacks
    
    def _get_api_client(self, platform: str) -> Union[FanqieAPI, QimaoAPI]:
        """根据平台获取API客户端"""
        if platform == Platform.FANQIE.value or platform == "fanqie":
            return FanqieAPI()
        if platform == Platform.QIMAO.value or platform == "qimao":
            return QimaoAPI()
        raise ValueError(f"Unsupported platform: {platform}")


__all__ = [
    "DownloadError",
    "QuotaReachedError",
    "TaskCancelledError",
    "DownloadServiceBase",
]
