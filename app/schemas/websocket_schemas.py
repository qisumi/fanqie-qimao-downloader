"""
WebSocket 相关 Pydantic Schemas

定义 WebSocket 消息相关的数据模型
"""

from datetime import datetime
from typing import Any, Dict, Union
from enum import Enum

from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """WebSocket 消息类型"""
    PROGRESS = "progress"      # 进度更新
    COMPLETED = "completed"    # 任务完成
    ERROR = "error"            # 错误通知
    PING = "ping"              # 心跳检测
    PONG = "pong"              # 心跳响应


class WSProgressData(BaseModel):
    """WebSocket 进度更新数据"""
    
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    total_chapters: int = Field(default=0, description="总章节数")
    downloaded_chapters: int = Field(default=0, description="已下载章节数")
    failed_chapters: int = Field(default=0, description="失败章节数")
    progress: float = Field(default=0.0, description="进度百分比")
    error_message: str = Field(default=None, description="错误信息")
    book_title: str = Field(default=None, description="书籍标题")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class WSCompletedData(BaseModel):
    """WebSocket 任务完成数据"""
    
    task_id: str = Field(..., description="任务ID")
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="完成消息")
    book_title: str = Field(default=None, description="书籍标题")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class WSErrorData(BaseModel):
    """WebSocket 错误数据"""
    
    task_id: str = Field(..., description="任务ID")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class WebSocketMessage(BaseModel):
    """WebSocket 消息"""
    
    type: WebSocketMessageType = Field(..., description="消息类型")
    data: Union[WSProgressData, WSCompletedData, WSErrorData, Dict[str, Any]] = Field(..., description="消息数据")