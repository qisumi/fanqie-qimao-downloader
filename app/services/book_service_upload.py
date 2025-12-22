import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Optional

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
