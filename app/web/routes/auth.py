"""
认证 API 路由 - JSON 格式接口

为 Vue SPA 前端提供认证 API
"""

from fastapi import APIRouter, Response, HTTPException, Request
from pydantic import BaseModel, Field, ConfigDict

from app.config import get_settings
from app.web.middleware.auth import get_auth_middleware

router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求模型"""
    password: str = Field(..., description="登录密码", min_length=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "password": "your_password"
            }
        }
    )


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")


class AuthStatusResponse(BaseModel):
    """认证状态响应模型"""
    authenticated: bool = Field(..., description="当前是否已认证")
    require_auth: bool = Field(..., description="系统是否启用了认证")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    response_description="返回登录结果并设置认证Cookie",
    responses={
        200: {
            "description": "登录成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "登录成功"
                    }
                }
            }
        },
        401: {
            "description": "密码错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "密码错误"
                    }
                }
            }
        }
    }
)
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


@router.post(
    "/logout",
    response_model=LoginResponse,
    summary="用户登出",
    response_description="删除认证Cookie",
    responses={
        200: {
            "description": "登出成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "已登出"
                    }
                }
            }
        }
    }
)
async def api_logout(response: Response):
    """
    JSON 格式登出接口
    
    删除认证 Cookie
    """
    auth_middleware = get_auth_middleware()
    response.delete_cookie(key=auth_middleware.COOKIE_NAME)
    return LoginResponse(success=True, message="已登出")


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="检查认证状态",
    response_description="返回当前认证状态和系统认证配置",
    responses={
        200: {
            "description": "查询成功",
            "content": {
                "application/json": {
                    "examples": {
                        "authenticated": {
                            "summary": "已认证",
                            "value": {
                                "authenticated": True,
                                "require_auth": True
                            }
                        },
                        "not_authenticated": {
                            "summary": "未认证",
                            "value": {
                                "authenticated": False,
                                "require_auth": True
                            }
                        },
                        "no_auth_required": {
                            "summary": "无需认证",
                            "value": {
                                "authenticated": True,
                                "require_auth": False
                            }
                        }
                    }
                }
            }
        }
    }
)
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
