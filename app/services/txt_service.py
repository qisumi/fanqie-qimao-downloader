"""
TXT生成服务模块

提供将小说章节合并为TXT文件的功能，包括：
- 创建TXT文件结构
- 添加书籍元信息
- 合并章节内容
- 按卷分组组织内容
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.services.storage_service import StorageService
from app.config import settings

logger = logging.getLogger(__name__)


class TXTService:
    """
    TXT生成服务
    
    将书籍章节合并为单个TXT文件，保持原有格式和结构
    
    特性:
    - 自动添加书籍元信息
    - 支持按卷分组
    - 保持章节原始格式
    """
    
    def __init__(
        self,
        db: Optional[Session] = None,
        storage: Optional[StorageService] = None,
    ):
        """
        初始化TXT服务
        
        Args:
            db: 数据库会话（可选，用于查询章节）
            storage: 存储服务实例
        """
        self.db = db
        self.storage = storage or StorageService()
    
    def generate_txt(
        self,
        book: Book,
        chapters: Optional[List[Chapter]] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        生成TXT文件
        
        Args:
            book: 书籍对象
            chapters: 章节列表（如果为None且有db，则自动查询）
            output_path: 输出路径（可选，默认使用标准路径）
        
        Returns:
            生成的TXT文件路径
        """
        # 获取章节列表
        if chapters is None and self.db:
            chapters = self.db.query(Chapter).filter(
                Chapter.book_id == book.id,
                Chapter.download_status == "completed"
            ).order_by(Chapter.chapter_index).all()
        
        if not chapters:
            raise ValueError("No chapters available for TXT generation")
        
        logger.info(f"Generating TXT for book: {book.title} ({len(chapters)} chapters)")
        
        # 构建TXT内容
        txt_content = self._build_txt_content(book, chapters)
        
        # 确定输出路径
        if output_path is None:
            output_path = str(self.storage.get_txt_path(book.title, book.id))
        
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        logger.info(f"TXT generated: {output_path}")
        
        return output_path
    
    def _build_txt_content(self, book: Book, chapters: List[Chapter]) -> str:
        """
        构建TXT文件内容
        
        Args:
            book: 书籍对象
            chapters: 章节列表
        
        Returns:
            完整的TXT内容
        """
        lines = []
        
        # 添加文件头信息
        # lines.extend(self._build_header(book))
        
        # 添加分隔线
        # lines.append("=" * 80)
        # lines.append("")
        
        # 添加章节内容
        lines.extend(self._build_chapters_content(book, chapters))
        
        return "\n".join(lines)
    
    def _build_header(self, book: Book) -> List[str]:
        """构建文件头信息"""
        lines = [
            "=" * 80,
            f"书名：{book.title}",
            f"作者：{book.author or '未知作者'}",
            f"来源：{book.platform}",
            f"平台ID：{book.book_id}",
            f"总章节数：{book.total_chapters}",
        ]
        
        if book.creation_status:
            lines.append(f"状态：{book.creation_status}")
        
        if book.word_count:
            lines.append(f"总字数：{book.word_count:,}")
        
        lines.append(f"生成时间：{self._get_current_time()}")
        lines.append("=" * 80)
        lines.append("")
        
        return lines
    
    def _build_chapters_content(self, book: Book, chapters: List[Chapter]) -> List[str]:
        """构建章节内容"""
        lines = []
        
        # 按卷分组
        current_volume = None
        volume_chapters = {}
        
        for chapter in chapters:
            volume_name = chapter.volume_name or "正文"
            
            if volume_name not in volume_chapters:
                volume_chapters[volume_name] = []
            
            volume_chapters[volume_name].append(chapter)
        
        # 按卷顺序添加内容
        for volume_name, volume_chaps in volume_chapters.items():
            if volume_name != "正文":
                lines.append(f"\n\n【{volume_name}】")
                lines.append("=" * 60)
                lines.append("")
            
            for chapter in volume_chaps:
                lines.extend(self._build_chapter_content(book, chapter))
        
        return lines
    
    def _build_chapter_content(self, book: Book, chapter: Chapter) -> List[str]:
        """构建单个章节内容"""
        lines = [
            f"\n{chapter.title}",
            "-" * 40,
            ""
        ]
        
        # 读取章节内容
        content = ""
        if chapter.content_path:
            content = self.storage.get_chapter_content(chapter.content_path) or ""
        
        # 如果没有内容路径但有章节索引，尝试直接按索引读取
        if not content and hasattr(chapter, 'chapter_index'):
            content = self.storage.get_chapter_content_by_index(
                book.id, chapter.chapter_index
            ) or ""
        
        if not content:
            logger.warning(f"Empty content for chapter: {chapter.title}")
            content = f"[章节内容未下载: {chapter.title}]"
        
        # 添加章节内容（保持原有格式）
        lines.append(content)
        lines.append("")
        
        return lines
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_txt_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取TXT文件信息
        
        Args:
            file_path: TXT文件路径
        
        Returns:
            {
                "title": str,
                "chapter_count": int,
                "file_size": int,
                "file_size_mb": float
            }
        """
        try:
            if not Path(file_path).exists():
                return None
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 尝试从文件名提取书名
            file_name = Path(file_path).stem
            
            return {
                "title": file_name,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
            }
            
        except Exception as e:
            logger.error(f"Failed to read TXT info: {e}")
            return None