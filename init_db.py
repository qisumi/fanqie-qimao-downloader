"""
数据库初始化脚本
创建所有表结构
"""

from app.utils.database import Base, engine

def init_database():
    """初始化数据库，创建所有表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")

if __name__ == "__main__":
    init_database()