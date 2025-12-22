import re
import uuid
import logging
import io
from datetime import datetime, timezone
from typing import List, Tuple, Optional

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from app.models.book import Book
from app.models.chapter import Chapter
from app.services.book_service_base import BookServiceBase

logger = logging.getLogger(__name__)

class BookServiceUploadMixin(BookServiceBase):
    """
    书籍上传相关逻辑
    """

    async def upload_txt_book(
        self,
        title: str,
        author: str,
        content: str,
        regex_pattern: str,
    ) -> Book:
        """
        上传TXT书籍并解析
        """
        # Create book record
        book_uuid = str(uuid.uuid4())
        # Use a fake book_id or same as uuid for local books
        platform_book_id = f"local_{book_uuid[:8]}"
        
        book = Book(
            id=book_uuid,
            platform="local",
            book_id=platform_book_id,
            title=title,
            author=author,
            word_count=len(content),
            creation_status="已完结", # Assume completed for uploaded files
            download_status="completed", # Local files are already "downloaded"
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Parse chapters
        chapters_data = self._parse_txt_chapters(content, regex_pattern, title)
        book.total_chapters = len(chapters_data)
        if chapters_data:
            book.last_chapter_title = chapters_data[-1][0]
        
        # Save book to DB first to ensure it exists
        self.db.add(book)
        self.db.commit() # Commit to get the ID usable if needed, though UUID is pre-generated
        
        # Save chapters
        for index, (ch_title, ch_content) in enumerate(chapters_data, 1):
             # Save content to file system
            content_path = self.storage.save_chapter_content(book_uuid, index, ch_content)
            
            chapter = Chapter(
                id=str(uuid.uuid4()),
                book_id=book_uuid,
                item_id=f"{platform_book_id}_{index}",
                title=ch_title,
                chapter_index=index,
                word_count=len(ch_content),
                download_status="completed",
                content_path=content_path,
            )
            self.db.add(chapter)
        
        book.downloaded_chapters = book.total_chapters
        self.db.commit()
        self.db.refresh(book)
        
        logger.info(f"Uploaded book: {book.title} ({book.id}), {book.total_chapters} chapters")
        return book

    async def upload_epub_book(
        self,
        title: str,
        author: str,
        file_content: bytes,
    ) -> Book:
        """
        上传EPUB书籍并解析
        """
        # Create book record
        book_uuid = str(uuid.uuid4())
        platform_book_id = f"local_{book_uuid[:8]}"
        
        # Parse chapters from EPUB
        chapters_data, epub_metadata = self._parse_epub_chapters(file_content)
        
        # Use metadata if provided title/author are empty
        final_title = title or epub_metadata.get('title') or "未命名书籍"
        final_author = author or epub_metadata.get('author') or "未知作者"

        book = Book(
            id=book_uuid,
            platform="local",
            book_id=platform_book_id,
            title=final_title,
            author=final_author,
            word_count=sum(len(c[1]) for c in chapters_data),
            creation_status="已完结",
            download_status="completed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            total_chapters=len(chapters_data),
            downloaded_chapters=len(chapters_data),
        )
        
        if chapters_data:
            book.last_chapter_title = chapters_data[-1][0]
        
        self.db.add(book)
        self.db.commit()
        
        # Save chapters
        for index, (ch_title, ch_content) in enumerate(chapters_data, 1):
            content_path = self.storage.save_chapter_content(book_uuid, index, ch_content)
            
            chapter = Chapter(
                id=str(uuid.uuid4()),
                book_id=book_uuid,
                item_id=f"{platform_book_id}_{index}",
                title=ch_title,
                chapter_index=index,
                word_count=len(ch_content),
                download_status="completed",
                content_path=content_path,
            )
            self.db.add(chapter)
        
        self.db.commit()
        self.db.refresh(book)
        
        logger.info(f"Uploaded EPUB book: {book.title} ({book.id}), {book.total_chapters} chapters")
        return book

    def _parse_epub_chapters(self, file_content: bytes) -> Tuple[List[Tuple[str, str]], dict]:
        """
        解析EPUB章节
        Returns: (List of (title, content), metadata)
        """
        book = epub.read_epub(io.BytesIO(file_content))
        
        metadata = {
            'title': book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else None,
            'author': book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else None,
        }
        
        chapters = []
        
        # Iterate through the spine to get items in order
        for item_id, linear in book.spine:
            item = book.get_item_with_id(item_id)
            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # Try to find a title in the document
                title = ""
                h1 = soup.find('h1')
                h2 = soup.find('h2')
                h3 = soup.find('h3')
                if h1: title = h1.get_text().strip()
                elif h2: title = h2.get_text().strip()
                elif h3: title = h3.get_text().strip()
                
                # If no title found in headers, use the item name or a generic one
                if not title:
                    title = f"章节 {len(chapters) + 1}"
                
                # Get text content
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text, preserving some structure if possible, but here we want plain text
                text = soup.get_text(separator='\n').strip()
                
                if text:
                    chapters.append((title, text))
        
        return chapters, metadata

    def _parse_txt_chapters(self, content: str, pattern: str, book_title: str) -> List[Tuple[str, str]]:
        """
        根据正则解析TXT章节
        Returns: List of (title, content)
        """
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        matches = list(regex.finditer(content))
        
        chapters = []
        
        # Handle content before first match (Prologue/Preface)
        if matches:
            preface_end = matches[0].start()
            if preface_end > 0:
                preface_content = content[:preface_end].strip()
                if preface_content:
                    chapters.append(("前言", preface_content))
        
        for i, match in enumerate(matches):
            title = match.group().strip()
            start = match.end()
            end = matches[i+1].start() if i + 1 < len(matches) else len(content)
            
            chapter_content = content[start:end].strip()
            if not chapter_content:
                continue
                
            chapters.append((title, chapter_content))
            
        if not chapters and content.strip():
             # If no matches, treat whole file as one chapter
             chapters.append((book_title or "全文", content.strip()))
             
        return chapters

__all__ = ["BookServiceUploadMixin"]
