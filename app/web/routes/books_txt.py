import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.services import BookService, TXTService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储TXT生成任务状态
_txt_tasks: Dict[str, Dict[str, Any]] = {}


async def _generate_txt_async(
    book_id: str,
    db_session_maker,
):
    """后台TXT生成任务"""
    _txt_tasks[book_id] = {
        "status": "running",
        "progress": 0,
        "message": "正在生成TXT...",
        "file_path": None,
        "error": None,
    }
    
    try:
        from app.utils.database import SessionLocal
        db = SessionLocal()
        
        try:
            storage = StorageService()
            book_service = BookService(db=db, storage=storage)
            txt_service = TXTService(db=db, storage=storage)
            
            result = book_service.get_book_with_chapters(book_id)
            if not result:
                raise ValueError("书籍不存在")
            
            book = result["book"]
            chapters = result["chapters"]
            
            completed_chapters = [
                ch for ch in chapters 
                if ch.download_status == "completed"
            ]
            
            if not completed_chapters:
                raise ValueError("没有已下载的章节可生成TXT")
            
            _txt_tasks[book_id]["progress"] = 30
            _txt_tasks[book_id]["message"] = f"准备生成TXT，共{len(completed_chapters)}章"
            
            txt_path = txt_service.generate_txt(book, completed_chapters)
            
            _txt_tasks[book_id] = {
                "status": "completed",
                "progress": 100,
                "message": "TXT生成成功",
                "file_path": txt_path,
                "error": None,
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"TXT generation error: {e}")
        _txt_tasks[book_id] = {
            "status": "failed",
            "progress": 0,
            "message": str(e),
            "file_path": None,
            "error": str(e),
        }


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
    book_id: str = Path(..., description="书籍UUID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    异步生成TXT
    
    在后台启动TXT生成任务，立即返回任务状态。
    使用 GET /api/books/{book_id}/txt/status 查询进度。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        if book_id in _txt_tasks and _txt_tasks[book_id].get("status") == "running":
            return {
                "success": True,
                "message": "TXT生成任务已在进行中",
                "status": _txt_tasks[book_id],
            }
        
        from app.utils.database import SessionLocal
        background_tasks.add_task(_generate_txt_async, book_id, SessionLocal)
        
        return {
            "success": True,
            "message": "TXT生成任务已启动",
            "book_id": book_id,
        }
        
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
) -> Dict[str, Any]:
    """
    获取TXT生成状态
    
    查询异步TXT生成任务的当前状态。
    
    - **book_id**: 书籍UUID
    """
    if book_id not in _txt_tasks:
        return {
            "status": "not_started",
            "message": "没有正在进行的TXT生成任务",
        }
    
    return _txt_tasks[book_id]


@router.get("/{book_id}/txt/download")
async def download_txt(
    book_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    下载TXT文件
    
    如果TXT文件已生成，返回文件下载。
    如果尚未生成，返回404错误。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        txt_path = storage.get_txt_path(book.title, book.id)

        # 如果文件不存在，启动后台生成任务并返回 202
        if not txt_path.exists():
            # 如果已有后台任务在运行或排队，告知客户端稍后重试
            if book_id in _txt_tasks and _txt_tasks[book_id].get("status") in ("running", "queued"):
                return JSONResponse({"detail": "TXT正在生成中，请稍后再试"}, status_code=202)

            # 标记为排队中并启动后台任务
            _txt_tasks[book_id] = {
                "status": "queued",
                "progress": 0,
                "message": "TXT生成任务已排队",
                "file_path": None,
                "error": None,
            }

            from app.utils.database import SessionLocal
            background_tasks.add_task(_generate_txt_async, book_id, SessionLocal)

            return JSONResponse({"detail": "TXT生成任务已启动，请稍后再试下载"}, status_code=202, background=background_tasks)

        # 文件存在，直接返回
        return FileResponse(
            path=str(txt_path),
            filename=f"{book.title}.txt",
            media_type="text/plain",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download TXT error: {e}")
        raise HTTPException(status_code=500, detail=f"下载TXT失败: {str(e)}")