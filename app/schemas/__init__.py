"""Pydantic schemas 数据模型

定义请求/响应的数据验证模型
"""

from app.schemas.api_responses import (
    # 枚举类型
    CreationStatus,
    ContentType,
    PlatformType,
    # 搜索相关
    BookSearchResult,
    SearchResponse,
    # 书籍详情
    BookDetail,
    # 章节相关
    ChapterInfo,
    VolumeInfo,
    ChapterListResponse,
    # 章节内容
    TextContent,
    AudioContent,
    ChapterContent,
    # 配额相关
    QuotaUsage,
    # 通用响应
    APIResponse,
    ErrorResponse,
)

from app.schemas.service_schemas import (
    # 枚举类型
    DownloadStatus,
    TaskStatus,
    TaskType,
    # 书籍相关
    BookCreate,
    BookUpdate,
    BookResponse,
    BookListResponse,
    BookDetailResponse,
    BookStatistics,
    # 章节相关
    ChapterResponse,
    # 任务相关
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    DownloadProgress,
    # 存储相关
    StorageStats,
    # 配额相关
    QuotaResponse,
    AllQuotaResponse,
    # 统计相关
    SystemStats,
    # 搜索相关
    SearchRequest,
    # 通用响应
    SuccessResponse,
    ErrorDetail,
    ErrorResponseModel,
)

__all__ = [
    # 枚举类型
    "CreationStatus",
    "ContentType",
    "PlatformType",
    # 搜索相关
    "BookSearchResult",
    "SearchResponse",
    # 书籍详情
    "BookDetail",
    # 章节相关
    "ChapterInfo",
    "VolumeInfo",
    "ChapterListResponse",
    # 章节内容
    "TextContent",
    "AudioContent",
    "ChapterContent",
    # 配额相关
    "QuotaUsage",
    # 通用响应
    "APIResponse",
    "ErrorResponse",
]