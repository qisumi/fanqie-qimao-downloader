"""Repository for user read/write operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_users(self) -> List[User]:
        return self.db.query(User).order_by(User.created_at.asc()).all()

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_name(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_name_excluding_id(self, username: str, excluded_user_id: str) -> Optional[User]:
        return self.db.query(User).filter(
            User.username == username,
            User.id != excluded_user_id,
        ).first()
