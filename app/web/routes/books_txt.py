import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.usecases import ExportUseCase
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/{book_id}/txt",
    summary="异步生成TXT",
    response_description="返回任务启动结果",
    responses={
        200: {
            "description": "任务启动成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "TXT生成任务已启动",
                        "book_id": "uuid-string"
                    }
                }
            }
        },
        404: {"description": "书籍不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def generate_txt(
    background_tasks: BackgroundTasks,
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    异步生成TXT
    
    在后台启动TXT生成任务，立即返回任务状态。
    使用 GET /api/books/{book_id}/txt/status 查询进度。
    
    - **book_id**: 书籍UUID
    """
    try:
        usecase = ExportUseCase(db=db)
        return usecase.start_txt_generation(book_id=book_id, background_tasks=background_tasks)
    except ValueError as exc:
        if str(exc) == "书籍不存在":
            raise HTTPException(status_code=404, detail="书籍不存在")
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate TXT error: {e}")
        raise HTTPException(status_code=500, detail=f"启动TXT生成失败: {str(e)}")


@router.get(
    "/{book_id}/txt/status",
    summary="获取TXT生成状态",
    response_description="返回TXT生成任务的当前状态",
    responses={
        200: {
            "description": "状态查询成功",
            "content": {
                "application/json": {
                    "examples": {
                        "running": {
                            "summary": "生成中",
                            "value": {
                                "status": "running",
                                "progress": 50,
                                "message": "正在生成TXT..."
                            }
                        },
                        "completed": {
                            "summary": "生成完成",
                            "value": {
                                "status": "completed",
                                "progress": 100,
                                "message": "TXT生成成功",
                                "file_path": "/path/to/book.txt"
                            }
                        },
                        "not_started": {
                            "summary": "未启动",
                            "value": {
                                "status": "not_started",
                                "message": "没有正在进行的TXT生成任务"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_txt_status(
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取TXT生成状态
    
    查询异步TXT生成任务的当前状态。
    
    - **book_id**: 书籍UUID
    """
    return ExportUseCase(db=db).get_txt_status(book_id)


@router.get("/{book_id}/txt/download")
async def download_txt(
    background_tasks: BackgroundTasks,
    book_id: str,
    db: Session = Depends(get_db),
):
    """
    下载TXT文件
    
    如果TXT文件已生成，返回文件下载。
    如果尚未生成，返回404错误。
    
    - **book_id**: 书籍UUID
    """
    try:
        usecase = ExportUseCase(db=db)
        action = usecase.ensure_txt_download_ready(
            book_id=book_id,
            background_tasks=background_tasks,
        )

        if action["type"] == "queued":
            return JSONResponse(
                {"detail": action["detail"]},
                status_code=action["status_code"],
                background=background_tasks,
            )

        return FileResponse(
            path=action["path"],
            filename=action["filename"],
            media_type="text/plain",
        )
    except ValueError as exc:
        if str(exc) == "书籍不存在":
            raise HTTPException(status_code=404, detail="书籍不存在")
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download TXT error: {e}")
        raise HTTPException(status_code=500, detail=f"下载TXT失败: {str(e)}")
