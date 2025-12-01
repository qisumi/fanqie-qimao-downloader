import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.schemas.service_schemas import BookResponse, BookStatistics, BookStatusResponse
from app.services import BookService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{book_id}/status", response_model=BookStatusResponse)
async def get_book_status(
    book_id: str,
    db: Session = Depends(get_db),
) -> BookStatusResponse:
    """
    获取书籍状态（轻量级）
    
    仅返回书籍基本信息和统计数据，不包含章节列表。
    适用于前端轮询下载进度等场景。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        stats = book_service.get_book_statistics(book_id)
        
        book_response = BookResponse(
            id=book.id,
            platform=book.platform,
            book_id=book.book_id,
            title=book.title,
            author=book.author or "",
            cover_url=book.cover_url,
            cover_path=book.cover_path,
            total_chapters=book.total_chapters or 0,
            downloaded_chapters=book.downloaded_chapters or 0,
            word_count=book.word_count,
            creation_status=book.creation_status,
            last_chapter_title=book.last_chapter_title,
            last_update_time=book.last_update_time,
            download_status=book.download_status or "pending",
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
        
        statistics = BookStatistics(
            total_chapters=stats.get("total_chapters", 0),
            completed_chapters=stats.get("completed_chapters", 0),
            failed_chapters=stats.get("failed_chapters", 0),
            pending_chapters=stats.get("pending_chapters", 0),
            progress=stats.get("progress", 0.0),
            exists=stats.get("exists", False),
            has_cover=stats.get("has_cover", False),
            chapter_count=stats.get("chapter_count", 0),
            size_bytes=stats.get("size_bytes", 0),
            size_mb=stats.get("size_mb", 0.0),
        )
        
        return BookStatusResponse(
            book=book_response,
            statistics=statistics,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get book status error: {e}")
        raise HTTPException(status_code=500, detail=f"获取书籍状态失败: {str(e)}")


@router.get("/{book_id}/chapters/summary")
async def get_chapter_status_summary(
    book_id: str,
    segment_size: int = Query(50, ge=10, le=200, description="每段章节数"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取章节状态摘要
    
    将章节按固定数量分段，返回每段的下载状态统计。
    用于前端热力图展示章节下载进度。
    
    - **book_id**: 书籍UUID
    - **segment_size**: 每段章节数，默认50
    """
    from app.models.chapter import Chapter
    from sqlalchemy import func
    
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        chapters = db.query(Chapter).filter(
            Chapter.book_id == book_id
        ).order_by(Chapter.chapter_index).all()
        
        if not chapters:
            return {
                "book_id": book_id,
                "total_chapters": 0,
                "completed_chapters": 0,
                "pending_chapters": 0,
                "failed_chapters": 0,
                "segment_size": segment_size,
                "segments": []
            }
        
        total = len(chapters)
        completed = sum(1 for ch in chapters if ch.download_status == "completed")
        failed = sum(1 for ch in chapters if ch.download_status == "failed")
        pending = total - completed - failed
        
        segments = []
        for i in range(0, total, segment_size):
            segment_chapters = chapters[i:i + segment_size]
            segment_completed = sum(1 for ch in segment_chapters if ch.download_status == "completed")
            segment_failed = sum(1 for ch in segment_chapters if ch.download_status == "failed")
            segment_pending = len(segment_chapters) - segment_completed - segment_failed
            
            segments.append({
                "start_index": segment_chapters[0].chapter_index,
                "end_index": segment_chapters[-1].chapter_index,
                "total": len(segment_chapters),
                "completed": segment_completed,
                "pending": segment_pending,
                "failed": segment_failed,
                "completion_rate": segment_completed / len(segment_chapters) if segment_chapters else 0,
                "first_chapter_title": segment_chapters[0].title if segment_chapters else None,
                "last_chapter_title": segment_chapters[-1].title if segment_chapters else None,
            })
        
        return {
            "book_id": book_id,
            "total_chapters": total,
            "completed_chapters": completed,
            "pending_chapters": pending,
            "failed_chapters": failed,
            "segment_size": segment_size,
            "segments": segments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get chapter summary error: {e}")
        raise HTTPException(status_code=500, detail=f"获取章节摘要失败: {str(e)}")
