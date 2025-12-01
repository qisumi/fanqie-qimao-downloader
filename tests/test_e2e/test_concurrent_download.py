import asyncio
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.book import Book
from app.models.chapter import Chapter
from app.services import DownloadService
from tests.test_e2e.test_data import MOCK_CHAPTER_CONTENT


class TestE2EConcurrentDownload:
    """
    并发下载端到端测试
    """
    
    @pytest.mark.asyncio
    async def test_concurrent_download_limit(self, db_session, storage_service):
        """测试并发下载限制"""
        book = Book(
            id=str(uuid.uuid4()),
            platform="fanqie",
            book_id="7123456789",
            title="测试小说",
            author="测试作者",
            total_chapters=10,
            downloaded_chapters=0,
            download_status="pending",
        )
        db_session.add(book)
        
        for i in range(10):
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
        
        max_concurrent = 0
        current_concurrent = 0
        concurrent_lock = asyncio.Lock()
        
        original_content = MOCK_CHAPTER_CONTENT.copy()
        
        async def mock_get_content(*args, **kwargs):
            nonlocal max_concurrent, current_concurrent
            async with concurrent_lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            
            await asyncio.sleep(0.05)
            
            async with concurrent_lock:
                current_concurrent -= 1
            
            return original_content
        
        with patch('app.services.download_service_base.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_content = mock_get_content
            MockFanqieAPI.return_value = mock_api
            
            download_service = DownloadService(
                db=db_session,
                storage=storage_service,
                concurrent_downloads=3,
                download_delay=0.01,
            )
            
            task = await download_service.download_book(book.id)
            
            assert task.status == "completed"
            assert task.downloaded_chapters == 10
            assert max_concurrent <= 3
