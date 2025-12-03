"""
书籍API路由聚合器

将原本的单文件路由拆分为多个子模块，便于维护和扩展:
- books_search: 搜索接口
- books_crud: 创建、列表、详情
- books_status: 轻量状态与章节摘要
- books_maintenance: 删除、刷新、增量检查
- books_epub: EPUB 生成与下载
"""

import logging

from fastapi import APIRouter

from app.web.routes import (
    books_crud,
    books_epub,
    books_maintenance,
    books_reader,
    books_search,
    books_status,
)

logger = logging.getLogger(__name__)

router = APIRouter()

for sub_router in (
    books_search.router,
    books_crud.router,
    books_status.router,
    books_maintenance.router,
    books_epub.router,
    books_reader.router,
):
    router.include_router(sub_router)

__all__ = ["router"]
