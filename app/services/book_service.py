"""
书籍管理服务聚合模块

将原有的大型 BookService 拆分为多个 mixin，按职责划分：
- book_service_add: 搜索与添加书籍
- book_service_query: 列表/详情/统计
- book_service_update: 元数据刷新、章节增量、状态更新
- book_service_delete: 删除逻辑
"""

import logging

from app.api.fanqie import FanqieAPI
from app.api.qimao import QimaoAPI
from app.services.book_service_add import BookServiceAddMixin
from app.services.book_service_base import BookServiceBase
from app.services.book_service_delete import BookServiceDeleteMixin
from app.services.book_service_query import BookServiceQueryMixin
from app.services.book_service_update import BookServiceUpdateMixin

logger = logging.getLogger(__name__)


class BookService(
    BookServiceAddMixin,
    BookServiceQueryMixin,
    BookServiceUpdateMixin,
    BookServiceDeleteMixin,
):
    """组合 mixin 的书籍管理服务实现。"""


__all__ = [
    "BookService",
    "FanqieAPI",
    "QimaoAPI",
]
