"""
通用 Pydantic Schemas

定义存储、配额、统计和通用响应相关的数据模型
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


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
    biquge: QuotaResponse = Field(..., description="笔趣阁配额")


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
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_books": 25,
                "books_by_platform": {
                    "fanqie": 15,
                    "qimao": 10
                },
                "books_by_status": {
                    "completed": 10,
                    "partial": 8,
                    "downloading": 3,
                    "pending": 4
                },
                "total_chapters": 30000,
                "downloaded_chapters": 25000,
                "storage": {
                    "books_count": 25,
                    "epubs_count": 10,
                    "total_chapters": 25000,
                    "total_size_mb": 1250.5
                },
                "quota": {
                    "fanqie": {
                        "date": "2024-01-01",
                        "platform": "fanqie",
                        "downloaded": 5000000,
                        "limit": 20000000,
                        "remaining": 15000000,
                        "percentage": 25.0
                    },
                    "qimao": {
                        "date": "2024-01-01",
                        "platform": "qimao",
                        "downloaded": 3000000,
                        "limit": 20000000,
                        "remaining": 17000000,
                        "percentage": 15.0
                    }
                }
            }
        }
    )


# ============ 通用响应 ============

class SuccessResponse(BaseModel):
    """成功响应"""
    
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(default="", description="消息")


class ErrorDetail(BaseModel):
    """错误详情"""
    
    field: str = Field(default=None, description="字段名")
    message: str = Field(..., description="错误消息")


class ErrorResponseModel(BaseModel):
    """错误响应"""
    
    success: bool = Field(default=False, description="是否成功")
    error_code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: List[ErrorDetail] = Field(default=[], description="详细信息")