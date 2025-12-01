import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Book, User, UserBook

logger = logging.getLogger(__name__)


class UserService:
    """用户与个人书架相关的服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 用户管理 ==========
    def list_users(self) -> List[User]:
        return self.db.query(User).order_by(User.created_at.asc()).all()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_name(self, username: str) -> Optional[User]:
        return (
            self.db.query(User)
            .filter(User.username == username.strip())
            .first()
        )

    def create_user(self, username: str) -> User:
        clean_name = (username or "").strip()
        if not clean_name:
            raise ValueError("用户名不能为空")

        existing = self.get_user_by_name(clean_name)
        if existing:
            raise ValueError("用户名已存在")

        user = User(username=clean_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Created user: {user.username} ({user.id})")
        return user

    def rename_user(self, user_id: str, new_username: str) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        clean_name = (new_username or "").strip()
        if not clean_name:
            raise ValueError("新用户名不能为空")

        existing = (
            self.db.query(User)
            .filter(User.username == clean_name, User.id != user_id)
            .first()
        )
        if existing:
            raise ValueError("用户名已存在")

        user.username = clean_name
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Renamed user {user_id} to {clean_name}")
        return user

    def delete_user(self, user_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        logger.info(f"Deleted user: {user.username} ({user.id})")
        return True

    # ========== 个人书架 ==========
    def list_user_books(
        self,
        user_id: str,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        query = (
            self.db.query(Book)
            .join(UserBook, UserBook.book_id == Book.id)
            .filter(UserBook.user_id == user_id)
        )

        if platform:
            query = query.filter(Book.platform == platform)

        if status:
            query = query.filter(Book.download_status == status)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.ilike(search_pattern),
                    Book.author.ilike(search_pattern),
                )
            )

        total = query.count()
        query = query.order_by(Book.updated_at.desc())
        query = query.offset(page * limit).limit(limit)

        books = query.all()
        pages = (total + limit - 1) // limit

        return {
            "books": books,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
        }

    def add_book_to_user(self, user_id: str, book_id: str) -> UserBook:
        # 确认用户和书籍存在
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError("书籍不存在")

        existing = (
            self.db.query(UserBook)
            .filter(UserBook.user_id == user_id, UserBook.book_id == book_id)
            .first()
        )
        if existing:
            return existing

        link = UserBook(user_id=user_id, book_id=book_id)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        logger.info(f"Added book {book_id} to user {user_id} shelf")
        return link

    def remove_book_from_user(self, user_id: str, book_id: str) -> bool:
        link = (
            self.db.query(UserBook)
            .filter(UserBook.user_id == user_id, UserBook.book_id == book_id)
            .first()
        )
        if not link:
            return False

        self.db.delete(link)
        self.db.commit()
        logger.info(f"Removed book {book_id} from user {user_id} shelf")
        return True

    def get_user_book_ids(self, user_id: str) -> List[str]:
        return [
            row.book_id
            for row in self.db.query(UserBook.book_id)
            .filter(UserBook.user_id == user_id)
            .all()
        ]


__all__ = ["UserService"]
