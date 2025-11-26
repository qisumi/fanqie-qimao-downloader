"""
测试脚本 - 验证Phase 1基础架构是否正常工作
"""

from app.config import settings
from app.utils.database import SessionLocal, engine
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.task import DownloadTask
from app.models.quota import DailyQuota
from sqlalchemy import text

def test_database_connection():
    """测试数据库连接"""
    print("测试数据库连接...")
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_models():
    """测试模型定义"""
    print("测试数据模型...")
    try:
        # 测试Book模型
        book = Book(
            platform="fanqie",
            book_id="12345",
            title="测试书籍",
            author="测试作者"
        )
        print(f"✅ Book模型创建成功: {book}")

        # 测试Chapter模型
        chapter = Chapter(
            book_id="test-book-id",
            item_id="123",
            title="测试章节",
            chapter_index=1
        )
        print(f"✅ Chapter模型创建成功: {chapter}")

        # 测试DownloadTask模型
        task = DownloadTask(
            book_id="test-book-id",
            task_type="full_download"
        )
        print(f"✅ DownloadTask模型创建成功: {task}")

        # 测试DailyQuota模型
        from datetime import date
        quota = DailyQuota(
            id="test-id",
            date=date.today(),
            platform="fanqie"
        )
        print(f"✅ DailyQuota模型创建成功: {quota}")

        return True
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")
        return False

def test_config():
    """测试配置加载"""
    print("测试配置加载...")
    try:
        print(f"✅ 数据库URL: {settings.database_url}")
        print(f"✅ API密钥: {settings.rain_api_key}")
        print(f"✅ 下载限制: {settings.daily_chapter_limit}")
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Phase 1 基础架构测试")
    print("=" * 50)

    tests = [
        test_config,
        test_database_connection,
        test_models
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 Phase 1 基础架构搭建完成！所有测试通过。")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置。")
        return False

if __name__ == "__main__":
    main()