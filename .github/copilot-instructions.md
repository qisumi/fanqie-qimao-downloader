# GitHub Copilot 指令

## 项目概述

**Qisumi的书库** - 基于 Rain API V3 的番茄小说、七猫小说和笔趣阁下载工具，支持批量下载和EPUB导出。

这是一个全栈 Web 应用，包含：
- **后端**: Python FastAPI 异步 Web 框架
- **前端**: Vue 3 + Naive UI 单页应用
- **数据库**: SQLite + SQLAlchemy ORM + Alembic 迁移

## 技术栈

### 后端 (Python 3.8+)
- **Web 框架**: FastAPI + Uvicorn
- **数据验证**: Pydantic v2, pydantic-settings
- **数据库**: SQLAlchemy 2.0 (异步兼容), Alembic
- **HTTP 客户端**: httpx (异步)
- **文件处理**: aiofiles (异步文件 IO)
- **HTML 解析**: BeautifulSoup4
- **EPUB 生成**: ebooklib
- **模板引擎**: Jinja2
- **日志**: structlog

### 前端 (Node.js 18+)
- **框架**: Vue 3 (Composition API)
- **UI 库**: Naive UI
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **构建工具**: Vite 5
- **PWA**: vite-plugin-pwa + Workbox

## 项目结构

```
├── app/                    # 后端应用
│   ├── api/               # 外部 API 封装 (番茄、七猫、笔趣阁)
│   ├── models/            # SQLAlchemy 数据模型
│   ├── schemas/           # Pydantic 数据模式
│   ├── services/          # 业务逻辑服务层
│   ├── utils/             # 工具函数 (数据库、日志、限流)
│   ├── web/               # Web 层 (路由、中间件、WebSocket)
│   ├── config.py          # 配置管理
│   └── main.py            # FastAPI 应用入口
├── frontend/              # Vue 前端应用
│   ├── src/
│   │   ├── api/          # API 调用封装
│   │   ├── components/   # Vue 组件
│   │   ├── views/        # 页面视图
│   │   ├── stores/       # Pinia 状态管理
│   │   └── router/       # 路由配置
│   └── public/           # 静态资源
├── alembic/               # 数据库迁移
├── data/                  # 数据存储目录
├── tests/                 # 测试文件
└── reference/             # 参考文档 (API 规则)
```

## 编码规范

### Python 后端

1. **类型注解**: 所有函数必须使用类型注解
   ```python
   async def get_book(book_id: str) -> Optional[Book]:
   ```

2. **异步优先**: 使用 `async/await` 进行 IO 操作
   ```python
   async with httpx.AsyncClient() as client:
       response = await client.get(url)
   ```

3. **Pydantic 模型**: 使用 Pydantic v2 语法
   ```python
   class BookSchema(BaseModel):
       model_config = ConfigDict(from_attributes=True)
   ```

4. **日志**: 使用项目的 `get_logger` 函数
   ```python
   from app.utils.logger import get_logger
   logger = get_logger(__name__)
   ```

5. **数据库操作**: 使用 SQLAlchemy 2.0 风格
   ```python
   from sqlalchemy import select
   stmt = select(Book).where(Book.id == book_id)
   ```

6. **配置**: 通过 `settings` 单例访问配置
   ```python
   from app.config import settings
   ```

### Vue 前端

1. **组合式 API**: 使用 `<script setup>` 语法
   ```vue
   <script setup>
   import { ref, onMounted } from 'vue'
   const data = ref(null)
   </script>
   ```

2. **Naive UI**: 遵循 Naive UI 组件规范
   ```vue
   <n-button type="primary" @click="handleClick">
     按钮
   </n-button>
   ```

3. **API 调用**: 使用 `src/api/` 目录下的封装函数

4. **状态管理**: 使用 Pinia stores

5. **样式**: 使用 scoped CSS

## 数据库约定

- **主键**: 使用 UUID 字符串 (`str`)
- **时间戳**: 使用 `datetime` 类型，存储 UTC 时间
- **迁移**: 使用 Alembic 管理数据库迁移
  ```bash
  alembic revision --autogenerate -m "描述"
  alembic upgrade head
  ```

## API 设计

- **RESTful**: 遵循 REST 风格
- **路由前缀**: `/api/v1/`
- **响应格式**: 统一使用 `schemas/api_responses.py` 中的响应模型
- **WebSocket**: `/ws` 用于实时任务进度推送

## 测试

- 使用 pytest + pytest-asyncio
- 测试文件位于 `tests/` 目录
- 运行测试: `pytest`

## 常见任务

### 添加新的数据模型
1. 在 `app/models/` 创建模型文件
2. 在 `app/models/__init__.py` 导出
3. 创建对应的 Pydantic schema
4. 生成 Alembic 迁移

### 添加新的 API 端点
1. 在 `app/web/routes/` 添加路由
2. 在 `app/main.py` 注册路由
3. 添加对应的 schema 和服务

### 添加新的前端页面
1. 在 `frontend/src/views/` 创建视图
2. 在路由配置中注册
3. 添加必要的组件和 API 调用

## 环境变量

关键配置项（通过 `.env` 文件设置）：
- `RAIN_API_KEY`: Rain API 密钥
- `APP_PASSWORD`: 应用访问密码（可选）
- `SECRET_KEY`: Cookie 签名密钥
- `DATABASE_URL`: 数据库连接字符串

## 注意事项

1. **中文支持**: 项目面向中文用户，UI 和日志使用中文
2. **异步**: 后端全面使用异步，避免阻塞操作
3. **配额限制**: 遵守每日 2000 万字的下载限制
4. **PWA**: 前端支持 PWA，注意 Service Worker 缓存策略
5. **Docker**: 支持 Docker 部署，参考 `docker-compose.yml`
