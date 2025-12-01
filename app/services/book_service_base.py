import logging
from typing import Optional, Union

from sqlalchemy.orm import Session

from app.api.base import Platform
from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class BookServiceBase:
    """提供公共初始化和 API 客户端选择"""
    
    def __init__(
        self,
        db: Session,
        storage: Optional[StorageService] = None,
    ):
        self.db = db
        self.storage = storage or StorageService()
    
    def _get_api_client(self, platform: str) -> Union[FanqieAPI, QimaoAPI]:
        """
        根据平台获取API客户端
        
        从聚合模块获取客户端类，便于在测试中通过 patch
        app.services.book_service.FanqieAPI/QimaoAPI 进行替换。
        """
        from app.services import book_service  # 延迟导入以避免循环
        
        if platform == Platform.FANQIE.value or platform == "fanqie":
            return book_service.FanqieAPI()
        if platform == Platform.QIMAO.value or platform == "qimao":
            return book_service.QimaoAPI()
        raise ValueError(f"Unsupported platform: {platform}")


__all__ = ["BookServiceBase", "FanqieAPI", "QimaoAPI"]
