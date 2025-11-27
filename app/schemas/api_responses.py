"""
API 响应数据模型

定义 Rain API V3 响应的 Pydantic 模型，用于数据验证和类型提示
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# ============ 枚举类型 ============

class CreationStatus(str, Enum):
    """连载状态"""
    ONGOING = "连载中"
    COMPLETED = "已完结"


class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"
    AUDIO = "audio"


class PlatformType(str, Enum):
    """平台类型"""
    FANQIE = "fanqie"
    QIMAO = "qimao"


# ============ 搜索相关模型 ============

class BookSearchResult(BaseModel):
    """搜索结果中的书籍信息"""
    
    book_id: str = Field(..., description="书籍ID")
    book_name: str = Field(..., description="书名")
    author: str = Field(default="", description="作者")
    cover_url: str = Field(default="", description="封面URL")
    abstract: str = Field(default="", description="简介")
    word_count: int = Field(default=0, description="字数")
    creation_status: str = Field(default="连载中", description="连载状态")
    creation_status_code: int = Field(default=0, description="连载状态码 (0=连载, 1=完结)")
    score: float = Field(default=0.0, description="评分")
    tags: Union[List[str], str] = Field(default=[], description="标签")
    sub_info: str = Field(default="", description="附加信息")
    gender: int = Field(default=0, description="性别分类 (1=男频, 2=女频)")
    
    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """统一标签格式为列表"""
        if isinstance(v, str):
            # 处理七猫的标签字符串格式 "玄幻・热血・成长"
            if v:
                return [tag.strip() for tag in v.replace("・", ",").replace("、", ",").split(",") if tag.strip()]
            return []
        return v or []
    
    class Config:
        extra = "ignore"


class SearchResponse(BaseModel):
    """搜索响应"""
    
    books: List[BookSearchResult] = Field(default=[], description="书籍列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=0, description="当前页码")
    audio_mode: str = Field(default="none", description="音频模式")
    
    class Config:
        extra = "ignore"


# ============ 书籍详情模型 ============

class BookDetail(BaseModel):
    """书籍详情"""
    
    book_id: str = Field(..., description="书籍ID")
    book_name: str = Field(..., description="书名")
    author: str = Field(default="", description="作者")
    cover_url: str = Field(default="", description="封面URL")
    abstract: str = Field(default="", description="简介")
    word_count: int = Field(default=0, description="字数")
    category: str = Field(default="", description="分类")
    creation_status: str = Field(default="连载中", description="连载状态")
    creation_status_code: int = Field(default=0, description="连载状态码")
    score: float = Field(default=0.0, description="评分")
    last_chapter_title: str = Field(default="", description="最新章节标题")
    last_update_time: str = Field(default="", description="最后更新时间")
    last_update_timestamp: int = Field(default=0, description="最后更新时间戳")
    tags: Union[List[str], str] = Field(default=[], description="标签")
    roles: List[str] = Field(default=[], description="主要角色")
    gender: int = Field(default=0, description="性别分类")
    source: str = Field(default="", description="来源 (七猫专用)")
    
    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """统一标签格式为列表"""
        if isinstance(v, str):
            if v:
                return [tag.strip() for tag in v.replace("・", ",").replace("、", ",").split(",") if tag.strip()]
            return []
        return v or []
    
    class Config:
        extra = "ignore"


# ============ 章节相关模型 ============

class ChapterInfo(BaseModel):
    """章节信息"""
    
    item_id: str = Field(..., alias="item_id", description="章节ID (番茄)")
    chapter_id: Optional[str] = Field(default=None, description="章节ID (七猫)")
    title: str = Field(default="", description="章节标题")
    volume_name: str = Field(default="", description="卷名")
    chapter_index: int = Field(default=0, description="章节序号")
    word_count: int = Field(default=0, description="章节字数")
    update_time: str = Field(default="", description="更新时间")
    update_timestamp: int = Field(default=0, description="更新时间戳")
    
    def get_id(self) -> str:
        """获取章节ID (兼容两个平台)"""
        return self.chapter_id or self.item_id
    
    class Config:
        extra = "ignore"
        populate_by_name = True


class VolumeInfo(BaseModel):
    """卷信息"""
    
    name: str = Field(..., description="卷名")
    chapter_count: int = Field(default=0, description="章节数")
    
    class Config:
        extra = "ignore"


class ChapterListResponse(BaseModel):
    """章节列表响应"""
    
    book_id: str = Field(..., description="书籍ID")
    total_chapters: int = Field(default=0, description="总章节数")
    chapters: List[ChapterInfo] = Field(default=[], description="章节列表")
    volumes: List[VolumeInfo] = Field(default=[], description="卷列表")
    
    class Config:
        extra = "ignore"


# ============ 章节内容模型 ============

class TextContent(BaseModel):
    """文本内容"""
    
    type: str = Field(default="text", description="内容类型")
    content: str = Field(..., description="章节正文")
    chapter_id: str = Field(..., description="章节ID")
    
    class Config:
        extra = "ignore"


class AudioContent(BaseModel):
    """音频内容"""
    
    type: str = Field(default="audio", description="内容类型")
    audio_url: str = Field(..., description="音频URL")
    duration: int = Field(default=0, description="音频时长(秒)")
    chapter_id: str = Field(..., description="章节ID")
    tone_changed: bool = Field(default=False, description="音色是否被自动切换")
    
    class Config:
        extra = "ignore"


ChapterContent = Union[TextContent, AudioContent]


# ============ 配额相关模型 ============

class QuotaUsage(BaseModel):
    """配额使用情况"""
    
    date: str = Field(..., description="日期")
    platform: str = Field(..., description="平台")
    downloaded: int = Field(default=0, description="已下载章节数")
    limit: int = Field(default=200, description="每日限制")
    remaining: int = Field(default=200, description="剩余配额")
    percentage: float = Field(default=0.0, description="使用百分比")
    
    class Config:
        extra = "ignore"


# ============ 通用响应模型 ============

class APIResponse(BaseModel):
    """通用API响应"""
    
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="", description="消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="数据")
    
    class Config:
        extra = "ignore"


class ErrorResponse(BaseModel):
    """错误响应"""
    
    success: bool = Field(default=False, description="是否成功")
    error_code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细信息")
    
    class Config:
        extra = "ignore"
