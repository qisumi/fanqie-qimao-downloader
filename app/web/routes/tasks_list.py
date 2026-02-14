import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.schemas import TaskListResponse, TaskResponse
from app.usecases import TaskReadUseCase
from app.utils.database import get_db
from app.web.mappers import to_task_response

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
        usecase = TaskReadUseCase(db=db)
        result = usecase.list_tasks(
            book_id=book_id,
            status=status,
            page=page,
            limit=limit,
        )
        tasks = [to_task_response(task) for task in result["tasks"]]
        
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
        usecase = TaskReadUseCase(db=db)
        task = usecase.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return to_task_response(task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task error: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")
