import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.repositories import BookRepository
from app.services import (
    BookService,
    DownloadService,
    StorageService,
)
from app.usecases import TaskOrchestrator
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

_running_downloads = TaskOrchestrator.get_running_downloads()
_run_download_task = TaskOrchestrator.run_download_task


@router.post(
    "/{book_id}/download",
    summary="启动下载任务",
    response_description="返回任务启动结果",
    responses={
        200: {
            "description": "任务启动成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "《第一序列》下载任务已启动",
                        "task_id": "task-uuid",
                        "book_id": "book-uuid"
                    }
                }
            }
        },
        404: {"description": "书籍不存在"},
        429: {"description": "配额已用尽"},
        500: {"description": "服务器内部错误"}
    }
)
async def start_download(
    book_id: str = Path(..., description="书籍UUID"),
    start_chapter: int = Query(0, ge=0, description="起始章节索引，默认从第0章开始"),
    end_chapter: Optional[int] = Query(None, ge=0, description="结束章节索引（包含），留空表示下载到最后一章"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    开始下载书籍
    
    在后台启动下载任务，下载书籍的所有未完成章节。
    """
    try:
        storage = StorageService()
        book_repo = BookRepository(db)
        download_service = DownloadService(db=db, storage=storage)
        
        book = book_repo.get_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        if TaskOrchestrator.has_active_download(book_id):
            return {
                "success": True,
                "message": "该书籍已有下载任务正在进行中",
                "book_id": book_id,
            }
        
        task = download_service.create_task(
            book_id,
            "full_download",
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            skip_completed=True,
        )
        
        ws_callback = TaskOrchestrator.build_ws_progress_callback(
            book_title=book.title,
            completed_message="下载完成",
            failed_message="下载失败",
        )
        TaskOrchestrator.ensure_progress_callback(download_service, task.id, ws_callback)
        TaskOrchestrator.start_background_task(
            book_id=book_id,
            task_type="full_download",
            task_id=task.id,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
        )
        
        if end_chapter is not None:
            message = f"《{book.title}》第{start_chapter+1}-{end_chapter+1}章下载任务已启动"
        elif start_chapter > 0:
            message = f"《{book.title}》从第{start_chapter+1}章开始的下载任务已启动"
        else:
            message = f"《{book.title}》下载任务已启动"
        
        return {
            "success": True,
            "message": message,
            "task_id": task.id,
            "book_id": book_id,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start download error: {e}")
        raise HTTPException(status_code=500, detail=f"启动下载失败: {str(e)}")


@router.post(
    "/{book_id}/update",
    summary="更新书籍（下载新章节）",
    response_description="返回更新任务启动结果",
    responses={
        200: {
            "description": "任务启动成功或无需更新",
            "content": {
                "application/json": {
                    "examples": {
                        "has_updates": {
                            "summary": "有新章节",
                            "value": {
                                "success": True,
                                "message": "《第一序列》发现15个新章节，更新任务已启动",
                                "task_id": "task-uuid",
                                "book_id": "book-uuid",
                                "new_chapters_count": 15
                            }
                        },
                        "no_updates": {
                            "summary": "无新章节",
                            "value": {
                                "success": True,
                                "message": "《第一序列》已是最新版本，无需更新",
                                "book_id": "book-uuid",
                                "new_chapters_count": 0
                            }
                        }
                    }
                }
            }
        },
        404: {"description": "书籍不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def start_update(
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新书籍（下载新章节）
    
    检查并下载书籍的新章节。
    """
    try:
        storage = StorageService()
        book_repo = BookRepository(db)
        book_service = BookService(db=db, storage=storage)
        download_service = DownloadService(db=db, storage=storage)
        
        book = book_repo.get_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        if TaskOrchestrator.has_active_download(book_id):
            return {
                "success": True,
                "message": "该书籍已有下载任务正在进行中",
                "book_id": book_id,
            }
        
        new_chapters = await book_service.check_new_chapters(book_id)
        if not new_chapters:
            return {
                "success": True,
                "message": f"《{book.title}》已是最新版本，无需更新",
                "book_id": book_id,
                "new_chapters_count": 0,
            }
        
        task = download_service.create_task(book_id, "update")
        
        ws_callback = TaskOrchestrator.build_ws_progress_callback(
            book_title=book.title,
            completed_message="更新完成",
            failed_message="更新失败",
        )
        TaskOrchestrator.ensure_progress_callback(download_service, task.id, ws_callback)
        TaskOrchestrator.start_background_task(
            book_id=book_id,
            task_type="update",
            task_id=task.id,
        )
        
        return {
            "success": True,
            "message": f"《{book.title}》发现{len(new_chapters)}个新章节，更新任务已启动",
            "task_id": task.id,
            "book_id": book_id,
            "new_chapters_count": len(new_chapters),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start update error: {e}")
        raise HTTPException(status_code=500, detail=f"启动更新失败: {str(e)}")


__all__ = ["router", "_running_downloads", "_run_download_task"]
