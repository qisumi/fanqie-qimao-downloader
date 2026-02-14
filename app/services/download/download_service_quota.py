import logging
from typing import Any, Dict

from app.repositories import BookRepository, ChapterRepository
from app.services.download.download_service_base import DownloadServiceBase

logger = logging.getLogger(__name__)


class DownloadQuotaMixin(DownloadServiceBase):
    """配额与进度查询逻辑。"""

    @property
    def _book_repo(self) -> BookRepository:
        return BookRepository(self.db)

    @property
    def _chapter_repo(self) -> ChapterRepository:
        return ChapterRepository(self.db)
    
    def get_download_progress(self, book_uuid: str) -> Dict[str, Any]:
        """获取书籍下载进度"""
        book = self._book_repo.get_by_id(book_uuid)
        if not book:
            return {}
        
        status_counts = self._chapter_repo.get_status_counts(book_uuid)
        
        counts = {status: count for status, count in status_counts}
        
        total = sum(counts.values())
        completed = counts.get("completed", 0)
        failed = counts.get("failed", 0)
        pending = counts.get("pending", 0)
        
        progress = round(completed / total * 100, 2) if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress": progress,
        }
    
    def get_quota_usage(self, platform: str) -> Dict[str, Any]:
        """获取平台配额使用情况"""
        return self.rate_limiter.get_usage(platform)
    
    def get_all_quota_usage(self) -> Dict[str, Dict[str, Any]]:
        """获取所有平台配额使用情况"""
        return {
            "fanqie": self.rate_limiter.get_usage("fanqie"),
            "qimao": self.rate_limiter.get_usage("qimao"),
            "biquge": self.rate_limiter.get_usage("biquge"),
        }


__all__ = ["DownloadQuotaMixin"]
