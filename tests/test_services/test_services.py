"""
服务层单元测试

测试 Phase 3 实现的四个服务:
- StorageService
- BookService  
- DownloadService
- EPUBService
"""

import os
import uuid
import asyncio
import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# 设置测试环境
os.environ["RAIN_API_KEY"] = "test_key"

from app.services import (
    StorageService,
    BookService,
    DownloadService,
    EPUBService,
)
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.utils.database import SessionLocal


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
def mock_db_session():
    """模拟数据库会话"""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []
    session.query.return_value.count.return_value = 0
    return session


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
    for i in range(10):
        chapter = Chapter(
            id=str(uuid.uuid4()),
            book_id=sample_book.id,
            item_id=f"chapter_{i}",
            title=f"第{i+1}章 测试章节",
            chapter_index=i,
            word_count=3000,
            download_status="completed" if i < 5 else "pending",
        )
        chapters.append(chapter)
    return chapters


# ============ StorageService Tests ============

class TestStorageService:
    """StorageService 测试类"""
    
    def test_init(self, storage_service):
        """测试初始化"""
        assert storage_service.books_path.exists()
        assert storage_service.epubs_path.exists()
    
    def test_get_book_dir(self, storage_service):
        """测试获取书籍目录"""
        book_uuid = str(uuid.uuid4())
        book_dir = storage_service.get_book_dir(book_uuid)
        assert str(book_uuid) in str(book_dir)
    
    def test_save_and_get_chapter_content(self, storage_service):
        """测试保存和读取章节内容"""
        book_uuid = str(uuid.uuid4())
        content = "这是测试章节内容。\n第一段。\n第二段。"
        
        # 保存
        path = storage_service.save_chapter_content(book_uuid, 1, content)
        assert path is not None
        
        # 读取
        retrieved = storage_service.get_chapter_content(path)
        assert retrieved == content
    
    @pytest.mark.asyncio
    async def test_save_chapter_content_async(self, storage_service):
        """测试异步保存章节内容"""
        book_uuid = str(uuid.uuid4())
        content = "异步保存的测试内容"
        
        path = await storage_service.save_chapter_content_async(book_uuid, 0, content)
        assert path is not None
        
        retrieved = storage_service.get_chapter_content(path)
        assert retrieved == content
    
    def test_save_cover(self, storage_service):
        """测试保存封面"""
        book_uuid = str(uuid.uuid4())
        # 创建一个简单的测试图片数据
        image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        
        path = storage_service.save_cover(book_uuid, image_data)
        assert path is not None
        assert storage_service.cover_exists(book_uuid)
    
    def test_delete_book_files(self, storage_service):
        """测试删除书籍文件"""
        book_uuid = str(uuid.uuid4())
        
        # 先创建一些文件
        storage_service.save_chapter_content(book_uuid, 0, "test content")
        assert storage_service.get_book_dir(book_uuid).exists()
        
        # 删除
        result = storage_service.delete_book_files(book_uuid)
        assert result is True
        assert not storage_service.get_book_dir(book_uuid).exists()
    
    def test_get_storage_stats(self, storage_service):
        """测试获取存储统计"""
        # 创建一些测试数据
        book_uuid = str(uuid.uuid4())
        storage_service.save_chapter_content(book_uuid, 0, "test")
        storage_service.save_chapter_content(book_uuid, 1, "test")
        
        stats = storage_service.get_storage_stats()
        assert stats["books_count"] >= 1
        assert stats["total_chapters"] >= 2
    
    def test_sanitize_filename(self, storage_service):
        """测试文件名清理"""
        # 包含非法字符
        filename = 'Test<>:"/\\|?*File'
        safe = storage_service._sanitize_filename(filename)
        assert '<' not in safe
        assert '>' not in safe
        
        # 长度限制
        long_name = "a" * 200
        safe = storage_service._sanitize_filename(long_name)
        assert len(safe) <= 100


# ============ BookService Tests ============

class TestBookService:
    """BookService 测试类"""
    
    def test_init(self, mock_db_session, storage_service):
        """测试初始化"""
        service = BookService(db=mock_db_session, storage=storage_service)
        assert service.db is mock_db_session
        assert service.storage is storage_service
    
    def test_get_book_not_found(self, mock_db_session, storage_service):
        """测试获取不存在的书籍"""
        service = BookService(db=mock_db_session, storage=storage_service)
        book = service.get_book("nonexistent-uuid")
        assert book is None
    
    def test_list_books_empty(self, mock_db_session, storage_service):
        """测试空书籍列表"""
        mock_db_session.query.return_value.filter.return_value = mock_db_session.query.return_value
        mock_db_session.query.return_value.order_by.return_value = mock_db_session.query.return_value
        mock_db_session.query.return_value.offset.return_value = mock_db_session.query.return_value
        mock_db_session.query.return_value.limit.return_value = mock_db_session.query.return_value
        mock_db_session.query.return_value.all.return_value = []
        
        service = BookService(db=mock_db_session, storage=storage_service)
        result = service.list_books()
        
        assert result["books"] == []
        assert result["total"] == 0


# ============ DownloadService Tests ============

class TestDownloadService:
    """DownloadService 测试类"""
    
    def test_init(self, mock_db_session, storage_service):
        """测试初始化"""
        service = DownloadService(db=mock_db_session, storage=storage_service)
        assert service.db is mock_db_session
        assert service.storage is storage_service
        assert service.concurrent_downloads > 0
    
    def test_get_quota_usage(self, mock_db_session, storage_service):
        """测试获取配额使用情况"""
        service = DownloadService(db=mock_db_session, storage=storage_service)
        usage = service.get_quota_usage("fanqie")
        
        assert "downloaded" in usage
        assert "limit" in usage
        assert "remaining" in usage
    
    def test_cancel_nonexistent_task(self, mock_db_session, storage_service):
        """测试取消不存在的任务"""
        service = DownloadService(db=mock_db_session, storage=storage_service)
        result = service.cancel_task("nonexistent-task-id")
        assert result is False
    
    def test_get_pending_chapters_skip_completed(self, mock_db_session, storage_service, sample_book, sample_chapters):
        """测试获取待下载章节时跳过已完成章节"""
        # 设置一些章节为已完成状态
        sample_chapters[0].download_status = "completed"
        sample_chapters[1].download_status = "completed"
        sample_chapters[2].download_status = "pending"
        sample_chapters[3].download_status = "failed"
        
        # Mock 查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_chapters[2], sample_chapters[3]]  # 只返回未完成的
        mock_db_session.query.return_value = mock_query
        
        service = DownloadService(db=mock_db_session, storage=storage_service)
        
        # skip_completed=True（默认）应该只返回未完成的章节
        chapters = service._get_pending_chapters(
            sample_book.id,
            task_type="full_download",
            start_chapter=0,
            end_chapter=None,
            skip_completed=True
        )
        
        # 验证只获取了未完成的章节
        assert len(chapters) == 2
        assert all(ch.download_status != "completed" for ch in chapters)


# ============ EPUBService Tests ============

class TestEPUBService:
    """EPUBService 测试类"""
    
    def test_init(self, storage_service):
        """测试初始化"""
        service = EPUBService(storage=storage_service)
        assert service.storage is storage_service
    
    def test_escape_html(self, storage_service):
        """测试HTML转义"""
        service = EPUBService(storage=storage_service)
        
        text = '<script>alert("test")</script>'
        escaped = service._escape_html(text)
        
        assert '<' not in escaped
        assert '>' not in escaped
        assert '&lt;' in escaped
        assert '&gt;' in escaped
    
    def test_format_content_to_html(self, storage_service):
        """测试内容格式化为HTML"""
        service = EPUBService(storage=storage_service)
        
        content = "第一段内容\n第二段内容\n第三段内容"
        html = service._format_content_to_html(content)
        
        assert "<p>" in html
        assert "</p>" in html
        assert html.count("<p>") == 3
    
    def test_generate_epub_no_chapters(self, storage_service, sample_book):
        """测试无章节时生成EPUB抛出错误"""
        service = EPUBService(storage=storage_service)
        
        with pytest.raises(ValueError, match="No chapters"):
            service.generate_epub(sample_book, chapters=[])
    
    def test_generate_epub_success(self, storage_service, sample_book, sample_chapters):
        """测试成功生成EPUB"""
        service = EPUBService(storage=storage_service)
        
        # 为章节创建内容文件，使用完整路径作为 content_path
        for chapter in sample_chapters[:5]:  # 只用已完成的章节
            storage_service.save_chapter_content(
                sample_book.id,
                chapter.chapter_index,
                f"这是{chapter.title}的内容。\n测试段落。"
            )
            # 不设置 content_path，让 EPUBService 使用 get_chapter_content_by_index
        
        # 生成EPUB
        epub_path = service.generate_epub(sample_book, chapters=sample_chapters[:5])
        
        assert epub_path is not None
        assert Path(epub_path).exists()
        assert epub_path.endswith(".epub")
    
    def test_validate_epub(self, storage_service, sample_book, sample_chapters):
        """测试验证EPUB"""
        service = EPUBService(storage=storage_service)
        
        # 先生成一个EPUB
        for chapter in sample_chapters[:3]:
            storage_service.save_chapter_content(
                sample_book.id,
                chapter.chapter_index,
                f"测试内容 - {chapter.title}"
            )
        
        epub_path = service.generate_epub(sample_book, chapters=sample_chapters[:3])
        
        # 验证
        is_valid = service.validate_epub(epub_path)
        assert is_valid is True
        
        # 验证不存在的文件
        is_valid = service.validate_epub("/nonexistent/path.epub")
        assert is_valid is False
    
    def test_get_epub_info(self, storage_service, sample_book, sample_chapters):
        """测试获取EPUB信息"""
        service = EPUBService(storage=storage_service)
        
        # 创建EPUB
        for chapter in sample_chapters[:3]:
            storage_service.save_chapter_content(
                sample_book.id,
                chapter.chapter_index,
                f"测试内容 - {chapter.title}"
            )
        
        epub_path = service.generate_epub(sample_book, chapters=sample_chapters[:3])
        
        # 获取信息
        info = service.get_epub_info(epub_path)
        
        assert info is not None
        assert info["title"] == sample_book.title
        assert info["file_size"] > 0


# ============ Integration Tests ============

class TestServiceIntegration:
    """服务集成测试"""
    
    def test_storage_and_epub_integration(self, storage_service, sample_book, sample_chapters):
        """测试存储服务和EPUB服务集成"""
        epub_service = EPUBService(storage=storage_service)
        
        # 保存章节内容
        for i, chapter in enumerate(sample_chapters[:5]):
            content = f"这是第{i+1}章的内容。\n\n这是一个测试段落。"
            storage_service.save_chapter_content(
                sample_book.id, 
                chapter.chapter_index, 
                content
            )
            chapter.download_status = "completed"
        
        # 生成EPUB
        epub_path = epub_service.generate_epub(sample_book, chapters=sample_chapters[:5])
        
        # 验证
        assert Path(epub_path).exists()
        
        info = epub_service.get_epub_info(epub_path)
        assert info["title"] == sample_book.title
        assert info["chapter_count"] == 5


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
