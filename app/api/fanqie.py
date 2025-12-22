"""
番茄小说 API 客户端

基于 Rain API V3 的番茄小说接口封装
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


class FanqieAPI(RainAPIClient):
    """
    番茄小说 API 客户端
    
    实现4个核心接口:
    - search: 搜索书籍 (type=1)
    - get_book_detail: 书籍详情 (type=2)
    - get_chapter_list: 章节列表 (type=3)
    - get_chapter_content: 章节内容 (type=4)
    
    特性:
    - 支持AI朗读模式 (@前缀) 和真人朗读 (!前缀)
    - 自动转换封面URL为高质量版本
    - 统一的响应数据格式
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        初始化番茄小说API客户端
        
        Args:
            api_key: API密钥，默认从配置读取
            base_url: API基础URL，默认从配置读取
            timeout: 请求超时时间(秒)
            max_retries: 最大重试次数
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            platform=Platform.FANQIE,
            timeout=timeout,
            max_retries=max_retries,
        )
    
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
            page: 页码 (从0开始)
            audio_mode: 音频模式
                - AudioMode.NONE: 普通文本搜索
                - AudioMode.AI: AI朗读搜索 (@前缀)
                - AudioMode.REAL_PERSON: 真人朗读搜索 (!前缀)
        
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
                        "tags": ["玄幻", "热血"]
                    },
                    ...
                ],
                "total": 100,
                "page": 0,
                "audio_mode": "none"
            }
        
        Raises:
            APIError: API相关错误
        """
        # 处理音频模式前缀
        search_keyword = f"{audio_mode.value}{keyword}"
        
        params = {
            "keywords": search_keyword,
            "page": page,
        }
        
        response = await self._request(APIType.SEARCH, params)
        
        # 解析搜索结果
        books = self._parse_search_results(response)
        
        return {
            "books": books,
            "total": len(books),  # API未提供总数，返回当前页数量
            "page": page,
            "audio_mode": audio_mode.value or "none",
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
                "cover_url": "封面URL (已转换)",
                "abstract": "简介",
                "word_count": 1250000,
                "category": "玄幻奇幻",
                "creation_status": "连载中",
                "score": 8.5,
                "last_chapter_title": "第125章 标题",
                "last_update_time": "2024-01-15 12:30:00",
                "last_update_timestamp": 1698765432,
                "tags": ["玄幻", "热血"],
                "roles": ["主角1", "主角2"]
            }
        
        Raises:
            BookNotFoundError: 书籍不存在
            APIError: API相关错误
        """
        params = {"bookid": book_id}
        
        response = await self._request(APIType.BOOK_DETAIL, params)
        
        # 检查响应数据
        if not response.get("data"):
            raise BookNotFoundError(book_id, self.platform.value)
        
        book_data = response["data"]
        
        # 转换封面URL
        cover_url = self.replace_cover_url(book_data.get("thumb_url", ""))
        
        # 解析更新时间
        update_timestamp = self._safe_int(book_data.get("last_chapter_update_time", 0))
        update_time = ""
        if update_timestamp:
            try:
                update_time = datetime.fromtimestamp(update_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError, TypeError):
                update_time = ""
        
        # 解析连载状态
        # 修正：与 search 接口逻辑保持一致 (根据实际测试：0=完结，1=连载中)
        creation_status_code = self._safe_int(book_data.get("creation_status", 1))
        creation_status = "连载中" if creation_status_code == 1 else "已完结"
        
        return {
            "book_id": str(book_data.get("book_id", book_id)),
            "book_name": book_data.get("book_name", ""),
            "author": book_data.get("author", ""),
            "cover_url": cover_url,
            "abstract": book_data.get("abstract", ""),
            "word_count": self._safe_int(book_data.get("word_number", 0)),
            "category": book_data.get("category", ""),
            "creation_status": creation_status,
            "creation_status_code": creation_status_code,
            "score": self._safe_float(book_data.get("score", 0)),
            "last_chapter_title": book_data.get("last_chapter_title", ""),
            "last_update_time": update_time,
            "last_update_timestamp": update_timestamp,
            "tags": book_data.get("tags", []),
            "roles": book_data.get("roles", []),
            "gender": self._safe_int(book_data.get("gender", 0)),  # 1=男频, 2=女频
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
                        "item_id": "111111",
                        "title": "第1章 标题",
                        "volume_name": "第一卷 卷名",
                        "chapter_index": 0,
                        "word_count": 3245,
                        "update_time": "2024-01-15 10:00:00",
                        "update_timestamp": 1698765400
                    },
                    ...
                ],
                "volumes": [
                    {
                        "name": "第一卷 卷名",
                        "chapter_count": 50
                    },
                    ...
                ]
            }
        
        Raises:
            BookNotFoundError: 书籍不存在
            APIError: API相关错误
        """
        params = {"bookid": book_id}
        
        response = await self._request(APIType.CHAPTER_LIST, params)
        
        # 检查响应数据
        if not response.get("data"):
            raise BookNotFoundError(book_id, self.platform.value)
        
        toc_data = response["data"]
        item_list = toc_data.get("item_data_list", [])
        
        chapters = []
        volumes_map: Dict[str, int] = {}  # 卷名 -> 章节数
        
        for index, item in enumerate(item_list):
            # 解析时间戳
            update_timestamp = self._safe_int(item.get("first_pass_time", 0))
            update_time = ""
            if update_timestamp:
                try:
                    update_time = datetime.fromtimestamp(update_timestamp).strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, OSError, TypeError):
                    update_time = ""
            
            volume_name = item.get("volume_name", "") or ""
            
            chapter = {
                "item_id": str(item.get("item_id", "")),
                "title": item.get("title", ""),
                "volume_name": volume_name,
                "chapter_index": index,
                "word_count": self._safe_int(item.get("chapter_word_number", 0)),
                "update_time": update_time,
                "update_timestamp": update_timestamp,
            }
            chapters.append(chapter)
            
            # 统计卷信息
            if volume_name:
                volumes_map[volume_name] = volumes_map.get(volume_name, 0) + 1
        
        # 构建卷列表
        volumes = [
            {"name": name, "chapter_count": count}
            for name, count in volumes_map.items()
        ]
        
        return {
            "book_id": book_id,
            "total_chapters": len(chapters),
            "chapters": chapters,
            "volumes": volumes,
        }
    
    async def get_chapter_content(
        self,
        chapter_id: str,
        tone_id: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        获取章节内容
        
        Args:
            chapter_id: 章节ID (item_id)
            tone_id: 音色ID (用于AI朗读模式)
                - 74: 成熟大叔升级版
                - 4: 成熟大叔
                - 0: 甜美少女
                - 5: 开朗青年
                - 2: 清亮青叔
                - 6: 温柔淑女
        
        Returns:
            # 文本模式
            {
                "type": "text",
                "content": "章节正文内容...",
                "chapter_id": "111111"
            }
            
            # 音频模式
            {
                "type": "audio",
                "audio_url": "https://audio.example.com/xxx.mp3",
                "duration": 356,
                "chapter_id": "111111",
                "tone_changed": False
            }
        
        Raises:
            ChapterNotFoundError: 章节不存在
            APIError: API相关错误
        """
        params = {"itemid": chapter_id}
        
        if tone_id is not None:
            params["tone_id"] = tone_id
        
        response = await self._request(APIType.CHAPTER_CONTENT, params)
        
        # 检查响应类型
        content_type = response.get("type", "text")
        
        if content_type == "audio":
            # 音频模式
            audio_data = response.get("data", {})
            return {
                "type": "audio",
                "audio_url": audio_data.get("audio1", ""),
                "duration": audio_data.get("duration", 0),
                "chapter_id": chapter_id,
                "tone_changed": response.get("change", "false") == "true",
            }
        else:
            # 文本模式
            content_data = response.get("data", {})
            content = content_data.get("content", "")
            
            if not content:
                raise ChapterNotFoundError(chapter_id, self.platform.value)
            
            return {
                "type": "text",
                "content": content,
                "chapter_id": chapter_id,
            }
    
    # ============ 工具方法 ============
    
    @staticmethod
    def replace_cover_url(original_url: str) -> str:
        """
        转换番茄封面URL为高质量版本
        
        原始URL格式:
        - https://sf1-ttcdn-tos.pstatp.com/img/novel-static/xxx~300x400.image
        - https://p3-novel.byteimg.com/origin/abc123.jpg?query=params
        
        目标URL格式:
        - https://p6-novel.byteimg.com/origin/novel-static/xxx.image
        
        转换规则:
        1. 移除 https:// 或 http:// 协议前缀
        2. 替换域名为 p6-novel.byteimg.com/origin
        3. 移除 ~ 后的尺寸信息 (如 ~300x400)
        4. 移除 ? 后的查询参数
        
        Args:
            original_url: 原始封面URL
            
        Returns:
            转换后的高质量封面URL
        """
        if not original_url:
            return ""
        
        url = original_url
        
        # 移除协议前缀
        if url.startswith("https://"):
            url = url[8:]
        elif url.startswith("http://"):
            url = url[7:]
        
        # 分割路径
        parts = url.split("/")
        
        if len(parts) < 2:
            return original_url  # 无法解析，返回原始URL
        
        # 替换域名为目标域名
        parts[0] = "p6-novel.byteimg.com"
        
        # 在第一个路径段后插入 origin
        if len(parts) > 1 and parts[1] != "origin":
            parts.insert(1, "origin")
        
        # 清理每个路径段
        cleaned_parts = []
        for part in parts:
            # 移除查询参数
            if "?" in part:
                part = part.split("?")[0]
            # 移除波浪号后缀 (尺寸信息)
            if "~" in part:
                part = part.split("~")[0]
            cleaned_parts.append(part)
        
        return "https://" + "/".join(cleaned_parts)
    
    # ============ 内部方法 ============
    
    def _parse_search_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析搜索结果
        
        处理两种响应格式:
        1. 直接在 data 字段中
        2. 在 search_tabs[].data 中
        
        Args:
            response: API响应数据
            
        Returns:
            书籍列表
        """
        if not isinstance(response, dict):
            logger.warning("Fanqie search response is not a dict, got %s", type(response).__name__)
            return []
        
        books_raw: List[Any] = []
        
        # 检查 search_tabs 格式
        search_tabs = response.get("search_tabs")
        if search_tabs and isinstance(search_tabs, list):
            for tab in search_tabs:
                if tab.get("data"):
                    books_raw = tab["data"]
                    break
        
        # 如果 search_tabs 为空或无效，使用 data 字段
        if not books_raw:
            raw_data = response.get("data", [])
            if isinstance(raw_data, list):
                books_raw = raw_data
            elif isinstance(raw_data, dict):
                # 某些返回会把列表包在 data.data 或 data.books 中
                if isinstance(raw_data.get("data"), list):
                    books_raw = raw_data.get("data")  # type: ignore[assignment]
                elif isinstance(raw_data.get("books"), list):
                    books_raw = raw_data.get("books")  # type: ignore[assignment]
                else:
                    # 将单个对象包装为列表，避免抛 502
                    logger.warning("Fanqie search data is dict, wrapping into list; keys=%s", list(raw_data.keys()))
                    books_raw = [raw_data]
            else:
                logger.warning("Fanqie search data is unexpected type: %s", type(raw_data).__name__)
                books_raw = []
        
        # 解析书籍数据
        books = []
        for item in books_raw:
            if not isinstance(item, dict):
                logger.warning("Skip invalid search item type: %s", type(item).__name__)
                continue
            # 某些响应格式中书籍数据在 book_data 数组中
            book_data = item
            if "book_data" in item and isinstance(item["book_data"], list):
                book_data = item["book_data"][0] if item["book_data"] else item
            
            # 转换封面URL
            cover_url = self.replace_cover_url(book_data.get("thumb_url", ""))
            
            # 解析连载状态
            # 注意：根据实际测试，API返回的值与文档相反！
            # 0 = 完结，1 = 连载中
            creation_status_code = self._safe_int(book_data.get("creation_status", 1))
            creation_status = "连载中" if creation_status_code == 1 else "已完结"
            
            book = {
                "book_id": str(book_data.get("book_id", "")),
                "book_name": book_data.get("book_name", ""),
                "author": book_data.get("author", ""),
                "cover_url": cover_url,
                "abstract": book_data.get("abstract", ""),
                "word_count": self._safe_int(book_data.get("word_number", 0)),
                "creation_status": creation_status,
                "creation_status_code": creation_status_code,
                "score": self._safe_float(book_data.get("score", 0)),
                "tags": book_data.get("tags", []),
                "sub_info": book_data.get("sub_info", ""),
                "gender": self._safe_int(book_data.get("gender", 0)),
            }
            
            # 只添加有效的书籍
            if book["book_id"]:
                books.append(book)
        
        return books
