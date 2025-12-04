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
]
