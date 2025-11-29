"""
页面路由 - HTML页面渲染
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.web.middleware.auth import AuthMiddleware

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/login")
async def login_page(request: Request, next: str = "/", error: str = None):
    """登录页面"""
    settings = get_settings()
    
    # 如果没有配置密码，直接重定向到首页
    if not settings.app_password:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse(request, "login.html", {
        "next": next,
        "error": error
    })


@router.post("/login")
async def login(request: Request, password: str = Form(...), next: str = Form("/")):
    """处理登录请求"""
    settings = get_settings()
    
    # 如果没有配置密码，直接重定向
    if not settings.app_password:
        return RedirectResponse(url=next, status_code=302)
    
    # 验证密码
    if password != settings.app_password:
        # 密码错误，重定向回登录页并显示错误
        return RedirectResponse(
            url=f"/login?next={next}&error=密码错误，请重试",
            status_code=302
        )
    
    # 密码正确，创建认证令牌并设置Cookie
    auth_middleware = AuthMiddleware(app=None, settings=settings)
    token = auth_middleware.create_auth_token()
    
    response = RedirectResponse(url=next, status_code=302)
    response.set_cookie(
        key=AuthMiddleware.COOKIE_NAME,
        value=token,
        max_age=settings.session_expire_hours * 3600,  # 秒
        httponly=True,  # 防止XSS
        samesite="lax"  # CSRF保护
    )
    
    return response


@router.get("/logout")
async def logout(request: Request):
    """登出"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key=AuthMiddleware.COOKIE_NAME)
    return response


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