"""
数据库初始化脚本
创建所有表结构
"""

from app.utils.database import Base, engine

# 导入所有模型，确保它们被注册到 Base.metadata
from app.models import Book, Chapter, DownloadTask, DailyQuota, User, UserBook

def init_database():
    """初始化数据库，创建所有表"""
    print("正在创建数据库表...")
    print(f"将创建以下表: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")

if __name__ == "__main__":
    init_database()
