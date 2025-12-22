import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.services import BookService, EPUBService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储EPUB生成任务状态
_epub_tasks: Dict[str, Dict[str, Any]] = {}


async def _generate_epub_async(
    book_id: str,
    db_session_maker,
):
    """后台EPUB生成任务"""
    _epub_tasks[book_id] = {
        "status": "running",
        "progress": 0,
        "message": "正在生成EPUB...",
        "file_path": None,
        "error": None,
    }
    
    try:
        from app.utils.database import SessionLocal
        db = SessionLocal()
        
        try:
            storage = StorageService()
            book_service = BookService(db=db, storage=storage)
            epub_service = EPUBService(db=db, storage=storage)
            
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
                raise ValueError("没有已下载的章节可生成EPUB")
            
            _epub_tasks[book_id]["progress"] = 30
            _epub_tasks[book_id]["message"] = f"准备生成EPUB，共{len(completed_chapters)}章"
            
            epub_path = epub_service.generate_epub(book, completed_chapters)
            
            _epub_tasks[book_id] = {
                "status": "completed",
                "progress": 100,
                "message": "EPUB生成成功",
                "file_path": epub_path,
                "error": None,
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"EPUB generation error: {e}")
        _epub_tasks[book_id] = {
            "status": "failed",
            "progress": 0,
            "message": str(e),
            "file_path": None,
            "error": str(e),
        }


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
    book_id: str = Path(..., description="书籍UUID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    异步生成EPUB
    
    在后台启动EPUB生成任务，立即返回任务状态。
    使用 GET /api/books/{book_id}/epub/status 查询进度。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        if book_id in _epub_tasks and _epub_tasks[book_id].get("status") == "running":
            return {
                "success": True,
                "message": "EPUB生成任务已在进行中",
                "status": _epub_tasks[book_id],
            }
        
        from app.utils.database import SessionLocal
        background_tasks.add_task(_generate_epub_async, book_id, SessionLocal)
        
        return {
            "success": True,
            "message": "EPUB生成任务已启动",
            "book_id": book_id,
        }
        
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
) -> Dict[str, Any]:
    """
    获取EPUB生成状态
    
    查询异步EPUB生成任务的当前状态。
    
    - **book_id**: 书籍UUID
    """
    if book_id not in _epub_tasks:
        return {
            "status": "not_started",
            "message": "没有正在进行的EPUB生成任务",
        }
    
    return _epub_tasks[book_id]


@router.get("/{book_id}/epub/download")
async def download_epub(
    book_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    下载EPUB文件
    
    如果EPUB文件已生成，返回文件下载。
    如果尚未生成，返回404错误。
    
    - **book_id**: 书籍UUID
    """
    try:
        logger.info(f"请求下载EPUB: {book_id}")
        
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            logger.error(f"书籍不存在: {book_id}")
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        epub_path = storage.get_epub_path(book.title, book.id)
        logger.info(f"EPUB文件路径: {epub_path}")

        # 如果EPUB不存在，或已存在但不包含所有已下载章节，则启动后台生成并返回202
        result = book_service.get_book_with_chapters(book_id)
        if not result:
            raise HTTPException(status_code=404, detail="书籍不存在")

        chapters = result["chapters"]
        completed_chapters = [ch for ch in chapters if ch.download_status == "completed"]
        
        logger.info(f"已下载章节数: {len(completed_chapters)}")

        # 如果没有任何已下载章节，无法生成EPUB
        if not completed_chapters:
            logger.error(f"没有已下载的章节可生成EPUB: {book_id}")
            raise HTTPException(status_code=404, detail="没有已下载的章节可生成EPUB")

        # 如果文件不存在，直接排队生成并返回202
        if not epub_path.exists():
            logger.warning(f"EPUB文件不存在，开始生成: {epub_path}")
            if book_id in _epub_tasks and _epub_tasks[book_id].get("status") in ("running", "queued"):
                return JSONResponse({"detail": "EPUB正在生成中，请稍后再试"}, status_code=202)

            _epub_tasks[book_id] = {
                "status": "queued",
                "progress": 0,
                "message": "EPUB生成任务已排队",
                "file_path": None,
                "error": None,
            }

            from app.utils.database import SessionLocal
            background_tasks.add_task(_generate_epub_async, book_id, SessionLocal)

            return JSONResponse({"detail": "EPUB生成任务已启动，请稍后再试下载"}, status_code=202, background=background_tasks)

        # 文件存在，检查是否包含所有已下载章节
        epub_service = EPUBService(db=db, storage=storage)
        info = epub_service.get_epub_info(str(epub_path))
        epub_chapter_count = info.get("chapter_count") if info else None

        if epub_chapter_count is None or epub_chapter_count < len(completed_chapters):
            # 需要重新生成
            if book_id in _epub_tasks and _epub_tasks[book_id].get("status") in ("running", "queued"):
                return JSONResponse({"detail": "EPUB正在重新生成中，请稍后再试"}, status_code=202)

            _epub_tasks[book_id] = {
                "status": "queued",
                "progress": 0,
                "message": "EPUB重新生成任务已排队",
                "file_path": None,
                "error": None,
            }

            from app.utils.database import SessionLocal
            background_tasks.add_task(_generate_epub_async, book_id, SessionLocal)

            return JSONResponse({"detail": "EPUB重新生成任务已启动，请稍后再试下载"}, status_code=202, background=background_tasks)

        # 否则直接返回文件
        logger.info(f"返回EPUB文件: {epub_path}")
        return FileResponse(
            path=str(epub_path),
            filename=f"{book.title}.epub",
            media_type="application/epub+zip",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download EPUB error: {e}")
        raise HTTPException(status_code=500, detail=f"下载EPUB失败: {str(e)}")
