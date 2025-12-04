"""
笔趣阁 API 客户端

参考 reference/BIQUGE_EXAMPLE.md，直接调用站点接口解析搜索、详情、目录和章节内容。
"""

import html
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.api.base import (
    APIError,
    AudioMode,
    BookNotFoundError,
    ChapterNotFoundError,
    InvalidResponseError,
    Platform,
    RainAPIClient,
)

logger = logging.getLogger(__name__)


class BiqugeAPI(RainAPIClient):
    """
    笔趣阁 API 客户端
    
    直接抓取笔趣阁站点:
    - 搜索: https://www.510f2f.xyz/api/search?q=关键词
    - 详情: https://www.510f2f.xyz/api/book?id={book_id}
    - 目录: https://www.510f2f.xyz/api/booklist?id={book_id}
    - 章节内容: https://m.510f2f.xyz/api/chapter?id={book_id}&chapterid={chapter_id}
    """
    
    SEARCH_URL = "https://www.510f2f.xyz/api/search"
    DETAIL_API_URL = "https://www.510f2f.xyz/api/book"
    BOOKLIST_API_URL = "https://www.510f2f.xyz/api/booklist"
    CONTENT_API_URL = "https://www.510f2f.xyz/api/chapter"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            platform=Platform.BIQUGE,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._current_book_id: Optional[str] = None  # 内容接口需要的book_id
        self._resolved_ids: Dict[str, str] = {}  # 请求ID -> 解析出的真实ID
    
    # ============ 工具方法 ============
    
    @staticmethod
    def _strip_html(text: str) -> str:
        """去除简介中的简单 HTML 标记并做反转义。"""
        if not text:
            return ""
        cleaned = re.sub(r"<[^>]+>", "", text)
        return html.unescape(cleaned).strip()

    @staticmethod
    def _clean_content(content: str) -> str:
        """
        清理章节正文中的占位文本。
        笔趣阁返回的正文里偶尔会插入“<<---展开全部章节--->>”提示，需要过滤掉。
        """
        if not content:
            return ""
        cleaned = content.replace("<<---展开全部章节--->>", "")
        # 合并多余的空行，避免删除占位后出现大片空白
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()
    
    @staticmethod
    def _extract_book_id(url_path: str) -> str:
        """从 /book/12345/ 这样的路径中提取数字ID。"""
        if not url_path:
            return ""
        match = re.search(r"/book/(\d+)/?", url_path)
        if match:
            return match.group(1)
        return url_path.strip("/").split("/")[-1]
    
    # ============ 公共接口 ============
    
    async def search(
        self,
        keyword: str,
        page: int = 0,
        audio_mode: AudioMode = AudioMode.NONE,
    ) -> Dict[str, Any]:
        """搜索书籍，使用站点新的 JSON 接口，不分页。"""
        _ = audio_mode  # 保留参数以兼容接口，当前站点不区分音频模式
        try:
            client = await self._get_client()
            response = await client.get(
                self.SEARCH_URL,
                params={"q": keyword},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise APIError(f"搜索请求失败: {exc}") from exc
        
        try:
            data = response.json()
        except ValueError:
            raise InvalidResponseError("搜索响应解析失败", response.text)
        
        if not isinstance(data, dict) or "data" not in data:
            raise InvalidResponseError("搜索响应格式错误，期望包含 data 字段", response.text)
        
        books = []
        for item in data.get("data", []):
            if not isinstance(item, dict):
                logger.warning("Skip invalid search item: %s", item)
                continue
            book_id = str(item.get("id", "")).strip()
            if not book_id:
                continue
            abstract = self._strip_html(item.get("intro", ""))
            # 站点未直接返回封面，按约定路径拼接: /bookimg/{head}/{bookid}.jpg，其中 head 为去掉末 3 位
            head = book_id[:-3] if len(book_id) > 3 else book_id
            cover_url = f"https://www.510f2f.xyz/bookimg/{head}/{book_id}.jpg"
            
            books.append({
                "book_id": book_id,
                "book_name": item.get("title", ""),
                "author": item.get("author", ""),
                "cover_url": cover_url,
                "abstract": abstract,
                "word_count": 0,
                "creation_status": item.get("full", "") or "连载中",
                "creation_status_code": 1 if "完" in (item.get("full", "") or "") else 0,
                "score": 0.0,
                "tags": [],
                "sub_info": book_id,
                "gender": 0,
            })
        
        return {
            "books": books,
            "total": len(books),
            "page": page,
            "audio_mode": "none",
        }
    
    async def get_book_detail(self, book_id: str) -> Dict[str, Any]:
        """获取书籍详情，同时解析最新章节信息。"""
        try:
            client = await self._get_client()
            response = await client.get(self.DETAIL_API_URL, params={"id": book_id})
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise APIError(f"详情请求失败: {exc}") from exc
        except ValueError:
            raise InvalidResponseError("详情响应解析失败", response.text if 'response' in locals() else None)
        
        if not isinstance(data, dict) or not data.get("id"):
            raise BookNotFoundError(book_id, self.platform.value)
        
        resolved_id = str(data.get("dirid") or data.get("id") or book_id)
        self._resolved_ids[book_id] = resolved_id
        self._current_book_id = resolved_id
        
        creation_status = data.get("full") or ""
        creation_status_code = 1 if "完" in creation_status else 0
        
        last_update_time = data.get("lastupdate") or ""
        last_update_timestamp = 0
        if last_update_time:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    last_update_timestamp = int(datetime.strptime(last_update_time, fmt).timestamp())
                    break
                except Exception:
                    continue
        
        abstract = self._strip_html(data.get("intro", ""))
        
        return {
            "book_id": resolved_id,
            "source_book_id": book_id,
            "book_name": data.get("title", ""),
            "author": data.get("author", ""),
            "cover_url": "",
            "abstract": abstract,
            "word_count": 0,
            "category": data.get("sortname", ""),
            "creation_status": creation_status or "连载中",
            "creation_status_code": creation_status_code,
            "score": 0.0,
            "last_chapter_title": data.get("lastchapter", ""),
            "last_update_time": last_update_time,
            "last_update_timestamp": last_update_timestamp,
            "tags": [],
            "roles": [],
            "gender": 0,
        }
    
    async def get_chapter_list(self, book_id: str) -> Dict[str, Any]:
        """解析目录列表。"""
        try:
            client = await self._get_client()
            response = await client.get(self.BOOKLIST_API_URL, params={"id": book_id})
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise APIError(f"目录请求失败: {exc}") from exc
        except ValueError:
            raise InvalidResponseError("目录响应解析失败", response.text if 'response' in locals() else None)
        
        chapter_list = data.get("list")
        if not isinstance(chapter_list, list):
            raise InvalidResponseError("目录响应格式错误，期望 list 字段", response.text)
        
        resolved_id = str(data.get("dirid") or book_id)
        self._resolved_ids[book_id] = resolved_id
        self._current_book_id = resolved_id
        
        chapters: List[Dict[str, Any]] = []
        for idx, title in enumerate(chapter_list, start=1):
            chapters.append({
                "item_id": str(idx),
                "title": str(title),
                "volume_name": "",
                "chapter_index": idx - 1,
                "word_count": 0,
                "update_time": "",
                "update_timestamp": 0,
            })
        
        return {
            "book_id": resolved_id,
            "total_chapters": len(chapters),
            "chapters": chapters,
            "volumes": [],
        }
    
    async def get_chapter_content(
        self,
        chapter_id: str,
        book_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """获取章节正文内容。"""
        if book_id:
            self.set_current_book_id(book_id)
        
        effective_book_id = book_id or self._current_book_id or self._resolved_ids.get(book_id or "", "")
        if not effective_book_id and self._resolved_ids:
            # 兜底使用最近解析到的ID
            effective_book_id = list(self._resolved_ids.values())[-1]
        if not effective_book_id:
            raise APIError("获取笔趣阁章节内容需要提供 book_id", code="MISSING_BOOK_ID")
        
        try:
            client = await self._get_client()
            response = await client.get(
                self.CONTENT_API_URL,
                params={"id": effective_book_id, "chapterid": chapter_id},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise APIError(f"章节请求失败: {exc}") from exc
        except ValueError:
            raise InvalidResponseError("章节内容解析失败", response.text)
        
        if not isinstance(data, dict):
            raise InvalidResponseError("章节内容响应格式错误", response.text)
        
        content = self._clean_content(data.get("txt", ""))
        if not content:
            raise ChapterNotFoundError(chapter_id, self.platform.value)
        
        return {
            "type": "text",
            "content": content,
            "chapter_id": str(chapter_id),
        }
    
    def set_current_book_id(self, book_id: str):
        """手动设置内容接口需要的 book_id。"""
        self._current_book_id = book_id
        self._resolved_ids[book_id] = book_id
