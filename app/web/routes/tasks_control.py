import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.services import BookService, DownloadService, StorageService
from app.schemas import SuccessResponse
from app.utils.database import get_db
from app.web.routes.tasks_start import _run_download_task, _running_downloads

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{task_id}/cancel",
    response_model=SuccessResponse,
    summary="取消任务",
    response_description="返回取消结果",
    responses={
        200: {"description": "取消成功"},
        400: {"description": "任务状态不允许取消"},
        404: {"description": "任务不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def cancel_task(
    task_id: str = Path(..., description="任务UUID"),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    取消任务
    
    取消正在进行的下载任务。
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        task = download_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status not in ("pending", "running"):
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status}，无法取消"
            )
        
        success = download_service.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=500, detail="取消任务失败")
        
        book_id = task.book_id
        if book_id in _running_downloads:
            _running_downloads[book_id].cancel()
            _running_downloads.pop(book_id, None)
        
        return SuccessResponse(
            success=True,
            message="任务已取消",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel task error: {e}")
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


@router.post("/{book_id}/retry")
async def retry_failed_chapters(
    book_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    重试失败章节
    
    重新下载书籍中所有失败的章节。
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        download_service = DownloadService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        if book_id in _running_downloads:
            async_task = _running_downloads[book_id]
            if not async_task.done():
                return {
                    "success": False,
                    "message": "该书籍已有下载任务正在进行中，请等待完成后再重试",
                    "book_id": book_id,
                }
            _running_downloads.pop(book_id, None)
            logger.warning(f"Cleaned up completed task for book {book_id}")
        
        failed_count = db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "failed"
        ).count()
        
        if failed_count == 0:
            return {
                "success": True,
                "message": "没有需要重试的失败章节",
                "book_id": book_id,
                "retried_count": 0,
            }
        
        db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "failed"
        ).update({"download_status": "pending"})
        db.commit()
        
        task = download_service.create_task(book_id, "full_download")
        
        async_task = asyncio.create_task(
            _run_download_task(book_id, "full_download", task.id)
        )
        _running_downloads[book_id] = async_task
        
        return {
            "success": True,
            "message": f"开始重试{failed_count}个失败章节",
            "task_id": task.id,
            "book_id": book_id,
            "retried_count": failed_count,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry failed chapters error: {e}")
        raise HTTPException(status_code=500, detail=f"重试失败章节失败: {str(e)}")
