"""
书签服务：管理用户的阅读书签
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Bookmark, Book, Chapter

logger = logging.getLogger(__name__)


class BookmarkService:
    """书签服务类，负责书签的增删查操作"""

    def __init__(self, db: Session):
        """初始化书签服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def list_bookmarks(self, user_id: str, book_id: str) -> List[Bookmark]:
        """列出指定用户和书籍的所有书签

        Args:
            user_id: 用户ID
            book_id: 书籍ID

        Returns:
            书签列表，按创建时间倒序排列

        Raises:
            ValueError: 当 user_id 或 book_id 为空时
        """
        if not user_id:
            raise ValueError("user_id 不能为空")
        if not book_id:
            raise ValueError("book_id 不能为空")

        try:
            bookmarks = (
                self.db.query(Bookmark)
                .filter(
                    Bookmark.user_id == user_id,
                    Bookmark.book_id == book_id,
                )
                .order_by(Bookmark.created_at.desc())
                .all()
            )
            logger.debug(f"用户 {user_id} 在书籍 {book_id} 中有 {len(bookmarks)} 个书签")
            return bookmarks
        except Exception as e:
            logger.error(f"查询书签失败: user_id={user_id}, book_id={book_id}, error={e}")
            raise

    def add_bookmark(
        self,
        user_id: str,
        book_id: str,
        chapter_id: str,
        offset_px: int,
        percent: float,
        note: Optional[str] = None,
    ) -> Bookmark:
        """添加新书签

        Args:
            user_id: 用户ID
            book_id: 书籍ID
            chapter_id: 章节ID
            offset_px: 章节内偏移量（像素）
            percent: 阅读进度百分比（0-100）
            note: 书签备注（可选）

        Returns:
            创建的书签对象

        Raises:
            ValueError: 当必填参数为空或 percent 超出范围时
        """
        # 参数验证
        if not user_id:
            raise ValueError("user_id 不能为空")
        if not book_id:
            raise ValueError("book_id 不能为空")
        if not chapter_id:
            raise ValueError("chapter_id 不能为空")

        # 验证书籍和章节是否存在
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError(f"书籍不存在: book_id={book_id}")

        chapter = self.db.query(Chapter).filter(
            Chapter.id == chapter_id,
            Chapter.book_id == book_id,
        ).first()
        if not chapter:
            raise ValueError(f"章节不存在: chapter_id={chapter_id}, book_id={book_id}")

        # 规范化百分比
        percent = max(0.0, min(percent, 100.0))

        try:
            bookmark = Bookmark(
                user_id=user_id,
                book_id=book_id,
                chapter_id=chapter_id,
                offset_px=offset_px,
                percent=percent,
                note=note,
            )
            self.db.add(bookmark)
            self.db.commit()
            self.db.refresh(bookmark)

            logger.info(
                f"添加书签成功: user_id={user_id}, book_id={book_id}, "
                f"chapter_id={chapter_id}, bookmark_id={bookmark.id}"
            )
            return bookmark
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"添加书签失败: user_id={user_id}, book_id={book_id}, "
                f"chapter_id={chapter_id}, error={e}"
            )
            raise

    def delete_bookmark(self, user_id: str, book_id: str, bookmark_id: str) -> bool:
        """删除指定书签

        Args:
            user_id: 用户ID
            book_id: 书籍ID
            bookmark_id: 书签ID

        Returns:
            删除成功返回 True，书签不存在返回 False

        Raises:
            ValueError: 当必填参数为空时
        """
        if not user_id:
            raise ValueError("user_id 不能为空")
        if not book_id:
            raise ValueError("book_id 不能为空")
        if not bookmark_id:
            raise ValueError("bookmark_id 不能为空")

        try:
            bookmark = (
                self.db.query(Bookmark)
                .filter(
                    Bookmark.id == bookmark_id,
                    Bookmark.user_id == user_id,
                    Bookmark.book_id == book_id,
                )
                .first()
            )

            if not bookmark:
                logger.debug(
                    f"书签不存在: bookmark_id={bookmark_id}, "
                    f"user_id={user_id}, book_id={book_id}"
                )
                return False

            self.db.delete(bookmark)
            self.db.commit()

            logger.info(
                f"删除书签成功: bookmark_id={bookmark_id}, "
                f"user_id={user_id}, book_id={book_id}"
            )
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"删除书签失败: bookmark_id={bookmark_id}, "
                f"user_id={user_id}, book_id={book_id}, error={e}"
            )
            raise

    def get_bookmark(self, bookmark_id: str) -> Optional[Bookmark]:
        """根据ID获取单个书签

        Args:
            bookmark_id: 书签ID

        Returns:
            书签对象，不存在时返回 None

        Raises:
            ValueError: 当 bookmark_id 为空时
        """
        if not bookmark_id:
            raise ValueError("bookmark_id 不能为空")

        try:
            bookmark = (
                self.db.query(Bookmark)
                .filter(Bookmark.id == bookmark_id)
                .first()
            )
            return bookmark
        except Exception as e:
            logger.error(f"查询书签失败: bookmark_id={bookmark_id}, error={e}")
            raise

    def update_bookmark(
        self,
        bookmark_id: str,
        note: Optional[str] = None,
        offset_px: Optional[int] = None,
        percent: Optional[float] = None,
    ) -> Optional[Bookmark]:
        """更新书签信息

        Args:
            bookmark_id: 书签ID
            note: 新的备注（可选）
            offset_px: 新的偏移量（可选）
            percent: 新的进度百分比（可选）

        Returns:
            更新后的书签对象，书签不存在时返回 None

        Raises:
            ValueError: 当 bookmark_id 为空或 percent 超出范围时
        """
        if not bookmark_id:
            raise ValueError("bookmark_id 不能为空")

        try:
            bookmark = (
                self.db.query(Bookmark)
                .filter(Bookmark.id == bookmark_id)
                .first()
            )

            if not bookmark:
                logger.debug(f"书签不存在: bookmark_id={bookmark_id}")
                return None

            # 更新字段
            if note is not None:
                bookmark.note = note
            if offset_px is not None:
                bookmark.offset_px = offset_px
            if percent is not None:
                bookmark.percent = max(0.0, min(percent, 100.0))

            self.db.commit()
            self.db.refresh(bookmark)

            logger.info(f"更新书签成功: bookmark_id={bookmark_id}")
            return bookmark
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新书签失败: bookmark_id={bookmark_id}, error={e}")
            raise