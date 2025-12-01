import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.models.book import Book
from app.models.chapter import Chapter
from app.services import BookService, DownloadService, EPUBService
from tests.test_e2e.test_data import (
    MOCK_BOOK_DETAIL,
    MOCK_CHAPTER_CONTENT,
    MOCK_CHAPTER_LIST,
    MOCK_SEARCH_RESULT,
)


class TestE2ECompleteWorkflow:
    """
    完整工作流程端到端测试
    
    模拟用户从搜索到生成EPUB的完整流程
    """
    
    @pytest.mark.asyncio
    async def test_complete_download_flow(self, db_session, storage_service, temp_storage_path):
        """完整的下载与生成流程"""
        books_path, epubs_path = temp_storage_path
        
        with patch('app.services.book_service.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.search.return_value = MOCK_SEARCH_RESULT
            mock_api.get_book_detail.return_value = MOCK_BOOK_DETAIL
            mock_api.get_chapter_list.return_value = MOCK_CHAPTER_LIST
            MockFanqieAPI.return_value = mock_api
            
            book_service = BookService(db=db_session, storage=storage_service)
            
            search_result = await book_service.search_books("fanqie", "测试小说")
            assert len(search_result["books"]) > 0
            assert search_result["books"][0]["book_name"] == "测试小说"
            
            with patch.object(storage_service, 'download_and_save_cover', return_value=str(books_path / "cover.jpg")):
                book = await book_service.add_book("fanqie", "7123456789")
            
            assert book is not None
            assert book.title == "测试小说"
            assert book.author == "测试作者"
            assert book.total_chapters == 5
            
            chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
            assert len(chapters) == 5
        
        with patch('app.services.download_service_base.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_content.return_value = MOCK_CHAPTER_CONTENT
            MockFanqieAPI.return_value = mock_api
            
            download_service = DownloadService(
                db=db_session,
                storage=storage_service,
                concurrent_downloads=2,
                download_delay=0.01,
            )
            
            task = await download_service.download_book(book.id)
            
            assert task is not None
            assert task.status == "completed"
            assert task.downloaded_chapters == 5
            assert task.failed_chapters == 0
            
            db_session.expire_all()
            chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
            for chapter in chapters:
                assert chapter.download_status == "completed"
                assert chapter.content_path is not None
        
        epub_service = EPUBService(db=db_session, storage=storage_service)
        
        db_session.expire_all()
        book = db_session.query(Book).filter(Book.id == book.id).first()
        chapters = db_session.query(Chapter).filter(
            Chapter.book_id == book.id,
            Chapter.download_status == "completed"
        ).order_by(Chapter.chapter_index).all()
        
        epub_path = epub_service.generate_epub(book, chapters)
        
        assert epub_path is not None
        assert Path(epub_path).exists()
        assert epub_service.validate_epub(epub_path)
        
        info = epub_service.get_epub_info(epub_path)
        assert info["title"] == "测试小说"
        assert info["author"] == "测试作者"
        assert info["chapter_count"] == 5
    
    @pytest.mark.asyncio
    async def test_incremental_update_flow(self, db_session, storage_service, temp_storage_path):
        """测试增量更新流程"""
        books_path, epubs_path = temp_storage_path
        
        initial_chapters = {
            "total_chapters": 3,
            "chapters": MOCK_CHAPTER_LIST["chapters"][:3],
        }
        
        with patch('app.services.book_service.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.search.return_value = MOCK_SEARCH_RESULT
            mock_api.get_book_detail.return_value = MOCK_BOOK_DETAIL
            mock_api.get_chapter_list.return_value = initial_chapters
            MockFanqieAPI.return_value = mock_api
            
            book_service = BookService(db=db_session, storage=storage_service)
            
            with patch.object(storage_service, 'download_and_save_cover', return_value=str(books_path / "cover.jpg")):
                book = await book_service.add_book("fanqie", "7123456789")
            
            assert book.total_chapters == 3
        
        with patch('app.services.download_service_base.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_content.return_value = MOCK_CHAPTER_CONTENT
            MockFanqieAPI.return_value = mock_api
            
            download_service = DownloadService(
                db=db_session,
                storage=storage_service,
                concurrent_downloads=2,
                download_delay=0.01,
            )
            
            task = await download_service.download_book(book.id)
            assert task.downloaded_chapters == 3
        
        with patch('app.services.book_service.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_list.return_value = MOCK_CHAPTER_LIST
            MockFanqieAPI.return_value = mock_api
            
            book_service = BookService(db=db_session, storage=storage_service)
            new_chapters = await book_service.check_new_chapters(book.id)
            
            assert len(new_chapters) == 2
            assert new_chapters[0]["title"] == "第4章 转折"
            assert new_chapters[1]["title"] == "第5章 结局"
            
            count = await book_service.add_new_chapters(book.id)
            assert count == 2
        
        with patch('app.services.download_service_base.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_content.return_value = MOCK_CHAPTER_CONTENT
            MockFanqieAPI.return_value = mock_api
            
            download_service = DownloadService(
                db=db_session,
                storage=storage_service,
                concurrent_downloads=2,
                download_delay=0.01,
            )
            
            task = await download_service.update_book(book.id)
            assert task.downloaded_chapters == 2
        
        db_session.expire_all()
        chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
        assert len(chapters) == 5
        completed = [c for c in chapters if c.download_status == "completed"]
        assert len(completed) == 5
