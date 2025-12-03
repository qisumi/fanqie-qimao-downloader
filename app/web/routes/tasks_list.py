import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.schemas.service_schemas import TaskListResponse, TaskResponse
from app.services import DownloadService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=TaskListResponse,
    summary="获取任务列表",
    response_description="返回分页的任务列表",
    responses={
        200: {"description": "获取成功"},
        500: {"description": "服务器内部错误"}
    }
)
async def list_tasks(
    book_id: Optional[str] = Query(None, description="按书籍UUID筛选"),
    status: Optional[str] = Query(None, description="按状态筛选", pattern="^(pending|running|completed|failed|cancelled)$"),
    page: int = Query(0, ge=0, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """
    获取任务列表
    
    - **book_id**: 按书籍UUID筛选
    - **status**: 按状态筛选 (pending/running/completed/failed/cancelled)
    - **page**: 页码，从0开始
    - **limit**: 每页数量
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        result = download_service.list_tasks(
            book_uuid=book_id,
            status=status,
            page=page,
            limit=limit,
        )
        
        tasks = []
        for task in result["tasks"]:
            tasks.append(TaskResponse(
                id=task.id,
                book_id=task.book_id,
                task_type=task.task_type,
                status=task.status or "pending",
                total_chapters=task.total_chapters or 0,
                downloaded_chapters=task.downloaded_chapters or 0,
                failed_chapters=task.failed_chapters or 0,
                progress=task.progress or 0.0,
                error_message=task.error_message,
                started_at=task.started_at,
                completed_at=task.completed_at,
                created_at=task.created_at,
            ))
        
        return TaskListResponse(
            tasks=tasks,
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
        )
        
    except Exception as e:
        logger.error(f"List tasks error: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    获取任务详情
    
    - **task_id**: 任务UUID
    """
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        task = download_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TaskResponse(
            id=task.id,
            book_id=task.book_id,
            task_type=task.task_type,
            status=task.status or "pending",
            total_chapters=task.total_chapters or 0,
            downloaded_chapters=task.downloaded_chapters or 0,
            failed_chapters=task.failed_chapters or 0,
            progress=task.progress or 0.0,
            error_message=task.error_message,
            started_at=task.started_at,
            completed_at=task.completed_at,
            created_at=task.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task error: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")
