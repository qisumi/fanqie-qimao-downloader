"""
FanqieQimaoDownloader - 番茄七猫小说下载器
FastAPI Web应用入口
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.web.routes import pages, books, tasks, stats

# 创建FastAPI应用
app = FastAPI(
    title="FanqieQimaoDownloader",
    description="番茄小说和七猫小说下载器，支持EPUB导出",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="app/web/templates")

# 注册路由
app.include_router(pages.router, prefix="", tags=["pages"])
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )