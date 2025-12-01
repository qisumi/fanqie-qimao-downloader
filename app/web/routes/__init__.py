"""
路由模块

导出所有API路由器:
- books: 书籍API路由
- tasks: 任务API路由
- stats: 统计API路由
- ws: WebSocket路由
- auth: 认证API路由
"""

from app.web.routes import books, tasks, stats, ws, auth, users

__all__ = [
    "books",
    "tasks",
    "stats",
    "ws",
    "auth",
    "users",
]
