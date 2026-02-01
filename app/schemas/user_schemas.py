"""
用户相关 Pydantic Schemas

定义用户相关的请求/响应数据模型
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """用户响应"""

    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    created_at: datetime = Field(..., description="创建时间")

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """用户列表响应"""

    users: List[UserResponse] = Field(default=[], description="用户列表")


class UserCreateRequest(BaseModel):
    """创建用户请求"""

    username: str = Field(..., min_length=1, max_length=50, description="用户名")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""

    username: str = Field(..., min_length=1, max_length=50, description="新用户名")