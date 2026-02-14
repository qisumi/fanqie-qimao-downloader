import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.repositories import BookRepository, ChapterRepository
from app.services import DownloadService, StorageService
from app.schemas import SuccessResponse
from app.usecases import TaskOrchestrator, TaskReadUseCase
from app.utils.database import get_db

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
        task_read_usecase = TaskReadUseCase(db)
        download_service = DownloadService(db=db, storage=storage)
        
        task = task_read_usecase.get_task(task_id)
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
        TaskOrchestrator.cancel_background_task(book_id)
        
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
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    重试失败章节
    
    重新下载书籍中所有失败的章节。
    """
    try:
        storage = StorageService()
        book_repo = BookRepository(db)
        chapter_repo = ChapterRepository(db)
        download_service = DownloadService(db=db, storage=storage)
        
        book = book_repo.get_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        if TaskOrchestrator.has_active_download(book_id):
            return {
                "success": False,
                "message": "该书籍已有下载任务正在进行中，请等待完成后再重试",
                "book_id": book_id,
            }
        
        failed_count = chapter_repo.count_failed_by_book(book_id)
        
        if failed_count == 0:
            return {
                "success": True,
                "message": "没有需要重试的失败章节",
                "book_id": book_id,
                "retried_count": 0,
            }
        
        chapter_repo.reset_failed_to_pending(book_id)
        db.commit()
        
        task = download_service.create_task(book_id, "full_download")
        
        TaskOrchestrator.start_background_task(
            book_id=book_id,
            task_type="full_download",
            task_id=task.id,
        )
        
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
