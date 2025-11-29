"""
WebSocket 功能测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from app.web.websocket import ConnectionManager, get_connection_manager
from app.schemas.service_schemas import (
    WebSocketMessageType,
    WSProgressData,
    WSCompletedData,
    WSErrorData,
    WebSocketMessage,
)


class TestConnectionManager:
    """测试 WebSocket 连接管理器"""

    @pytest.fixture
    def manager(self):
        """创建连接管理器实例"""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """创建模拟 WebSocket 连接"""
        from starlette.websockets import WebSocketState
        
        ws = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """测试连接"""
        result = await manager.connect(mock_websocket, "task-123")
        
        assert result is True
        mock_websocket.accept.assert_called_once()
        assert manager.has_subscribers("task-123")
        assert manager.get_connection_count("task-123") == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """测试断开连接"""
        await manager.connect(mock_websocket, "task-123")
        await manager.disconnect(mock_websocket)
        
        assert not manager.has_subscribers("task-123")
        assert manager.get_connection_count("task-123") == 0

    @pytest.mark.asyncio
    async def test_multiple_connections_same_task(self, manager):
        """测试同一任务的多个连接"""
        from starlette.websockets import WebSocketState
        
        ws1 = AsyncMock()
        ws1.client_state = WebSocketState.CONNECTED
        ws1.accept = AsyncMock()
        
        ws2 = AsyncMock()
        ws2.client_state = WebSocketState.CONNECTED
        ws2.accept = AsyncMock()
        
        await manager.connect(ws1, "task-123")
        await manager.connect(ws2, "task-123")
        
        assert manager.get_connection_count("task-123") == 2

    @pytest.mark.asyncio
    async def test_broadcast_to_task(self, manager, mock_websocket):
        """测试任务广播"""
        await manager.connect(mock_websocket, "task-123")
        
        message = {"type": "test", "data": "hello"}
        await manager.broadcast_to_task("task-123", message)
        
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_progress(self, manager, mock_websocket):
        """测试进度广播"""
        await manager.connect(mock_websocket, "task-123")
        
        await manager.broadcast_progress(
            task_id="task-123",
            status="running",
            total_chapters=100,
            downloaded_chapters=50,
            failed_chapters=2,
            progress=52.0,
            book_title="测试书籍"
        )
        
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        
        assert call_args["type"] == "progress"
        assert call_args["data"]["task_id"] == "task-123"
        assert call_args["data"]["status"] == "running"
        assert call_args["data"]["total_chapters"] == 100
        assert call_args["data"]["downloaded_chapters"] == 50
        assert call_args["data"]["progress"] == 52.0
        assert call_args["data"]["book_title"] == "测试书籍"

    @pytest.mark.asyncio
    async def test_broadcast_completed(self, manager, mock_websocket):
        """测试完成广播"""
        await manager.connect(mock_websocket, "task-123")
        
        await manager.broadcast_completed(
            task_id="task-123",
            success=True,
            message="下载完成",
            book_title="测试书籍"
        )
        
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        
        assert call_args["type"] == "completed"
        assert call_args["data"]["task_id"] == "task-123"
        assert call_args["data"]["success"] is True
        assert call_args["data"]["message"] == "下载完成"

    @pytest.mark.asyncio
    async def test_broadcast_error(self, manager, mock_websocket):
        """测试错误广播"""
        await manager.connect(mock_websocket, "task-123")
        
        await manager.broadcast_error(
            task_id="task-123",
            error_code="QUOTA_EXCEEDED",
            error_message="配额已用尽"
        )
        
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        
        assert call_args["type"] == "error"
        assert call_args["data"]["error_code"] == "QUOTA_EXCEEDED"
        assert call_args["data"]["error_message"] == "配额已用尽"

    @pytest.mark.asyncio
    async def test_no_subscribers(self, manager):
        """测试没有订阅者时的广播"""
        # 不应该抛出异常
        await manager.broadcast_to_task("non-existent-task", {"type": "test"})
        await manager.broadcast_progress(
            task_id="non-existent-task",
            status="running",
            total_chapters=100,
            downloaded_chapters=50,
            failed_chapters=0,
            progress=50.0
        )

    def test_get_connection_manager(self):
        """测试获取全局连接管理器"""
        manager1 = get_connection_manager()
        manager2 = get_connection_manager()
        
        assert manager1 is manager2  # 应该是同一个实例


class TestWebSocketSchemas:
    """测试 WebSocket 消息模型"""

    def test_ws_progress_data(self):
        """测试进度数据模型"""
        data = WSProgressData(
            task_id="task-123",
            status="running",
            total_chapters=100,
            downloaded_chapters=50,
            failed_chapters=2,
            progress=52.0,
            book_title="测试书籍"
        )
        
        assert data.task_id == "task-123"
        assert data.status == "running"
        assert data.progress == 52.0

    def test_ws_completed_data(self):
        """测试完成数据模型"""
        data = WSCompletedData(
            task_id="task-123",
            success=True,
            message="下载完成",
            book_title="测试书籍"
        )
        
        assert data.task_id == "task-123"
        assert data.success is True

    def test_ws_error_data(self):
        """测试错误数据模型"""
        data = WSErrorData(
            task_id="task-123",
            error_code="QUOTA_EXCEEDED",
            error_message="配额已用尽"
        )
        
        assert data.error_code == "QUOTA_EXCEEDED"

    def test_websocket_message_type_enum(self):
        """测试消息类型枚举"""
        assert WebSocketMessageType.PROGRESS == "progress"
        assert WebSocketMessageType.COMPLETED == "completed"
        assert WebSocketMessageType.ERROR == "error"
        assert WebSocketMessageType.PING == "ping"
        assert WebSocketMessageType.PONG == "pong"
