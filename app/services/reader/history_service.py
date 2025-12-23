"""
阅读历史服务
负责管理用户的阅读历史记录
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import ReadingHistory

logger = logging.getLogger(__name__)


class HistoryService:
    """阅读历史服务类
    
    职责：
    - 查询用户的阅读历史记录
    - 清除用户的阅读历史记录
    """

    def __init__(self, db: Session):
        """初始化历史服务
        
        Args:
            db: 数据库会话
        """
        self.db = db

    def list_history(
        self,
        user_id: str,
        book_id: str,
        limit: int = 50,
    ) -> List[ReadingHistory]:
        """列出指定书籍的阅读历史记录
        
        按更新时间倒序返回历史记录，最新的记录排在最前面。
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            limit: 返回记录的最大数量，默认50条
            
        Returns:
            阅读历史记录列表，按更新时间倒序排列
            
        Raises:
            ValueError: 当 limit 参数无效时
        """
        try:
            # 验证 limit 参数
            if limit <= 0:
                logger.warning(f"Invalid limit value: {limit}, using default 50")
                limit = 50
            elif limit > 1000:
                logger.warning(f"Limit value too large: {limit}, capping at 1000")
                limit = 1000

            # 查询历史记录
            history_records = (
                self.db.query(ReadingHistory)
                .filter(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.book_id == book_id,
                )
                .order_by(ReadingHistory.updated_at.desc())
                .limit(limit)
                .all()
            )

            logger.debug(
                f"Retrieved {len(history_records)} history records "
                f"for user={user_id}, book={book_id}"
            )
            return history_records

        except Exception as e:
            logger.error(
                f"Failed to list history for user={user_id}, book={book_id}: {e}",
                exc_info=True
            )
            raise

    def clear_history(self, user_id: str, book_id: str) -> int:
        """清除指定书籍的阅读历史记录
        
        删除指定用户在指定书籍下的所有阅读历史记录。
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            
        Returns:
            删除的记录数量
            
        Raises:
            Exception: 当数据库操作失败时
        """
        try:
            # 执行删除操作
            rows_deleted = (
                self.db.query(ReadingHistory)
                .filter(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.book_id == book_id,
                )
                .delete()
            )

            # 提交事务
            self.db.commit()

            logger.info(
                f"Cleared {rows_deleted} history records "
                f"for user={user_id}, book={book_id}"
            )
            return rows_deleted

        except Exception as e:
            # 回滚事务
            self.db.rollback()
            logger.error(
                f"Failed to clear history for user={user_id}, book={book_id}: {e}",
                exc_info=True
            )
            raise

    def get_latest_history(
        self,
        user_id: str,
        book_id: str,
    ) -> Optional[ReadingHistory]:
        """获取指定书籍的最新阅读历史记录
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            
        Returns:
            最新的阅读历史记录，如果不存在则返回 None
        """
        try:
            latest_record = (
                self.db.query(ReadingHistory)
                .filter(
                    ReadingHistory.user_id == user_id,
                    ReadingHistory.book_id == book_id,
                )
                .order_by(ReadingHistory.updated_at.desc())
                .first()
            )

            return latest_record

        except Exception as e:
            logger.error(
                f"Failed to get latest history for user={user_id}, book={book_id}: {e}",
                exc_info=True
            )
            raise