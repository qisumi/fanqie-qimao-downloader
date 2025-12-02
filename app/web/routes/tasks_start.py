import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.models.task import DownloadTask
from app.services import (
    BookService,
    DownloadService,
    QuotaReachedError,
    StorageService,
    TaskCancelledError,
)
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储正在运行的下载任务
_running_downloads: Dict[str, asyncio.Task] = {}


async def _run_download_task(
    book_id: str,
    task_type: str,
    task_id: str,
    start_chapter: int = 0,
    end_chapter: Optional[int] = None,
):
    """后台下载任务执行函数"""
    from app.utils.database import SessionLocal
    from app.models.book import Book
    from app.models.task import DownloadTask
    
    db = SessionLocal()
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        if task_type == "update":
            book_service = BookService(db=db, storage=storage)
            new_count = await book_service.add_new_chapters(book_id)
            logger.info(f"Found {new_count} new chapters for book {book_id}")
            
            await download_service.update_book(book_id, task_id=task_id)
        else:
            await download_service.download_book(
                book_uuid=book_id,
                task_type=task_type,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                task_id=task_id,
                skip_completed=True,
            )
            
    except QuotaReachedError as e:
        logger.warning(f"Download quota reached: {e}")
    except TaskCancelledError:
        logger.info(f"Download task cancelled: {book_id}")
    except asyncio.CancelledError:
        logger.info(f"Download task was cancelled by user: {book_id}")
        try:
            book = db.query(Book).filter(Book.id == book_id).first()
            task = db.query(DownloadTask).filter(DownloadTask.id == task_id).first()
            if book and book.download_status == "downloading":
                if book.downloaded_chapters > 0:
                    book.download_status = "partial"
                else:
                    book.download_status = "pending"
            if task and task.status == "running":
                task.status = "cancelled"
                from datetime import datetime
                task.completed_at = datetime.utcnow()
            db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update status after cancel: {update_error}")
    except Exception as e:
        logger.error(f"Download task error: {e}", exc_info=True)
    finally:
        db.close()
        _running_downloads.pop(book_id, None)
        logger.debug(f"Cleaned up download task for book {book_id}")


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
    background_tasks: BackgroundTasks = BackgroundTasks(),
    start_chapter: int = Query(0, ge=0, description="起始章节索引，默认从第0章开始", example=0),
    end_chapter: Optional[int] = Query(None, ge=0, description="结束章节索引（包含），留空表示下载到最后一章", example=None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    开始下载书籍
    
    在后台启动下载任务，下载书籍的所有未完成章节。
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
                    "success": True,
                    "message": "该书籍已有下载任务正在进行中",
                    "book_id": book_id,
                }
            _running_downloads.pop(book_id, None)
            logger.warning(f"Cleaned up completed task for book {book_id}")
        
        task = download_service.create_task(
            book_id,
            "full_download",
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            skip_completed=True,
        )
        
        from app.web.websocket import get_connection_manager
        from datetime import datetime
        manager = get_connection_manager()
        
        def sync_ws_callback(updated_task: DownloadTask):
            """WebSocket 进度回调"""
            async def broadcast():
                try:
                    logger.debug(f"Task {updated_task.id} progress callback: {updated_task.status} - {updated_task.progress}%")
                    
                    if updated_task.status in ("completed", "failed", "cancelled"):
                        await manager.broadcast_completed(
                            task_id=updated_task.id,
                            success=updated_task.status == "completed",
                            message=updated_task.error_message or (
                                "下载完成" if updated_task.status == "completed"
                                else "任务已取消" if updated_task.status == "cancelled"
                                else "下载失败"
                            ),
                            book_title=book.title,
                        )
                    else:
                        await manager.broadcast_progress(
                            task_id=updated_task.id,
                            status=updated_task.status,
                            total_chapters=updated_task.total_chapters or 0,
                            downloaded_chapters=updated_task.downloaded_chapters or 0,
                            failed_chapters=updated_task.failed_chapters or 0,
                            progress=updated_task.progress or 0.0,
                            error_message=updated_task.error_message,
                            book_title=book.title,
                        )
                except Exception as e:
                    logger.warning(f"WebSocket callback error: {e}")
            
            asyncio.create_task(broadcast())
        
        download_service.register_progress_callback(task.id, sync_ws_callback)
        logger.info(f"Registered WebSocket callback for task {task.id}")
        
        async_task = asyncio.create_task(
            _run_download_task(book_id, "full_download", task.id, start_chapter, end_chapter)
        )
        _running_downloads[book_id] = async_task
        
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新书籍（下载新章节）
    
    检查并下载书籍的新章节。
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
                    "success": True,
                    "message": "该书籍已有下载任务正在进行中",
                    "book_id": book_id,
                }
            _running_downloads.pop(book_id, None)
            logger.warning(f"Cleaned up completed task for book {book_id}")
        
        new_chapters = await book_service.check_new_chapters(book_id)
        if not new_chapters:
            return {
                "success": True,
                "message": f"《{book.title}》已是最新版本，无需更新",
                "book_id": book_id,
                "new_chapters_count": 0,
            }
        
        task = download_service.create_task(book_id, "update")
        
        from app.web.websocket import get_connection_manager
        from datetime import datetime
        manager = get_connection_manager()
        
        def sync_ws_callback(updated_task: DownloadTask):
            """WebSocket 进度回调"""
            async def broadcast():
                try:
                    logger.debug(f"Task {updated_task.id} progress callback: {updated_task.status} - {updated_task.progress}%")
                    
                    if updated_task.status in ("completed", "failed", "cancelled"):
                        await manager.broadcast_completed(
                            task_id=updated_task.id,
                            success=updated_task.status == "completed",
                            message=updated_task.error_message or (
                                "更新完成" if updated_task.status == "completed"
                                else "任务已取消" if updated_task.status == "cancelled"
                                else "更新失败"
                            ),
                            book_title=book.title,
                        )
                    else:
                        await manager.broadcast_progress(
                            task_id=updated_task.id,
                            status=updated_task.status,
                            total_chapters=updated_task.total_chapters or 0,
                            downloaded_chapters=updated_task.downloaded_chapters or 0,
                            failed_chapters=updated_task.failed_chapters or 0,
                            progress=updated_task.progress or 0.0,
                            error_message=updated_task.error_message,
                            book_title=book.title,
                        )
                except Exception as e:
                    logger.warning(f"WebSocket callback error: {e}")
            
            asyncio.create_task(broadcast())
        
        download_service.register_progress_callback(task.id, sync_ws_callback)
        logger.info(f"Registered WebSocket callback for task {task.id}")
        
        async_task = asyncio.create_task(
            _run_download_task(book_id, "update", task.id)
        )
        _running_downloads[book_id] = async_task
        
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
