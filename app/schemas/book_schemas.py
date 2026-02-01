"""
书籍相关 Pydantic Schemas

定义书籍相关的请求/响应数据模型
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookCreate(BaseModel):
    """添加书籍请求"""
    
    platform: str = Field(..., description="平台 (fanqie/qimao/biquge)")
    book_id: str = Field(..., description="平台书籍ID")
    download_cover: bool = Field(default=True, description="是否下载封面")
    fetch_chapters: bool = Field(default=True, description="是否获取章节列表")
    
    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("fanqie", "qimao", "biquge"):
            raise ValueError("platform must be 'fanqie', 'qimao' or 'biquge'")
        return v


class BookMetadataUpdateRequest(BaseModel):
    """更新书籍元数据请求"""
    
    title: Optional[str] = Field(default=None, description="书名")
    author: Optional[str] = Field(default=None, description="作者")
    creation_status: Optional[str] = Field(default=None, description="连载状态")
    cover_url: Optional[str] = Field(default=None, description="封面URL")


class BookUpdate(BaseModel):
    """更新书籍请求"""
    
    title: Optional[str] = Field(default=None, description="书名")
    author: Optional[str] = Field(default=None, description="作者")
    download_status: Optional[str] = Field(default=None, description="下载状态")


class BookResponse(BaseModel):
    """书籍响应"""
    
    id: str = Field(..., description="书籍UUID")
    platform: str = Field(..., description="平台")
    book_id: str = Field(..., description="平台书籍ID")
    title: str = Field(..., description="书名")
    author: str = Field(default="", description="作者")
    cover_url: Optional[str] = Field(default=None, description="封面URL")
    cover_path: Optional[str] = Field(default=None, description="封面路径")
    epub_path: Optional[str] = Field(default=None, description="EPUB文件路径")
    txt_path: Optional[str] = Field(default=None, description="TXT文件路径")
    total_chapters: int = Field(default=0, description="总章节数")
    downloaded_chapters: int = Field(default=0, description="已下载章节数")
    word_count: Optional[int] = Field(default=None, description="字数")
    creation_status: Optional[str] = Field(default=None, description="连载状态")
    last_chapter_title: Optional[str] = Field(default=None, description="最新章节标题")
    last_update_time: Optional[datetime] = Field(default=None, description="最后更新时间")
    download_status: str = Field(default="pending", description="下载状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "platform": "fanqie",
                "book_id": "7384886245497586234",
                "title": "第一序列",
                "author": "爱潜水的乌贼",
                "cover_url": "https://example.com/cover.jpg",
                "cover_path": "/data/books/fanqie_7384886245497586234/cover.jpg",
                "total_chapters": 1273,
                "downloaded_chapters": 856,
                "word_count": 3250000,
                "creation_status": "已完结",
                "last_chapter_title": "第一千二百七十三章 新的开始",
                "last_update_time": "2024-01-01T12:00:00",
                "download_status": "partial",
                "created_at": "2024-01-01T10:00:00",
                "updated_at": "2024-01-01T12:30:00"
            }
        }
    )


class BookListResponse(BaseModel):
    """书籍列表响应"""
    
    books: List[BookResponse] = Field(default=[], description="书籍列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=0, description="当前页")
    limit: int = Field(default=20, description="每页数量")
    pages: int = Field(default=0, description="总页数")


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


class BookDetailResponse(BaseModel):
    """书籍详情响应"""
    
    book: BookResponse = Field(..., description="书籍信息")
    chapters: List["ChapterResponse"] = Field(default=[], description="章节列表")
    statistics: BookStatistics = Field(..., description="统计信息")


class BookStatusResponse(BaseModel):
    """书籍状态响应（轻量级，用于轮询进度）"""
    
    book: BookResponse = Field(..., description="书籍信息")
    statistics: BookStatistics = Field(..., description="统计信息")


class SearchRequest(BaseModel):
    """搜索请求"""
    
    platform: str = Field(..., description="平台 (fanqie/qimao/biquge)")
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    page: int = Field(default=0, ge=0, description="页码")
    
    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v):
        if v not in ("fanqie", "qimao", "biquge"):
            raise ValueError("platform must be 'fanqie', 'qimao' or 'biquge'")
        return v


# 前向引用将在 __init__.py 中处理