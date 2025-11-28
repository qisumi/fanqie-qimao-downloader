"""
API 客户端单元测试

使用 pytest 和 httpx Mock 测试 FanqieAPI 和 QimaoAPI
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date
import json

import httpx

from app.api import (
    FanqieAPI,
    QimaoAPI,
    APIError,
    QuotaExceededError,
    NetworkError,
    BookNotFoundError,
    ChapterNotFoundError,
    AudioMode,
)
from app.utils import RateLimiter


# ============ 辅助函数 ============

def create_mock_response(status_code: int, json_data: dict) -> httpx.Response:
    """创建带有 request 实例的 Mock Response"""
    request = httpx.Request("GET", "http://test.api/")
    response = httpx.Response(status_code, json=json_data, request=request)
    return response


# ============ 测试数据 ============

MOCK_SEARCH_RESPONSE_FANQIE = {
    "message": "SUCCESS",
    "data": [
        {
            "book_id": "7123456789",
            "book_name": "禁神之下",
            "author": "夜雨声烦",
            "thumb_url": "https://p3-novel.byteimg.com/origin/abc123.jpg",
            "abstract": "这是一个关于神明与凡人的故事...",
            "word_number": 1250000,
            "gender": 1,
            "creation_status": 0,
            "score": 8.5,
            "tags": ["玄幻", "热血", "成长"],
        }
    ],
    "search_tabs": None,
}

MOCK_BOOK_DETAIL_RESPONSE = {
    "data": {
        "book_id": "7123456789",
        "book_name": "禁神之下",
        "author": "夜雨声烦",
        "thumb_url": "https://p3-novel.byteimg.com/origin/abc123~300x400.jpg",
        "abstract": "在神明统治的世界里...",
        "word_number": 1250000,
        "category": "玄幻奇幻",
        "gender": 1,
        "creation_status": 0,
        "score": 8.5,
        "last_chapter_update_time": 1700000000,
        "last_chapter_title": "第125章 神战开启",
        "tags": ["玄幻", "热血"],
    }
}

MOCK_CHAPTER_LIST_RESPONSE = {
    "data": {
        "item_data_list": [
            {
                "volume_name": "第一卷 凡人崛起",
                "item_id": "111111",
                "title": "第1章 禁神觉醒",
                "chapter_word_number": 3245,
                "first_pass_time": 1698765400,
            },
            {
                "volume_name": "第一卷 凡人崛起",
                "item_id": "111112",
                "title": "第2章 神秘老者",
                "chapter_word_number": 2987,
                "first_pass_time": 1698851800,
            },
        ]
    }
}

MOCK_CHAPTER_CONTENT_RESPONSE = {
    "type": "text",
    "data": {
        "content": "林风站在悬崖边，望着远方巍峨的神殿...",
    }
}

MOCK_AUDIO_CONTENT_RESPONSE = {
    "type": "audio",
    "change": "false",
    "data": {
        "audio1": "https://audio.example.com/chapter/111111.mp3",
        "duration": 356,
    }
}

MOCK_ERROR_RESPONSE = {
    "message": "ERROR",
    "data": {
        "content": "今日阅读章节数已达上限"
    }
}

# 七猫测试数据
MOCK_SEARCH_RESPONSE_QIMAO = {
    "data": {
        "books": [
            {
                "id": "12345",
                "original_title": "测试小说",
                "original_author": "测试作者",
                "image_link": "https://example.com/cover_300x400.jpg",
                "intro": "这是一个测试简介",
                "words_num": 500000,
                "score": 7.5,
                "ptags": "玄幻・热血",
                "alias_title": "连载中",
            }
        ]
    }
}

MOCK_QIMAO_BOOK_DETAIL = {
    "data": {
        "book": {
            "id": "12345",
            "title": "测试小说",
            "author": "测试作者",
            "image_link": "https://example.com/cover_300x400.jpg",
            "intro": "详细简介...",
            "words_num": 500000,
            "score": 7.5,
            "latest_chapter_title": "第100章",
            "update_time": 1700000000,
            "ptags": "玄幻・热血",
            "source": "七猫小说",
            "category_over_words": "玄幻・100万字",
            "book_tag_list": [{"title": "玄幻"}],
        }
    }
}

MOCK_QIMAO_CHAPTER_LIST = {
    "data": {
        "chapter_lists": [
            {"id": "1001", "title": "第1章 开始", "words": 2500},
            {"id": "1002", "title": "第2章 继续", "words": 3000},
        ]
    }
}


# ============ FanqieAPI 测试 ============

class TestFanqieAPI:
    """FanqieAPI 测试类"""
    
    @pytest.fixture
    def api(self):
        """创建测试用的 API 实例"""
        return FanqieAPI(api_key="test_key", base_url="http://test.api")
    
    @pytest.mark.asyncio
    async def test_search_success(self, api):
        """测试搜索成功"""
        mock_response = create_mock_response(200, MOCK_SEARCH_RESPONSE_FANQIE)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.search("禁神之下")
            
            assert "books" in result
            assert len(result["books"]) == 1
            assert result["books"][0]["book_id"] == "7123456789"
            assert result["books"][0]["book_name"] == "禁神之下"
    
    @pytest.mark.asyncio
    async def test_search_with_audio_mode(self, api):
        """测试音频模式搜索"""
        mock_response = create_mock_response(200, MOCK_SEARCH_RESPONSE_FANQIE)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response) as mock_get:
            await api.search("禁神之下", audio_mode=AudioMode.AI)
            
            # 验证请求参数包含 @ 前缀
            call_args = mock_get.call_args
            params = call_args.kwargs.get('params', {})
            assert "@禁神之下" in params.get("keywords", "")
    
    @pytest.mark.asyncio
    async def test_get_book_detail_success(self, api):
        """测试获取书籍详情成功"""
        mock_response = create_mock_response(200, MOCK_BOOK_DETAIL_RESPONSE)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.get_book_detail("7123456789")
            
            assert result["book_id"] == "7123456789"
            assert result["book_name"] == "禁神之下"
            assert result["creation_status"] == "连载中"
            # 验证封面URL转换
            assert "p6-novel.byteimg.com" in result["cover_url"]
            assert "~300x400" not in result["cover_url"]
    
    @pytest.mark.asyncio
    async def test_get_book_detail_not_found(self, api):
        """测试书籍不存在"""
        mock_response = create_mock_response(200, {"data": None})
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            with pytest.raises(BookNotFoundError) as exc_info:
                await api.get_book_detail("invalid_id")
            
            assert exc_info.value.book_id == "invalid_id"
    
    @pytest.mark.asyncio
    async def test_get_chapter_list_success(self, api):
        """测试获取章节列表成功"""
        mock_response = create_mock_response(200, MOCK_CHAPTER_LIST_RESPONSE)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.get_chapter_list("7123456789")
            
            assert result["book_id"] == "7123456789"
            assert result["total_chapters"] == 2
            assert len(result["chapters"]) == 2
            assert result["chapters"][0]["item_id"] == "111111"
            assert result["chapters"][0]["title"] == "第1章 禁神觉醒"
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_text(self, api):
        """测试获取文本章节内容"""
        mock_response = create_mock_response(200, MOCK_CHAPTER_CONTENT_RESPONSE)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.get_chapter_content("111111")
            
            assert result["type"] == "text"
            assert "林风" in result["content"]
            assert result["chapter_id"] == "111111"
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_audio(self, api):
        """测试获取音频章节内容"""
        mock_response = create_mock_response(200, MOCK_AUDIO_CONTENT_RESPONSE)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.get_chapter_content("111111", tone_id=74)
            
            assert result["type"] == "audio"
            assert "mp3" in result["audio_url"]
            assert result["duration"] == 356
            assert result["tone_changed"] is False
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_error(self, api):
        """测试配额超限错误"""
        mock_response = create_mock_response(200, MOCK_ERROR_RESPONSE)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            with pytest.raises(QuotaExceededError) as exc_info:
                await api.get_chapter_content("111111")
            
            assert exc_info.value.platform == "fanqie"
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, api):
        """测试网络错误重试"""
        # 前两次失败，第三次成功
        call_count = 0
        
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            return create_mock_response(200, MOCK_SEARCH_RESPONSE_FANQIE)
        
        with patch.object(httpx.AsyncClient, 'get', side_effect=mock_get):
            result = await api.search("test")
            
            assert call_count == 3
            assert len(result["books"]) == 1
    
    def test_replace_cover_url(self):
        """测试封面URL转换"""
        # 测试带波浪号的URL
        url1 = "https://sf1-ttcdn-tos.pstatp.com/img/novel-static/abc~300x400.image"
        result1 = FanqieAPI.replace_cover_url(url1)
        assert "p6-novel.byteimg.com" in result1
        assert "~300x400" not in result1
        
        # 测试带查询参数的URL
        url2 = "https://p3-novel.byteimg.com/origin/abc.jpg?x-expires=123"
        result2 = FanqieAPI.replace_cover_url(url2)
        assert "?" not in result2
        
        # 测试空URL
        assert FanqieAPI.replace_cover_url("") == ""
        assert FanqieAPI.replace_cover_url(None) == ""


# ============ QimaoAPI 测试 ============

class TestQimaoAPI:
    """QimaoAPI 测试类"""
    
    @pytest.fixture
    def api(self):
        """创建测试用的 API 实例"""
        return QimaoAPI(api_key="test_key", base_url="http://test.api")
    
    @pytest.mark.asyncio
    async def test_search_success(self, api):
        """测试搜索成功"""
        mock_response = create_mock_response(200, MOCK_SEARCH_RESPONSE_QIMAO)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.search("测试")
            
            assert "books" in result
            assert len(result["books"]) == 1
            assert result["books"][0]["book_id"] == "12345"
            assert result["books"][0]["book_name"] == "测试小说"
    
    @pytest.mark.asyncio
    async def test_search_page_conversion(self, api):
        """测试页码转换 page*10 (page从0开始)"""
        mock_response = create_mock_response(200, MOCK_SEARCH_RESPONSE_QIMAO)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response) as mock_get:
            await api.search("测试", page=2)
            
            call_args = mock_get.call_args
            params = call_args.kwargs.get('params', {})
            # page=2 应该转换为 offset=20 (page从0开始，与番茄一致)
            assert params.get("page") == 20
    
    @pytest.mark.asyncio
    async def test_get_book_detail_success(self, api):
        """测试获取书籍详情成功"""
        mock_response = create_mock_response(200, MOCK_QIMAO_BOOK_DETAIL)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.get_book_detail("12345")
            
            assert result["book_id"] == "12345"
            assert result["book_name"] == "测试小说"
            # 验证封面URL尺寸后缀被移除
            assert "_300x400" not in result["cover_url"]
    
    @pytest.mark.asyncio
    async def test_get_chapter_list_success(self, api):
        """测试获取章节列表成功"""
        mock_response = create_mock_response(200, MOCK_QIMAO_CHAPTER_LIST)
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):
            result = await api.get_chapter_list("12345")
            
            assert result["total_chapters"] == 2
            assert result["chapters"][0]["chapter_id"] == "1001"
            assert result["chapters"][0]["item_id"] == "1001"  # 兼容字段
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_with_book_id(self, api):
        """测试获取章节内容 (需要 book_id)"""
        mock_response = create_mock_response(200, {"data": {"content": "章节内容..."}})
        
        with patch.object(httpx.AsyncClient, 'get', return_value=mock_response) as mock_get:
            result = await api.get_chapter_content("1001", book_id="12345")
            
            assert result["type"] == "text"
            assert result["content"] == "章节内容..."
            
            # 验证参数包含 id 和 chapterid
            call_args = mock_get.call_args
            params = call_args.kwargs.get('params', {})
            assert params.get("id") == "12345"
            assert params.get("chapterid") == "1001"
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_uses_stored_book_id(self, api):
        """测试章节内容使用存储的 book_id"""
        # 先调用 get_book_detail 存储 book_id
        detail_response = create_mock_response(200, MOCK_QIMAO_BOOK_DETAIL)
        content_response = create_mock_response(200, {"data": {"content": "内容"}})
        
        with patch.object(httpx.AsyncClient, 'get', side_effect=[detail_response, content_response]):
            await api.get_book_detail("12345")
            result = await api.get_chapter_content("1001")  # 不传 book_id
            
            assert result["content"] == "内容"
    
    @pytest.mark.asyncio
    async def test_get_chapter_content_missing_book_id(self, api):
        """测试缺少 book_id 时抛出错误"""
        with pytest.raises(APIError) as exc_info:
            await api.get_chapter_content("1001")
        
        assert "MISSING_BOOK_ID" in str(exc_info.value.code)
    
    def test_replace_cover_url(self):
        """测试封面URL转换"""
        url = "https://example.com/cover_300x400.jpg"
        result = QimaoAPI.replace_cover_url(url)
        
        assert "_300x400" not in result
        assert result == "https://example.com/cover.jpg"


# ============ RateLimiter 测试 ============

class TestRateLimiter:
    """RateLimiter 测试类"""
    
    @pytest.fixture
    def mock_session(self):
        """创建 Mock 数据库会话"""
        session = MagicMock()
        return session
    
    @pytest.fixture
    def limiter(self, mock_session):
        """创建测试用的限制器"""
        return RateLimiter(db_session=mock_session, limit=20000000)  # 2000万字
    
    def test_can_download_no_quota_record(self, limiter, mock_session):
        """测试没有配额记录时可以下载"""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        assert limiter.can_download("fanqie") is True
    
    def test_can_download_under_limit(self, limiter, mock_session):
        """测试在限额内可以下载"""
        mock_quota = MagicMock()
        mock_quota.words_downloaded = 10000000  # 1000万字
        mock_session.query.return_value.filter.return_value.first.return_value = mock_quota
        
        assert limiter.can_download("fanqie") is True
    
    def test_can_download_at_limit(self, limiter, mock_session):
        """测试达到限额时不能下载"""
        mock_quota = MagicMock()
        mock_quota.words_downloaded = 20000000  # 2000万字
        mock_session.query.return_value.filter.return_value.first.return_value = mock_quota
        
        assert limiter.can_download("fanqie") is False
    
    def test_record_download_creates_quota(self, limiter, mock_session):
        """测试记录下载会创建配额记录"""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        limiter.record_download("fanqie", word_count=5000)
        
        # 验证调用了 add
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_record_download_updates_quota(self, limiter, mock_session):
        """测试记录下载会更新配额"""
        mock_quota = MagicMock()
        mock_quota.words_downloaded = 5000000  # 500万字
        mock_session.query.return_value.filter.return_value.first.return_value = mock_quota
        
        result = limiter.record_download("fanqie", word_count=50000)
        
        assert mock_quota.words_downloaded == 5050000  # 500万 + 5万
        assert result == 5050000
    
    def test_get_remaining_no_quota(self, limiter, mock_session):
        """测试没有记录时返回完整配额"""
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        assert limiter.get_remaining("fanqie") == 20000000  # 2000万字
    
    def test_get_remaining_with_usage(self, limiter, mock_session):
        """测试有使用记录时返回剩余配额"""
        mock_quota = MagicMock()
        mock_quota.words_downloaded = 15000000  # 1500万字
        mock_session.query.return_value.filter.return_value.first.return_value = mock_quota
        
        assert limiter.get_remaining("fanqie") == 5000000  # 剩余500万字
    
    def test_get_usage(self, limiter, mock_session):
        """测试获取使用情况"""
        mock_quota = MagicMock()
        mock_quota.words_downloaded = 10000000  # 1000万字
        mock_session.query.return_value.filter.return_value.first.return_value = mock_quota
        
        usage = limiter.get_usage("fanqie")
        
        assert usage["downloaded"] == 10000000
        assert usage["limit"] == 20000000
        assert usage["remaining"] == 10000000
        assert usage["percentage"] == 50.0
    
    def test_no_session_raises_error(self):
        """测试没有设置会话时抛出错误"""
        limiter = RateLimiter(limit=20000000)
        
        with pytest.raises(RuntimeError) as exc_info:
            limiter.can_download("fanqie")
        
        assert "数据库会话未设置" in str(exc_info.value)
    
    def test_get_seconds_until_reset(self):
        """测试获取重置倒计时"""
        seconds = RateLimiter.get_seconds_until_reset()
        
        # 应该返回一个正数 (距离明天0点的秒数)
        assert seconds >= 0
        assert seconds <= 86400  # 不超过24小时


# ============ 集成测试 ============

class TestAPIClientIntegration:
    """API客户端集成测试"""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试上下文管理器"""
        async with FanqieAPI(api_key="test") as api:
            assert api._client is None or not api._client.is_closed
        
        # 退出后客户端应该关闭
        # 注意: 由于延迟初始化，如果没有请求，_client 可能仍为 None
    
    @pytest.mark.asyncio
    async def test_fanqie_complete_flow(self):
        """测试番茄完整流程: 搜索 -> 详情 -> 章节列表 -> 内容"""
        search_response = create_mock_response(200, MOCK_SEARCH_RESPONSE_FANQIE)
        detail_response = create_mock_response(200, MOCK_BOOK_DETAIL_RESPONSE)
        chapters_response = create_mock_response(200, MOCK_CHAPTER_LIST_RESPONSE)
        content_response = create_mock_response(200, MOCK_CHAPTER_CONTENT_RESPONSE)
        
        responses = [search_response, detail_response, chapters_response, content_response]
        
        async with FanqieAPI(api_key="test") as api:
            with patch.object(httpx.AsyncClient, 'get', side_effect=responses):
                # 1. 搜索
                search_result = await api.search("禁神之下")
                assert len(search_result["books"]) > 0
                book_id = search_result["books"][0]["book_id"]
                
                # 2. 获取详情
                detail = await api.get_book_detail(book_id)
                assert detail["book_name"] == "禁神之下"
                
                # 3. 获取章节列表
                chapters = await api.get_chapter_list(book_id)
                assert chapters["total_chapters"] > 0
                chapter_id = chapters["chapters"][0]["item_id"]
                
                # 4. 获取章节内容
                content = await api.get_chapter_content(chapter_id)
                assert content["type"] == "text"
                assert len(content["content"]) > 0
