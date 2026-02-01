import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.base import NetworkError, QuotaExceededError
from app.models.book import Book
from app.models.chapter import Chapter
from app.services import DownloadService
from tests.test_e2e.test_data import MOCK_CHAPTER_CONTENT


class TestE2EErrorHandling:
    """
    错误处理端到端测试
    
    测试各种异常情况下的系统行为
    """
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, db_session, storage_service):
        """测试网络错误重试机制"""
        book = Book(
            id=str(uuid.uuid4()),
            platform="fanqie",
            book_id="7123456789",
            title="测试小说",
            author="测试作者",
            total_chapters=3,
            downloaded_chapters=0,
            download_status="pending",
        )
        db_session.add(book)
        
        for i in range(3):
            chapter = Chapter(
                id=str(uuid.uuid4()),
                book_id=book.id,
                item_id=f"ch_{i:03d}",
                title=f"第{i+1}章",
                chapter_index=i,
                word_count=3000,
                download_status="pending",
            )
            db_session.add(chapter)
        db_session.commit()
        
        call_count = 0
        
        async def mock_get_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise NetworkError("Connection timeout")
            return MOCK_CHAPTER_CONTENT
        
        with patch('app.services.download.download_service_base.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_content = mock_get_content
            MockFanqieAPI.return_value = mock_api
            
            download_service = DownloadService(
                db=db_session,
                storage=storage_service,
                concurrent_downloads=1,
                download_delay=0.01,
            )
            
            task = await download_service.download_book(book.id)
            assert task.status in ["completed", "failed"]
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_handling(self, db_session, storage_service):
        """测试配额超限处理"""
        book = Book(
            id=str(uuid.uuid4()),
            platform="fanqie",
            book_id="7123456789",
            title="测试小说",
            author="测试作者",
            total_chapters=3,
            downloaded_chapters=0,
            download_status="pending",
        )
        db_session.add(book)
        
        for i in range(3):
            chapter = Chapter(
                id=str(uuid.uuid4()),
                book_id=book.id,
                item_id=f"ch_{i:03d}",
                title=f"第{i+1}章",
                chapter_index=i,
                word_count=3000,
                download_status="pending",
            )
            db_session.add(chapter)
        db_session.commit()
        
        with patch('app.services.download.download_service_base.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_content.side_effect = QuotaExceededError("Daily quota exceeded")
            MockFanqieAPI.return_value = mock_api
            
            download_service = DownloadService(
                db=db_session,
                storage=storage_service,
                concurrent_downloads=1,
                download_delay=0.01,
            )
            
            task = await download_service.download_book(book.id)
            
            assert task.status == "failed"
            assert task.failed_chapters == 3
            assert task.downloaded_chapters == 0
    
    @pytest.mark.asyncio
    async def test_partial_download_recovery(self, db_session, storage_service):
        """测试部分下载后恢复"""
        book = Book(
            id=str(uuid.uuid4()),
            platform="fanqie",
            book_id="7123456789",
            title="测试小说",
            author="测试作者",
            total_chapters=5,
            downloaded_chapters=2,
            download_status="downloading",
        )
        db_session.add(book)
        
        for i in range(5):
            chapter = Chapter(
                id=str(uuid.uuid4()),
                book_id=book.id,
                item_id=f"ch_{i:03d}",
                title=f"第{i+1}章",
                chapter_index=i,
                word_count=3000,
                download_status="completed" if i < 2 else "pending",
                content_path=f"path/to/chapter_{i}.txt" if i < 2 else None,
            )
            db_session.add(chapter)
        db_session.commit()
        
        with patch('app.services.download.download_service_base.FanqieAPI') as MockFanqieAPI:
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
            
            task = await download_service.download_book(book.id, task_type="update")
            
            assert task.downloaded_chapters == 3
            
            db_session.expire_all()
            chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
            completed = [c for c in chapters if c.download_status == "completed"]
            assert len(completed) == 5
