"""
EPUB生成服务模块

使用ebooklib生成EPUB3格式电子书，包括：
- 创建EPUB结构
- 添加元数据（标题、作者、语言）
- 添加封面图片
- 添加章节内容（HTML格式）
- 生成目录（TOC）
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from ebooklib import epub
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.services.storage_service import StorageService
from app.config import settings

logger = logging.getLogger(__name__)


class EPUBService:
    """
    EPUB生成服务
    
    使用ebooklib库生成符合EPUB3标准的电子书文件
    
    特性:
    - 自动生成封面页
    - 支持卷分组目录
    - 内容HTML格式化
    - 元数据完整（书名、作者、语言等）
    """
    
    # CSS样式
    DEFAULT_CSS = """
    @namespace epub "http://www.idpf.org/2007/ops";
    
    body {
        font-family: "Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
        font-size: 1em;
        line-height: 1.8;
        margin: 1em;
        text-align: justify;
    }
    
    h1 {
        font-size: 1.5em;
        font-weight: bold;
        margin: 1em 0 0.5em 0;
        text-align: center;
    }
    
    h2 {
        font-size: 1.3em;
        font-weight: bold;
        margin: 1em 0 0.5em 0;
        text-align: center;
        color: #333;
    }
    
    p {
        margin: 0.5em 0;
        text-indent: 2em;
    }
    
    .cover {
        text-align: center;
        padding: 0;
        margin: 0;
    }
    
    .cover img {
        max-width: 100%;
        max-height: 100%;
    }
    
    .volume-title {
        font-size: 1.4em;
        font-weight: bold;
        margin: 2em 0 1em 0;
        text-align: center;
        color: #666;
        border-bottom: 1px solid #ddd;
        padding-bottom: 0.5em;
    }
    
    .chapter-title {
        font-size: 1.2em;
        font-weight: bold;
        margin: 1.5em 0 1em 0;
        text-align: center;
    }
    
    .info {
        text-align: center;
        color: #666;
        margin: 1em 0;
    }
    """
    
    def __init__(
        self,
        db: Optional[Session] = None,
        storage: Optional[StorageService] = None,
    ):
        """
        初始化EPUB服务
        
        Args:
            db: 数据库会话（可选，用于查询章节）
            storage: 存储服务实例
        """
        self.db = db
        self.storage = storage or StorageService()
    
    def generate_epub(
        self,
        book: Book,
        chapters: Optional[List[Chapter]] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        生成EPUB文件
        
        Args:
            book: 书籍对象
            chapters: 章节列表（如果为None且有db，则自动查询）
            output_path: 输出路径（可选，默认使用标准路径）
        
        Returns:
            生成的EPUB文件路径
        """
        # 获取章节列表
        if chapters is None and self.db:
            chapters = self.db.query(Chapter).filter(
                Chapter.book_id == book.id,
                Chapter.download_status == "completed"
            ).order_by(Chapter.chapter_index).all()
        
        if not chapters:
            raise ValueError("No chapters available for EPUB generation")
        
        logger.info(f"Generating EPUB for book: {book.title} ({len(chapters)} chapters)")
        
        # 创建EPUB书籍对象
        epub_book = epub.EpubBook()
        
        # 设置元数据
        self._set_metadata(epub_book, book)
        
        # 添加CSS样式
        css_item = self._add_css(epub_book)
        
        # 添加封面
        cover_item = self._add_cover(epub_book, book)
        
        # 添加章节内容
        chapter_items = self._add_chapters(epub_book, book, chapters, css_item)
        
        # 生成目录和脊柱
        self._build_toc_and_spine(epub_book, chapter_items, cover_item, chapters)
        
        # 添加导航
        epub_book.add_item(epub.EpubNcx())
        epub_book.add_item(epub.EpubNav())
        
        # 确定输出路径
        if output_path is None:
            output_path = str(self.storage.get_epub_path(book.title, book.id))
        
        # 确保目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        epub.write_epub(output_path, epub_book, {})
        
        logger.info(f"EPUB generated: {output_path}")
        
        return output_path
    
    def _set_metadata(self, epub_book: epub.EpubBook, book: Book):
        """设置EPUB元数据"""
        # 唯一标识符
        epub_book.set_identifier(f"fanqie-qimao-{book.id}")
        
        # 标题
        epub_book.set_title(book.title)
        
        # 语言
        epub_book.set_language(settings.epub_language)
        
        # 作者
        if book.author:
            epub_book.add_author(book.author)
        
        # 出版商
        epub_book.add_metadata('DC', 'publisher', settings.epub_publisher)
        
        # 来源
        epub_book.add_metadata('DC', 'source', f"{book.platform}:{book.book_id}")
        
        # 描述
        description = f"从{book.platform}平台下载，共{book.total_chapters}章"
        if book.creation_status:
            description += f"，{book.creation_status}"
        epub_book.add_metadata('DC', 'description', description)
    
    def _add_css(self, epub_book: epub.EpubBook) -> epub.EpubItem:
        """添加CSS样式"""
        css_item = epub.EpubItem(
            uid="style",
            file_name="style/main.css",
            media_type="text/css",
            content=self.DEFAULT_CSS.encode('utf-8')
        )
        epub_book.add_item(css_item)
        return css_item
    
    def _add_cover(
        self,
        epub_book: epub.EpubBook,
        book: Book,
    ) -> Optional[epub.EpubHtml]:
        """添加封面"""
        cover_path = self.storage.get_cover_full_path(book.id)
        
        if cover_path is None or not cover_path.exists():
            logger.warning(f"Cover not found for book: {book.title}")
            return None
        
        try:
            # 读取封面图片
            cover_data = cover_path.read_bytes()
            
            # 确定图片类型
            if cover_path.suffix.lower() in ('.jpg', '.jpeg'):
                media_type = "image/jpeg"
            elif cover_path.suffix.lower() == '.png':
                media_type = "image/png"
            else:
                media_type = "image/jpeg"
            
            # 添加封面图片
            cover_image = epub.EpubItem(
                uid="cover-image",
                file_name="images/cover.jpg",
                media_type=media_type,
                content=cover_data
            )
            epub_book.add_item(cover_image)
            
            # 设置封面
            epub_book.set_cover("images/cover.jpg", cover_data)
            
            # 创建封面页
            cover_html = epub.EpubHtml(
                uid="cover",
                file_name="cover.xhtml",
                title="封面"
            )
            cover_content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>封面</title>
    <style>
        body {{ margin: 0; padding: 0; text-align: center; }}
        img {{ max-width: 100%; max-height: 100%; }}
    </style>
</head>
<body>
    <div class="cover">
        <img src="images/cover.jpg" alt="{book.title}" />
    </div>
</body>
</html>'''
            cover_html.set_content(cover_content.encode('utf-8'))
            epub_book.add_item(cover_html)
            
            logger.debug(f"Added cover for book: {book.title}")
            return cover_html
            
        except Exception as e:
            logger.error(f"Failed to add cover: {e}")
            return None
    
    def _add_chapters(
        self,
        epub_book: epub.EpubBook,
        book: Book,
        chapters: List[Chapter],
        css_item: epub.EpubItem,
    ) -> List[epub.EpubHtml]:
        """
        添加所有章节
        
        Returns:
            章节EpubHtml对象列表
        """
        chapter_items = []
        
        for chapter in chapters:
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
                # 使用占位内容，而不是跳过
                content = f"[章节内容未下载: {chapter.title}]"
            
            # 创建章节HTML
            chapter_html = self._create_chapter_html(
                chapter,
                content,
                css_item
            )
            
            epub_book.add_item(chapter_html)
            chapter_items.append(chapter_html)
        
        return chapter_items
    
    def _create_chapter_html(
        self,
        chapter: Chapter,
        content: str,
        css_item: epub.EpubItem,
    ) -> epub.EpubHtml:
        """创建章节HTML内容"""
        # 格式化内容为HTML段落
        html_content = self._format_content_to_html(content)
        
        # 创建章节
        chapter_html = epub.EpubHtml(
            uid=f"chapter_{chapter.chapter_index}",
            file_name=f"chapter_{chapter.chapter_index:04d}.xhtml",
            title=chapter.title
        )
        
        # 构建完整HTML - 使用 set_content 方法或直接设置字节
        html_str = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{self._escape_html(chapter.title)}</title>
    <link rel="stylesheet" type="text/css" href="style/main.css"/>
</head>
<body>
    <h1 class="chapter-title">{self._escape_html(chapter.title)}</h1>
    {html_content}
</body>
</html>'''
        
        # ebooklib 需要字符串或字节，使用 set_content 更安全
        chapter_html.set_content(html_str.encode('utf-8'))
        
        # 添加CSS引用
        chapter_html.add_item(css_item)
        
        return chapter_html
    
    def _format_content_to_html(self, content: str) -> str:
        """
        将纯文本内容格式化为HTML段落
        
        Args:
            content: 纯文本内容
        
        Returns:
            HTML格式的内容
        """
        if not content:
            return ""
        
        # 转义HTML特殊字符
        content = self._escape_html(content)
        
        # 按换行符分割段落
        paragraphs = content.split('\n')
        
        # 过滤空行并包装为<p>标签
        html_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p:
                html_paragraphs.append(f'    <p>{p}</p>')
        
        return '\n'.join(html_paragraphs)
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))
    
    def _build_toc_and_spine(
        self,
        epub_book: epub.EpubBook,
        chapter_items: List[epub.EpubHtml],
        cover_item: Optional[epub.EpubHtml],
        chapters: List[Chapter],
    ):
        """
        构建目录和脊柱
        
        支持按卷分组的嵌套目录结构
        """
        # 构建脊柱（阅读顺序）
        spine = ['nav']
        if cover_item:
            spine.insert(0, cover_item)
        spine.extend(chapter_items)
        epub_book.spine = spine
        
        # 构建目录
        toc = []
        
        # 按卷分组
        current_volume = None
        volume_sections: Dict[str, List] = {}
        volume_order = []
        
        for chapter_html, chapter in zip(chapter_items, chapters):
            volume_name = chapter.volume_name or ""
            
            if volume_name:
                if volume_name not in volume_sections:
                    volume_sections[volume_name] = []
                    volume_order.append(volume_name)
                volume_sections[volume_name].append(
                    epub.Link(chapter_html.file_name, chapter.title, chapter_html.id)
                )
            else:
                # 无卷名的章节直接添加到顶层
                toc.append(
                    epub.Link(chapter_html.file_name, chapter.title, chapter_html.id)
                )
        
        # 将卷章节添加到目录
        for volume_name in volume_order:
            volume_links = volume_sections[volume_name]
            if volume_links:
                # 创建卷分组
                volume_section = (
                    epub.Section(volume_name),
                    volume_links
                )
                toc.append(volume_section)
        
        epub_book.toc = toc
    
    def validate_epub(self, file_path: str) -> bool:
        """
        验证EPUB文件是否有效
        
        Args:
            file_path: EPUB文件路径
        
        Returns:
            是否有效
        """
        try:
            epub_book = epub.read_epub(file_path)
            # 基本验证：检查是否能读取
            return epub_book is not None
        except Exception as e:
            logger.error(f"EPUB validation failed: {e}")
            return False
    
    def get_epub_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取EPUB文件信息
        
        Args:
            file_path: EPUB文件路径
        
        Returns:
            {
                "title": str,
                "author": str,
                "language": str,
                "chapter_count": int,
                "file_size": int
            }
        """
        try:
            epub_book = epub.read_epub(file_path)
            
            # 获取元数据
            title = epub_book.get_metadata('DC', 'title')
            author = epub_book.get_metadata('DC', 'creator')
            language = epub_book.get_metadata('DC', 'language')
            
            # 统计章节数
            chapter_count = len([
                item for item in epub_book.get_items()
                if isinstance(item, epub.EpubHtml) and 'chapter_' in item.id
            ])
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            return {
                "title": title[0][0] if title else "",
                "author": author[0][0] if author else "",
                "language": language[0][0] if language else "",
                "chapter_count": chapter_count,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
            }
            
        except Exception as e:
            logger.error(f"Failed to read EPUB info: {e}")
            return None
