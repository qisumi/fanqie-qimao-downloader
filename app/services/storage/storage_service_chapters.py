"""
存储服务章节内容操作模块

提供章节内容的保存和读取功能
"""

import logging
import aiofiles
from pathlib import Path
from typing import Optional

from app.services.storage.storage_service_base import StorageServiceBase

logger = logging.getLogger(__name__)


class StorageServiceChapters(StorageServiceBase):
    """章节内容操作服务"""
    
    def save_chapter_content(
        self,
        book_uuid: str,
        chapter_index: int,
        content: str,
    ) -> str:
        """
        同步保存章节内容
        
        Args:
            book_uuid: 书籍UUID
            chapter_index: 章节索引
            content: 章节内容
        
        Returns:
            保存的文件路径（相对路径）
        """
        chapters_dir = self.get_chapters_dir(book_uuid)
        chapters_dir.mkdir(parents=True, exist_ok=True)
        
        chapter_path = self.get_chapter_path(book_uuid, chapter_index)
        chapter_path.write_text(content, encoding="utf-8")
        
        logger.debug(f"Saved chapter {chapter_index} for book {book_uuid}")
        
        # 返回相对路径
        return str(chapter_path.relative_to(self.books_path))
    
    async def save_chapter_content_async(
        self,
        book_uuid: str,
        chapter_index: int,
        content: str,
    ) -> str:
        """
        异步保存章节内容
        
        Args:
            book_uuid: 书籍UUID
            chapter_index: 章节索引
            content: 章节内容
        
        Returns:
            保存的文件路径（相对路径）
        """
        chapters_dir = self.get_chapters_dir(book_uuid)
        chapters_dir.mkdir(parents=True, exist_ok=True)
        
        chapter_path = self.get_chapter_path(book_uuid, chapter_index)
        
        async with aiofiles.open(chapter_path, "w", encoding="utf-8") as f:
            await f.write(content)
        
        logger.debug(f"Saved chapter {chapter_index} for book {book_uuid}")
        
        return str(chapter_path.relative_to(self.books_path))
    
    def get_chapter_content(self, content_path: str) -> Optional[str]:
        """
        同步读取章节内容
        
        Args:
            content_path: 章节文件路径（相对路径或绝对路径）
        
        Returns:
            章节内容，如果文件不存在返回None
        """
        import os
        
        # 处理相对路径
        if not os.path.isabs(content_path):
            full_path = self.books_path / content_path
        else:
            full_path = Path(content_path)
        
        if not full_path.exists():
            logger.warning(f"Chapter file not found: {full_path}")
            return None
        
        return full_path.read_text(encoding="utf-8")
    
    async def get_chapter_content_async(self, content_path: str) -> Optional[str]:
        """
        异步读取章节内容
        
        Args:
            content_path: 章节文件路径（相对路径或绝对路径）
        
        Returns:
            章节内容，如果文件不存在返回None
        """
        import os
        
        # 处理相对路径
        if not os.path.isabs(content_path):
            full_path = self.books_path / content_path
        else:
            full_path = Path(content_path)
        
        if not full_path.exists():
            logger.warning(f"Chapter file not found: {full_path}")
            return None
        
        async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
            return await f.read()
    
    def get_chapter_content_by_index(
        self,
        book_uuid: str,
        chapter_index: int,
    ) -> Optional[str]:
        """
        根据索引读取章节内容
        
        Args:
            book_uuid: 书籍UUID
            chapter_index: 章节索引
        
        Returns:
            章节内容，如果文件不存在返回None
        """
        chapter_path = self.get_chapter_path(book_uuid, chapter_index)
        
        if not chapter_path.exists():
            return None
        
        return chapter_path.read_text(encoding="utf-8")