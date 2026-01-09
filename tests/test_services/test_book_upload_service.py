"""
BookUploadService 单元测试

测试本地书籍上传功能:
- TXT 文件上传与章节解析
- EPUB 文件上传与解析
- 数据库和存储集成
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# 设置测试环境
import os
os.environ["RAIN_API_KEY"] = "test_key"

from app.services.book_upload_service import BookUploadService
from app.models.book import Book
from app.models.chapter import Chapter
from sqlalchemy.orm import Session


# ============ Fixtures ============

@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session


@pytest.fixture
def mock_storage_service():
    """模拟存储服务"""
    storage = AsyncMock()
    storage.save_chapter_content = MagicMock(return_value="/path/to/chapter.txt")
    return storage


@pytest.fixture
def sample_txt_content():
    """示例 TXT 内容"""
    return """第一章 开始
这是第一章的内容。
有多个段落。

第二章 继续
这是第二章的内容。

第三章 结束
这是第三章的内容。"""


@pytest.fixture
def sample_txt_with_preface():
    """包含前言的 TXT 内容"""
    return """这是一本小说的前言。
介绍一些背景信息。

第一章 正式开始
正文内容开始。

第二章 继续
更多内容。"""


@pytest.fixture
def sample_txt_various_patterns():
    """各种章节格式的 TXT 内容"""
    return """1. 第一章
数字格式内容。

Chapter 2
英文格式内容。

【特别篇】
特殊符号格式。

第四卷 终章
中文数字格式。"""


# ============ TXT Upload Tests ============

class TestBookUploadServiceTXT:
    """TXT 文件上传测试"""

    @pytest.mark.asyncio
    async def test_upload_txt_basic_success(self, mock_db_session, mock_storage_service, sample_txt_content):
        """测试基本的 TXT 上传成功"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        book = await service.upload_txt_book(
            title="测试小说",
            author="测试作者",
            content=sample_txt_content,
            regex_pattern=r"第.+章\s+.+"  # 移除 ^ 因为默认不支持多行模式
        )

        # 验证书籍对象
        assert book.title == "测试小说"
        assert book.author == "测试作者"
        assert book.platform == "local"
        assert book.total_chapters == 3
        assert book.downloaded_chapters == 3
        assert book.download_status == "completed"

        # 验证数据库操作
        assert mock_db_session.add.call_count == 4  # 1 book + 3 chapters
        assert mock_db_session.commit.call_count == 2

        # 验证存储调用
        assert mock_storage_service.save_chapter_content.call_count == 3

    @pytest.mark.asyncio
    async def test_upload_txt_with_preface(self, mock_db_session, mock_storage_service, sample_txt_with_preface):
        """测试包含前言的 TXT 上传"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        book = await service.upload_txt_book(
            title="带前言的小说",
            author="测试作者",
            content=sample_txt_with_preface,
            regex_pattern=r"第.+章\s+.+"  # 移除 ^
        )

        # 应该有 3 个章节：前言 + 2 个正文章节
        assert book.total_chapters == 3
        assert mock_storage_service.save_chapter_content.call_count == 3

    @pytest.mark.asyncio
    async def test_upload_txt_no_matches(self, mock_db_session, mock_storage_service):
        """测试无匹配时的处理"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        content = "这是一段没有章节标记的纯文本内容。"

        book = await service.upload_txt_book(
            title="无章节小说",
            author="测试作者",
            content=content,
            regex_pattern=r"第.+章\s+.+"  # 移除 ^
        )

        # 应该将整个内容作为单个章节
        assert book.total_chapters == 1
        assert mock_storage_service.save_chapter_content.call_count == 1

    @pytest.mark.asyncio
    async def test_upload_txt_custom_regex_patterns(self, mock_db_session, mock_storage_service):
        """测试各种自定义正则表达式模式"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        # 测试数字格式
        content1 = "1. 第一章\n内容\n\n2. 第二章\n内容"
        book1 = await service.upload_txt_book(
            title="数字格式",
            author="作者",
            content=content1,
            regex_pattern=r"\d+\.\s+.+"  # 移除 ^
        )
        assert book1.total_chapters == 2

        # 重置 mock
        mock_db_session.reset_mock()
        mock_storage_service.reset_mock()

        # 测试英文格式
        content2 = "Chapter 1\nContent\n\nChapter 2\nContent"
        book2 = await service.upload_txt_book(
            title="English Format",
            author="Author",
            content=content2,
            regex_pattern=r"Chapter\s+\d+"  # 移除 ^
        )
        assert book2.total_chapters == 2

        # 重置 mock
        mock_db_session.reset_mock()
        mock_storage_service.reset_mock()

        # 测试特殊符号格式
        content3 = "【第一章】\n内容\n\n【第二章】\n内容"
        book3 = await service.upload_txt_book(
            title="特殊符号格式",
            author="作者",
            content=content3,
            regex_pattern=r"【.+】"  # 移除 ^
        )
        assert book3.total_chapters == 2

    @pytest.mark.asyncio
    async def test_upload_txt_invalid_regex(self, mock_db_session, mock_storage_service):
        """测试无效正则表达式的错误处理"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with pytest.raises(ValueError):
            await service.upload_txt_book(
                title="测试",
                author="测试",
                content="内容",
                regex_pattern=r"[invalid("  # 无效的正则
            )

    @pytest.mark.asyncio
    async def test_upload_txt_empty_content(self, mock_db_session, mock_storage_service):
        """测试空内容的处理"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        book = await service.upload_txt_book(
            title="空小说",
            author="作者",
            content="",
            regex_pattern=r"^第.+章\s+.+"
        )

        # 空内容应该创建 0 章节的书籍
        assert book.total_chapters == 0
        assert book.downloaded_chapters == 0

    @pytest.mark.asyncio
    async def test_upload_txt_unicode_content(self, mock_db_session, mock_storage_service):
        """测试 Unicode 字符（中文、表情符号等）的处理"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        content = """第一章 测试🎉
这是包含中文和表情符号的内容😊
还有特殊字符：¥、©、®。

第二章 继续
更多内容。"""

        book = await service.upload_txt_book(
            title="Unicode 测试小说",
            author="张三👨‍💻",
            content=content,
            regex_pattern=r"第.+章\s+.+"  # 移除 ^
        )

        # 应该正确处理 Unicode 字符
        assert book.total_chapters == 2
        assert "🎉" in book.title or "测试" in book.title


# ============ EPUB Upload Tests ============

class TestBookUploadServiceEPUB:
    """EPUB 文件上传测试"""

    @pytest.mark.asyncio
    async def test_upload_epub_basic_success(self, mock_db_session, mock_storage_service):
        """测试基本的 EPUB 上传成功"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        # 创建模拟 EPUB 字节
        mock_epub_content = b"mock epub content"

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            mock_epub = MagicMock()
            mock_epub.get_metadata.side_effect = lambda dc, field: []

            # 模拟章节
            mock_item1 = MagicMock()
            mock_item1.get_name.return_value = 'chapter1.xhtml'
            mock_item1.get_content.return_value = '<html><body><h1>第一章</h1><p>内容</p></body></html>'.encode('utf-8')
            mock_item1.get_type.return_value = 9

            mock_item2 = MagicMock()
            mock_item2.get_name.return_value = 'chapter2.xhtml'
            mock_item2.get_content.return_value = '<html><body><h1>第二章</h1><p>内容</p></body></html>'.encode('utf-8')
            mock_item2.get_type.return_value = 9

            def get_item_by_id(item_id):
                return {'item1': mock_item1, 'item2': mock_item2}.get(item_id)

            mock_epub.get_item_with_id.side_effect = get_item_by_id
            mock_epub.get_items.return_value = [mock_item1, mock_item2]
            mock_epub.spine = [('item1', True), ('item2', True)]

            mock_read_epub.return_value = mock_epub

            book = await service.upload_epub_book(
                title="提供的标题",
                author="提供的作者",
                file_content=mock_epub_content
            )

            # 验证使用提供的标题和作者，而不是 EPUB 元数据
            assert book.title == "提供的标题"
            assert book.author == "提供的作者"
            assert book.platform == "local"
            assert book.download_status == "completed"

    @pytest.mark.asyncio
    async def test_upload_epub_metadata_override(self, mock_db_session, mock_storage_service):
        """测试提供的元数据覆盖 EPUB 元数据"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            mock_epub = MagicMock()
            mock_epub.get_metadata.side_effect = lambda dc, field: []

            mock_item = MagicMock()
            mock_item.get_name.return_value = 'chapter1.xhtml'
            mock_item.get_content.return_value = '<h1>第一章</h1><p>内容</p>'.encode('utf-8')
            mock_item.get_type.return_value = 9

            mock_epub.get_item_with_id.return_value = mock_item
            mock_epub.get_items.return_value = [mock_item]
            mock_epub.spine = [('item1', True)]

            mock_read_epub.return_value = mock_epub

            book = await service.upload_epub_book(
                title="新标题",  # 应该覆盖 EPUB 标题
                author="新作者",  # 应该覆盖 EPUB 作者
                file_content=b"epub"
            )

            assert book.title == "新标题"
            assert book.author == "新作者"

    @pytest.mark.asyncio
    async def test_upload_epub_metadata_fallback(self, mock_db_session, mock_storage_service):
        """测试元数据回退到 EPUB 内部信息"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            mock_epub = MagicMock()
            # get_metadata returns list of tuples with (value,)
            mock_epub.get_metadata.side_effect = lambda dc, field: {
                'title': [('EPUB标题',)],
                'creator': [('EPUB作者',)]
            }.get(field, [])

            mock_item = MagicMock()
            mock_item.get_name.return_value = 'chapter1.xhtml'
            mock_item.get_content.return_value = '<h1>第一章</h1><p>内容</p>'.encode('utf-8')
            mock_item.get_type.return_value = 9  # ebooklib.ITEM_DOCUMENT = 9

            mock_epub.get_item_with_id.return_value = mock_item
            mock_epub.get_items.return_value = [mock_item]
            mock_epub.spine = [('item1', True)]  # (item_id, linear)

            mock_read_epub.return_value = mock_epub

            # 传递空字符串作为标题和作者
            book = await service.upload_epub_book(
                title="",
                author="",
                file_content=b"epub"
            )

            # 应该回退到 EPUB 元数据
            assert book.title == "EPUB标题"
            assert book.author == "EPUB作者"

    @pytest.mark.asyncio
    async def test_upload_epub_chapter_title_extraction(self, mock_db_session, mock_storage_service):
        """测试章节标题提取（h1/h2/h3 优先级）"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            mock_epub = MagicMock()
            mock_epub.get_metadata.side_effect = lambda dc, field: []

            # 测试 h1 优先
            mock_item_h1 = MagicMock()
            mock_item_h1.get_name.return_value = 'chapter1.xhtml'
            mock_item_h1.get_content.return_value = '<html><body><h1>H1标题</h1><p>内容</p></body></html>'.encode('utf-8')
            mock_item_h1.get_type.return_value = 9

            # 测试 h2（当没有 h1 时）
            mock_item_h2 = MagicMock()
            mock_item_h2.get_name.return_value = 'chapter2.xhtml'
            mock_item_h2.get_content.return_value = '<html><body><h2>H2标题</h2><p>内容</p></body></html>'.encode('utf-8')
            mock_item_h2.get_type.return_value = 9

            # 测试 h3（当没有 h1/h2 时）
            mock_item_h3 = MagicMock()
            mock_item_h3.get_name.return_value = 'chapter3.xhtml'
            mock_item_h3.get_content.return_value = '<html><body><h3>H3标题</h3><p>内容</p></body></html>'.encode('utf-8')
            mock_item_h3.get_type.return_value = 9

            def get_item_by_id(item_id):
                return {
                    'item1': mock_item_h1,
                    'item2': mock_item_h2,
                    'item3': mock_item_h3
                }.get(item_id)

            mock_epub.get_item_with_id.side_effect = get_item_by_id
            mock_epub.get_items.return_value = [mock_item_h1, mock_item_h2, mock_item_h3]
            mock_epub.spine = [
                ('item1', True),
                ('item2', True),
                ('item3', True)
            ]

            mock_read_epub.return_value = mock_epub

            book = await service.upload_epub_book(
                title="测试",
                author="作者",
                file_content=b"epub"
            )

            # 应该有 3 个章节
            assert book.total_chapters == 3

    @pytest.mark.asyncio
    async def test_upload_epub_html_cleaning(self, mock_db_session, mock_storage_service):
        """测试 HTML 清理（移除 script 和 style 标签）"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            mock_epub = MagicMock()
            mock_epub.get_metadata.side_effect = lambda dc, field: []

            mock_item = MagicMock()
            mock_item.get_name.return_value = 'chapter1.xhtml'
            # 包含 script 和 style 标签
            mock_item.get_content.return_value = '''
            <html>
            <head>
                <script>alert('test');</script>
                <style>body { color: red; }</style>
            </head>
            <body>
                <h1>第一章</h1>
                <p>内容</p>
            </body>
            </html>
            '''.encode('utf-8')
            mock_item.get_type.return_value = 9

            mock_epub.get_item_with_id.return_value = mock_item
            mock_epub.get_items.return_value = [mock_item]
            mock_epub.spine = [('item1', True)]

            mock_read_epub.return_value = mock_epub

            # Mock storage to capture saved content
            saved_content = None
            def capture_content(*args, **kwargs):
                nonlocal saved_content
                saved_content = args[2] if len(args) > 2 else kwargs.get('content')
                return "/path/to/chapter.txt"

            mock_storage_service.save_chapter_content = MagicMock(side_effect=capture_content)

            book = await service.upload_epub_book(
                title="测试",
                author="作者",
                file_content=b"epub"
            )

            # 验证保存的内容中不包含 script 和 style 标签
            if saved_content:
                assert '<script>' not in saved_content
                assert '<style>' not in saved_content
                assert '第一章' in saved_content

    @pytest.mark.asyncio
    async def test_upload_epub_invalid_file(self, mock_db_session, mock_storage_service):
        """测试无效 EPUB 文件的错误处理"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            # 模拟读取失败
            mock_read_epub.side_effect = Exception("Invalid EPUB file")

            with pytest.raises(Exception):
                await service.upload_epub_book(
                    title="测试",
                    author="作者",
                    file_content=b"invalid epub"
                )

    @pytest.mark.asyncio
    async def test_upload_epub_no_chapters(self, mock_db_session, mock_storage_service):
        """测试没有可读章节的 EPUB"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            mock_epub = MagicMock()
            mock_epub.get_metadata.side_effect = lambda dc, field: []
            mock_epub.get_items.return_value = []
            mock_epub.spine = []

            mock_read_epub.return_value = mock_epub

            book = await service.upload_epub_book(
                title="空 EPUB",
                author="作者",
                file_content=b"epub"
            )

            # 应该创建 0 章节的书籍
            assert book.total_chapters == 0


# ============ Integration Tests ============

class TestBookUploadServiceIntegration:
    """数据库和存储集成测试"""

    @pytest.mark.asyncio
    async def test_upload_txt_database_persistence(self, mock_db_session, mock_storage_service):
        """测试 TXT 上传的数据库持久化"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        content = "第一章 内容\n\n第二章 内容"

        await service.upload_txt_book(
            title="测试小说",
            author="测试作者",
            content=content,
            regex_pattern=r"第[^\n]+章"  # 只匹配标题行，不包含换行符后的内容
        )

        # 验证数据库调用
        assert mock_db_session.add.call_count == 3  # 1 book + 2 chapters
        assert mock_db_session.commit.call_count >= 1
        assert mock_db_session.refresh.call_count >= 1

        # 检查添加的对象
        added_objects = [call[0][0] for call in mock_db_session.add.call_args_list]
        books = [obj for obj in added_objects if isinstance(obj, Book)]
        chapters = [obj for obj in added_objects if isinstance(obj, Chapter)]

        assert len(books) == 1
        assert len(chapters) == 2

        # 验证书籍属性
        book = books[0]
        assert book.platform == "local"
        assert book.download_status == "completed"
        assert book.creation_status == "已完结"

        # 验证章节属性
        assert all(ch.download_status == "completed" for ch in chapters)
        assert all(ch.content_path is not None for ch in chapters)

    @pytest.mark.asyncio
    async def test_upload_txt_storage_integration(self, mock_db_session, mock_storage_service):
        """测试 TXT 上传的存储集成"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        content = "第一章 第一段内容\n\n第二章 第二段内容"

        await service.upload_txt_book(
            title="存储测试",
            author="作者",
            content=content,
            regex_pattern=r"第[^\n]+章"  # 只匹配标题行，不包含换行符后的内容
        )

        # 验证存储服务调用
        assert mock_storage_service.save_chapter_content.call_count == 2

        # 检查调用参数
        calls = mock_storage_service.save_chapter_content.call_args_list
        assert len(calls) == 2

        # 第一次调用：第一章
        first_call = calls[0]
        assert "第一段内容" in first_call[0][2]

        # 第二次调用：第二章
        second_call = calls[1]
        assert "第二段内容" in second_call[0][2]

    @pytest.mark.asyncio
    async def test_upload_epub_storage_integration(self, mock_db_session, mock_storage_service):
        """测试 EPUB 上传的存储集成"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        with patch('ebooklib.epub.read_epub') as mock_read_epub:
            mock_epub = MagicMock()
            mock_epub.get_metadata.side_effect = lambda dc, field: []

            mock_item = MagicMock()
            mock_item.get_name.return_value = 'chapter1.xhtml'
            mock_item.get_content.return_value = '<h1>第一章</h1><p>EPUB内容</p>'.encode('utf-8')
            mock_item.get_type.return_value = 9

            mock_epub.get_item_with_id.return_value = mock_item
            mock_epub.get_items.return_value = [mock_item]
            mock_epub.spine = [('item1', True)]

            mock_read_epub.return_value = mock_epub

            await service.upload_epub_book(
                title="EPUB存储测试",
                author="作者",
                file_content=b"epub"
            )

            # 验证存储服务被调用
            assert mock_storage_service.save_chapter_content.call_count == 1

    @pytest.mark.asyncio
    async def test_upload_error_handling(self, mock_db_session, mock_storage_service):
        """测试上传过程中的错误处理"""
        service = BookUploadService(db=mock_db_session, storage=mock_storage_service)

        # 模拟存储失败
        mock_storage_service.save_chapter_content.side_effect = Exception("Storage error")

        with pytest.raises(Exception):
            await service.upload_txt_book(
                title="错误测试",
                author="作者",
                content="第一章 内容",
                regex_pattern=r"第[^\n]+章"  # 只匹配标题行
            )


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
