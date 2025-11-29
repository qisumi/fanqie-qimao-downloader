"""
WebSocket 连接管理器

管理 WebSocket 客户端连接、消息广播和进度推送
"""

import asyncio
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    WebSocket 连接管理器
    
    支持:
    - 单任务多客户端订阅
    - 消息广播
    - 断线检测和清理
    - 指数退避重连建议
    """
    
    def __init__(self):
        # task_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> task_id (反向映射，用于快速查找)
        self._websocket_to_task: Dict[WebSocket, str] = {}
        # 锁，保证线程安全
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, task_id: str) -> bool:
        """
        接受 WebSocket 连接并关联到任务
        
        Args:
            websocket: WebSocket 连接
            task_id: 任务 ID
            
        Returns:
            是否连接成功
        """
        try:
            await websocket.accept()
            
            async with self._lock:
                if task_id not in self._connections:
                    self._connections[task_id] = set()
                self._connections[task_id].add(websocket)
                self._websocket_to_task[websocket] = task_id
            
            logger.info(f"WebSocket connected: task_id={task_id}, total_connections={len(self._connections.get(task_id, []))}")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """
        断开 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接
        """
        async with self._lock:
            task_id = self._websocket_to_task.pop(websocket, None)
            if task_id and task_id in self._connections:
                self._connections[task_id].discard(websocket)
                # 如果没有更多连接，清理任务条目
                if not self._connections[task_id]:
                    del self._connections[task_id]
                logger.info(f"WebSocket disconnected: task_id={task_id}")
    
    async def send_message(self, websocket: WebSocket, message: dict):
        """
        向单个客户端发送消息
        
        Args:
            websocket: WebSocket 连接
            message: 消息字典
        """
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send message: {e}")
            await self.disconnect(websocket)
    
    async def broadcast_to_task(self, task_id: str, message: dict):
        """
        向订阅特定任务的所有客户端广播消息
        
        Args:
            task_id: 任务 ID
            message: 消息字典
        """
        async with self._lock:
            connections = self._connections.get(task_id, set()).copy()
        
        if not connections:
            return
        
        # 并发发送消息
        disconnected = []
        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.append(websocket)
            except Exception as e:
                logger.warning(f"Broadcast failed for one client: {e}")
                disconnected.append(websocket)
        
        # 清理断开的连接
        for ws in disconnected:
            await self.disconnect(ws)
    
    async def broadcast_progress(
        self,
        task_id: str,
        status: str,
        total_chapters: int,
        downloaded_chapters: int,
        failed_chapters: int,
        progress: float,
        error_message: Optional[str] = None,
        book_title: Optional[str] = None,
    ):
        """
        广播任务进度更新
        
        Args:
            task_id: 任务 ID
            status: 任务状态
            total_chapters: 总章节数
            downloaded_chapters: 已下载章节数
            failed_chapters: 失败章节数
            progress: 进度百分比
            error_message: 错误信息
            book_title: 书籍标题
        """
        message = {
            "type": "progress",
            "data": {
                "task_id": task_id,
                "status": status,
                "total_chapters": total_chapters,
                "downloaded_chapters": downloaded_chapters,
                "failed_chapters": failed_chapters,
                "progress": progress,
                "error_message": error_message,
                "book_title": book_title,
                "timestamp": datetime.now().isoformat(),
            }
        }
        await self.broadcast_to_task(task_id, message)
    
    async def broadcast_completed(
        self,
        task_id: str,
        success: bool,
        message: str = "",
        book_title: Optional[str] = None,
    ):
        """
        广播任务完成通知
        
        Args:
            task_id: 任务 ID
            success: 是否成功
            message: 完成消息
            book_title: 书籍标题
        """
        msg = {
            "type": "completed",
            "data": {
                "task_id": task_id,
                "success": success,
                "message": message,
                "book_title": book_title,
                "timestamp": datetime.now().isoformat(),
            }
        }
        await self.broadcast_to_task(task_id, msg)
    
    async def broadcast_error(
        self,
        task_id: str,
        error_code: str,
        error_message: str,
    ):
        """
        广播错误通知
        
        Args:
            task_id: 任务 ID
            error_code: 错误代码
            error_message: 错误消息
        """
        message = {
            "type": "error",
            "data": {
                "task_id": task_id,
                "error_code": error_code,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            }
        }
        await self.broadcast_to_task(task_id, message)
    
    def get_connection_count(self, task_id: Optional[str] = None) -> int:
        """
        获取连接数
        
        Args:
            task_id: 任务 ID，如果为 None 则返回总连接数
            
        Returns:
            连接数
        """
        if task_id:
            return len(self._connections.get(task_id, set()))
        return sum(len(conns) for conns in self._connections.values())
    
    def has_subscribers(self, task_id: str) -> bool:
        """
        检查任务是否有订阅者
        
        Args:
            task_id: 任务 ID
            
        Returns:
            是否有订阅者
        """
        return task_id in self._connections and len(self._connections[task_id]) > 0


# 全局连接管理器实例
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器"""
    return manager
