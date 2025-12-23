import logging

from app.services.book.book_service_base import BookServiceBase

logger = logging.getLogger(__name__)


class BookServiceDeleteMixin(BookServiceBase):
    """删除相关逻辑"""
    
    def delete_book(
        self,
        book_uuid: str,
        delete_files: bool = True,
    ) -> bool:
        book = self.get_book(book_uuid)
        if not book:
            return False
        
        book_title = book.title
        
        if delete_files:
            self.storage.delete_book_files(book_uuid)
            self.storage.delete_epub(book.title, book_uuid)
        
        self.db.delete(book)
        self.db.commit()
        
        logger.info(f"Deleted book: {book_title} ({book_uuid})")
        return True


__all__ = ["BookServiceDeleteMixin"]
