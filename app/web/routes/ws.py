"""
WebSocket 路由

提供任务进度实时推送的 WebSocket 端点
"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.utils.database import SessionLocal
from app.utils.logger import get_logger
from app.config import get_settings
from app.repositories import BookRepository, DownloadTaskRepository
from app.services import StorageService, DownloadService
from app.usecases import TaskOrchestrator
from app.models.task import DownloadTask
from app.web.websocket import get_connection_manager

logger = get_logger(__name__)

router = APIRouter()


def verify_auth_cookie(websocket: WebSocket) -> bool:
    """
    验证 WebSocket 连接的认证 Cookie
    
    Args:
        websocket: WebSocket 连接
        
    Returns:
        是否已认证
    """
    settings = get_settings()
    
    # 如果没有配置密码，不需要认证
    if not settings.app_password:
        return True
    
    # 从 Cookie 中获取认证令牌
    token = websocket.cookies.get("auth_token")
    if not token:
        return False
    
    try:
        serializer = URLSafeTimedSerializer(settings.secret_key)
        max_age = settings.session_expire_hours * 3600
        data = serializer.loads(token, max_age=max_age)
        return data.get("authenticated") == True
    except (BadSignature, SignatureExpired):
        return False


@router.websocket("/tasks/{task_id}")
async def websocket_task_progress(
    websocket: WebSocket,
    task_id: str,
):
    """
    WebSocket 端点：订阅任务进度更新
    
    连接后会立即发送当前任务状态，之后实时推送进度更新。
    
    消息格式:
    ```json
    {
        "type": "progress",
        "data": {
            "task_id": "...",
            "status": "running",
            "total_chapters": 100,
            "downloaded_chapters": 50,
            "failed_chapters": 0,
            "progress": 50.0,
            "book_title": "书名",
            "timestamp": "2024-01-01T12:00:00"
        }
    }
    ```
    
    完成时:
    ```json
    {
        "type": "completed",
        "data": {
            "task_id": "...",
            "success": true,
            "message": "下载完成",
            "book_title": "书名",
            "timestamp": "2024-01-01T12:00:00"
        }
    }
    ```
    """
    manager = get_connection_manager()
    
    # 验证认证
    if not verify_auth_cookie(websocket):
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # 接受连接
    connected = await manager.connect(websocket, task_id)
    if not connected:
        return
    
    db = SessionLocal()
    current_task_id = task_id
    registered_callback = None
    try:
        task_repo = DownloadTaskRepository(db)
        book_repo = BookRepository(db)
        # 发送当前任务状态
        task = task_repo.get_by_id(task_id)
        if not task:
            await websocket.send_json({
                "type": "error",
                "data": {
                    "task_id": task_id,
                    "error_code": "TASK_NOT_FOUND",
                    "error_message": "任务不存在",
                }
            })
            await manager.disconnect(websocket)
            return
        
        # 获取书籍标题
        book = book_repo.get_by_id(task.book_id)
        book_title = book.title if book else None
        
        # 发送初始状态
        await websocket.send_json({
            "type": "progress",
            "data": {
                "task_id": task.id,
                "status": task.status,
                "total_chapters": task.total_chapters or 0,
                "downloaded_chapters": task.downloaded_chapters or 0,
                "failed_chapters": task.failed_chapters or 0,
                "progress": task.progress or 0.0,
                "error_message": task.error_message,
                "book_title": book_title,
            }
        })
        
        # 注册进度回调
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        sync_callback = TaskOrchestrator.build_ws_progress_callback(
            book_title=book_title or "",
            completed_message="下载完成",
            failed_message="下载失败",
        )
        if TaskOrchestrator.ensure_progress_callback(download_service, task_id, sync_callback):
            registered_callback = sync_callback
        
        # 保持连接，等待客户端消息或断开
        try:
            while True:
                # 等待客户端消息（主要用于心跳检测）
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: task_id={task_id}")
        except Exception as e:
            logger.warning(f"WebSocket error: {e}")
            
    finally:
        # 清理
        db.close()
        await manager.disconnect(websocket)
        
        # 注销回调，避免长时间保留无效回调
        if current_task_id and registered_callback:
            try:
                db_cleanup = SessionLocal()
                storage = StorageService()
                download_service_cleanup = DownloadService(db=db_cleanup, storage=storage)
                download_service_cleanup.unregister_progress_callback(current_task_id, registered_callback)
                db_cleanup.close()
            except Exception as e:
                logger.warning(f"Failed to unregister callback: {e}")


@router.websocket("/books/{book_id}")
async def websocket_book_progress(
    websocket: WebSocket,
    book_id: str,
):
    """
    WebSocket 端点：订阅书籍下载进度
    
    自动查找书籍关联的最新运行中任务并订阅其进度。
    如果没有正在运行的任务，会等待新任务启动。
    """
    manager = get_connection_manager()
    
    # 验证认证
    if not verify_auth_cookie(websocket):
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # 接受连接
    await websocket.accept()
    logger.info(f"WebSocket connected for book {book_id}")
    
    db = SessionLocal()
    current_task_id = None
    registered_callback = None
    monitor_task = None
    
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        task_repo = DownloadTaskRepository(db)
        book_repo = BookRepository(db)
        
        # 查找书籍
        book = book_repo.get_by_id(book_id)
        if not book:
            logger.warning(f"Book not found: {book_id}")
            await websocket.send_json({
                "type": "error",
                "data": {
                    "error_code": "BOOK_NOT_FOUND",
                    "error_message": "书籍不存在",
                }
            })
            await websocket.close()
            return
        
        def get_running_task() -> Optional[DownloadTask]:
            return task_repo.get_latest_running_by_book(book_id)
        
        async def attach_task(task: DownloadTask):
            """发送初始状态并注册进度回调/连接管理"""
            nonlocal current_task_id, registered_callback
            current_task_id = task.id
            logger.info(f"Found running task {current_task_id} for book {book_id}")
            
            await websocket.send_json({
                "type": "progress",
                "data": {
                    "task_id": task.id,
                    "status": task.status,
                    "total_chapters": task.total_chapters or 0,
                    "downloaded_chapters": task.downloaded_chapters or 0,
                    "failed_chapters": task.failed_chapters or 0,
                    "progress": task.progress or 0.0,
                    "error_message": task.error_message,
                    "book_title": book.title,
                    "timestamp": datetime.now().isoformat(),
                }
            })
            
            await manager.attach_existing_connection(websocket, current_task_id)
            logger.info(
                f"Registered WebSocket for task {current_task_id}, "
                f"total connections: {manager.get_connection_count(current_task_id)}"
            )
            
            sync_callback = TaskOrchestrator.build_ws_progress_callback(
                book_title=book.title,
                completed_message="下载完成",
                failed_message="下载失败",
            )
            if TaskOrchestrator.ensure_progress_callback(download_service, current_task_id, sync_callback):
                registered_callback = sync_callback
        
        async def monitor_new_task_if_needed():
            """当书籍标记为下载中但未找到任务时，轮询等待任务创建"""
            while current_task_id is None and websocket.client_state == WebSocketState.CONNECTED:
                await asyncio.sleep(1)
                db.expire_all()
                new_task = get_running_task()
                if new_task:
                    await attach_task(new_task)
                    break
        
        # 查找最新的运行中任务
        task = get_running_task()
        
        if task:
            await attach_task(task)
        else:
            # 没有正在运行的任务，发送当前书籍状态
            logger.info(f"No running task for book {book_id}, sending book status")
            await websocket.send_json({
                "type": "status",
                "data": {
                    "book_id": book_id,
                    "book_title": book.title,
                    "download_status": book.download_status,
                    "total_chapters": book.total_chapters,
                    "downloaded_chapters": book.downloaded_chapters,
                    "message": "没有正在运行的下载任务",
                }
            })
            if book.download_status == "downloading":
                logger.info(f"Book {book_id} marked downloading but no task found, waiting for task to start")
            monitor_task = asyncio.create_task(monitor_new_task_if_needed())
        
        # 保持连接
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    logger.debug(f"Heartbeat for book {book_id}")
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: book_id={book_id}")
        except Exception as e:
            logger.error(f"WebSocket error for book {book_id}: {e}", exc_info=True)
            
    finally:
        if monitor_task:
            monitor_task.cancel()
        db.close()
        await manager.disconnect(websocket)
        
