"""Web-layer response mappers."""

from app.web.mappers.book_mapper import (
    to_book_detail_response,
    to_book_response,
    to_book_statistics,
)
from app.web.mappers.task_mapper import to_task_response

__all__ = [
    "to_book_response",
    "to_book_statistics",
    "to_book_detail_response",
    "to_task_response",
]
