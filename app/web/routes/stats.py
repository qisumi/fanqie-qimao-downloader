"""
统计信息API路由

提供系统统计相关的RESTful API端点:
- 系统概览统计
- 存储统计
- 配额使用情况
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.utils.database import get_db
from app.services import StorageService, DownloadService
from app.models.book import Book
from app.models.chapter import Chapter
from app.schemas.service_schemas import (
    SystemStats,
    StorageStats,
    AllQuotaResponse,
    QuotaResponse,
)
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.get("/", response_model=SystemStats)
async def get_stats(
    db: Session = Depends(get_db),
) -> SystemStats:
    """
    获取系统统计信息
    
    返回系统整体概览，包括:
    - 书籍数量统计（按平台、状态分组）
    - 章节数量统计
    - 存储使用情况
    - 配额使用情况
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        # 统计书籍数量
        total_books = db.query(func.count(Book.id)).scalar() or 0
        
        # 按平台统计
        platform_stats = db.query(
            Book.platform,
            func.count(Book.id)
        ).group_by(Book.platform).all()
        books_by_platform = {p: c for p, c in platform_stats}
        
        # 按状态统计
        status_stats = db.query(
            Book.download_status,
            func.count(Book.id)
        ).group_by(Book.download_status).all()
        books_by_status = {s or "unknown": c for s, c in status_stats}
        
        # 统计章节数量
        total_chapters = db.query(func.count(Chapter.id)).scalar() or 0
        downloaded_chapters = db.query(func.count(Chapter.id)).filter(
            Chapter.download_status == "completed"
        ).scalar() or 0
        
        # 获取存储统计
        storage_stats_dict = storage.get_storage_stats()
        storage_stats = StorageStats(
            books_count=storage_stats_dict.get("books_count", 0),
            epubs_count=storage_stats_dict.get("epubs_count", 0),
            total_chapters=storage_stats_dict.get("total_chapters", 0),
            books_size_bytes=storage_stats_dict.get("books_size_bytes", 0),
            epubs_size_bytes=storage_stats_dict.get("epubs_size_bytes", 0),
            total_size_bytes=storage_stats_dict.get("total_size_bytes", 0),
            books_size_mb=storage_stats_dict.get("books_size_mb", 0.0),
            epubs_size_mb=storage_stats_dict.get("epubs_size_mb", 0.0),
            total_size_mb=storage_stats_dict.get("total_size_mb", 0.0),
        )
        
        # 获取配额使用情况
        all_quota = download_service.get_all_quota_usage()
        
        # 构建配额响应
        fanqie_quota = all_quota.get("fanqie", {})
        qimao_quota = all_quota.get("qimao", {})
        
        # 使用配置中的每日字数限制作为默认值
        default_limit = settings.daily_word_limit
        
        quota = AllQuotaResponse(
            fanqie=QuotaResponse(
                date=fanqie_quota.get("date", ""),
                platform="fanqie",
                downloaded=fanqie_quota.get("downloaded", 0),
                limit=fanqie_quota.get("limit", default_limit),
                remaining=fanqie_quota.get("remaining", default_limit),
                percentage=fanqie_quota.get("percentage", 0.0),
            ),
            qimao=QuotaResponse(
                date=qimao_quota.get("date", ""),
                platform="qimao",
                downloaded=qimao_quota.get("downloaded", 0),
                limit=qimao_quota.get("limit", default_limit),
                remaining=qimao_quota.get("remaining", default_limit),
                percentage=qimao_quota.get("percentage", 0.0),
            ),
        )
        
        return SystemStats(
            total_books=total_books,
            books_by_platform=books_by_platform,
            books_by_status=books_by_status,
            total_chapters=total_chapters,
            downloaded_chapters=downloaded_chapters,
            storage=storage_stats,
            quota=quota,
        )
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/storage", response_model=StorageStats)
async def get_storage_stats() -> StorageStats:
    """
    获取存储统计信息
    
    返回存储使用详情:
    - 书籍目录大小
    - EPUB目录大小
    - 章节文件数量
    """
    try:
        storage = StorageService()
        stats = storage.get_storage_stats()
        
        return StorageStats(
            books_count=stats.get("books_count", 0),
            epubs_count=stats.get("epubs_count", 0),
            total_chapters=stats.get("total_chapters", 0),
            books_size_bytes=stats.get("books_size_bytes", 0),
            epubs_size_bytes=stats.get("epubs_size_bytes", 0),
            total_size_bytes=stats.get("total_size_bytes", 0),
            books_size_mb=stats.get("books_size_mb", 0.0),
            epubs_size_mb=stats.get("epubs_size_mb", 0.0),
            total_size_mb=stats.get("total_size_mb", 0.0),
        )
        
    except Exception as e:
        logger.error(f"Get storage stats error: {e}")
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}")


@router.get("/quota", response_model=AllQuotaResponse)
async def get_quota_stats(
    db: Session = Depends(get_db),
) -> AllQuotaResponse:
    """
    获取配额使用情况
    
    返回所有平台的今日配额使用情况
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        all_quota = download_service.get_all_quota_usage()
        
        fanqie_quota = all_quota.get("fanqie", {})
        qimao_quota = all_quota.get("qimao", {})
        
        return AllQuotaResponse(
            fanqie=QuotaResponse(
                date=fanqie_quota.get("date", ""),
                platform="fanqie",
                downloaded=fanqie_quota.get("downloaded", 0),
                limit=fanqie_quota.get("limit", 200),
                remaining=fanqie_quota.get("remaining", 200),
                percentage=fanqie_quota.get("percentage", 0.0),
            ),
            qimao=QuotaResponse(
                date=qimao_quota.get("date", ""),
                platform="qimao",
                downloaded=qimao_quota.get("downloaded", 0),
                limit=qimao_quota.get("limit", 200),
                remaining=qimao_quota.get("remaining", 200),
                percentage=qimao_quota.get("percentage", 0.0),
            ),
        )
        
    except Exception as e:
        logger.error(f"Get quota stats error: {e}")
        raise HTTPException(status_code=500, detail=f"获取配额统计失败: {str(e)}")


@router.get("/books/summary")
async def get_books_summary(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取书籍摘要统计
    
    返回书籍相关的汇总统计:
    - 各平台书籍数量
    - 各状态书籍数量
    - 最近添加的书籍
    """
    try:
        # 按平台统计
        platform_stats = db.query(
            Book.platform,
            func.count(Book.id)
        ).group_by(Book.platform).all()
        
        # 按状态统计
        status_stats = db.query(
            Book.download_status,
            func.count(Book.id)
        ).group_by(Book.download_status).all()
        
        # 最近添加的书籍
        recent_books = db.query(Book).order_by(
            Book.created_at.desc()
        ).limit(5).all()
        
        return {
            "by_platform": {p: c for p, c in platform_stats},
            "by_status": {s or "unknown": c for s, c in status_stats},
            "recent_books": [
                {
                    "id": book.id,
                    "title": book.title,
                    "platform": book.platform,
                    "status": book.download_status,
                    "created_at": book.created_at.isoformat() if book.created_at else None,
                }
                for book in recent_books
            ],
        }
        
    except Exception as e:
        logger.error(f"Get books summary error: {e}")
        raise HTTPException(status_code=500, detail=f"获取书籍摘要失败: {str(e)}")