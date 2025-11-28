"""
页面路由 - HTML页面渲染
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

@router.get("/")
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse(request, "index.html")

@router.get("/search")
async def search_page(request: Request):
    """搜索页面"""
    return templates.TemplateResponse(request, "search.html")

@router.get("/books")
async def books_page(request: Request):
    """书籍列表页面"""
    return templates.TemplateResponse(request, "books.html")

@router.get("/book/{book_id}")
async def book_detail_page(request: Request, book_id: str):
    """书籍详情页面"""
    return templates.TemplateResponse(request, "book_detail.html", {
        "book_id": book_id
    })

@router.get("/tasks")
async def tasks_page(request: Request):
    """任务管理页面"""
    return templates.TemplateResponse(request, "tasks.html")