"""
统计信息API路由
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class SystemStats(BaseModel):
    total_books: int
    total_chapters: int
    storage_used: int  # bytes
    daily_quota_used: int
    daily_quota_limit: int

@router.get("/", response_model=SystemStats)
async def get_stats():
    """获取系统统计信息"""
    # TODO: 实现获取统计信息逻辑
    return SystemStats(
        total_books=0,
        total_chapters=0,
        storage_used=0,
        daily_quota_used=0,
        daily_quota_limit=200
    )