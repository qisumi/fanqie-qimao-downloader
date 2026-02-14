import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.schemas import BookStatusResponse
from app.repositories import ChapterRepository
from app.services import BookService, StorageService
from app.web.mappers.book_mapper import to_book_response, to_book_statistics
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
        
        book_response = to_book_response(book)
        statistics = to_book_statistics(stats)
        
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
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        chapter_repo = ChapterRepository(db)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        chapters = chapter_repo.list_by_book(book_id)
        
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
