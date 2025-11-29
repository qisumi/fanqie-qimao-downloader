"""
认证中间件 - 基于签名Cookie的密码保护
"""

import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import get_settings


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    
    使用 itsdangerous 对 Cookie 进行签名，确保认证状态安全。
    如果配置中 app_password 为空，则跳过认证。
    """
    
    # 不需要认证的路径前缀
    EXCLUDE_PATHS = [
        "/login",
        "/static",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    
    COOKIE_NAME = "auth_token"
    
    def __init__(self, app, settings=None):
        super().__init__(app)
        self.settings = settings or get_settings()
        self.serializer = URLSafeTimedSerializer(self.settings.secret_key)
    
    def _is_excluded_path(self, path: str) -> bool:
        """检查路径是否在排除列表中"""
        return any(path.startswith(prefix) for prefix in self.EXCLUDE_PATHS)
    
    def _is_authenticated(self, request: Request) -> bool:
        """检查请求是否已认证"""
        token = request.cookies.get(self.COOKIE_NAME)
        if not token:
            return False
        
        try:
            # 验证签名并检查过期时间
            max_age = self.settings.session_expire_hours * 3600  # 转换为秒
            data = self.serializer.loads(token, max_age=max_age)
            return data.get("authenticated") == True
        except (BadSignature, SignatureExpired):
            return False
    
    def create_auth_token(self) -> str:
        """创建认证令牌"""
        return self.serializer.dumps({
            "authenticated": True,
            "created_at": time.time()
        })
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 如果没有配置密码，跳过认证
        if not self.settings.app_password:
            return await call_next(request)
        
        path = request.url.path
        
        # 排除不需要认证的路径
        if self._is_excluded_path(path):
            return await call_next(request)
        
        # 检查认证状态
        if not self._is_authenticated(request):
            # 记录原始请求路径用于登录后重定向
            redirect_url = f"/login?next={path}"
            return RedirectResponse(url=redirect_url, status_code=302)
        
        return await call_next(request)


def get_auth_middleware():
    """获取认证中间件实例（用于创建/验证令牌）"""
    settings = get_settings()
    return AuthMiddleware(app=None, settings=settings)
