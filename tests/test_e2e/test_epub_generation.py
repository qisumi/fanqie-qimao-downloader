import uuid
from pathlib import Path

from app.models.book import Book
from app.models.chapter import Chapter
from app.services import EPUBService
from tests.test_e2e.test_data import MOCK_CHAPTER_LIST


class TestE2EEpubGeneration:
    """
    EPUB生成端到端测试
    """
    
    def test_epub_with_volumes(self, db_session, storage_service, temp_storage_path):
        """测试带卷结构的EPUB生成"""
        books_path, epubs_path = temp_storage_path
        
        book = Book(
            id=str(uuid.uuid4()),
            platform="fanqie",
            book_id="7123456789",
            title="测试小说",
            author="测试作者",
            total_chapters=5,
            downloaded_chapters=5,
            download_status="completed",
        )
        db_session.add(book)
        
        for i, ch_data in enumerate(MOCK_CHAPTER_LIST["chapters"]):
            content_path = storage_service.save_chapter_content(
                book.id, i, f"第{i+1}章内容\n\n这是测试内容..."
            )
            
            chapter = Chapter(
                id=str(uuid.uuid4()),
                book_id=book.id,
                item_id=ch_data["item_id"],
                title=ch_data["title"],
                volume_name=ch_data["volume_name"],
                chapter_index=i,
                word_count=ch_data["word_count"],
                download_status="completed",
                content_path=content_path,
            )
            db_session.add(chapter)
        db_session.commit()
        
        epub_service = EPUBService(db=db_session, storage=storage_service)
        chapters = db_session.query(Chapter).filter(
            Chapter.book_id == book.id
        ).order_by(Chapter.chapter_index).all()
        
        epub_path = epub_service.generate_epub(book, chapters)
        
        assert epub_path is not None
        assert Path(epub_path).exists()
        
        info = epub_service.get_epub_info(epub_path)
        assert info["chapter_count"] == 5
        assert info["title"] == "测试小说"
    
    def test_epub_with_special_characters(self, db_session, storage_service, temp_storage_path):
        """测试包含特殊字符的EPUB生成"""
        books_path, epubs_path = temp_storage_path
        
        book = Book(
            id=str(uuid.uuid4()),
            platform="fanqie",
            book_id="7123456789",
            title="测试<小说>&特殊\"字符'",
            author="测试\"作者'",
            total_chapters=1,
            downloaded_chapters=1,
            download_status="completed",
        )
        db_session.add(book)
        
        content_with_special_chars = """第一章内容
        
这里有一些特殊字符：<>&"'
还有一些HTML标签：<script>alert('xss')</script>
以及中文特殊符号：《》「」【】"""
        
        content_path = storage_service.save_chapter_content(book.id, 0, content_with_special_chars)
        
        chapter = Chapter(
            id=str(uuid.uuid4()),
            book_id=book.id,
            item_id="ch_001",
            title="第1章 测试<特殊>字符",
            chapter_index=0,
            word_count=100,
            download_status="completed",
            content_path=content_path,
        )
        db_session.add(chapter)
        db_session.commit()
        
        epub_service = EPUBService(db=db_session, storage=storage_service)
        chapters = db_session.query(Chapter).filter(
            Chapter.book_id == book.id
        ).order_by(Chapter.chapter_index).all()
        
        epub_path = epub_service.generate_epub(book, chapters)
        
        assert epub_path is not None
        assert Path(epub_path).exists()
        assert epub_service.validate_epub(epub_path)
