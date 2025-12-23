"""
阅读进度管理服务
负责处理阅读进度的查询、更新、同步和清除
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import ReadingHistory, ReadingProgress

logger = logging.getLogger(__name__)


class ProgressService:
    """阅读进度管理服务
    
    职责：
    - 查询阅读进度（支持跨设备同步）
    - 更新或插入阅读进度
    - 清除阅读进度
    - 记录阅读历史
    """

    def __init__(self, db: Session):
        """初始化进度服务
        
        Args:
            db: 数据库会话
        """
        self.db = db

    def get_progress(
        self,
        user_id: str,
        book_id: str,
        device_id: Optional[str] = None,
    ) -> Optional[ReadingProgress]:
        """获取阅读进度
        
        当 device_id 为 None 时，获取跨设备同步进度（最新的进度记录）
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            device_id: 设备ID，可选。为None时获取跨设备同步进度
            
        Returns:
            ReadingProgress 对象，如果不存在则返回 None
        """
        try:
            query = self.db.query(ReadingProgress).filter(
                ReadingProgress.user_id == user_id,
                ReadingProgress.book_id == book_id,
            )
            
            if device_id:
                # 获取指定设备的进度
                query = query.filter(ReadingProgress.device_id == device_id)
            else:
                # 不指定设备ID时，获取最新的跨设备同步进度
                query = query.order_by(ReadingProgress.updated_at.desc())
            
            progress = query.first()
            
            if progress:
                logger.debug(
                    f"获取进度成功: user_id={user_id}, book_id={book_id}, "
                    f"device_id={device_id or 'sync'}, chapter_id={progress.chapter_id}"
                )
            else:
                logger.debug(
                    f"未找到进度记录: user_id={user_id}, book_id={book_id}, "
                    f"device_id={device_id or 'sync'}"
                )
            
            return progress
            
        except Exception as e:
            logger.error(
                f"获取进度失败: user_id={user_id}, book_id={book_id}, "
                f"device_id={device_id or 'sync'}, error={str(e)}"
            )
            raise

    def get_all_device_progress(
        self,
        user_id: str,
        book_id: str,
    ) -> List[ReadingProgress]:
        """获取用户在该书籍的所有设备进度记录
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            
        Returns:
            ReadingProgress 对象列表，按更新时间降序排列
        """
        try:
            progress_list = self.db.query(ReadingProgress).filter(
                ReadingProgress.user_id == user_id,
                ReadingProgress.book_id == book_id,
            ).order_by(ReadingProgress.updated_at.desc()).all()
            
            logger.debug(
                f"获取所有设备进度成功: user_id={user_id}, book_id={book_id}, "
                f"count={len(progress_list)}"
            )
            
            return progress_list
            
        except Exception as e:
            logger.error(
                f"获取所有设备进度失败: user_id={user_id}, book_id={book_id}, "
                f"error={str(e)}"
            )
            raise

    def upsert_progress(
        self,
        user_id: str,
        book_id: str,
        chapter_id: str,
        device_id: str,
        offset_px: int,
        percent: float,
    ) -> ReadingProgress:
        """更新或插入阅读进度（支持跨设备同步）
        
        跨设备同步策略：
        - 更新统一的进度记录（不区分设备）
        - 同时记录到历史表（保留设备信息用于分析）
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            chapter_id: 章节ID
            device_id: 设备ID
            offset_px: 像素偏移量
            percent: 阅读进度百分比（0-100）
            
        Returns:
            更新或创建的 ReadingProgress 对象
            
        Raises:
            ValueError: 当参数无效时
        """
        try:
            # 参数校验
            if percent < 0:
                percent = 0.0
                logger.warning(f"进度百分比小于0，已修正为0: user_id={user_id}, book_id={book_id}")
            if percent > 100:
                percent = 100.0
                logger.warning(f"进度百分比大于100，已修正为100: user_id={user_id}, book_id={book_id}")
            
            if offset_px < 0:
                offset_px = 0
                logger.warning(f"像素偏移小于0，已修正为0: user_id={user_id}, book_id={book_id}")
            
            now = datetime.now(timezone.utc)
            
            # 跨设备同步：更新统一的进度记录（不区分设备）
            progress = self.get_progress(user_id, book_id)
            
            if progress:
                # 更新现有进度
                progress.chapter_id = chapter_id
                progress.offset_px = offset_px
                progress.percent = percent
                progress.updated_at = now
                # 仍然记录当前设备ID，用于统计
                progress.device_id = device_id
                
                logger.debug(
                    f"更新进度成功: user_id={user_id}, book_id={book_id}, "
                    f"chapter_id={chapter_id}, device_id={device_id}, percent={percent:.2f}%"
                )
            else:
                # 创建新的跨设备同步进度
                progress = ReadingProgress(
                    user_id=user_id,
                    book_id=book_id,
                    chapter_id=chapter_id,
                    device_id=device_id,
                    offset_px=offset_px,
                    percent=percent,
                    updated_at=now,
                )
                self.db.add(progress)
                
                logger.debug(
                    f"创建进度成功: user_id={user_id}, book_id={book_id}, "
                    f"chapter_id={chapter_id}, device_id={device_id}, percent={percent:.2f}%"
                )
            
            # 同时记录到历史表（保留设备信息用于分析）
            history = ReadingHistory(
                user_id=user_id,
                book_id=book_id,
                chapter_id=chapter_id,
                percent=percent,
                device_id=device_id,
                updated_at=now,
            )
            self.db.add(history)
            
            self.db.commit()
            self.db.refresh(progress)
            
            return progress
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"更新进度失败: user_id={user_id}, book_id={book_id}, "
                f"chapter_id={chapter_id}, device_id={device_id}, error={str(e)}"
            )
            raise

    def clear_progress(
        self,
        user_id: str,
        book_id: str,
        device_id: Optional[str] = None,
    ) -> bool:
        """清除阅读进度
        
        Args:
            user_id: 用户ID
            book_id: 书籍ID
            device_id: 设备ID，可选。为None时清除跨设备同步进度
            
        Returns:
            True 表示成功清除，False 表示未找到进度记录
        """
        try:
            progress = self.get_progress(user_id, book_id, device_id)
            
            if not progress:
                logger.debug(
                    f"未找到进度记录，无法清除: user_id={user_id}, book_id={book_id}, "
                    f"device_id={device_id or 'sync'}"
                )
                return False
            
            self.db.delete(progress)
            self.db.commit()
            
            logger.info(
                f"清除进度成功: user_id={user_id}, book_id={book_id}, "
                f"device_id={device_id or 'sync'}"
            )
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"清除进度失败: user_id={user_id}, book_id={book_id}, "
                f"device_id={device_id or 'sync'}, error={str(e)}"
            )
            raise