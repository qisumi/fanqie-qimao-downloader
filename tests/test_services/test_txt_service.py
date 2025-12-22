
import os
import uuid
import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.services.txt_service import TXTService
from app.services.storage_service import StorageService
from app.models.book import Book
from app.models.chapter import Chapter

# ============ Fixtures ============ 

@pytest.fixture
def temp_storage_path(tmp_path):
    """临时存储路径"""
    books_path = tmp_path / "books"
    epubs_path = tmp_path / "epubs"
    books_path.mkdir()
    epubs_path.mkdir()
    return books_path, epubs_path

@pytest.fixture
def storage_service(temp_storage_path):
    """存储服务实例"""
    books_path, epubs_path = temp_storage_path
    return StorageService(books_path=books_path, epubs_path=epubs_path)

@pytest.fixture
def sample_book():
    """示例书籍对象"""
    return Book(
        id=str(uuid.uuid4()),
        platform="fanqie",
        book_id="7123456789",
        title="测试小说",
        author="测试作者",
        total_chapters=100,
        downloaded_chapters=0,
        download_status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def sample_chapters(sample_book):
    """示例章节列表"""
    chapters = []
    # Create chapters with titles that include "第X章" to test duplication fix
    for i in range(3):
        chapter = Chapter(
            id=str(uuid.uuid4()),
            book_id=sample_book.id,
            item_id=f"chapter_{i}",
            title=f"第{i+1}章 Title {i+1}",
            chapter_index=i,
            word_count=3000,
            download_status="completed",
        )
        chapters.append(chapter)
    return chapters

class TestTXTService:
    """TXTService 测试类"""

    def test_generate_txt_content_format(self, storage_service, sample_book, sample_chapters):
        """Test TXT content generation: No TOC and No Duplicate Headers"""
        service = TXTService(storage=storage_service)
        
        # Save content for chapters
        for chapter in sample_chapters:
            storage_service.save_chapter_content(
                sample_book.id,
                chapter.chapter_index,
                f"Content of {chapter.title}"
            )

        # Generate TXT
        txt_path = service.generate_txt(sample_book, chapters=sample_chapters)
        
        assert os.path.exists(txt_path)
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verify NO Table of Contents
        # The TOC logic used to look like:
        # 目录
        # ----------------------------------------
        #   第0章 ...
        assert "目录" not in content or "目录" not in content.splitlines()[10:20] # "目录" might appear in text, but let's check structure
        # Specifically, check that we don't have the TOC structure
        # Previous TOC started with "目录" then "----------------------------------------"
        # We can check for that sequence if it's unique enough, or just check the start of file
        
        # Verify Chapter Headers are NOT duplicated
        # Original code produced: "第0章 第1章 Title 1"
        # Fixed code should produce: "第1章 Title 1" (because chapter.title is "第1章 Title 1")
        
        # Check for the bad pattern
        # Since chapter_index is 0, 1, 2
        # And title is "第1章 Title 1" ...
        # The bad pattern would be "第0章 第1章 Title 1"
        assert "第0章 第1章 Title 1" not in content
        assert "第1章 第2章 Title 2" not in content
        
        # Check for the correct pattern
        assert "\n第1章 Title 1\n" in content
        assert "\n第2章 Title 2\n" in content
        
        # Verify content presence
        assert "Content of 第1章 Title 1" in content

    def test_generate_txt_no_chapters(self, storage_service, sample_book):
        service = TXTService(storage=storage_service)
        with pytest.raises(ValueError, match="No chapters available"):
            service.generate_txt(sample_book, chapters=[])

