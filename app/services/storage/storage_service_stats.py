"""
存储服务统计模块

提供存储统计信息查询功能
"""

import logging
from pathlib import Path
from typing import Dict, Any

from app.services.storage.storage_service_base import StorageServiceBase

logger = logging.getLogger(__name__)


class StorageServiceStats(StorageServiceBase):
    """存储统计服务"""
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            {
                "books_count": 10,
                "epubs_count": 5,
                "total_chapters": 1500,
                "books_size_bytes": 52428800,
                "epubs_size_bytes": 20971520,
                "total_size_bytes": 73400320,
                "books_size_mb": 50.0,
                "epubs_size_mb": 20.0,
                "total_size_mb": 70.0
            }
        """
        books_count = 0
        total_chapters = 0
        books_size = 0
        
        # 统计书籍目录
        if self.books_path.exists():
            for book_dir in self.books_path.iterdir():
                if book_dir.is_dir():
                    books_count += 1
                    chapters_dir = book_dir / "chapters"
                    if chapters_dir.exists():
                        chapter_files = list(chapters_dir.glob("*.txt"))
                        total_chapters += len(chapter_files)
                    
                    # 计算目录大小
                    for file in book_dir.rglob("*"):
                        if file.is_file():
                            books_size += file.stat().st_size
        
        # 统计EPUB目录
        epubs_count = 0
        epubs_size = 0
        
        if self.epubs_path.exists():
            for epub_file in self.epubs_path.glob("*.epub"):
                if epub_file.is_file():
                    epubs_count += 1
                    epubs_size += epub_file.stat().st_size
        
        # 统计TXT目录
        txts_count = 0
        txts_size = 0
        
        if self.txts_path.exists():
            for txt_file in self.txts_path.glob("*.txt"):
                if txt_file.is_file():
                    txts_count += 1
                    txts_size += txt_file.stat().st_size
        
        total_size = books_size + epubs_size + txts_size
        
        return {
            "books_count": books_count,
            "epubs_count": epubs_count,
            "txts_count": txts_count,
            "total_chapters": total_chapters,
            "books_size_bytes": books_size,
            "epubs_size_bytes": epubs_size,
            "txts_size_bytes": txts_size,
            "total_size_bytes": total_size,
            "books_size_mb": round(books_size / (1024 * 1024), 2),
            "epubs_size_mb": round(epubs_size / (1024 * 1024), 2),
            "txts_size_mb": round(txts_size / (1024 * 1024), 2),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
    
    def get_book_stats(self, book_uuid: str) -> Dict[str, Any]:
        """
        获取单本书的存储统计
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            {
                "exists": True,
                "has_cover": True,
                "chapter_count": 125,
                "size_bytes": 1048576,
                "size_mb": 1.0
            }
        """
        book_dir = self.get_book_dir(book_uuid)
        
        if not book_dir.exists():
            return {
                "exists": False,
                "has_cover": False,
                "chapter_count": 0,
                "size_bytes": 0,
                "size_mb": 0.0,
            }
        
        has_cover = self.cover_exists(book_uuid)
        
        chapters_dir = self.get_chapters_dir(book_uuid)
        chapter_count = 0
        if chapters_dir.exists():
            chapter_count = len(list(chapters_dir.glob("*.txt")))
        
        total_size = 0
        for file in book_dir.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        
        return {
            "exists": True,
            "has_cover": has_cover,
            "chapter_count": chapter_count,
            "size_bytes": total_size,
            "size_mb": round(total_size / (1024 * 1024), 2),
        }
    
    def get_downloaded_chapter_indices(self, book_uuid: str) -> set:
        """
        获取已下载的章节索引集合
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            已下载的章节索引集合
        """
        chapters_dir = self.get_chapters_dir(book_uuid)
        
        if not chapters_dir.exists():
            return set()
        
        indices = set()
        for chapter_file in chapters_dir.glob("*.txt"):
            try:
                # 从文件名提取索引 (e.g., "0001.txt" -> 1)
                index = int(chapter_file.stem)
                indices.add(index)
            except ValueError:
                continue
        
        return indices