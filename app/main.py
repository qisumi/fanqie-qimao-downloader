"""
FanqieQimaoDownloader - 番茄七猫小说下载器
FastAPI Web应用入口
"""

from contextlib import asynccontextmanager

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.utils.logger import init_from_settings, get_logger
from app.web.routes import books, tasks, stats, ws, auth
from app.web.middleware import AuthMiddleware

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
    
    yield
    
    # 关闭时
    logger.info("FanqieQimaoDownloader 正在关闭...")


# 创建FastAPI应用
app = FastAPI(
    title="FanqieQimaoDownloader",
    description="番茄小说和七猫小说下载器，支持EPUB导出",
    version="1.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(ws.router, prefix="/ws", tags=["websocket"])

@app.get("/health")
@app.head("/health")
async def health_check():
    """健康检查接口"""
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
