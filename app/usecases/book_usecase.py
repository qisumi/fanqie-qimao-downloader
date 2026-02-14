"""Book usecase layer.

Coordinates book-related workflows for API routes and keeps routing layer thin.
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.schemas import BookMetadataUpdateRequest
from app.services import BookService, StorageService


class BookUseCase:
    """Application usecase for book CRUD/overview workflows."""

    def __init__(self, db: Session):
        self.storage = StorageService()
        self.book_service = BookService(db=db, storage=self.storage)

    async def add_book(
        self,
        platform: str,
        book_id: str,
    ):
        return await self.book_service.add_book(
            platform=platform,
            book_id=book_id,
            download_cover=True,
            fetch_chapters=True,
        )

    def update_book_metadata(
        self,
        book_id: str,
        payload: BookMetadataUpdateRequest,
    ):
        return self.book_service.update_book_metadata(
            book_uuid=book_id,
            title=payload.title,
            author=payload.author,
            creation_status=payload.creation_status,
            cover_url=payload.cover_url,
        )

    def list_books(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        return self.book_service.list_books(
            platform=platform,
            status=status,
            search=search,
            page=page,
            limit=limit,
        )

    def get_book_overview(self, book_id: str) -> Optional[Dict[str, Any]]:
        return self.book_service.get_book_overview(book_id)
