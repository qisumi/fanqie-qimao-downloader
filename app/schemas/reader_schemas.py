"""
阅读器相关 Pydantic Schemas

定义阅读器相关的请求/响应数据模型
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReaderTocChapter(BaseModel):
    """阅读器目录章节"""

    id: str = Field(..., description="章节UUID")
    index: int = Field(..., description="章节索引")
    title: str = Field(..., description="章节标题")
    word_count: Optional[int] = Field(default=None, description="字数")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    download_status: Optional[str] = Field(default=None, description="下载状态")


class ReaderTocResponse(BaseModel):
    """阅读器目录响应"""

    book_id: str = Field(..., description="书籍UUID")
    chapters: List[ReaderTocChapter] = Field(default=[], description="章节列表")
    total: int = Field(default=0, description="章节总数")
    page: int = Field(default=1, description="当前页(1-based)")
    limit: int = Field(default=50, description="每页数量")
    pages: int = Field(default=0, description="总页数")
    has_more: bool = Field(default=False, description="是否还有更多章节可加载")


class ChapterContentResponse(BaseModel):
    """章节内容响应"""

    title: str = Field(..., description="章节标题")
    index: int = Field(..., description="章节索引")
    prev_id: Optional[str] = Field(default=None, description="上一章ID")
    next_id: Optional[str] = Field(default=None, description="下一章ID")
    word_count: int = Field(default=0, description="字数")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    status: str = Field(..., description="状态 ready|fetching")
    content_html: Optional[str] = Field(default=None, description="HTML 内容（format=html 时返回）")
    content_text: Optional[str] = Field(default=None, description="纯文本内容（format=text 时返回）")
    message: Optional[str] = Field(default=None, description="状态说明或错误提示")


class ReaderProgressRequest(BaseModel):
    """阅读进度上报"""

    chapter_id: str = Field(..., description="章节UUID")
    offset_px: int = Field(default=0, description="像素偏移")
    percent: float = Field(default=0.0, ge=0, le=100, description="进度百分比 0-100")
    device_id: str = Field(..., description="设备ID")


class ReaderProgressResponse(BaseModel):
    """阅读进度响应"""

    chapter_id: str = Field(..., description="章节UUID")
    offset_px: int = Field(default=0, description="像素偏移")
    percent: float = Field(default=0.0, description="进度百分比")
    device_id: str = Field(..., description="设备ID")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class BookmarkCreateRequest(BaseModel):
    """创建书签请求"""

    chapter_id: str = Field(..., description="章节UUID")
    offset_px: int = Field(default=0, description="像素偏移")
    percent: float = Field(default=0.0, ge=0, le=100, description="进度百分比")
    note: Optional[str] = Field(default=None, description="备注")


class BookmarkResponse(BaseModel):
    """书签响应"""

    id: str = Field(..., description="书签ID")
    chapter_id: str = Field(..., description="章节UUID")
    offset_px: int = Field(default=0, description="像素偏移")
    percent: float = Field(default=0.0, description="进度百分比")
    note: Optional[str] = Field(default=None, description="备注")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class ReadingHistoryResponse(BaseModel):
    """阅读历史项"""

    chapter_id: str = Field(..., description="章节UUID")
    percent: float = Field(default=0.0, description="进度百分比")
    device_id: Optional[str] = Field(default=None, description="设备ID")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class CacheStatusResponse(BaseModel):
    """缓存状态响应"""

    cached_chapters: List[str] = Field(default=[], description="已缓存章节ID")
    cached_at: datetime = Field(..., description="状态生成时间")