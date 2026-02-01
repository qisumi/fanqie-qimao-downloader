"""
下载服务聚合模块

通过组合多个 mixin（任务管理、下载执行、配额查询）来提供完整的下载能力，
降低单文件体积，便于维护。
"""

import logging

from app.services.download.download_service_base import (
    DownloadError,
    DownloadServiceBase,
    QuotaReachedError,
    TaskCancelledError,
)
from app.services.download.download_service_operations import DownloadOperationMixin
from app.services.download.download_service_quota import DownloadQuotaMixin
from app.services.download.download_service_tasks import DownloadTaskMixin

logger = logging.getLogger(__name__)


class DownloadService(
    DownloadTaskMixin,
    DownloadOperationMixin,
    DownloadQuotaMixin,
):
    """组合 mixin 的下载服务实现。"""


__all__ = [
    "DownloadService",
    "DownloadError",
    "QuotaReachedError",
    "TaskCancelledError",
]
