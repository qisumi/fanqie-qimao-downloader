"""
章节相关 Pydantic Schemas

定义章节相关的请求/响应数据模型
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    
    model_config = ConfigDict(from_attributes=True)


class ChapterSegmentStatus(BaseModel):
    """章节分段状态（用于热力图展示）"""
    
    start_index: int = Field(..., description="分段起始章节索引")
    end_index: int = Field(..., description="分段结束章节索引")
    total: int = Field(..., description="本段章节总数")
    completed: int = Field(default=0, description="已完成数量")
    pending: int = Field(default=0, description="待下载数量")
    failed: int = Field(default=0, description="失败数量")
    completion_rate: float = Field(default=0.0, description="完成率 0-1")
    first_chapter_title: Optional[str] = Field(default=None, description="第一章标题")
    last_chapter_title: Optional[str] = Field(default=None, description="最后一章标题")


class ChapterStatusSummary(BaseModel):
    """章节状态摘要响应"""
    
    book_id: str = Field(..., description="书籍UUID")
    total_chapters: int = Field(..., description="总章节数")
    completed_chapters: int = Field(default=0, description="已完成章节数")
    pending_chapters: int = Field(default=0, description="待下载章节数")
    failed_chapters: int = Field(default=0, description="失败章节数")
    segment_size: int = Field(default=50, description="每段章节数")
    segments: List[ChapterSegmentStatus] = Field(default=[], description="分段状态列表")