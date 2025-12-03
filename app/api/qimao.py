"""
七猫小说 API 客户端

基于 Rain API V3 的七猫小说接口封装
"""

import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.api.base import (
    RainAPIClient,
    Platform,
    APIType,
    AudioMode,
    APIError,
    BookNotFoundError,
    ChapterNotFoundError,
    InvalidResponseError,
)

logger = logging.getLogger(__name__)


class QimaoAPI(RainAPIClient):
    """
    七猫小说 API 客户端
    
    实现4个核心接口:
    - search: 搜索书籍 (type=1)
    - get_book_detail: 书籍详情 (type=2)
    - get_chapter_list: 章节列表 (type=3)
    - get_chapter_content: 章节内容 (type=4)
    
    与番茄的主要区别:
    - 搜索参数: wd (非keywords)
    - 页码处理: (page-1)*10
    - 章节内容: 需同时传 id (书籍) 和 chapterid (章节)
    - 字段名差异: original_title/title, words_num 等
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        初始化七猫小说API客户端
        
        Args:
            api_key: API密钥，默认从配置读取
            base_url: API基础URL，默认从配置读取
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            platform=Platform.QIMAO,
            timeout=timeout,
            max_retries=max_retries,
        )
        
        # 存储当前操作的书籍ID (用于章节内容获取)
        self._current_book_id: Optional[str] = None
    
    # ============ 辅助方法 ============
    
    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        """安全转换为整数"""
        if value is None:
            return default
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    # ============ 公共方法 ============
    
    async def search(
        self,
        keyword: str,
        page: int = 0,
        audio_mode: AudioMode = AudioMode.NONE,
    ) -> Dict[str, Any]:
        """
        搜索书籍
        
        Args:
            keyword: 搜索关键词
            page: 页码 (从0开始，与番茄保持一致)
            audio_mode: 音频模式 (七猫暂不支持，仅为接口兼容)
        
        Returns:
            {
                "books": [
                    {
                        "book_id": "123456789",
                        "book_name": "书名",
                        "author": "作者",
                        "cover_url": "封面URL",
                        "abstract": "简介",
                        "word_count": 1250000,
                        "creation_status": "连载中",
                        "score": 8.5,
                        "tags": "玄幻・热血"
                    },
                    ...
                ],
                "total": 100,
                "page": 0
            }
        
        Raises:
            APIError: API相关错误
        """
        # 七猫的页码需要转换: 传入page从0开始，API需要 page*10 的偏移量
        page_offset = page * 10
        
        params = {
            "wd": keyword,
            "page": page_offset,
        }
        
        response = await self._request(APIType.SEARCH, params)
        
        # 解析搜索结果
        books = self._parse_search_results(response)
        
        return {
            "books": books,
            "total": len(books),
            "page": page,
        }
    
    async def get_book_detail(self, book_id: str) -> Dict[str, Any]:
        """
        获取书籍详情
        
        Args:
            book_id: 书籍ID
        
        Returns:
            {
                "book_id": "123456789",
                "book_name": "书名",
                "author": "作者",
                "cover_url": "封面URL",
                "abstract": "简介",
                "word_count": 1250000,
                "category": "玄幻奇幻",
                "creation_status": "连载中",
                "score": 8.5,
                "last_chapter_title": "第125章 标题",
                "last_update_time": "2024-01-15 12:30:00",
                "tags": "玄幻・热血",
                "source": "七猫小说"
            }
        
        Raises:
            BookNotFoundError: 书籍不存在
            APIError: API相关错误
        """
        params = {"id": book_id}
        
        response = await self._request(APIType.BOOK_DETAIL, params)
        
        # 检查响应数据
        if not response.get("data"):
            raise BookNotFoundError(book_id, self.platform.value)
        
        book_data = response["data"].get("book", response["data"])
        
        # 存储书籍ID (用于后续章节内容获取)
        self._current_book_id = book_id
        
        # 转换封面URL
        cover_url = self.replace_cover_url(book_data.get("image_link", ""))
        
        # 解析更新时间
        update_timestamp = self._safe_int(book_data.get("update_time", 0))
        update_time = ""
        if update_timestamp:
            try:
                update_time = datetime.fromtimestamp(update_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError, TypeError):
                update_time = ""
        
        # 解析连载状态 (从 category_over_words 提取)
        category_info = book_data.get("category_over_words", "")
        creation_status = "已完结" if "完结" in category_info else "连载中"
        
        # 提取分类
        category = ""
        book_tags = book_data.get("book_tag_list", [])
        if book_tags:
            category = book_tags[0].get("title", "") if isinstance(book_tags[0], dict) else str(book_tags[0])
        
        return {
            "book_id": str(book_data.get("id", book_id)),
            "book_name": book_data.get("title") or book_data.get("original_title", ""),
            "author": book_data.get("author", ""),
            "cover_url": cover_url,
            "abstract": book_data.get("intro", ""),
            "word_count": self._safe_int(book_data.get("words_num", 0)),
            "category": category,
            "creation_status": creation_status,
            "score": self._safe_float(book_data.get("score", 0)),
            "last_chapter_title": book_data.get("latest_chapter_title", ""),
            "last_update_time": update_time,
            "last_update_timestamp": self._safe_int(update_timestamp),
            "tags": book_data.get("ptags", ""),  # 七猫的标签是字符串格式
            "source": book_data.get("source", "七猫小说"),
        }
    
    async def get_chapter_list(self, book_id: str) -> Dict[str, Any]:
        """
        获取章节列表
        
        Args:
            book_id: 书籍ID
        
        Returns:
            {
                "book_id": "123456789",
                "total_chapters": 125,
                "chapters": [
                    {
                        "chapter_id": "111111",
                        "item_id": "111111",  # 兼容番茄格式
                        "title": "第1章 标题",
                        "chapter_index": 0,
                        "word_count": 3245
                    },
                    ...
                ]
            }
        
        Raises:
            BookNotFoundError: 书籍不存在
            APIError: API相关错误
        """
        # 存储书籍ID
        self._current_book_id = book_id
        
        params = {"id": book_id}
        
        response = await self._request(APIType.CHAPTER_LIST, params)
        
        # 检查响应数据
        if not response.get("data"):
            raise BookNotFoundError(book_id, self.platform.value)
        
        chapter_list = response["data"].get("chapter_lists", [])
        
        chapters = []
        for index, item in enumerate(chapter_list):
            chapter_id = str(item.get("id", ""))
            
            chapter = {
                "chapter_id": chapter_id,
                "item_id": chapter_id,  # 兼容番茄格式
                "title": item.get("title", ""),
                "chapter_index": index,
                "word_count": self._safe_int(item.get("words", 0)),
                # 七猫章节列表不提供卷信息和时间
                "volume_name": "",
                "update_time": "",
                "update_timestamp": 0,
            }
            chapters.append(chapter)
        
        return {
            "book_id": book_id,
            "total_chapters": len(chapters),
            "chapters": chapters,
            "volumes": [],  # 七猫不提供卷信息
        }
    
    async def get_chapter_content(
        self,
        chapter_id: str,
        book_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        获取章节内容
        
        七猫需要同时传递书籍ID和章节ID
        
        Args:
            chapter_id: 章节ID
            book_id: 书籍ID (如果不传，使用上次获取详情时存储的ID)
        
        Returns:
            {
                "type": "text",
                "content": "章节正文内容...",
                "chapter_id": "111111"
            }
        
        Raises:
            ChapterNotFoundError: 章节不存在
            APIError: API相关错误
        """
        # 确定书籍ID
        effective_book_id = book_id or self._current_book_id
        if not effective_book_id:
            raise APIError("获取章节内容需要提供书籍ID", code="MISSING_BOOK_ID")
        
        params = {
            "id": effective_book_id,
            "chapterid": chapter_id,
        }
        
        response = await self._request(APIType.CHAPTER_CONTENT, params)
        
        # 解析内容
        content = ""
        if response.get("data"):
            content = response["data"].get("content", "")
        
        if not content:
            raise ChapterNotFoundError(chapter_id, self.platform.value)
        
        return {
            "type": "text",
            "content": content,
            "chapter_id": chapter_id,
        }
    
    def set_current_book_id(self, book_id: str):
        """
        设置当前操作的书籍ID
        
        用于批量获取章节内容时避免重复传递book_id
        
        Args:
            book_id: 书籍ID
        """
        self._current_book_id = book_id
    
    # ============ 工具方法 ============
    
    @staticmethod
    def replace_cover_url(original_url: str) -> str:
        """
        处理七猫封面URL
        
        移除尺寸后缀 (如 _300x400)
        
        Args:
            original_url: 原始封面URL
            
        Returns:
            处理后的封面URL
        """
        if not original_url:
            return ""
        
        # 移除尺寸后缀 _数字x数字
        cleaned_url = re.sub(r'_\d+x\d+', '', original_url)
        
        return cleaned_url
    
    # ============ 内部方法 ============
    
    def _parse_search_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析搜索结果
        
        Args:
            response: API响应数据
            
        Returns:
            书籍列表
        """
        if not isinstance(response, dict):
            raise InvalidResponseError(
                "搜索响应格式错误，期望 JSON 对象",
                str(response),
            )
        
        books_raw = []
        
        # 七猫搜索结果在 data.books 中
        if response.get("data"):
            books_raw = response["data"].get("books", [])
        
        if not isinstance(books_raw, list):
            raise InvalidResponseError(
                "搜索结果 data.books 格式错误，期望数组",
                str(response),
            )
        
        books = []
        for item in books_raw:
            if not isinstance(item, dict):
                raise InvalidResponseError(
                    "搜索结果项格式错误，期望对象",
                    str(item),
                )
            # 转换封面URL
            cover_url = self.replace_cover_url(item.get("image_link", ""))
            
            # 解析连载状态
            alias_title = item.get("alias_title", "")
            creation_status = "已完结" if "完结" in alias_title else "连载中"
            
            book = {
                "book_id": str(item.get("id", "")),
                "book_name": item.get("original_title") or item.get("title", ""),
                "author": item.get("original_author") or item.get("author", ""),
                "cover_url": cover_url,
                "abstract": item.get("intro", ""),
                "word_count": item.get("words_num", 0),
                "creation_status": creation_status,
                "score": item.get("score", 0),
                "tags": item.get("ptags", ""),  # 字符串格式
                "alias_title": alias_title,
            }
            
            # 只添加有效的书籍
            if book["book_id"]:
                books.append(book)
        
        return books
