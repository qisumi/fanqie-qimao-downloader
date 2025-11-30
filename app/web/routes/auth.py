"""
认证 API 路由 - JSON 格式接口

为 Vue SPA 前端提供认证 API
"""

from fastapi import APIRouter, Response, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings
from app.web.middleware.auth import get_auth_middleware

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求"""
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    message: str


class AuthStatusResponse(BaseModel):
    """认证状态响应"""
    authenticated: bool
    require_auth: bool


@router.post("/login", response_model=LoginResponse)
async def api_login(request: LoginRequest, response: Response):
    """
    JSON 格式登录接口
    
    验证密码并设置认证 Cookie
    """
    settings = get_settings()
    
    # 如果没有配置密码，直接返回成功
    if not settings.app_password:
        return LoginResponse(success=True, message="无需密码")
    
    # 验证密码
    if request.password != settings.app_password:
        raise HTTPException(status_code=401, detail="密码错误")
    
    # 创建认证令牌
    auth_middleware = get_auth_middleware()
    token = auth_middleware.create_auth_token()
    
    # 设置 Cookie
    response.set_cookie(
        key=auth_middleware.COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.session_expire_hours * 3600,
        samesite="lax"
    )
    
    return LoginResponse(success=True, message="登录成功")


@router.post("/logout", response_model=LoginResponse)
async def api_logout(response: Response):
    """
    JSON 格式登出接口
    
    删除认证 Cookie
    """
    auth_middleware = get_auth_middleware()
    response.delete_cookie(key=auth_middleware.COOKIE_NAME)
    return LoginResponse(success=True, message="已登出")


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(request: Request):
    """
    检查当前认证状态
    
    返回是否已认证以及是否需要认证
    """
    settings = get_settings()
    
    # 检查是否需要认证
    require_auth = bool(settings.app_password)
    
    if not require_auth:
        # 不需要认证，始终返回已认证
        return AuthStatusResponse(authenticated=True, require_auth=False)
    
    # 验证当前认证状态
    auth_middleware = get_auth_middleware()
    authenticated = auth_middleware._is_authenticated(request)
    
    return AuthStatusResponse(authenticated=authenticated, require_auth=True)
