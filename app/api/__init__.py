"""API客户端模块

提供 Rain API V3 的番茄/七猫小说 API 封装
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

__all__ = [
    # 客户端类
    "RainAPIClient",
    "FanqieAPI",
    "QimaoAPI",
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
]