# 测试覆盖率提升指南

> 本文档基于 2026-01-10 的测试覆盖率分析生成，旨在帮助开发者系统性地提升项目测试覆盖率。

## 📊 当前测试覆盖率概况

| 指标 | 数值 |
|------|------|
| **总体覆盖率** | 63% |
| **总语句数** | 4814 |
| **未覆盖语句** | 1800 |
| **测试用例数** | 159 |

### 覆盖率分布

```
🟢 高覆盖率 (>80%): schemas, models, config, book_upload_service
🟡 中等覆盖率 (50-80%): api/fanqie, api/qimao, reader_service, epub_service
🔴 低覆盖率 (<50%): biquge, ws, user_service, tasks_start, books_epub, books_txt
```

---

## 🏗️ 项目测试架构

### 目录结构

```
tests/
├── conftest.py              # 全局 fixtures (如有)
├── test_api/                # API 客户端测试
│   └── test_api_client.py   # FanqieAPI, QimaoAPI 测试
├── test_e2e/                # 端到端测试
│   ├── conftest.py          # E2E 共享 fixtures
│   ├── test_data.py         # 测试数据常量
│   ├── test_concurrent_download.py
│   ├── test_epub_generation.py
│   ├── test_error_handling.py
│   └── test_workflow.py
├── test_services/           # 服务层测试
│   ├── test_services.py
│   ├── test_book_upload_service.py
│   └── test_txt_service.py
└── test_web/                # Web 层测试
    ├── test_web_routes.py
    ├── test_websocket.py
    └── test_reader_routes.py
```

### 核心 Fixtures

```python
# tests/test_e2e/conftest.py 中的关键 fixtures

@pytest.fixture
async def test_db():
    """创建内存 SQLite 测试数据库"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine

@pytest.fixture
def authenticated_client(test_db):
    """已认证的 FastAPI TestClient"""
    app.dependency_overrides[get_db] = lambda: test_db
    with TestClient(app) as client:
        # 设置认证 cookie
        client.cookies.set("auth_token", "test_token")
        yield client

@pytest.fixture
def temp_storage_path(tmp_path):
    """临时存储路径"""
    books_dir = tmp_path / "books"
    epubs_dir = tmp_path / "epubs"
    books_dir.mkdir()
    epubs_dir.mkdir()
    return tmp_path
```

### 测试配置 (pytest.ini)

```ini
[pytest]
addopts = -v --tb=short
testpaths = tests
python_files = test_*.py
python_functions = test_*
asyncio_mode = strict
log_cli_level = INFO
```

---

## 🔴 低覆盖率模块测试建议

按优先级排序：**高影响低难度 → 高影响中难度 → WebSocket 端到端**

---

### 1. `app/services/user_service.py` (23% → 目标 80%+)

**优先级**: ⭐⭐⭐ 高 | **难度**: 🟢 低

#### 需要测试的函数

| 函数 | 行号 | 功能描述 |
|------|------|---------|
| `list_users()` | 18 | 列出所有用户 |
| `get_user()` / `get_user_by_name()` | 21-30 | 用户查询 |
| `create_user()` | 32-46 | 创建新用户 |
| `rename_user()` | 48-68 | 重命名用户 |
| `delete_user()` | 70-79 | 删除用户 |
| `list_user_books()` | 82-116 | 列出用户书架 |
| `add_book_to_user()` | 118-136 | 添加书籍到书架 |
| `remove_book_from_user()` | 138-149 | 从书架移除书籍 |
| `get_user_book_ids()` | 151-157 | 获取用户所有书籍 ID |

#### 推荐测试文件

创建 `tests/test_services/test_user_service.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.models import User, Book, UserBook


class TestUserService:
    """用户服务测试"""

    @pytest.fixture
    def mock_db(self):
        """Mock 数据库会话"""
        db = MagicMock(spec=Session)
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建 UserService 实例"""
        return UserService(db=mock_db)

    # ========== list_users 测试 ==========

    def test_list_users_empty(self, service, mock_db):
        """测试空用户列表"""
        mock_db.query.return_value.all.return_value = []
        result = service.list_users()
        assert result == []

    def test_list_users_with_data(self, service, mock_db):
        """测试返回用户列表"""
        users = [User(id="1", username="user1"), User(id="2", username="user2")]
        mock_db.query.return_value.all.return_value = users
        result = service.list_users()
        assert len(result) == 2

    # ========== create_user 测试 ==========

    def test_create_user_success(self, service, mock_db):
        """测试成功创建用户"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user = service.create_user("new_user")
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        assert user.username == "new_user"

    def test_create_user_empty_name_raises(self, service):
        """测试空用户名抛出异常"""
        with pytest.raises(ValueError, match="用户名不能为空"):
            service.create_user("")

    def test_create_user_whitespace_name_raises(self, service):
        """测试空白用户名抛出异常"""
        with pytest.raises(ValueError, match="用户名不能为空"):
            service.create_user("   ")

    def test_create_user_duplicate_raises(self, service, mock_db):
        """测试重复用户名抛出异常"""
        existing_user = User(id="1", username="existing")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        with pytest.raises(ValueError, match="用户名已存在"):
            service.create_user("existing")

    # ========== rename_user 测试 ==========

    def test_rename_user_success(self, service, mock_db):
        """测试成功重命名用户"""
        user = User(id="1", username="old_name")
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, None]
        
        result = service.rename_user("1", "new_name")
        
        assert result.username == "new_name"
        mock_db.commit.assert_called_once()

    def test_rename_user_not_found_raises(self, service, mock_db):
        """测试用户不存在抛出异常"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="用户不存在"):
            service.rename_user("nonexistent", "new_name")

    def test_rename_user_duplicate_name_raises(self, service, mock_db):
        """测试重命名为已存在的用户名抛出异常"""
        user = User(id="1", username="user1")
        existing = User(id="2", username="existing")
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, existing]
        
        with pytest.raises(ValueError, match="用户名已存在"):
            service.rename_user("1", "existing")

    # ========== delete_user 测试 ==========

    def test_delete_user_success(self, service, mock_db):
        """测试成功删除用户"""
        user = User(id="1", username="to_delete")
        mock_db.query.return_value.filter.return_value.first.return_value = user
        
        service.delete_user("1")
        
        mock_db.delete.assert_called_once_with(user)
        mock_db.commit.assert_called_once()

    def test_delete_user_not_found_raises(self, service, mock_db):
        """测试删除不存在的用户抛出异常"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="用户不存在"):
            service.delete_user("nonexistent")

    # ========== add_book_to_user 测试 ==========

    def test_add_book_to_user_success(self, service, mock_db):
        """测试成功添加书籍到用户书架"""
        user = User(id="1", username="user1")
        book = Book(id="book1", title="Test Book")
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, book, None]
        
        service.add_book_to_user("1", "book1")
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_add_book_to_user_already_exists(self, service, mock_db):
        """测试书籍已在书架中"""
        user = User(id="1", username="user1")
        book = Book(id="book1", title="Test Book")
        user_book = UserBook(user_id="1", book_id="book1")
        mock_db.query.return_value.filter.return_value.first.side_effect = [user, book, user_book]
        
        # 应该不抛出异常，静默处理
        service.add_book_to_user("1", "book1")

    # ========== remove_book_from_user 测试 ==========

    def test_remove_book_from_user_success(self, service, mock_db):
        """测试成功从书架移除书籍"""
        user_book = UserBook(user_id="1", book_id="book1")
        mock_db.query.return_value.filter.return_value.first.return_value = user_book
        
        service.remove_book_from_user("1", "book1")
        
        mock_db.delete.assert_called_once_with(user_book)
        mock_db.commit.assert_called_once()

    # ========== list_user_books 测试 ==========

    def test_list_user_books_empty(self, service, mock_db):
        """测试空书架"""
        user = User(id="1", username="user1")
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        result = service.list_user_books("1")
        assert result == []
```

#### Mock 策略说明

- 使用 `MagicMock(spec=Session)` 模拟数据库会话
- 链式调用使用 `return_value` 连接
- 多次调用同一方法使用 `side_effect` 列表

---

### 2. `app/api/biquge.py` (16% → 目标 80%+)

**优先级**: ⭐⭐⭐ 高 | **难度**: 🟡 中

#### 需要测试的函数

| 函数 | 行号 | 功能描述 |
|------|------|---------|
| `search()` | 63-116 | 搜索书籍 |
| `get_book_detail()` | 118-163 | 获取书籍详情 |
| `get_chapter_list()` | 165-203 | 获取章节列表 |
| `get_chapter_content()` | 214-252 | 获取章节正文 |
| `set_current_book_id()` | 254-256 | 设置当前 book_id |

#### 推荐测试文件

在 `tests/test_api/test_api_client.py` 中添加或创建 `tests/test_api/test_biquge_api.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.api.biquge import BiqugeAPI


class TestBiqugeAPI:
    """笔趣阁 API 测试"""

    @pytest.fixture
    def api(self):
        """创建 BiqugeAPI 实例"""
        return BiqugeAPI()

    @pytest.fixture
    def mock_search_html(self):
        """搜索结果 HTML 模拟"""
        return """
        <html>
        <body>
            <div class="result-list">
                <div class="result-item">
                    <a class="result-game-item-title-link" href="/book/12345/">
                        <span>测试小说</span>
                    </a>
                    <p class="result-game-item-info-tag">作者：测试作者</p>
                </div>
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def mock_book_detail_html(self):
        """书籍详情 HTML 模拟"""
        return """
        <html>
        <body>
            <div id="info">
                <h1>测试小说</h1>
                <p>作者：测试作者</p>
            </div>
            <div id="intro">
                <p>这是简介内容</p>
            </div>
            <div id="fmimg">
                <img src="/cover/12345.jpg" />
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def mock_chapter_list_html(self):
        """章节列表 HTML 模拟"""
        return """
        <html>
        <body>
            <div id="list">
                <dl>
                    <dd><a href="/book/12345/1.html">第一章 开始</a></dd>
                    <dd><a href="/book/12345/2.html">第二章 继续</a></dd>
                </dl>
            </div>
        </body>
        </html>
        """

    @pytest.fixture
    def mock_chapter_content_html(self):
        """章节内容 HTML 模拟"""
        return """
        <html>
        <body>
            <div id="content">
                这是章节正文内容。
                第二段内容。
            </div>
        </body>
        </html>
        """

    # ========== search 测试 ==========

    @pytest.mark.asyncio
    async def test_search_success(self, api, mock_search_html):
        """测试搜索成功返回结果"""
        mock_response = MagicMock()
        mock_response.text = mock_search_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(api.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await api.search("测试")
            
            assert len(result) > 0
            assert result[0]["title"] == "测试小说"

    @pytest.mark.asyncio
    async def test_search_empty_keyword(self, api):
        """测试空关键词搜索"""
        result = await api.search("")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_no_results(self, api):
        """测试无搜索结果"""
        mock_response = MagicMock()
        mock_response.text = "<html><body><div class='result-list'></div></body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(api.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await api.search("不存在的书")
            assert result == []

    @pytest.mark.asyncio
    async def test_search_network_error(self, api):
        """测试网络错误处理"""
        with patch.object(api.client, 'get', new_callable=AsyncMock, 
                          side_effect=httpx.ConnectError("Connection failed")):
            with pytest.raises(httpx.ConnectError):
                await api.search("测试")

    # ========== get_book_detail 测试 ==========

    @pytest.mark.asyncio
    async def test_get_book_detail_success(self, api, mock_book_detail_html):
        """测试获取书籍详情成功"""
        mock_response = MagicMock()
        mock_response.text = mock_book_detail_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(api.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await api.get_book_detail("12345")
            
            assert result["title"] == "测试小说"
            assert result["author"] == "测试作者"

    @pytest.mark.asyncio
    async def test_get_book_detail_not_found(self, api):
        """测试书籍不存在"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        ))

        with patch.object(api.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await api.get_book_detail("nonexistent")

    # ========== get_chapter_list 测试 ==========

    @pytest.mark.asyncio
    async def test_get_chapter_list_success(self, api, mock_chapter_list_html):
        """测试获取章节列表成功"""
        mock_response = MagicMock()
        mock_response.text = mock_chapter_list_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(api.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await api.get_chapter_list("12345")
            
            assert len(result) == 2
            assert result[0]["title"] == "第一章 开始"

    @pytest.mark.asyncio
    async def test_get_chapter_list_empty(self, api):
        """测试空章节列表"""
        mock_response = MagicMock()
        mock_response.text = "<html><body><div id='list'><dl></dl></div></body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(api.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await api.get_chapter_list("12345")
            assert result == []

    # ========== get_chapter_content 测试 ==========

    @pytest.mark.asyncio
    async def test_get_chapter_content_success(self, api, mock_chapter_content_html):
        """测试获取章节内容成功"""
        api.set_current_book_id("12345")
        
        mock_response = MagicMock()
        mock_response.text = mock_chapter_content_html
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(api.client, 'get', new_callable=AsyncMock, return_value=mock_response):
            result = await api.get_chapter_content("1")
            
            assert "章节正文内容" in result["content"]

    @pytest.mark.asyncio
    async def test_get_chapter_content_missing_book_id(self, api):
        """测试未设置 book_id 时获取章节内容"""
        api._current_book_id = None
        
        with pytest.raises(ValueError, match="book_id"):
            await api.get_chapter_content("1")

    # ========== set_current_book_id 测试 ==========

    def test_set_current_book_id(self, api):
        """测试设置当前 book_id"""
        api.set_current_book_id("12345")
        assert api._current_book_id == "12345"

    def test_set_current_book_id_none(self, api):
        """测试设置 None book_id"""
        api.set_current_book_id("12345")
        api.set_current_book_id(None)
        assert api._current_book_id is None
```

#### Mock 策略说明

- 使用 HTML 字符串模拟网站响应
- `patch.object(api.client, 'get')` 模拟 HTTP 请求
- `new_callable=AsyncMock` 用于异步方法
- 需要模拟 `raise_for_status()` 方法

---

### 3. `app/web/routes/tasks_start.py` (20% → 目标 70%+)

**优先级**: ⭐⭐ 中 | **难度**: 🟡 中

#### 需要测试的函数

| 函数 | 行号 | 功能描述 |
|------|------|---------|
| `_download_book_background()` | 28-86 | 后台下载任务执行 |
| `start_download()` | 88-210 | 启动下载任务端点 |
| `update_book()` | 213-352 | 更新书籍（下载新章节）|

#### 推荐测试文件

在 `tests/test_web/` 中添加 `test_tasks_start.py`:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import Book, Task


class TestTasksStartRoutes:
    """任务启动路由测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        with TestClient(app) as client:
            client.cookies.set("auth_token", "test_token")
            yield client

    @pytest.fixture
    def mock_book(self):
        """模拟书籍对象"""
        book = MagicMock(spec=Book)
        book.id = "test-book-id"
        book.title = "测试小说"
        book.source = "fanqie"
        book.source_id = "12345"
        book.author = "测试作者"
        return book

    @pytest.fixture
    def mock_task(self):
        """模拟任务对象"""
        task = MagicMock(spec=Task)
        task.id = "test-task-id"
        task.book_id = "test-book-id"
        task.status = "pending"
        task.progress = 0
        return task

    # ========== start_download 测试 ==========

    def test_start_download_success(self, client, mock_book, mock_task):
        """测试成功启动下载任务"""
        with patch('app.web.routes.tasks_start.BookService') as MockBookService, \
             patch('app.web.routes.tasks_start.DownloadService') as MockDownloadService, \
             patch('app.web.routes.tasks_start.background_tasks', {}):
            
            mock_book_service = MagicMock()
            mock_book_service.get_or_create_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_book_service
            
            mock_download_service = MagicMock()
            mock_download_service.create_task = AsyncMock(return_value=mock_task)
            MockDownloadService.return_value = mock_download_service

            response = client.post("/api/v1/tasks/download", json={
                "source": "fanqie",
                "source_id": "12345"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "task_id" in data["data"]

    def test_start_download_invalid_source(self, client):
        """测试无效的源站"""
        response = client.post("/api/v1/tasks/download", json={
            "source": "invalid_source",
            "source_id": "12345"
        })
        
        assert response.status_code in [400, 422]

    def test_start_download_missing_source_id(self, client):
        """测试缺少 source_id"""
        response = client.post("/api/v1/tasks/download", json={
            "source": "fanqie"
        })
        
        assert response.status_code == 422

    def test_start_download_duplicate_task(self, client, mock_book):
        """测试重复任务检测"""
        with patch('app.web.routes.tasks_start.BookService') as MockBookService, \
             patch('app.web.routes.tasks_start.background_tasks', {"existing-task": MagicMock()}):
            
            mock_book_service = MagicMock()
            mock_book_service.get_book_by_source = AsyncMock(return_value=mock_book)
            mock_book_service.has_running_task = AsyncMock(return_value=True)
            MockBookService.return_value = mock_book_service

            response = client.post("/api/v1/tasks/download", json={
                "source": "fanqie",
                "source_id": "12345"
            })
            
            # 应该返回已存在的任务或错误
            assert response.status_code in [200, 409]

    # ========== update_book 测试 ==========

    def test_update_book_success(self, client, mock_book, mock_task):
        """测试成功更新书籍"""
        with patch('app.web.routes.tasks_start.BookService') as MockBookService, \
             patch('app.web.routes.tasks_start.DownloadService') as MockDownloadService:
            
            mock_book_service = MagicMock()
            mock_book_service.get_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_book_service
            
            mock_download_service = MagicMock()
            mock_download_service.create_update_task = AsyncMock(return_value=mock_task)
            MockDownloadService.return_value = mock_download_service

            response = client.post(f"/api/v1/tasks/update/{mock_book.id}")
            
            assert response.status_code == 200

    def test_update_book_not_found(self, client):
        """测试更新不存在的书籍"""
        with patch('app.web.routes.tasks_start.BookService') as MockBookService:
            mock_book_service = MagicMock()
            mock_book_service.get_book = AsyncMock(return_value=None)
            MockBookService.return_value = mock_book_service

            response = client.post("/api/v1/tasks/update/nonexistent-id")
            
            assert response.status_code == 404

    def test_update_book_already_running(self, client, mock_book):
        """测试书籍已有运行中的任务"""
        with patch('app.web.routes.tasks_start.BookService') as MockBookService, \
             patch('app.web.routes.tasks_start.DownloadService') as MockDownloadService:
            
            mock_book_service = MagicMock()
            mock_book_service.get_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_book_service
            
            mock_download_service = MagicMock()
            mock_download_service.has_running_task = AsyncMock(return_value=True)
            MockDownloadService.return_value = mock_download_service

            response = client.post(f"/api/v1/tasks/update/{mock_book.id}")
            
            assert response.status_code in [200, 409]
```

#### Mock 策略说明

- `patch('app.web.routes.tasks_start.background_tasks', {})` 清空后台任务字典
- 使用 `AsyncMock` 模拟异步服务方法
- 使用 FastAPI `TestClient` 进行端点测试

---

### 4. `app/web/routes/books_epub.py` & `books_txt.py` (16-21% → 目标 70%+)

**优先级**: ⭐⭐ 中 | **难度**: 🟡 中

#### 需要测试的函数

| 文件 | 函数 | 功能描述 |
|------|------|---------|
| books_epub.py | `generate_epub()` | 异步生成 EPUB |
| books_epub.py | `get_epub_status()` | 获取生成状态 |
| books_epub.py | `download_epub()` | 下载 EPUB 文件 |
| books_txt.py | `generate_txt()` | 异步生成 TXT |
| books_txt.py | `get_txt_status()` | 获取生成状态 |
| books_txt.py | `download_txt()` | 下载 TXT 文件 |

#### 推荐测试文件

创建 `tests/test_web/test_export_routes.py`:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.models import Book


class TestEPUBRoutes:
    """EPUB 导出路由测试"""

    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            client.cookies.set("auth_token", "test_token")
            yield client

    @pytest.fixture
    def mock_book(self):
        book = MagicMock(spec=Book)
        book.id = "test-book-id"
        book.title = "测试小说"
        book.author = "测试作者"
        return book

    # ========== generate_epub 测试 ==========

    def test_generate_epub_success(self, client, mock_book):
        """测试成功触发 EPUB 生成"""
        with patch('app.web.routes.books_epub.BookService') as MockBookService, \
             patch('app.web.routes.books_epub.epub_generation_tasks', {}):
            
            mock_service = MagicMock()
            mock_service.get_book = AsyncMock(return_value=mock_book)
            mock_service.get_chapter_count = AsyncMock(return_value=100)
            MockBookService.return_value = mock_service

            response = client.post(f"/api/v1/books/{mock_book.id}/epub/generate")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_generate_epub_book_not_found(self, client):
        """测试书籍不存在"""
        with patch('app.web.routes.books_epub.BookService') as MockBookService:
            mock_service = MagicMock()
            mock_service.get_book = AsyncMock(return_value=None)
            MockBookService.return_value = mock_service

            response = client.post("/api/v1/books/nonexistent/epub/generate")
            
            assert response.status_code == 404

    def test_generate_epub_no_chapters(self, client, mock_book):
        """测试没有章节的书籍"""
        with patch('app.web.routes.books_epub.BookService') as MockBookService:
            mock_service = MagicMock()
            mock_service.get_book = AsyncMock(return_value=mock_book)
            mock_service.get_chapter_count = AsyncMock(return_value=0)
            MockBookService.return_value = mock_service

            response = client.post(f"/api/v1/books/{mock_book.id}/epub/generate")
            
            assert response.status_code == 400

    # ========== get_epub_status 测试 ==========

    def test_get_epub_status_generating(self, client, mock_book):
        """测试获取生成中状态"""
        with patch('app.web.routes.books_epub.BookService') as MockBookService, \
             patch('app.web.routes.books_epub.epub_generation_tasks', {
                 mock_book.id: {"status": "generating", "progress": 50}
             }):
            
            mock_service = MagicMock()
            mock_service.get_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_service

            response = client.get(f"/api/v1/books/{mock_book.id}/epub/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "generating"
            assert data["data"]["progress"] == 50

    def test_get_epub_status_completed(self, client, mock_book):
        """测试获取完成状态"""
        with patch('app.web.routes.books_epub.BookService') as MockBookService, \
             patch('app.web.routes.books_epub.StorageService') as MockStorageService, \
             patch('app.web.routes.books_epub.epub_generation_tasks', {}):
            
            mock_book_service = MagicMock()
            mock_book_service.get_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_book_service
            
            mock_storage = MagicMock()
            mock_storage.get_epub_path.return_value = Path("/fake/path.epub")
            MockStorageService.return_value = mock_storage
            
            with patch.object(Path, 'exists', return_value=True):
                response = client.get(f"/api/v1/books/{mock_book.id}/epub/status")
                
                assert response.status_code == 200
                data = response.json()
                assert data["data"]["status"] == "completed"

    # ========== download_epub 测试 ==========

    def test_download_epub_success(self, client, mock_book, tmp_path):
        """测试成功下载 EPUB"""
        # 创建临时 EPUB 文件
        epub_file = tmp_path / "test.epub"
        epub_file.write_bytes(b"PK\x03\x04")  # EPUB 文件头
        
        with patch('app.web.routes.books_epub.BookService') as MockBookService, \
             patch('app.web.routes.books_epub.StorageService') as MockStorageService:
            
            mock_book_service = MagicMock()
            mock_book_service.get_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_book_service
            
            mock_storage = MagicMock()
            mock_storage.get_epub_path.return_value = epub_file
            MockStorageService.return_value = mock_storage

            response = client.get(f"/api/v1/books/{mock_book.id}/epub/download")
            
            assert response.status_code == 200
            assert "application/epub+zip" in response.headers.get("content-type", "")

    def test_download_epub_not_generated(self, client, mock_book):
        """测试 EPUB 未生成"""
        with patch('app.web.routes.books_epub.BookService') as MockBookService, \
             patch('app.web.routes.books_epub.StorageService') as MockStorageService:
            
            mock_book_service = MagicMock()
            mock_book_service.get_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_book_service
            
            mock_storage = MagicMock()
            mock_storage.get_epub_path.return_value = Path("/nonexistent/path.epub")
            MockStorageService.return_value = mock_storage

            response = client.get(f"/api/v1/books/{mock_book.id}/epub/download")
            
            assert response.status_code == 404


class TestTXTRoutes:
    """TXT 导出路由测试"""

    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            client.cookies.set("auth_token", "test_token")
            yield client

    @pytest.fixture
    def mock_book(self):
        book = MagicMock(spec=Book)
        book.id = "test-book-id"
        book.title = "测试小说"
        book.author = "测试作者"
        return book

    def test_generate_txt_success(self, client, mock_book):
        """测试成功触发 TXT 生成"""
        with patch('app.web.routes.books_txt.BookService') as MockBookService, \
             patch('app.web.routes.books_txt.txt_generation_tasks', {}):
            
            mock_service = MagicMock()
            mock_service.get_book = AsyncMock(return_value=mock_book)
            mock_service.get_chapter_count = AsyncMock(return_value=100)
            MockBookService.return_value = mock_service

            response = client.post(f"/api/v1/books/{mock_book.id}/txt/generate")
            
            assert response.status_code == 200

    def test_download_txt_success(self, client, mock_book, tmp_path):
        """测试成功下载 TXT"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("测试内容", encoding="utf-8")
        
        with patch('app.web.routes.books_txt.BookService') as MockBookService, \
             patch('app.web.routes.books_txt.StorageService') as MockStorageService:
            
            mock_book_service = MagicMock()
            mock_book_service.get_book = AsyncMock(return_value=mock_book)
            MockBookService.return_value = mock_book_service
            
            mock_storage = MagicMock()
            mock_storage.get_txt_path.return_value = txt_file
            MockStorageService.return_value = mock_storage

            response = client.get(f"/api/v1/books/{mock_book.id}/txt/download")
            
            assert response.status_code == 200
```

---

### 5. `app/web/routes/ws.py` (13% → 目标 60%+)

**优先级**: ⭐ 中低 | **难度**: 🔴 高

#### 需要测试的函数

| 函数 | 行号 | 功能描述 |
|------|------|---------|
| `verify_websocket_auth()` | 32-57 | 验证 WebSocket 认证 |
| `task_progress_websocket()` | 60-221 | 任务进度 WebSocket |
| `book_download_progress()` | 224-395 | 书籍下载进度 WebSocket |

#### 推荐测试文件

在 `tests/test_web/test_websocket.py` 中扩展:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from starlette.websockets import WebSocketState, WebSocketDisconnect

from app.web.routes.ws import verify_websocket_auth


class TestWebSocketAuth:
    """WebSocket 认证测试"""

    @pytest.fixture
    def mock_websocket(self):
        """模拟 WebSocket 对象"""
        ws = MagicMock()
        ws.cookies = {}
        ws.query_params = {}
        return ws

    @pytest.mark.asyncio
    async def test_verify_auth_no_password_required(self, mock_websocket):
        """测试无需密码时认证通过"""
        with patch('app.web.routes.ws.get_settings') as mock_settings:
            settings = MagicMock()
            settings.app_password = None
            mock_settings.return_value = settings

            result = await verify_websocket_auth(mock_websocket)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_auth_valid_cookie(self, mock_websocket):
        """测试有效 Cookie 认证"""
        mock_websocket.cookies = {"auth_token": "valid_token"}
        
        with patch('app.web.routes.ws.get_settings') as mock_settings, \
             patch('app.web.routes.ws.verify_auth_token') as mock_verify:
            settings = MagicMock()
            settings.app_password = "secret"
            mock_settings.return_value = settings
            mock_verify.return_value = True

            result = await verify_websocket_auth(mock_websocket)
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_auth_invalid_cookie(self, mock_websocket):
        """测试无效 Cookie 认证失败"""
        mock_websocket.cookies = {"auth_token": "invalid_token"}
        
        with patch('app.web.routes.ws.get_settings') as mock_settings, \
             patch('app.web.routes.ws.verify_auth_token') as mock_verify:
            settings = MagicMock()
            settings.app_password = "secret"
            mock_settings.return_value = settings
            mock_verify.return_value = False

            result = await verify_websocket_auth(mock_websocket)
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_auth_query_param_token(self, mock_websocket):
        """测试 Query 参数 Token 认证"""
        mock_websocket.query_params = {"token": "valid_token"}
        
        with patch('app.web.routes.ws.get_settings') as mock_settings, \
             patch('app.web.routes.ws.verify_auth_token') as mock_verify:
            settings = MagicMock()
            settings.app_password = "secret"
            mock_settings.return_value = settings
            mock_verify.return_value = True

            result = await verify_websocket_auth(mock_websocket)
            assert result is True


class TestWebSocketEndpoints:
    """WebSocket 端点测试"""

    @pytest.fixture
    def mock_websocket(self):
        """模拟完整的 WebSocket 对象"""
        ws = AsyncMock()
        ws.client_state = WebSocketState.CONNECTED
        ws.cookies = {"auth_token": "test_token"}
        ws.query_params = {}
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_json = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_task_progress_auth_fail(self, mock_websocket):
        """测试认证失败时关闭连接"""
        from app.web.routes.ws import task_progress_websocket
        
        with patch('app.web.routes.ws.verify_websocket_auth', return_value=False):
            await task_progress_websocket(mock_websocket, "task-id")
            
            mock_websocket.close.assert_called_once_with(code=4001)

    @pytest.mark.asyncio
    async def test_task_progress_disconnect_handling(self, mock_websocket):
        """测试 WebSocket 断开连接处理"""
        from app.web.routes.ws import task_progress_websocket
        
        mock_websocket.receive_json = AsyncMock(side_effect=WebSocketDisconnect())
        
        with patch('app.web.routes.ws.verify_websocket_auth', return_value=True), \
             patch('app.web.routes.ws.DownloadService') as MockDownloadService:
            
            mock_service = MagicMock()
            mock_service.get_task = AsyncMock(return_value=MagicMock(status="completed"))
            MockDownloadService.return_value = mock_service

            # 不应抛出异常
            await task_progress_websocket(mock_websocket, "task-id")
            
            mock_websocket.accept.assert_called_once()
```

#### WebSocket 测试挑战和解决方案

| 挑战 | 解决方案 |
|------|---------|
| WebSocket 生命周期 | 使用 `AsyncMock` 模拟所有方法 |
| `WebSocketDisconnect` 异常 | 在 `receive_json` 上使用 `side_effect` |
| 认证 Cookie | 在 mock 对象的 `cookies` 字典中设置 |
| 回调函数注册 | Mock `ConnectionManager.register_callback` |

---

## 🧪 通用测试模式参考

### 1. 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected_value
```

### 2. 数据库测试 Fixture

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models import Base

@pytest.fixture
async def async_db():
    """异步数据库测试 fixture"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    await engine.dispose()
```

### 3. HTTP 客户端 Mock

```python
from unittest.mock import AsyncMock, patch
import httpx

@pytest.mark.asyncio
async def test_api_call():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "test"}
    mock_response.status_code = 200
    
    with patch.object(httpx.AsyncClient, 'get', 
                      new_callable=AsyncMock, 
                      return_value=mock_response):
        result = await api.fetch_data()
        assert result["data"] == "test"
```

### 4. 文件系统测试

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_storage(tmp_path):
    """临时存储目录"""
    books_dir = tmp_path / "books"
    epubs_dir = tmp_path / "epubs"
    txts_dir = tmp_path / "txts"
    
    books_dir.mkdir()
    epubs_dir.mkdir()
    txts_dir.mkdir()
    
    return {
        "root": tmp_path,
        "books": books_dir,
        "epubs": epubs_dir,
        "txts": txts_dir
    }
```

### 5. FastAPI TestClient

```python
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def authenticated_client():
    """已认证的测试客户端"""
    with TestClient(app) as client:
        # 设置认证 cookie
        client.cookies.set("auth_token", "test_token")
        yield client
```

### 6. 依赖注入覆盖

```python
from app.utils.database import get_db
from app.main import app

def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
```

---

## 🚀 测试执行命令

### 运行所有测试

```bash
pytest
```

### 运行并生成覆盖率报告

```bash
# 终端报告（显示未覆盖行）
pytest --cov=app --cov-report=term-missing

# HTML 报告
pytest --cov=app --cov-report=html
# 报告位置: htmlcov/index.html

# 指定覆盖率阈值
pytest --cov=app --cov-fail-under=70
```

### 运行特定测试文件

```bash
# 运行单个文件
pytest tests/test_services/test_user_service.py

# 运行特定测试类
pytest tests/test_services/test_user_service.py::TestUserService

# 运行特定测试方法
pytest tests/test_services/test_user_service.py::TestUserService::test_create_user_success
```

### 运行带标记的测试

```bash
# 只运行异步测试
pytest -m asyncio

# 跳过慢速测试
pytest -m "not slow"
```

### 并行运行测试

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用 4 个进程并行运行
pytest -n 4
```

---

## 📋 测试优先级清单

按「高影响低难度优先」原则排序：

| 优先级 | 模块 | 当前覆盖率 | 目标覆盖率 | 预计测试数 |
|--------|------|-----------|-----------|-----------|
| 1 | `user_service.py` | 23% | 80%+ | 12-15 |
| 2 | `biquge.py` | 16% | 80%+ | 10-12 |
| 3 | `tasks_start.py` | 20% | 70%+ | 8-10 |
| 4 | `books_epub.py` | 16% | 70%+ | 8-10 |
| 5 | `books_txt.py` | 21% | 70%+ | 6-8 |
| 6 | `users.py` (routes) | 24% | 70%+ | 8-10 |
| 7 | `ws.py` | 13% | 60%+ | 10-12 |
| 8 | `auth.py` | 51% | 80%+ | 5-6 |
| 9 | `books_crud.py` | 47% | 70%+ | 8-10 |
| 10 | `books_maintenance.py` | 33% | 70%+ | 6-8 |

---

## 📝 附录：常见测试陷阱

### 1. 异步测试未使用 `@pytest.mark.asyncio`

```python
# ❌ 错误
async def test_async_function():
    pass

# ✅ 正确
@pytest.mark.asyncio
async def test_async_function():
    pass
```

### 2. Mock 对象未正确链式调用

```python
# ❌ 错误
mock_db.query.filter.first.return_value = None

# ✅ 正确
mock_db.query.return_value.filter.return_value.first.return_value = None
```

### 3. AsyncMock 与 MagicMock 混淆

```python
# ❌ 错误 - 同步 mock 用于异步方法
mock_service.get_book = MagicMock(return_value=book)

# ✅ 正确 - 异步 mock
mock_service.get_book = AsyncMock(return_value=book)
```

### 4. 全局状态未清理

```python
# ✅ 每个测试前清理全局字典
@pytest.fixture(autouse=True)
def clear_global_state():
    from app.web.routes.books_epub import epub_generation_tasks
    epub_generation_tasks.clear()
    yield
    epub_generation_tasks.clear()
```

### 5. 文件路径在 Windows/Linux 不兼容

```python
# ❌ 错误 - 硬编码路径分隔符
path = "/data/books/test.epub"

# ✅ 正确 - 使用 pathlib
from pathlib import Path
path = Path("data") / "books" / "test.epub"
```

---

> 💡 **提示**: 建议每完成一个模块的测试后，运行 `pytest --cov=app --cov-report=term-missing` 验证覆盖率提升情况。
