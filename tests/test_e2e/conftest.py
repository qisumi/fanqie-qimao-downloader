import os
from pathlib import Path
from typing import Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.main import app
from app.utils.database import Base, get_db
from app.web.middleware.auth import AuthMiddleware

# 测试环境变量
os.environ["RAIN_API_KEY"] = "test_key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖 get_db 依赖，使用内存数据库"""
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
def db_session(test_db):
    """获取数据库会话"""
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """创建测试客户端（已认证）"""
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        settings = get_settings()
        if settings.app_password:
            auth_middleware = AuthMiddleware(app=None, settings=settings)
            auth_token = auth_middleware.create_auth_token()
            c.cookies.set(AuthMiddleware.COOKIE_NAME, auth_token)
        
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture
def temp_storage_path(tmp_path) -> Tuple[Path, Path]:
    """临时存储路径"""
    books_path = tmp_path / "books"
    epubs_path = tmp_path / "epubs"
    books_path.mkdir()
    epubs_path.mkdir()
    return books_path, epubs_path


@pytest.fixture
def storage_service(temp_storage_path):
    """存储服务实例"""
    books_path, epubs_path = temp_storage_path
    from app.services import StorageService
    
    return StorageService(books_path=books_path, epubs_path=epubs_path)
