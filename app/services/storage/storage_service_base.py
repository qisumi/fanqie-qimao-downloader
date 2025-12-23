"""
存储服务基础模块

提供基础类和路径管理功能
"""

import logging
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class StorageServiceBase:
    """
    存储服务基础类
    
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
    
    def __init__(
        self,
        books_path: Optional[Path] = None,
        epubs_path: Optional[Path] = None,
        txts_path: Optional[Path] = None,
    ):
        """
        初始化存储服务
        
        Args:
            books_path: 书籍存储目录，默认使用配置
            epubs_path: EPUB存储目录，默认使用配置
            txts_path: TXT存储目录，默认使用配置
        """
        self.books_path = books_path or settings.books_path
        self.epubs_path = epubs_path or settings.epubs_path
        self.txts_path = txts_path or settings.txts_path
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.books_path.mkdir(parents=True, exist_ok=True)
        self.epubs_path.mkdir(parents=True, exist_ok=True)
        self.txts_path.mkdir(parents=True, exist_ok=True)
    
    # ============ 路径管理 ============
    
    def get_book_dir(self, book_uuid: str) -> Path:
        """获取书籍目录路径"""
        return self.books_path / book_uuid
    
    def get_chapters_dir(self, book_uuid: str) -> Path:
        """获取章节目录路径"""
        return self.get_book_dir(book_uuid) / "chapters"
    
    def get_cover_path(self, book_uuid: str) -> Path:
        """获取封面文件路径"""
        return self.get_book_dir(book_uuid) / "cover.jpg"
    
    def get_chapter_path(self, book_uuid: str, chapter_index: int) -> Path:
        """获取章节文件路径"""
        return self.get_chapters_dir(book_uuid) / f"{chapter_index:04d}.txt"
    
    def get_epub_path(self, book_title: str, book_uuid: str) -> Path:
        """获取EPUB文件路径"""
        # 清理文件名中的非法字符
        safe_title = self._sanitize_filename(book_title)
        return self.epubs_path / f"{safe_title}_{book_uuid[:8]}.epub"
    
    def get_txt_path(self, book_title: str, book_uuid: str) -> Path:
        """获取TXT文件路径"""
        # 清理文件名中的非法字符
        safe_title = self._sanitize_filename(book_title)
        return self.txts_path / f"{safe_title}_{book_uuid[:8]}.txt"
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 替换Windows文件名非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        # 移除首尾空格和点
        filename = filename.strip('. ')
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename or "untitled"