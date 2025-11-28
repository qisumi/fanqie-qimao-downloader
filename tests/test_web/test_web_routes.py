"""
Web层API路由测试

使用 FastAPI TestClient 测试所有API端点
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.utils.database import Base, get_db


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖get_db依赖，使用测试数据库"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ============ 健康检查测试 ============

class TestHealthCheck:
    """健康检查测试"""
    
    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


# ============ 书籍API测试 ============

class TestBooksAPI:
    """书籍API测试"""
    
    def test_list_books_empty(self, client):
        """测试空书籍列表"""
        response = client.get("/api/books/")
        assert response.status_code == 200
        data = response.json()
        assert data["books"] == []
        assert data["total"] == 0
    
    def test_list_books_with_pagination(self, client):
        """测试分页参数"""
        response = client.get("/api/books/", params={"page": 0, "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
    
    def test_get_book_not_found(self, client):
        """测试获取不存在的书籍"""
        response = client.get("/api/books/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    def test_delete_book_not_found(self, client):
        """测试删除不存在的书籍"""
        response = client.delete("/api/books/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    def test_search_invalid_platform(self, client):
        """测试无效平台搜索"""
        response = client.get("/api/books/search", params={"q": "test", "platform": "invalid"})
        assert response.status_code == 400
    
    def test_add_book_invalid_platform(self, client):
        """测试无效平台添加书籍"""
        response = client.post("/api/books/invalid/123456")
        assert response.status_code == 400


# ============ 任务API测试 ============

class TestTasksAPI:
    """任务API测试"""
    
    def test_list_tasks_empty(self, client):
        """测试空任务列表"""
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0
    
    def test_get_task_not_found(self, client):
        """测试获取不存在的任务"""
        response = client.get("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    def test_start_download_book_not_found(self, client):
        """测试下载不存在的书籍"""
        response = client.post("/api/tasks/00000000-0000-0000-0000-000000000000/download")
        assert response.status_code == 404
    
    def test_cancel_task_not_found(self, client):
        """测试取消不存在的任务"""
        response = client.post("/api/tasks/00000000-0000-0000-0000-000000000000/cancel")
        assert response.status_code == 404
    
    def test_get_quota_invalid_platform(self, client):
        """测试无效平台配额查询"""
        response = client.get("/api/tasks/quota/invalid")
        assert response.status_code == 400
    
    def test_get_quota_fanqie(self, client):
        """测试番茄平台配额查询"""
        response = client.get("/api/tasks/quota/fanqie")
        assert response.status_code == 200
        data = response.json()
        assert "remaining" in data
        assert "limit" in data
    
    def test_get_all_quota(self, client):
        """测试所有平台配额查询"""
        response = client.get("/api/tasks/quota")
        assert response.status_code == 200
        data = response.json()
        assert "fanqie" in data
        assert "qimao" in data


# ============ 统计API测试 ============

class TestStatsAPI:
    """统计API测试"""
    
    def test_get_stats(self, client):
        """测试获取系统统计"""
        response = client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()
        assert "total_books" in data
        assert "total_chapters" in data
        assert "storage" in data
        assert "quota" in data
    
    def test_get_storage_stats(self, client):
        """测试获取存储统计"""
        response = client.get("/api/stats/storage")
        assert response.status_code == 200
        data = response.json()
        assert "books_count" in data
        assert "total_size_mb" in data
    
    def test_get_quota_stats(self, client):
        """测试获取配额统计"""
        response = client.get("/api/stats/quota")
        assert response.status_code == 200
        data = response.json()
        assert "fanqie" in data
        assert "qimao" in data
    
    def test_get_books_summary(self, client):
        """测试获取书籍摘要"""
        response = client.get("/api/stats/books/summary")
        assert response.status_code == 200
        data = response.json()
        assert "by_platform" in data
        assert "by_status" in data
        assert "recent_books" in data


# ============ 页面路由测试 ============

class TestPagesRoutes:
    """页面路由测试"""
    
    def test_index_page(self, client):
        """测试首页"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_search_page(self, client):
        """测试搜索页面"""
        response = client.get("/search")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_books_page(self, client):
        """测试书籍列表页面"""
        response = client.get("/books")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_tasks_page(self, client):
        """测试任务页面"""
        response = client.get("/tasks")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
