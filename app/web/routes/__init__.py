"""
路由模块

导出所有API路由器:
- pages: 页面路由 (HTML渲染)
- books: 书籍API路由
- tasks: 任务API路由
- stats: 统计API路由
"""

from app.web.routes import pages, books, tasks, stats

__all__ = [
    "pages",
    "books",
    "tasks",
    "stats",
]