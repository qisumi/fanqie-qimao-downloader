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

# 从新的模块导入
from app.schemas.book_schemas import (
    BookCreate,
    BookMetadataUpdateRequest,
    BookUpdate,
    BookResponse,
    BookListResponse,
    BookStatistics,
    BookDetailResponse,
    BookStatusResponse,
    SearchRequest,
)

from app.schemas.chapter_schemas import (
    ChapterResponse,
    ChapterSegmentStatus,
    ChapterStatusSummary,
)

from app.schemas.reader_schemas import (
    ReaderTocChapter,
    ReaderTocResponse,
    ChapterContentResponse,
    ReaderProgressRequest,
    ReaderProgressResponse,
    BookmarkCreateRequest,
    BookmarkResponse,
    ReadingHistoryResponse,
    CacheStatusResponse,
)

from app.schemas.task_schemas import (
    DownloadStatus,
    TaskStatus,
    TaskType,
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    DownloadProgress,
)

from app.schemas.user_schemas import (
    UserResponse,
    UserListResponse,
    UserCreateRequest,
    UserUpdateRequest,
)

from app.schemas.common_schemas import (
    StorageStats,
    QuotaResponse,
    AllQuotaResponse,
    SystemStats,
    SuccessResponse,
    ErrorDetail,
    ErrorResponseModel,
)

from app.schemas.websocket_schemas import (
    WebSocketMessageType,
    WSProgressData,
    WSCompletedData,
    WSErrorData,
    WebSocketMessage,
)

# 处理前向引用
BookDetailResponse.model_rebuild()

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
    # 书籍相关
    "BookCreate",
    "BookMetadataUpdateRequest",
    "BookUpdate",
    "BookResponse",
    "BookListResponse",
    "BookStatistics",
    "BookDetailResponse",
    "BookStatusResponse",
    "SearchRequest",
    # 章节相关
    "ChapterResponse",
    "ChapterSegmentStatus",
    "ChapterStatusSummary",
    # 阅读器相关
    "ReaderTocChapter",
    "ReaderTocResponse",
    "ChapterContentResponse",
    "ReaderProgressRequest",
    "ReaderProgressResponse",
    "BookmarkCreateRequest",
    "BookmarkResponse",
    "ReadingHistoryResponse",
    "CacheStatusResponse",
    # 任务相关
    "DownloadStatus",
    "TaskStatus",
    "TaskType",
    "TaskCreate",
    "TaskResponse",
    "TaskListResponse",
    "DownloadProgress",
    # 用户相关
    "UserResponse",
    "UserListResponse",
    "UserCreateRequest",
    "UserUpdateRequest",
    # 通用
    "StorageStats",
    "QuotaResponse",
    "AllQuotaResponse",
    "SystemStats",
    "SuccessResponse",
    "ErrorDetail",
    "ErrorResponseModel",
    # WebSocket 相关
    "WebSocketMessageType",
    "WSProgressData",
    "WSCompletedData",
    "WSErrorData",
    "WebSocketMessage",
]