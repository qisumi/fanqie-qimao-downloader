"""
任务相关 Pydantic Schemas

定义任务相关的请求/响应数据模型
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DownloadStatus(str, Enum):
    """下载状态"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """任务类型"""
    FULL_DOWNLOAD = "full_download"
    UPDATE = "update"


class TaskCreate(BaseModel):
    """创建任务请求"""
    
    book_id: str = Field(..., description="书籍UUID")
    task_type: TaskType = Field(default=TaskType.FULL_DOWNLOAD, description="任务类型")
    start_chapter: int = Field(default=0, description="起始章节索引")
    end_chapter: Optional[int] = Field(default=None, description="结束章节索引（包含），None表示到最后一章")


class TaskResponse(BaseModel):
    """任务响应"""
    
    id: str = Field(..., description="任务UUID")
    book_id: str = Field(..., description="书籍UUID")
    task_type: str = Field(..., description="任务类型")
    status: str = Field(default="pending", description="任务状态")
    total_chapters: int = Field(default=0, description="总章节数")
    downloaded_chapters: int = Field(default=0, description="已下载章节")
    failed_chapters: int = Field(default=0, description="失败章节")
    progress: float = Field(default=0.0, description="进度(%)")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "task-uuid-123",
                "book_id": "book-uuid-456",
                "task_type": "full_download",
                "status": "running",
                "total_chapters": 1273,
                "downloaded_chapters": 856,
                "failed_chapters": 12,
                "progress": 67.2,
                "error_message": None,
                "started_at": "2024-01-01T12:00:00",
                "completed_at": None,
                "created_at": "2024-01-01T11:55:00"
            }
        }
    )


class TaskListResponse(BaseModel):
    """任务列表响应"""
    
    tasks: List[TaskResponse] = Field(default=[], description="任务列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=0, description="当前页")
    limit: int = Field(default=20, description="每页数量")


class DownloadProgress(BaseModel):
    """下载进度"""
    
    book_id: str = Field(..., description="书籍UUID")
    total: int = Field(default=0, description="总章节数")
    completed: int = Field(default=0, description="已完成")
    failed: int = Field(default=0, description="失败")
    pending: int = Field(default=0, description="待下载")
    progress: float = Field(default=0.0, description="进度(%)")