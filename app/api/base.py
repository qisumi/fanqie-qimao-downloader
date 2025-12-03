"""
Rain API V3 客户端基类

提供统一的HTTP请求处理、错误处理、重试机制
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, TypeVar, Generic

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


# ============ 自定义异常类 ============

class APIError(Exception):
    """API错误基类"""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class QuotaExceededError(APIError):
    """每日配额超限错误"""
    
    def __init__(self, platform: str, limit: int = 200):
        self.platform = platform
        self.limit = limit
        super().__init__(
            message=f"今日{platform}平台阅读章节数已达上限({limit}章)",
            code="QUOTA_EXCEEDED",
            details={"platform": platform, "limit": limit}
        )


class NetworkError(APIError):
    """网络错误"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(
            message=message,
            code="NETWORK_ERROR",
            details={"original_error": str(original_error) if original_error else None}
        )


class RateLimitError(APIError):
    """API速率限制错误"""
    
    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(
            message=f"API请求过于频繁，请稍后重试",
            code="RATE_LIMIT",
            details={"retry_after": retry_after}
        )


class InvalidResponseError(APIError):
    """无效响应错误"""
    
    def __init__(self, message: str, response_text: Optional[str] = None):
        super().__init__(
            message=message,
            code="INVALID_RESPONSE",
            details={"response_text": response_text[:500] if response_text else None}
        )


class BookNotFoundError(APIError):
    """书籍不存在错误"""
    
    def __init__(self, book_id: str, platform: str):
        self.book_id = book_id
        self.platform = platform
        super().__init__(
            message=f"书籍不存在: {book_id}",
            code="BOOK_NOT_FOUND",
            details={"book_id": book_id, "platform": platform}
        )


class ChapterNotFoundError(APIError):
    """章节不存在错误"""
    
    def __init__(self, chapter_id: str, platform: str):
        self.chapter_id = chapter_id
        self.platform = platform
        super().__init__(
            message=f"章节不存在: {chapter_id}",
            code="CHAPTER_NOT_FOUND",
            details={"chapter_id": chapter_id, "platform": platform}
        )


# ============ 枚举类型 ============

class Platform(str, Enum):
    """支持的平台"""
    FANQIE = "fanqie"
    QIMAO = "qimao"


class APIType(int, Enum):
    """API类型"""
    SEARCH = 1  # 搜索书籍
    BOOK_DETAIL = 2  # 书籍详情
    CHAPTER_LIST = 3  # 章节列表
    CHAPTER_CONTENT = 4  # 章节内容


class AudioMode(str, Enum):
    """音频模式"""
    NONE = ""  # 普通文本模式
    AI = "@"  # AI朗读模式
    REAL_PERSON = "!"  # 真人朗读模式


# ============ 基类 ============

class RainAPIClient(ABC):
    """
    Rain API V3 客户端基类
    
    提供统一的HTTP请求处理:
    - 异步HTTP请求 (httpx)
    - 指数退避重试
    - 错误处理和分类
    - 响应解析
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        platform: Platform = Platform.FANQIE,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥，默认从配置读取
            base_url: API基础URL，默认从配置读取
            platform: 平台类型 (fanqie/qimao)
            timeout: 请求超时时间(秒)，默认从配置读取
            max_retries: 最大重试次数，默认从配置读取
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.rain_api_key
        self.base_url = base_url or settings.rain_api_base_url
        self.platform = platform
        self.timeout = timeout or settings.api_timeout
        self.max_retries = max_retries or settings.api_retry_times
        
        # 构建平台特定的API URL
        self._api_url = f"{self.base_url.rstrip('/')}/{self.platform.value}/"
        
        # HTTP客户端 (延迟初始化)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端 (延迟初始化)"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                headers={
                    "User-Agent": "FanqieQimaoDownloader/1.0",
                    "Accept": "application/json",
                }
            )
        return self._client
    
    async def close(self):
        """关闭HTTP客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()
    
    async def _request(
        self,
        api_type: APIType,
        params: Optional[Dict[str, Any]] = None,
        retry_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            api_type: API类型 (1-4)
            params: 额外的请求参数
            retry_on_error: 是否在错误时重试
            
        Returns:
            解析后的JSON响应
            
        Raises:
            APIError: API相关错误
            NetworkError: 网络错误
        """
        # 构建请求参数
        request_params = {
            "apikey": self.api_key,
            "type": api_type.value,
        }
        if params:
            request_params.update(params)
        
        # 构建完整URL
        url = self._api_url
        
        last_error: Optional[Exception] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                client = await self._get_client()
                
                logger.debug(f"API请求: {url} 参数: {request_params} (尝试 {attempt + 1}/{self.max_retries + 1})")
                
                response = await client.get(url, params=request_params)
                
                # 检查HTTP状态码
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(retry_after=int(retry_after) if retry_after else None)
                
                response.raise_for_status()
                
                # 检查空响应（可能是服务器临时问题）
                if not response.text or not response.text.strip():
                    raise InvalidResponseError("API返回空响应", "")
                
                # 解析响应
                return self._parse_response(response.text, api_type)
                
            except httpx.TimeoutException as e:
                last_error = NetworkError(f"请求超时 ({self.timeout}秒)", e)
                logger.warning(f"请求超时 (尝试 {attempt + 1}): {e}")
                
            except httpx.HTTPStatusError as e:
                last_error = NetworkError(f"HTTP错误: {e.response.status_code}", e)
                logger.warning(f"HTTP错误 (尝试 {attempt + 1}): {e}")
                
            except httpx.RequestError as e:
                last_error = NetworkError(f"网络请求失败: {str(e)}", e)
                logger.warning(f"网络请求失败 (尝试 {attempt + 1}): {e}")
                
            except (QuotaExceededError, BookNotFoundError, ChapterNotFoundError):
                # 这些错误不需要重试
                raise
            
            except InvalidResponseError as e:
                # 空响应或JSON解析失败，可以重试
                last_error = e
                logger.warning(f"无效响应 (尝试 {attempt + 1}): {e}")
                
            except RateLimitError as e:
                if e.retry_after:
                    wait_time = e.retry_after
                else:
                    wait_time = (2 ** attempt) * 2  # 指数退避
                logger.warning(f"API速率限制，等待 {wait_time} 秒后重试")
                await asyncio.sleep(wait_time)
                continue
                
            except APIError:
                # 其他API错误直接抛出
                raise
                
            except Exception as e:
                last_error = APIError(f"未知错误: {str(e)}")
                logger.error(f"未知错误 (尝试 {attempt + 1}): {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if retry_on_error and attempt < self.max_retries:
                wait_time = (2 ** attempt) * 0.5  # 指数退避: 0.5s, 1s, 2s...
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        if last_error:
            raise last_error
        raise APIError("请求失败，未知原因")
    
    def _parse_response(self, response_text: str, api_type: APIType) -> Dict[str, Any]:
        """
        解析API响应
        
        Args:
            response_text: 响应文本
            api_type: API类型
            
        Returns:
            解析后的数据
            
        Raises:
            InvalidResponseError: 响应格式无效
            QuotaExceededError: 配额超限
            APIError: 其他API错误
        """
        import json
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"JSON解析失败: {e}", response_text)
        
        if not isinstance(data, dict):
            raise InvalidResponseError(
                f"API响应格式无效，期望 JSON 对象，实际为 {type(data).__name__}",
                response_text,
            )
        
        # 检查错误响应
        message = data.get("message", "")
        
        # 检查是否为错误响应
        if message == "ERROR":
            error_content = ""
            if "data" in data and isinstance(data["data"], dict):
                error_content = data["data"].get("content", "")
            
            # 检测配额超限
            if "上限" in error_content or "quota" in error_content.lower():
                raise QuotaExceededError(self.platform.value)
            
            raise APIError(error_content or "API返回错误", code="API_ERROR")
        
        return data
    
    # ============ 抽象方法 (子类实现) ============
    
    @abstractmethod
    async def search(
        self,
        keyword: str,
        page: int = 0,
        audio_mode: AudioMode = AudioMode.NONE,
    ) -> Dict[str, Any]:
        """搜索书籍"""
        pass
    
    @abstractmethod
    async def get_book_detail(self, book_id: str) -> Dict[str, Any]:
        """获取书籍详情"""
        pass
    
    @abstractmethod
    async def get_chapter_list(self, book_id: str) -> Dict[str, Any]:
        """获取章节列表"""
        pass
    
    @abstractmethod
    async def get_chapter_content(self, chapter_id: str, **kwargs) -> Dict[str, Any]:
        """获取章节内容"""
        pass
