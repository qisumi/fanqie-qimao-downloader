"""
存储服务模块

提供文件系统操作，包括：
- 章节内容保存/读取
- 封面下载和保存
- 书籍文件删除
- 存储统计

将原有的大型 StorageService 拆分为多个 mixin，按职责划分：
- storage_service_base: 基础类和路径管理
- storage_service_chapters: 章节内容操作
- storage_service_cover: 封面操作
- storage_service_files: 书籍文件管理
- storage_service_stats: 存储统计
"""

import logging

from app.services.storage.storage_service_base import StorageServiceBase
from app.services.storage.storage_service_chapters import StorageServiceChapters
from app.services.storage.storage_service_cover import StorageServiceCover
from app.services.storage.storage_service_files import StorageServiceFiles
from app.services.storage.storage_service_stats import StorageServiceStats

logger = logging.getLogger(__name__)


class StorageService(
    StorageServiceChapters,
    StorageServiceCover,
    StorageServiceFiles,
    StorageServiceStats,
):
    """
    文件存储服务
    
    组合 mixin 的存储服务实现。
    
    目录结构:
    data/
    ├── books/
    │   └── {book_uuid}/
    │       ├── cover.jpg
    │       └── chapters/
    │           ├── 0001.txt
    │           ├── 0002.txt
    │           └── ...
    ├── epubs/
    │   └── {book_title}_{book_id}.epub
    └── database.db
    """


__all__ = [
    "StorageService",
]