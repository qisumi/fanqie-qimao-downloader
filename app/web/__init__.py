"""
Web层模块

提供FastAPI Web应用的各个组件:
- routes: API和页面路由
- templates: Jinja2模板
- static: 静态资源
"""

from app.web import routes

__all__ = [
    "routes",
]