import logging
from typing import Any, Dict

from sqlalchemy import func

from app.models.book import Book
from app.models.chapter import Chapter
from app.services.download_service_base import DownloadServiceBase

logger = logging.getLogger(__name__)


class DownloadQuotaMixin(DownloadServiceBase):
    """配额与进度查询逻辑。"""
    
    def get_download_progress(self, book_uuid: str) -> Dict[str, Any]:
        """获取书籍下载进度"""
        book = self.db.query(Book).filter(Book.id == book_uuid).first()
        if not book:
            return {}
        
        status_counts = self.db.query(
            Chapter.download_status,
            func.count(Chapter.id)
        ).filter(
            Chapter.book_id == book_uuid
        ).group_by(Chapter.download_status).all()
        
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
