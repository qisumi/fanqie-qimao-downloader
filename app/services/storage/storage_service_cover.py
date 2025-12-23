"""
存储服务封面操作模块

提供封面的下载、保存和查询功能
"""

import logging
import aiofiles
import httpx
from pathlib import Path
from typing import Optional

from app.services.storage.storage_service_base import StorageServiceBase

logger = logging.getLogger(__name__)


class StorageServiceCover(StorageServiceBase):
    """封面操作服务"""
    
    async def download_and_save_cover(
        self,
        book_uuid: str,
        cover_url: str,
        timeout: int = 30,
    ) -> Optional[str]:
        """
        异步下载并保存封面图片
        
        Args:
            book_uuid: 书籍UUID
            cover_url: 封面URL
            timeout: 超时时间(秒)
        
        Returns:
            保存的文件路径（相对路径），失败返回None
        """
        if not cover_url:
            logger.warning(f"Empty cover URL for book {book_uuid}")
            return None
        
        book_dir = self.get_book_dir(book_uuid)
        book_dir.mkdir(parents=True, exist_ok=True)
        
        cover_path = self.get_cover_path(book_uuid)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(cover_url)
                response.raise_for_status()
                
                # 保存图片
                async with aiofiles.open(cover_path, "wb") as f:
                    await f.write(response.content)
                
                logger.info(f"Downloaded cover for book {book_uuid}")
                return str(cover_path.relative_to(self.books_path))
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to download cover for book {book_uuid}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading cover: {e}")
            return None
    
    def save_cover(
        self,
        book_uuid: str,
        image_data: bytes,
    ) -> str:
        """
        同步保存封面图片数据
        
        Args:
            book_uuid: 书籍UUID
            image_data: 图片二进制数据
        
        Returns:
            保存的文件路径（相对路径）
        """
        book_dir = self.get_book_dir(book_uuid)
        book_dir.mkdir(parents=True, exist_ok=True)
        
        cover_path = self.get_cover_path(book_uuid)
        cover_path.write_bytes(image_data)
        
        logger.debug(f"Saved cover for book {book_uuid}")
        
        return str(cover_path.relative_to(self.books_path))
    
    def cover_exists(self, book_uuid: str) -> bool:
        """检查封面是否存在"""
        return self.get_cover_path(book_uuid).exists()
    
    def get_cover_full_path(self, book_uuid: str) -> Optional[Path]:
        """获取封面完整路径，如果存在"""
        cover_path = self.get_cover_path(book_uuid)
        return cover_path if cover_path.exists() else None