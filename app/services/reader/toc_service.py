"""
目录服务：提供书籍目录查询、分页和相邻章节定位功能
"""

import logging
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Book, Chapter
from app.services.book_service import BookService

logger = logging.getLogger(__name__)


class TocService:
    """目录服务 - 负责书籍目录的查询和管理"""

    def __init__(
        self,
        db: Session,
        book_service: Optional[BookService] = None,
    ):
        """初始化目录服务

        Args:
            db: 数据库会话
            book_service: 书籍服务实例（可选）
        """
        self.db = db
        self.book_service = book_service or BookService(db=db)

    def _get_book(self, book_id: str) -> Optional[Book]:
        """获取书籍信息

        Args:
            book_id: 书籍UUID

        Returns:
            书籍对象，不存在时返回None
        """
        return self.book_service.get_book(book_id)

    def _get_chapter(self, book_id: str, chapter_id: str) -> Optional[Chapter]:
        """获取指定章节信息

        Args:
            book_id: 书籍UUID
            chapter_id: 章节UUID

        Returns:
            章节对象，不存在时返回None
        """
        try:
            return self.db.query(Chapter).filter(
                Chapter.id == chapter_id,
                Chapter.book_id == book_id,
            ).first()
        except Exception as e:
            logger.error(f"获取章节失败: book_id={book_id}, chapter_id={chapter_id}, error={e}")
            return None

    def _get_adjacent_chapters(
        self,
        book_id: str,
        chapter_index: int,
    ) -> Tuple[Optional[str], Optional[str]]:
        """获取指定章节的相邻章节ID

        Args:
            book_id: 书籍UUID
            chapter_index: 当前章节索引

        Returns:
            (上一章ID, 下一章ID) 元组，不存在时对应位置为None
        """
        try:
            # 查询上一章
            prev_id = self.db.query(Chapter.id).filter(
                Chapter.book_id == book_id,
                Chapter.chapter_index < chapter_index
            ).order_by(Chapter.chapter_index.desc()).limit(1).scalar()

            # 查询下一章
            next_id = self.db.query(Chapter.id).filter(
                Chapter.book_id == book_id,
                Chapter.chapter_index > chapter_index
            ).order_by(Chapter.chapter_index.asc()).limit(1).scalar()

            return prev_id, next_id
        except Exception as e:
            logger.error(f"获取相邻章节失败: book_id={book_id}, chapter_index={chapter_index}, error={e}")
            return None, None

    def get_toc(
        self,
        book_id: str,
        page: int = 1,
        limit: int = 50,
        anchor_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """获取书籍目录（轻量字段，支持分页和锚点定位）

        Args:
            book_id: 书籍UUID
            page: 页码（1-based）
            limit: 每页数量（最大500）
            anchor_id: 希望包含的章节ID（用于根据章节定位页码）

        Returns:
            包含目录信息的字典，结构如下：
            {
                "book": Book对象,
                "chapters": 章节列表,
                "total": 总章节数,
                "page": 当前页码,
                "limit": 每页数量,
                "pages": 总页数,
                "has_more": 是否有更多页
            }
            书籍不存在时返回None
        """
        try:
            # 获取书籍信息
            book = self._get_book(book_id)
            if not book:
                logger.warning(f"书籍不存在: book_id={book_id}")
                return None

            # 参数校验和规范化
            page = max(1, page)
            limit = max(1, min(limit, 500))

            # 构建基础查询
            base_query = self.db.query(Chapter).filter(Chapter.book_id == book_id)
            total = base_query.count()

            # 如果指定了 anchor_id，根据章节位置重算页码
            # 确保返回的数据包含该章节
            if anchor_id:
                anchor = self._get_chapter(book_id, anchor_id)
                if anchor and anchor.chapter_index is not None:
                    page = max(1, (anchor.chapter_index - 1) // limit + 1)
                    logger.debug(f"锚点定位: anchor_id={anchor_id}, chapter_index={anchor.chapter_index}, page={page}")

            # 计算偏移量并查询章节
            offset = (page - 1) * limit
            chapters = (
                base_query.order_by(Chapter.chapter_index)
                .offset(offset)
                .limit(limit)
                .all()
            )

            # 构建目录项列表（只包含轻量字段）
            toc_items = [
                {
                    "id": ch.id,
                    "index": ch.chapter_index,
                    "title": ch.title,
                    "word_count": ch.word_count,
                    "updated_at": ch.created_at,
                    "download_status": ch.download_status,
                }
                for ch in chapters
            ]

            # 计算总页数
            pages = (total + limit - 1) // limit if limit else 0

            return {
                "book": book,
                "chapters": toc_items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
                "has_more": offset + len(toc_items) < total,
            }
        except Exception as e:
            logger.exception(f"获取目录失败: book_id={book_id}, error={e}")
            return None