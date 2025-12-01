"""
任务管理API路由聚合器

将任务相关的接口拆分为独立模块，便于维护:
- tasks_list: 任务列表与详情
- tasks_quota: 配额查询
- tasks_start: 下载/更新启动与后台执行
- tasks_control: 取消与重试
"""

import logging

from fastapi import APIRouter

from app.web.routes import tasks_control, tasks_list, tasks_quota, tasks_start

logger = logging.getLogger(__name__)

router = APIRouter()

for sub_router in (
    tasks_list.router,
    tasks_quota.router,
    tasks_start.router,
    tasks_control.router,
):
    router.include_router(sub_router)

__all__ = ["router"]
