"""
FanqieQimaoDownloader - 番茄七猫笔趣阁小说下载器
FastAPI Web应用入口
"""

from contextlib import asynccontextmanager

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.utils.logger import init_from_settings, get_logger
from app.web.routes import books, tasks, stats, ws, auth, users
from app.web.middleware import AuthMiddleware
from app.utils.database import Base, engine

# 初始化日志系统
init_from_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 50)
    logger.info("FanqieQimaoDownloader 启动中...")
    logger.info(f"运行地址: http://{settings.host}:{settings.port}")
    logger.info(f"调试模式: {settings.debug}")
    logger.info(f"日志级别: {settings.log_level}")
    logger.info(f"密码保护: {'已启用' if settings.app_password else '未启用'}")
    logger.info("=" * 50)

    # 确保新增的数据表存在（不会影响已有数据）
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # 关闭时
    logger.info("FanqieQimaoDownloader 正在关闭...")


# OpenAPI 标签元数据
tags_metadata = [
    {
        "name": "books",
        "description": "书籍管理接口。包括搜索书籍、添加书籍、查看书籍详情、删除书籍、生成EPUB等功能。",
    },
    {
        "name": "tasks",
        "description": "下载任务管理接口。包括查看任务列表、启动下载、更新书籍、取消任务、重试失败章节等功能。",
    },
    {
        "name": "stats",
        "description": "统计信息接口。提供系统概览、存储使用情况、配额使用情况等统计数据。",
    },
    {
        "name": "auth",
        "description": "认证接口。提供登录、登出和认证状态检查功能（仅在配置了密码时需要）。",
    },
    {
        "name": "users",
        "description": "用户与私人书架接口。用于管理用户列表、个人书架关联。",
    },
    {
        "name": "websocket",
        "description": "WebSocket 接口。提供实时进度推送功能，用于下载进度的实时更新。",
    },
]

# 创建FastAPI应用
app = FastAPI(
    title="FanqieQimaoDownloader",
    description="""番茄小说和七猫小说下载器 API 文档
    
## 功能特性

- 🔍 **搜索书籍**: 支持在番茄小说和七猫小说平台搜索书籍
- 📚 **书籍管理**: 添加、删除书籍，查看书籍详情和章节列表
- ⬇️ **批量下载**: 支持完整下载和增量更新，智能跳过已下载章节
- 📖 **EPUB导出**: 将下载的章节生成标准EPUB电子书格式
- 📊 **统计信息**: 实时查看下载进度、存储使用、配额使用情况
- 🔒 **密码保护**: 可选的密码保护功能，保护您的下载内容
- ⚡ **实时推送**: WebSocket 实时推送下载进度
- 🚦 **速率限制**: 每日字数限制，避免过度使用API

## 支持平台

- **fanqie**: 番茄小说 (https://fanqienovel.com)
- **qimao**: 七猫小说 (https://www.qimao.com)

## 配额说明

系统默认每日字数限制为 20,000,000 字，可通过环境变量 `DAILY_WORD_LIMIT` 配置。
配额按平台分别计算，每日凌晨重置。
    """,
    version="1.6.3",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "GitHub Repository",
        "url": "https://github.com/qisumi/fanqie-qimao-downloader",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan
)

# 前端静态文件目录
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "../frontend/dist")

# 挂载旧静态文件目录（保留图标等资源）
if os.path.exists("app/web/static"):
    app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# 生产模式: 挂载前端构建产物
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

# 添加认证中间件（仅当配置了密码时启用）
if settings.app_password:
    app.add_middleware(AuthMiddleware)

# 注册路由
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])

@app.get("/health", summary="健康检查", tags=["system"])
@app.head("/health")
async def health_check():
    """
    健康检查接口
    
    用于检查服务是否正常运行，通常用于Docker容器健康检查和负载均衡器。
    
    返回服务状态和版本号。
    """
    # 使用应用声明的版本，避免硬编码不一致
    return {"status": "healthy", "version": app.version}


# SPA Catch-all: 所有未匹配路由返回 index.html
if os.path.exists(FRONTEND_DIR):
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA 前端路由，未匹配的路径返回 index.html"""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        # 静态文件直接返回
        if os.path.isfile(file_path):
            # 根据文件扩展名设置正确的 MIME 类型
            if full_path.endswith('.json'):
                return FileResponse(file_path, media_type='application/json')
            if full_path.endswith('.js'):
                return FileResponse(file_path, media_type='application/javascript')
            if full_path.endswith('.css'):
                return FileResponse(file_path, media_type='text/css')
            if full_path.endswith('.svg'):
                return FileResponse(file_path, media_type='image/svg+xml')
            return FileResponse(file_path)
        # 其他路径返回 index.html（SPA 路由）
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
