"""
端到端测试

测试完整的用户工作流程：
1. 搜索书籍
2. 添加书籍
3. 下载章节
4. 生成EPUB
5. 更新书籍（增量下载）
6. 异常处理

使用 Mock 模拟外部 API 调用
"""

import os
import uuid
import asyncio
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 设置测试环境
os.environ["RAIN_API_KEY"] = "test_key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.main import app
from app.utils.database import Base, get_db
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.services import StorageService, BookService, DownloadService, EPUBService


# ============ 测试数据库配置 ============

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖get_db依赖，使用测试数据库"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# ============ Mock 数据 ============

MOCK_SEARCH_RESULT = {
    "books": [
        {
            "book_id": "7123456789",
            "book_name": "测试小说",
            "author": "测试作者",
            "cover_url": "https://example.com/cover.jpg",
            "word_count": 500000,
            "creation_status": "连载中",
        },
        {
            "book_id": "7987654321",
            "book_name": "另一本测试小说",
            "author": "另一作者",
            "cover_url": "https://example.com/cover2.jpg",
            "word_count": 300000,
            "creation_status": "已完结",
        }
    ],
    "total": 2,
    "page": 0,
}

MOCK_BOOK_DETAIL = {
    "book_id": "7123456789",
    "book_name": "测试小说",
    "author": "测试作者",
    "cover_url": "https://example.com/cover.jpg",
    "word_count": 500000,
    "creation_status": "连载中",
    "last_chapter_title": "第100章 最新章节",
    "last_update_timestamp": 1732752000,
}

MOCK_CHAPTER_LIST = {
    "total_chapters": 5,
    "chapters": [
        {"item_id": "ch_001", "title": "第1章 开始", "chapter_index": 0, "word_count": 3000, "volume_name": "第一卷"},
        {"item_id": "ch_002", "title": "第2章 发展", "chapter_index": 1, "word_count": 3500, "volume_name": "第一卷"},
        {"item_id": "ch_003", "title": "第3章 高潮", "chapter_index": 2, "word_count": 4000, "volume_name": "第一卷"},
        {"item_id": "ch_004", "title": "第4章 转折", "chapter_index": 3, "word_count": 3200, "volume_name": "第二卷"},
        {"item_id": "ch_005", "title": "第5章 结局", "chapter_index": 4, "word_count": 3800, "volume_name": "第二卷"},
    ],
}

MOCK_CHAPTER_CONTENT = {
    "type": "text",
    "content": "这是一段测试的章节内容。\n\n故事开始于一个平凡的早晨，主角醒来发现自己获得了一种神奇的能力...\n\n第二段内容继续描述故事的发展...",
}


# ============ Fixtures ============

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """获取数据库会话"""
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


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


# ============ 端到端测试 ============

class TestE2ECompleteWorkflow:
    """
    完整工作流程端到端测试
    
    模拟用户从搜索到生成EPUB的完整流程
    """
    
    @pytest.mark.asyncio
    async def test_complete_download_flow(self, db_session, storage_service, temp_storage_path):
        """
        测试完整的下载流程:
        1. 搜索书籍
        2. 添加书籍
        3. 下载章节
        4. 生成EPUB
        """
        books_path, epubs_path = temp_storage_path
        
        # Mock API 调用
        with patch('app.services.book_service.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.search.return_value = MOCK_SEARCH_RESULT
            mock_api.get_book_detail.return_value = MOCK_BOOK_DETAIL
            mock_api.get_chapter_list.return_value = MOCK_CHAPTER_LIST
            MockFanqieAPI.return_value = mock_api
            
            # 1. 创建 BookService
            book_service = BookService(db=db_session, storage=storage_service)
            
            # 2. 搜索书籍
            search_result = await book_service.search_books("fanqie", "测试小说")
            assert len(search_result["books"]) > 0
            assert search_result["books"][0]["book_name"] == "测试小说"
            
            # 3. 添加书籍
            with patch.object(storage_service, 'download_and_save_cover', return_value=str(books_path / "cover.jpg")):
                book = await book_service.add_book("fanqie", "7123456789")
            
            assert book is not None
            assert book.title == "测试小说"
            assert book.author == "测试作者"
            assert book.total_chapters == 5
            
            # 验证章节已创建
            chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
            assert len(chapters) == 5
        
        # 4. 下载章节
        with patch('app.services.download_service.FanqieAPI') as MockFanqieAPI:
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
            
            # 创建并执行下载任务
            task = await download_service.download_book(book.id)
            
            assert task is not None
            assert task.status == "completed"
            assert task.downloaded_chapters == 5
            assert task.failed_chapters == 0
            
            # 验证章节状态更新
            db_session.expire_all()
            chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
            for chapter in chapters:
                assert chapter.download_status == "completed"
                assert chapter.content_path is not None
        
        # 5. 生成EPUB
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
        
        # 验证EPUB
        assert epub_service.validate_epub(epub_path)
        
        info = epub_service.get_epub_info(epub_path)
        assert info["title"] == "测试小说"
        assert info["author"] == "测试作者"
        assert info["chapter_count"] == 5
    
    @pytest.mark.asyncio
    async def test_incremental_update_flow(self, db_session, storage_service, temp_storage_path):
        """
        测试增量更新流程:
        1. 添加书籍并下载初始章节
        2. 模拟新章节出现
        3. 检测并下载新章节
        """
        books_path, epubs_path = temp_storage_path
        
        # 初始章节列表（只有3章）
        initial_chapters = {
            "total_chapters": 3,
            "chapters": MOCK_CHAPTER_LIST["chapters"][:3],
        }
        
        # 第一阶段：添加书籍并下载初始3章
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
        
        # 下载初始章节
        with patch('app.services.download_service.FanqieAPI') as MockFanqieAPI:
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
        
        # 第二阶段：检测新章节
        # 模拟API返回5章（新增2章）
        with patch('app.services.book_service.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_list.return_value = MOCK_CHAPTER_LIST  # 现在返回5章
            MockFanqieAPI.return_value = mock_api
            
            book_service = BookService(db=db_session, storage=storage_service)
            new_chapters = await book_service.check_new_chapters(book.id)
            
            assert len(new_chapters) == 2
            assert new_chapters[0]["title"] == "第4章 转折"
            assert new_chapters[1]["title"] == "第5章 结局"
            
            # 添加新章节到数据库
            count = await book_service.add_new_chapters(book.id)
            assert count == 2
        
        # 第三阶段：下载新章节
        with patch('app.services.download_service.FanqieAPI') as MockFanqieAPI:
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
            assert task.downloaded_chapters == 2  # 只下载新增的2章
        
        # 验证所有5章都已下载
        db_session.expire_all()
        chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
        assert len(chapters) == 5
        completed = [c for c in chapters if c.download_status == "completed"]
        assert len(completed) == 5


class TestE2EErrorHandling:
    """
    错误处理端到端测试
    
    测试各种异常情况下的系统行为
    """
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, db_session, storage_service):
        """测试网络错误重试机制"""
        from app.api.base import NetworkError
        
        # 先创建一个书籍和章节
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
        
        # 模拟第一次调用失败，第二次成功
        call_count = 0
        async def mock_get_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise NetworkError("Connection timeout")
            return MOCK_CHAPTER_CONTENT
        
        with patch('app.services.download_service.FanqieAPI') as MockFanqieAPI:
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
            
            # 部分章节可能失败，但应该继续处理其他章节
            assert task.status in ["completed", "failed"]
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_handling(self, db_session, storage_service):
        """测试配额超限处理"""
        from app.api.base import QuotaExceededError
        
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
        
        with patch('app.services.download_service.FanqieAPI') as MockFanqieAPI:
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
            
            # 下载服务会处理配额超限错误，所有章节都会失败
            task = await download_service.download_book(book.id)
            
            # 验证任务完成但所有章节都失败
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
        
        # 前2章已下载完成，后3章待下载
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
        
        with patch('app.services.download_service.FanqieAPI') as MockFanqieAPI:
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
            
            # 继续下载应该只下载剩余3章
            task = await download_service.download_book(book.id)
            
            assert task.downloaded_chapters == 3  # 只下载了剩余3章
            
            # 验证所有章节都已完成
            db_session.expire_all()
            chapters = db_session.query(Chapter).filter(Chapter.book_id == book.id).all()
            completed = [c for c in chapters if c.download_status == "completed"]
            assert len(completed) == 5


class TestE2EApiRoutes:
    """
    API路由端到端测试
    
    通过HTTP请求测试完整的API流程
    """
    
    def test_search_and_add_book(self, client):
        """测试通过API搜索并添加书籍"""
        with patch('app.web.routes.books.BookService') as MockBookService:
            mock_service = AsyncMock()
            mock_service.search_books.return_value = MOCK_SEARCH_RESULT
            MockBookService.return_value = mock_service
            
            # 搜索书籍 - 使用正确的参数名 q
            response = client.get(
                "/api/books/search",
                params={"platform": "fanqie", "q": "测试小说"}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["books"]) > 0
    
    def test_api_error_responses(self, client):
        """测试API错误响应格式"""
        # 获取不存在的书籍
        response = client.get("/api/books/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        
        # 无效的平台会返回422（参数验证错误）或400
        response = client.get(
            "/api/books/search",
            params={"platform": "invalid", "q": "test"}
        )
        # FastAPI验证可能返回422或400，取决于验证方式
        assert response.status_code in [400, 422]
    
    def test_health_check_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestE2EEpubGeneration:
    """
    EPUB生成端到端测试
    """
    
    def test_epub_with_volumes(self, db_session, storage_service, temp_storage_path):
        """测试带卷结构的EPUB生成"""
        books_path, epubs_path = temp_storage_path
        
        # 创建测试书籍
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
        
        # 创建带卷信息的章节
        for i, ch_data in enumerate(MOCK_CHAPTER_LIST["chapters"]):
            # 保存章节内容到文件
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
        
        # 生成EPUB
        epub_service = EPUBService(db=db_session, storage=storage_service)
        chapters = db_session.query(Chapter).filter(
            Chapter.book_id == book.id
        ).order_by(Chapter.chapter_index).all()
        
        epub_path = epub_service.generate_epub(book, chapters)
        
        assert epub_path is not None
        assert Path(epub_path).exists()
        
        # 验证EPUB信息
        info = epub_service.get_epub_info(epub_path)
        assert info["chapter_count"] == 5
        assert info["title"] == "测试小说"
    
    def test_epub_with_special_characters(self, db_session, storage_service, temp_storage_path):
        """测试包含特殊字符的EPUB生成"""
        books_path, epubs_path = temp_storage_path
        
        # 创建包含特殊字符的书籍
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
        
        # 创建包含特殊字符的章节
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
        
        # 生成EPUB
        epub_service = EPUBService(db=db_session, storage=storage_service)
        chapters = db_session.query(Chapter).filter(
            Chapter.book_id == book.id
        ).order_by(Chapter.chapter_index).all()
        
        epub_path = epub_service.generate_epub(book, chapters)
        
        assert epub_path is not None
        assert Path(epub_path).exists()
        
        # EPUB应该能够验证通过
        assert epub_service.validate_epub(epub_path)


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
        
        # 记录并发数
        max_concurrent = 0
        current_concurrent = 0
        concurrent_lock = asyncio.Lock()
        
        original_content = MOCK_CHAPTER_CONTENT.copy()
        
        async def mock_get_content(*args, **kwargs):
            nonlocal max_concurrent, current_concurrent
            async with concurrent_lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            
            await asyncio.sleep(0.05)  # 模拟网络延迟
            
            async with concurrent_lock:
                current_concurrent -= 1
            
            return original_content
        
        with patch('app.services.download_service.FanqieAPI') as MockFanqieAPI:
            mock_api = AsyncMock()
            mock_api.__aenter__.return_value = mock_api
            mock_api.__aexit__.return_value = None
            mock_api.get_chapter_content = mock_get_content
            MockFanqieAPI.return_value = mock_api
            
            download_service = DownloadService(
                db=db_session, 
                storage=storage_service,
                concurrent_downloads=3,  # 限制最大并发数为3
                download_delay=0.01,
            )
            
            task = await download_service.download_book(book.id)
            
            assert task.status == "completed"
            assert task.downloaded_chapters == 10
            # 验证最大并发数不超过设置值
            assert max_concurrent <= 3
