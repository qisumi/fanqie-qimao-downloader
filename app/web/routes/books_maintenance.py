import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.base import APIError
from app.schemas.service_schemas import BookResponse, SuccessResponse
from app.services import BookService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.delete(
    "/{book_id}",
    response_model=SuccessResponse,
    summary="删除书籍",
    response_description="返回删除结果",
    responses={
        200: {"description": "删除成功"},
        404: {"description": "书籍不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def delete_book(
    book_id: str = Path(..., description="书籍UUID"),
    delete_files: bool = Query(True, description="是否同时删除本地文件（章节内容、封面等）"),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """
    删除书籍
    
    从数据库中删除书籍记录，可选择同时删除本地文件。
    
    - **book_id**: 书籍UUID
    - **delete_files**: 是否删除本地文件（章节内容、封面等）
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        title = book.title
        
        book_service.delete_book(book_id, delete_files=delete_files)
        
        return SuccessResponse(
            success=True,
            message=f"书籍《{title}》已删除" + ("，本地文件已清理" if delete_files else ""),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete book error: {e}")
        raise HTTPException(status_code=500, detail=f"删除书籍失败: {str(e)}")


@router.post("/{book_id}/refresh", response_model=BookResponse)
async def refresh_book(
    book_id: str,
    db: Session = Depends(get_db),
) -> BookResponse:
    """
    刷新书籍元数据
    
    从API重新获取书籍详情并更新数据库。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = await book_service.refresh_book_metadata(book_id)
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        return BookResponse(
            id=book.id,
            platform=book.platform,
            book_id=book.book_id,
            title=book.title,
            author=book.author or "",
            cover_url=book.cover_url,
            cover_path=book.cover_path,
            total_chapters=book.total_chapters or 0,
            downloaded_chapters=book.downloaded_chapters or 0,
            word_count=book.word_count,
            creation_status=book.creation_status,
            last_chapter_title=book.last_chapter_title,
            last_update_time=book.last_update_time,
            download_status=book.download_status or "pending",
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
        
    except HTTPException:
        raise
    except APIError as e:
        logger.error(f"Refresh book API error: {e}")
        raise HTTPException(status_code=502, detail=f"API请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"Refresh book error: {e}")
        raise HTTPException(status_code=500, detail=f"刷新书籍失败: {str(e)}")


@router.get("/{book_id}/new-chapters")
async def check_new_chapters(
    book_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    检查新章节
    
    从API获取最新章节列表，与本地对比返回新章节信息。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        new_chapters = await book_service.check_new_chapters(book_id)
        
        return {
            "book_id": book_id,
            "book_title": book.title,
            "new_chapters_count": len(new_chapters),
            "new_chapters": new_chapters,
        }
        
    except HTTPException:
        raise
    except APIError as e:
        logger.error(f"Check new chapters API error: {e}")
        raise HTTPException(status_code=502, detail=f"API请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"Check new chapters error: {e}")
        raise HTTPException(status_code=500, detail=f"检查新章节失败: {str(e)}")
