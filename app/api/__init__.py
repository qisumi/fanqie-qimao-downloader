"""API客户端模块

提供番茄/七猫/笔趣阁的 API 封装
"""

from app.api.base import (
    RainAPIClient,
    Platform,
    APIType,
    AudioMode,
    # 异常类
    APIError,
    QuotaExceededError,
    NetworkError,
    RateLimitError,
    InvalidResponseError,
    BookNotFoundError,
    ChapterNotFoundError,
)
from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.api.biquge import BiqugeAPI
from app.api.utils import (
    clean_content,
    format_timestamp,
    parse_datetime,
    safe_float,
    safe_int,
    strip_html,
)

__all__ = [
    # 客户端类
    "RainAPIClient",
    "FanqieAPI",
    "QimaoAPI",
    "BiqugeAPI",
    # 枚举类型
    "Platform",
    "APIType",
    "AudioMode",
    # 异常类
    "APIError",
    "QuotaExceededError",
    "NetworkError",
    "RateLimitError",
    "InvalidResponseError",
    "BookNotFoundError",
    "ChapterNotFoundError",
    # 工具函数
    "safe_int",
    "safe_float",
    "format_timestamp",
    "parse_datetime",
    "strip_html",
    "clean_content",
]
