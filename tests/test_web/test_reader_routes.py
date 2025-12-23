"""
阅读相关 API 路由测试
"""

import os
from pathlib import Path
from typing import Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.main import app
from app.models import Book, Chapter, User, ReadingProgress, Bookmark, ReadingHistory
from app.utils.database import Base, get_db
from app.web.middleware.auth import AuthMiddleware
from app.services.storage_service import StorageService


# 使用内存数据库
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


def override_get_db():
    """覆盖 get_db 依赖，使用测试数据库"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def temp_dirs(tmp_path_factory):
    """为测试切换到独立的数据/缓存目录，避免污染真实数据"""
    settings = get_settings()
    old_data_dir = settings.data_dir
    old_books_dir = settings.books_dir
    old_epubs_dir = settings.epubs_dir

    base = tmp_path_factory.mktemp("data")
    settings.data_dir = str(base)
    settings.books_dir = str(base / "books")
    settings.epubs_dir = str(base / "epubs")
    settings.ensure_directories()

    try:
        yield settings
    finally:
        settings.data_dir = old_data_dir
        settings.books_dir = old_books_dir
        settings.epubs_dir = old_epubs_dir
        settings.ensure_directories()


@pytest.fixture(scope="function")
def test_db(temp_dirs):
    """创建测试数据库"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """创建测试客户端（自动带认证 Cookie 如果开启密码）"""
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        settings = get_settings()
        if settings.app_password:
            auth_middleware = AuthMiddleware(app=None, settings=settings)
            token = auth_middleware.create_auth_token()
            c.cookies.set(AuthMiddleware.COOKIE_NAME, token)
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_data():
    """插入用户、书籍和章节数据，返回相关 ID"""
    db = TestingSessionLocal()
    settings = get_settings()
    storage = StorageService()

    user = User(username="reader")
    db.add(user)
    db.commit()
    db.refresh(user)

    book = Book(
        platform="fanqie",
        book_id="book-001",
        title="测试书籍",
        author="作者",
        total_chapters=2,
        downloaded_chapters=1,
        download_status="partial",
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    # 已下载章节
    content_path = storage.save_chapter_content(book.id, 1, "第一段\n\n第二段")
    chapter1 = Chapter(
        book_id=book.id,
        item_id="item-001",
        title="第一章",
        chapter_index=1,
        word_count=4,
        content_path=content_path,
        download_status="completed",
    )
    # 未下载章节
    chapter2 = Chapter(
        book_id=book.id,
        item_id="item-002",
        title="第二章",
        chapter_index=2,
        word_count=0,
        download_status="pending",
    )
    db.add_all([chapter1, chapter2])
    db.commit()
    db.refresh(chapter1)
    db.refresh(chapter2)

    payload = {
        "user_id": user.id,
        "book_id": book.id,
        "chapter1_id": chapter1.id,
        "chapter2_id": chapter2.id,
        "books_dir": Path(settings.books_dir),
        "epubs_dir": Path(settings.epubs_dir),
    }
    db.close()

    return payload


class TestReaderRoutes:
    """阅读器相关接口测试"""

    def test_get_toc(self, client, seed_data):
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/toc",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["book_id"] == seed_data["book_id"]
        assert len(data["chapters"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["pages"] == 1
        ids = {c["id"] for c in data["chapters"]}
        assert seed_data["chapter1_id"] in ids
        assert seed_data["chapter2_id"] in ids

    def test_get_toc_with_pagination(self, client, seed_data):
        # 限制每页1条，验证分页与has_more
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/toc",
            params={"user_id": seed_data["user_id"], "limit": 1, "page": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["pages"] == 2
        assert data["has_more"] is True
        assert len(data["chapters"]) == 1
        first_id = data["chapters"][0]["id"]

        # 请求第二页，应包含另一章，has_more 为 False
        resp2 = client.get(
            f"/api/books/{seed_data['book_id']}/toc",
            params={"user_id": seed_data["user_id"], "limit": 1, "page": 2},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["page"] == 2
        assert data2["has_more"] is False
        assert len(data2["chapters"]) == 1
        second_id = data2["chapters"][0]["id"]
        assert first_id != second_id

    def test_get_chapter_content_ready(self, client, seed_data):
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/chapters/{seed_data['chapter1_id']}/content",
            params={
                "user_id": seed_data["user_id"],
                "fmt": "html",
                "prefetch": 0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["index"] == 1
        assert data["next_id"] == seed_data["chapter2_id"]
        assert "content_html" in data and data["content_html"]
        assert data["content_text"] is None

    def test_get_chapter_content_missing_fetching(self, monkeypatch, client, seed_data):
        async def fake_download(*args, **kwargs):
            return False

        monkeypatch.setattr(
            "app.services.download_service.DownloadService.download_chapter_with_retry",
            fake_download,
        )

        resp = client.get(
            f"/api/books/{seed_data['book_id']}/chapters/{seed_data['chapter2_id']}/content",
            params={
                "user_id": seed_data["user_id"],
                "fmt": "text",
                "prefetch": 0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "fetching"
        assert data["content_text"] is None

    def test_progress_roundtrip(self, client, seed_data):
        # 初始无进度
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/reader/progress",
            params={
                "user_id": seed_data["user_id"],
                "device_id": "device-1",
            },
        )
        assert resp.status_code == 204

        # 写入进度
        resp = client.post(
            f"/api/books/{seed_data['book_id']}/reader/progress",
            params={"user_id": seed_data["user_id"]},
            json={
                "chapter_id": seed_data["chapter1_id"],
                "offset_px": 120,
                "percent": 12.5,
                "device_id": "device-1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["chapter_id"] == seed_data["chapter1_id"]
        assert data["percent"] == 12.5

        # 读取进度
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/reader/progress",
            params={
                "user_id": seed_data["user_id"],
                "device_id": "device-1",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["percent"] == 12.5

        # 清空进度
        resp = client.delete(
            f"/api/books/{seed_data['book_id']}/reader/progress",
            params={
                "user_id": seed_data["user_id"],
                "device_id": "device-1",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 再次读取应无数据
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/reader/progress",
            params={
                "user_id": seed_data["user_id"],
                "device_id": "device-1",
            },
        )
        assert resp.status_code == 204

    def test_bookmarks_crud(self, client, seed_data):
        # 创建书签
        resp = client.post(
            f"/api/books/{seed_data['book_id']}/reader/bookmarks",
            params={"user_id": seed_data["user_id"]},
            json={
                "chapter_id": seed_data["chapter1_id"],
                "offset_px": 200,
                "percent": 25.0,
                "note": "标记",
            },
        )
        assert resp.status_code == 200
        bookmark = resp.json()
        assert bookmark["note"] == "标记"

        # 列表
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/reader/bookmarks",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        bookmarks = resp.json()
        assert len(bookmarks) == 1

        # 删除
        resp = client.delete(
            f"/api/books/{seed_data['book_id']}/reader/bookmarks/{bookmark['id']}",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 再次列表为空
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/reader/bookmarks",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_list_and_clear(self, client, seed_data):
        # 写一次进度 -> 自动写入历史
        client.post(
            f"/api/books/{seed_data['book_id']}/reader/progress",
            params={"user_id": seed_data["user_id"]},
            json={
                "chapter_id": seed_data["chapter1_id"],
                "offset_px": 50,
                "percent": 5.0,
                "device_id": "device-hist",
            },
        )

        resp = client.get(
            f"/api/books/{seed_data['book_id']}/reader/history",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) >= 1
        assert history[0]["chapter_id"] == seed_data["chapter1_id"]

        resp = client.delete(
            f"/api/books/{seed_data['book_id']}/reader/history",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        resp = client.get(
            f"/api/books/{seed_data['book_id']}/reader/history",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_cache_status(self, client, seed_data):
        # 状态
        resp = client.get(
            f"/api/books/{seed_data['book_id']}/cache/status",
            params={"user_id": seed_data["user_id"]},
        )
        assert resp.status_code == 200
        status = resp.json()
        assert seed_data["chapter1_id"] in status["cached_chapters"]
        assert "cached_at" in status
