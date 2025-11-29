"""
任务管理API路由

提供下载任务相关的RESTful API端点:
- 获取任务列表
- 获取任务详情
- 启动下载任务
- 启动更新任务
- 取消任务
- 重试失败章节
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models.task import DownloadTask
from app.services import (
    StorageService,
    BookService,
    DownloadService,
    DownloadError,
    QuotaReachedError,
    TaskCancelledError,
)
from app.schemas.service_schemas import (
    TaskResponse,
    TaskListResponse,
    SuccessResponse,
    DownloadProgress,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# 存储正在运行的下载任务
_running_downloads: Dict[str, asyncio.Task] = {}


# ============ 任务列表 ============

@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    book_id: Optional[str] = Query(None, description="按书籍筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(0, ge=0, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """
    获取任务列表
    
    - **book_id**: 按书籍UUID筛选
    - **status**: 按状态筛选 (pending/running/completed/failed/cancelled)
    - **page**: 页码，从0开始
    - **limit**: 每页数量
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        result = download_service.list_tasks(
            book_uuid=book_id,
            status=status,
            page=page,
            limit=limit,
        )
        
        # 转换为响应格式
        tasks = []
        for task in result["tasks"]:
            tasks.append(TaskResponse(
                id=task.id,
                book_id=task.book_id,
                task_type=task.task_type,
                status=task.status or "pending",
                total_chapters=task.total_chapters or 0,
                downloaded_chapters=task.downloaded_chapters or 0,
                failed_chapters=task.failed_chapters or 0,
                progress=task.progress or 0.0,
                error_message=task.error_message,
                started_at=task.started_at,
                completed_at=task.completed_at,
                created_at=task.created_at,
            ))
        
        return TaskListResponse(
            tasks=tasks,
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
        )
        
    except Exception as e:
        logger.error(f"List tasks error: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


# ============ 获取配额使用情况 (需要放在 /{task_id} 之前) ============

@router.get("/quota/{platform}")
async def get_quota(
    platform: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取指定平台的配额使用情况
    
    - **platform**: 平台名称 (fanqie/qimao)
    """
    if platform not in ("fanqie", "qimao"):
        raise HTTPException(status_code=400, detail="平台必须是 fanqie 或 qimao")
    
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        usage = download_service.get_quota_usage(platform)
        
        return usage
        
    except Exception as e:
        logger.error(f"Get quota error: {e}")
        raise HTTPException(status_code=500, detail=f"获取配额信息失败: {str(e)}")


@router.get("/quota")
async def get_all_quota(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取所有平台的配额使用情况
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        usage = download_service.get_all_quota_usage()
        
        return usage
        
    except Exception as e:
        logger.error(f"Get all quota error: {e}")
        raise HTTPException(status_code=500, detail=f"获取配额信息失败: {str(e)}")


# ============ 任务详情 ============

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    获取任务详情
    
    - **task_id**: 任务UUID
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        task = download_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskResponse(
            id=task.id,
            book_id=task.book_id,
            task_type=task.task_type,
            status=task.status or "pending",
            total_chapters=task.total_chapters or 0,
            downloaded_chapters=task.downloaded_chapters or 0,
            failed_chapters=task.failed_chapters or 0,
            progress=task.progress or 0.0,
            error_message=task.error_message,
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task error: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


# ============ 后台下载任务 ============

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
            # 先检查并添加新章节
            book_service = BookService(db=db, storage=storage)
            new_count = await book_service.add_new_chapters(book_id)
            logger.info(f"Found {new_count} new chapters for book {book_id}")
            
            # 下载新章节，复用已创建的任务
            await download_service.update_book(book_id, task_id=task_id)
        else:
            # 完整下载，复用已创建的任务
            # skip_completed=True 确保只下载未完成的章节，不会重新下载已完成的
            await download_service.download_book(
                book_uuid=book_id,
                task_type=task_type,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                task_id=task_id,
                skip_completed=True,  # 跳过已完成章节，只下载未完成的
            )
            
    except QuotaReachedError as e:
        logger.warning(f"Download quota reached: {e}")
    except TaskCancelledError:
        logger.info(f"Download task cancelled: {book_id}")
    except asyncio.CancelledError:
        logger.info(f"Download task was cancelled by user: {book_id}")
        # 当 asyncio 任务被取消时，确保更新书籍和任务状态
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
        # 清理运行任务记录
        # 注意：这里必须清理，即使任务失败也要从字典中移除
        _running_downloads.pop(book_id, None)
        logger.debug(f"Cleaned up download task for book {book_id}")


# ============ 开始下载 ============

@router.post("/{book_id}/download")
async def start_download(
    book_id: str,
    background_tasks: BackgroundTasks,
    start_chapter: int = Query(0, ge=0, description="起始章节索引"),
    end_chapter: Optional[int] = Query(None, ge=0, description="结束章节索引（包含），留空表示到最后一章"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    开始下载书籍
    
    在后台启动下载任务，下载书籍的所有未完成章节。
    
    - **book_id**: 书籍UUID
    - **start_chapter**: 起始章节索引，默认从第0章开始
    - **end_chapter**: 结束章节索引（包含），留空表示下载到最后一章
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        download_service = DownloadService(db=db, storage=storage)
        
        # 检查书籍是否存在
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查是否已有正在运行的任务
        # 注意：这里检查的是真正在运行的异步任务，而不是数据库记录
        if book_id in _running_downloads:
            # 检查该任务是否真的还在运行
            async_task = _running_downloads[book_id]
            if not async_task.done():
                return {
                    "success": True,
                    "message": "该书籍已有下载任务正在进行中",
                    "book_id": book_id,
                }
            else:
                # 任务已完成但未清理，清理之
                _running_downloads.pop(book_id, None)
                logger.warning(f"Cleaned up completed task for book {book_id}")
        
        # 检查配额
        usage = download_service.get_quota_usage(book.platform)
        if usage["remaining"] <= 0:
            raise HTTPException(
                status_code=429,
                detail=f"今日{book.platform}平台配额已用尽，请明天再试"
            )
        
        # 创建任务记录
        task = download_service.create_task(book_id, "full_download")
        
        # 先注册 WebSocket 回调(使用全局连接管理器)
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
        
        # 提前注册回调
        download_service.register_progress_callback(task.id, sync_ws_callback)
        logger.info(f"Registered WebSocket callback for task {task.id}")
        
        # 启动后台任务，传递 task_id 以复用任务
        async_task = asyncio.create_task(
            _run_download_task(book_id, "full_download", task.id, start_chapter, end_chapter)
        )
        _running_downloads[book_id] = async_task
        
        # 构建返回消息
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


# ============ 开始更新 ============

@router.post("/{book_id}/update")
async def start_update(
    book_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    更新书籍（下载新章节）
    
    检查并下载书籍的新章节。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        download_service = DownloadService(db=db, storage=storage)
        
        # 检查书籍是否存在
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查是否已有正在运行的任务
        if book_id in _running_downloads:
            # 检查该任务是否真的还在运行
            async_task = _running_downloads[book_id]
            if not async_task.done():
                return {
                    "success": True,
                    "message": "该书籍已有下载任务正在进行中",
                    "book_id": book_id,
                }
            else:
                # 任务已完成但未清理，清理之
                _running_downloads.pop(book_id, None)
                logger.warning(f"Cleaned up completed task for book {book_id}")
        
        # 先检查新章节数量
        new_chapters = await book_service.check_new_chapters(book_id)
        if not new_chapters:
            return {
                "success": True,
                "message": f"《{book.title}》已是最新版本，无需更新",
                "book_id": book_id,
                "new_chapters_count": 0,
            }
        
        # 创建任务记录
        task = download_service.create_task(book_id, "update")
        
        # 先注册 WebSocket 回调(使用全局连接管理器)
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
        
        # 提前注册回调
        download_service.register_progress_callback(task.id, sync_ws_callback)
        logger.info(f"Registered WebSocket callback for task {task.id}")
        
        # 启动后台任务，传递 task_id 以复用任务
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


# ============ 取消任务 ============

@router.post("/{task_id}/cancel", response_model=SuccessResponse)
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    取消任务
    
    取消正在进行的下载任务。
    
    - **task_id**: 任务UUID
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        # 获取任务信息
        task = download_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        if task.status not in ("pending", "running"):
            raise HTTPException(
                status_code=400,
                detail=f"任务状态为{task.status}，无法取消"
            )
        
        # 取消任务
        success = download_service.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="取消任务失败")
        
        # 如果有对应的异步任务，也取消它
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


# ============ 重试失败章节 ============

@router.post("/{book_id}/retry")
async def retry_failed_chapters(
    book_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    重试失败章节
    
    重新下载书籍中所有失败的章节。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        download_service = DownloadService(db=db, storage=storage)
        
        # 检查书籍是否存在
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查是否已有正在运行的任务
        if book_id in _running_downloads:
            # 检查该任务是否真的还在运行
            async_task = _running_downloads[book_id]
            if not async_task.done():
                return {
                    "success": False,
                    "message": "该书籍已有下载任务正在进行中，请等待完成后再重试",
                    "book_id": book_id,
                }
            else:
                # 任务已完成但未清理，清理之
                _running_downloads.pop(book_id, None)
                logger.warning(f"Cleaned up completed task for book {book_id}")
        
        # 获取失败章节数量
        from app.models.chapter import Chapter
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
        
        # 重置失败章节状态为pending
        db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.download_status == "failed"
        ).update({"download_status": "pending"})
        db.commit()
        
        # 创建任务记录
        task = download_service.create_task(book_id, "full_download")
        
        # 启动后台任务
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