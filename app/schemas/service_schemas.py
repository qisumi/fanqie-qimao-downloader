"""
服务层 Pydantic Schemas

定义服务层的请求/响应数据模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ============ 枚举类型 ============

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


# ============ 书籍相关 Schemas ============

class BookCreate(BaseModel):
    """添加书籍请求"""
    
    platform: str = Field(..., description="平台 (fanqie/qimao)")
    book_id: str = Field(..., description="平台书籍ID")
    download_cover: bool = Field(default=True, description="是否下载封面")
    fetch_chapters: bool = Field(default=True, description="是否获取章节列表")
    
    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("fanqie", "qimao"):
            raise ValueError("platform must be 'fanqie' or 'qimao'")
        return v


class BookUpdate(BaseModel):
    """更新书籍请求"""
    
    title: Optional[str] = Field(default=None, description="书名")
    author: Optional[str] = Field(default=None, description="作者")
    download_status: Optional[DownloadStatus] = Field(default=None, description="下载状态")


class BookResponse(BaseModel):
    """书籍响应"""
    
    id: str = Field(..., description="书籍UUID")
    platform: str = Field(..., description="平台")
    book_id: str = Field(..., description="平台书籍ID")
    title: str = Field(..., description="书名")
    author: str = Field(default="", description="作者")
    cover_path: Optional[str] = Field(default=None, description="封面路径")
    total_chapters: int = Field(default=0, description="总章节数")
    downloaded_chapters: int = Field(default=0, description="已下载章节数")
    word_count: Optional[int] = Field(default=None, description="字数")
    creation_status: Optional[str] = Field(default=None, description="连载状态")
    last_chapter_title: Optional[str] = Field(default=None, description="最新章节标题")
    last_update_time: Optional[datetime] = Field(default=None, description="最后更新时间")
    download_status: str = Field(default="pending", description="下载状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    """书籍列表响应"""
    
    books: List[BookResponse] = Field(default=[], description="书籍列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=0, description="当前页")
    limit: int = Field(default=20, description="每页数量")
    pages: int = Field(default=0, description="总页数")


class BookDetailResponse(BaseModel):
    """书籍详情响应"""
    
    book: BookResponse = Field(..., description="书籍信息")
    chapters: List["ChapterResponse"] = Field(default=[], description="章节列表")
    statistics: "BookStatistics" = Field(..., description="统计信息")


class BookStatistics(BaseModel):
    """书籍统计信息"""
    
    total_chapters: int = Field(default=0, description="总章节数")
    completed_chapters: int = Field(default=0, description="已完成章节")
    failed_chapters: int = Field(default=0, description="失败章节")
    pending_chapters: int = Field(default=0, description="待下载章节")
    progress: float = Field(default=0.0, description="下载进度")
    exists: bool = Field(default=False, description="文件是否存在")
    has_cover: bool = Field(default=False, description="是否有封面")
    chapter_count: int = Field(default=0, description="本地章节文件数")
    size_bytes: int = Field(default=0, description="存储大小(字节)")
    size_mb: float = Field(default=0.0, description="存储大小(MB)")


# ============ 章节相关 Schemas ============

class ChapterResponse(BaseModel):
    """章节响应"""
    
    id: str = Field(..., description="章节UUID")
    book_id: str = Field(..., description="书籍UUID")
    item_id: str = Field(..., description="平台章节ID")
    title: str = Field(..., description="章节标题")
    volume_name: Optional[str] = Field(default=None, description="卷名")
    chapter_index: int = Field(..., description="章节索引")
    word_count: Optional[int] = Field(default=None, description="字数")
    content_path: Optional[str] = Field(default=None, description="内容路径")
    download_status: str = Field(default="pending", description="下载状态")
    downloaded_at: Optional[datetime] = Field(default=None, description="下载时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


# ============ 任务相关 Schemas ============

class TaskCreate(BaseModel):
    """创建任务请求"""
    
    book_id: str = Field(..., description="书籍UUID")
    task_type: TaskType = Field(default=TaskType.FULL_DOWNLOAD, description="任务类型")
    start_chapter: int = Field(default=0, description="起始章节索引")


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
    
    class Config:
        from_attributes = True


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


# ============ 存储相关 Schemas ============

class StorageStats(BaseModel):
    """存储统计"""
    
    books_count: int = Field(default=0, description="书籍数量")
    epubs_count: int = Field(default=0, description="EPUB数量")
    total_chapters: int = Field(default=0, description="总章节数")
    books_size_bytes: int = Field(default=0, description="书籍存储大小(字节)")
    epubs_size_bytes: int = Field(default=0, description="EPUB存储大小(字节)")
    total_size_bytes: int = Field(default=0, description="总存储大小(字节)")
    books_size_mb: float = Field(default=0.0, description="书籍存储大小(MB)")
    epubs_size_mb: float = Field(default=0.0, description="EPUB存储大小(MB)")
    total_size_mb: float = Field(default=0.0, description="总存储大小(MB)")


# ============ 配额相关 Schemas ============

class QuotaResponse(BaseModel):
    """配额响应"""
    
    date: str = Field(..., description="日期")
    platform: str = Field(..., description="平台")
    downloaded: int = Field(default=0, description="已下载章节数")
    limit: int = Field(default=200, description="每日限制")
    remaining: int = Field(default=200, description="剩余配额")
    percentage: float = Field(default=0.0, description="使用百分比")


class AllQuotaResponse(BaseModel):
    """所有平台配额响应"""
    
    fanqie: QuotaResponse = Field(..., description="番茄配额")
    qimao: QuotaResponse = Field(..., description="七猫配额")


# ============ 统计相关 Schemas ============

class SystemStats(BaseModel):
    """系统统计"""
    
    total_books: int = Field(default=0, description="总书籍数")
    books_by_platform: Dict[str, int] = Field(default={}, description="按平台统计")
    books_by_status: Dict[str, int] = Field(default={}, description="按状态统计")
    total_chapters: int = Field(default=0, description="总章节数")
    downloaded_chapters: int = Field(default=0, description="已下载章节")
    storage: StorageStats = Field(..., description="存储统计")
    quota: AllQuotaResponse = Field(..., description="配额使用")


# ============ 搜索相关 Schemas ============

class SearchRequest(BaseModel):
    """搜索请求"""
    
    platform: str = Field(..., description="平台 (fanqie/qimao)")
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    page: int = Field(default=0, ge=0, description="页码")
    
    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("fanqie", "qimao"):
            raise ValueError("platform must be 'fanqie' or 'qimao'")
        return v


# ============ 通用响应 ============

class SuccessResponse(BaseModel):
    """成功响应"""
    
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="", description="消息")


class ErrorDetail(BaseModel):
    """错误详情"""
    
    field: Optional[str] = Field(default=None, description="字段名")
    message: str = Field(..., description="错误消息")


class ErrorResponseModel(BaseModel):
    """错误响应"""
    
    success: bool = Field(default=False, description="是否成功")
    error_code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: List[ErrorDetail] = Field(default=[], description="详细信息")


# 更新前向引用
BookDetailResponse.model_rebuild()
