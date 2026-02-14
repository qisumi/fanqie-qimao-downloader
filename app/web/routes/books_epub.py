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
    "/{book_id}/epub",
    summary="异步生成EPUB",
    response_description="返回任务启动结果",
    responses={
        200: {
            "description": "任务启动成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "EPUB生成任务已启动",
                        "book_id": "uuid-string"
                    }
                }
            }
        },
        404: {"description": "书籍不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def generate_epub(
    background_tasks: BackgroundTasks,
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    异步生成EPUB
    
    在后台启动EPUB生成任务，立即返回任务状态。
    使用 GET /api/books/{book_id}/epub/status 查询进度。
    
    - **book_id**: 书籍UUID
    """
    try:
        usecase = ExportUseCase(db=db)
        return usecase.start_epub_generation(book_id=book_id, background_tasks=background_tasks)
    except ValueError as exc:
        if str(exc) == "书籍不存在":
            raise HTTPException(status_code=404, detail="书籍不存在")
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate EPUB error: {e}")
        raise HTTPException(status_code=500, detail=f"启动EPUB生成失败: {str(e)}")


@router.get(
    "/{book_id}/epub/status",
    summary="获取EPUB生成状态",
    response_description="返回EPUB生成任务的当前状态",
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
                                "message": "正在生成EPUB..."
                            }
                        },
                        "completed": {
                            "summary": "生成完成",
                            "value": {
                                "status": "completed",
                                "progress": 100,
                                "message": "EPUB生成成功",
                                "file_path": "/path/to/book.epub"
                            }
                        },
                        "not_started": {
                            "summary": "未启动",
                            "value": {
                                "status": "not_started",
                                "message": "没有正在进行的EPUB生成任务"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_epub_status(
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取EPUB生成状态
    
    查询异步EPUB生成任务的当前状态。
    
    - **book_id**: 书籍UUID
    """
    return ExportUseCase(db=db).get_epub_status(book_id)


@router.get("/{book_id}/epub/download")
async def download_epub(
    background_tasks: BackgroundTasks,
    book_id: str,
    db: Session = Depends(get_db),
):
    """
    下载EPUB文件
    
    如果EPUB文件已生成，返回文件下载。
    如果尚未生成，返回404错误。
    
    - **book_id**: 书籍UUID
    """
    try:
        usecase = ExportUseCase(db=db)
        action = usecase.ensure_epub_download_ready(
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
            media_type="application/epub+zip",
        )
    except ValueError as exc:
        if str(exc) == "书籍不存在":
            raise HTTPException(status_code=404, detail="书籍不存在")
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download EPUB error: {e}")
        raise HTTPException(status_code=500, detail=f"下载EPUB失败: {str(e)}")
