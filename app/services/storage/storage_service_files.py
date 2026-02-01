"""
存储服务文件管理模块

提供书籍文件的删除和查询功能
"""

import logging
import shutil
from pathlib import Path

from app.services.storage.storage_service_base import StorageServiceBase

logger = logging.getLogger(__name__)


class StorageServiceFiles(StorageServiceBase):
    """书籍文件管理服务"""
    
    def delete_book_files(self, book_uuid: str) -> bool:
        """
        删除书籍所有文件
        
        Args:
            book_uuid: 书籍UUID
        
        Returns:
            是否成功删除
        """
        book_dir = self.get_book_dir(book_uuid)
        
        if not book_dir.exists():
            logger.warning(f"Book directory not found: {book_dir}")
            return False
        
        try:
            shutil.rmtree(book_dir)
            logger.info(f"Deleted book files for {book_uuid}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete book files for {book_uuid}: {e}")
            return False
    
    def delete_epub(self, book_title: str, book_uuid: str) -> bool:
        """
        删除EPUB文件
        
        Args:
            book_title: 书籍标题
            book_uuid: 书籍UUID
        
        Returns:
            是否成功删除
        """
        epub_path = self.get_epub_path(book_title, book_uuid)
        
        if not epub_path.exists():
            logger.warning(f"EPUB file not found: {epub_path}")
            return False
        
        try:
            epub_path.unlink()
            logger.info(f"Deleted EPUB: {epub_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete EPUB: {e}")
            return False
    
    def epub_exists(self, book_title: str, book_uuid: str) -> bool:
        """检查EPUB是否存在"""
        return self.get_epub_path(book_title, book_uuid).exists()
    
    def delete_txt(self, book_title: str, book_uuid: str) -> bool:
        """
        删除TXT文件
        
        Args:
            book_title: 书籍标题
            book_uuid: 书籍UUID
        
        Returns:
            是否成功删除
        """
        txt_path = self.get_txt_path(book_title, book_uuid)
        
        if not txt_path.exists():
            logger.warning(f"TXT file not found: {txt_path}")
            return False
        
        try:
            txt_path.unlink()
            logger.info(f"Deleted TXT: {txt_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete TXT: {e}")
            return False
    
    def txt_exists(self, book_title: str, book_uuid: str) -> bool:
        """检查TXT是否存在"""
        return self.get_txt_path(book_title, book_uuid).exists()