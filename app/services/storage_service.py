"""
存储服务模块

提供文件系统操作，包括：
- 章节内容保存/读取
- 封面下载和保存
- 书籍文件删除
- 存储统计
"""

import os
import shutil
import logging
import aiofiles
import httpx
from pathlib import Path
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    文件存储服务
    
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
    ):
        """
        初始化存储服务
        
        Args:
            books_path: 书籍存储目录，默认使用配置
            epubs_path: EPUB存储目录，默认使用配置
        """
        self.books_path = books_path or settings.books_path
        self.epubs_path = epubs_path or settings.epubs_path
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.books_path.mkdir(parents=True, exist_ok=True)
        self.epubs_path.mkdir(parents=True, exist_ok=True)
    
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
    
    # ============ 章节内容操作 ============
    
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
    
    # ============ 封面操作 ============
    
    async def download_and_save_cover(
        self,
        book_uuid: str,
        cover_url: str,
        timeout: int = 30,
    ) -> Optional[str]:
        """
        异步下载并保存封面图片
        
        Args:
            book_uuid: 书籍UUID
            cover_url: 封面URL
            timeout: 超时时间(秒)
        
        Returns:
            保存的文件路径（相对路径），失败返回None
        """
        if not cover_url:
            logger.warning(f"Empty cover URL for book {book_uuid}")
            return None
        
        book_dir = self.get_book_dir(book_uuid)
        book_dir.mkdir(parents=True, exist_ok=True)
        
        cover_path = self.get_cover_path(book_uuid)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(cover_url)
                response.raise_for_status()
                
                # 保存图片
                async with aiofiles.open(cover_path, "wb") as f:
                    await f.write(response.content)
                
                logger.info(f"Downloaded cover for book {book_uuid}")
                return str(cover_path.relative_to(self.books_path))
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to download cover for book {book_uuid}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading cover: {e}")
            return None
    
    def save_cover(
        self,
        book_uuid: str,
        image_data: bytes,
    ) -> str:
        """
        同步保存封面图片数据
        
        Args:
            book_uuid: 书籍UUID
            image_data: 图片二进制数据
        
        Returns:
            保存的文件路径（相对路径）
        """
        book_dir = self.get_book_dir(book_uuid)
        book_dir.mkdir(parents=True, exist_ok=True)
        
        cover_path = self.get_cover_path(book_uuid)
        cover_path.write_bytes(image_data)
        
        logger.debug(f"Saved cover for book {book_uuid}")
        
        return str(cover_path.relative_to(self.books_path))
    
    def cover_exists(self, book_uuid: str) -> bool:
        """检查封面是否存在"""
        return self.get_cover_path(book_uuid).exists()
    
    def get_cover_full_path(self, book_uuid: str) -> Optional[Path]:
        """获取封面完整路径，如果存在"""
        cover_path = self.get_cover_path(book_uuid)
        return cover_path if cover_path.exists() else None
    
    # ============ 书籍文件管理 ============
    
    def delete_book_files(self, book_uuid: str) -> bool:
        """
        删除书籍所有文件
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            是否成功删除
        """
        book_dir = self.get_book_dir(book_uuid)
        
        if not book_dir.exists():
            logger.warning(f"Book directory not found: {book_dir}")
            return False
        
        try:
            shutil.rmtree(book_dir)
            logger.info(f"Deleted book files for {book_uuid}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete book files for {book_uuid}: {e}")
            return False
    
    def delete_epub(self, book_title: str, book_uuid: str) -> bool:
        """
        删除EPUB文件
        
        Args:
            book_title: 书籍标题
            book_uuid: 书籍UUID
        
        Returns:
            是否成功删除
        """
        epub_path = self.get_epub_path(book_title, book_uuid)
        
        if not epub_path.exists():
            logger.warning(f"EPUB file not found: {epub_path}")
            return False
        
        try:
            epub_path.unlink()
            logger.info(f"Deleted EPUB: {epub_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete EPUB: {e}")
            return False
    
    def epub_exists(self, book_title: str, book_uuid: str) -> bool:
        """检查EPUB是否存在"""
        return self.get_epub_path(book_title, book_uuid).exists()
    
    # ============ 存储统计 ============
    
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
        
        total_size = books_size + epubs_size
        
        return {
            "books_count": books_count,
            "epubs_count": epubs_count,
            "total_chapters": total_chapters,
            "books_size_bytes": books_size,
            "epubs_size_bytes": epubs_size,
            "total_size_bytes": total_size,
            "books_size_mb": round(books_size / (1024 * 1024), 2),
            "epubs_size_mb": round(epubs_size / (1024 * 1024), 2),
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
