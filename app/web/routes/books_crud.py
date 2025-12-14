import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.base import APIError, BookNotFoundError
from app.schemas.service_schemas import (
    BookDetailResponse,
    BookListResponse,
    BookResponse,
    BookStatistics,
)
from app.services import BookService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/add/{platform}/{book_id}",
    response_model=Dict[str, Any],
    summary="添加书籍",
    response_description="返回添加结果和书籍信息",
    responses={
        200: {
            "description": "添加成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "书籍《第一序列》添加成功",
                        "book": {
                            "id": "uuid-string",
                            "platform": "fanqie",
                            "book_id": "7384886245497586234",
                            "title": "第一序列",
                            "author": "爱潜水的乌贼",
                            "total_chapters": 1273,
                            "downloaded_chapters": 0,
                            "download_status": "pending"
                        }
                    }
                }
            }
        },
        400: {"description": "参数错误"},
        404: {"description": "书籍在平台上不存在"},
        409: {"description": "书籍已存在"},
        502: {"description": "API请求失败"},
        500: {"description": "服务器内部错误"}
    }
)
async def add_book(
    platform: str = Path(..., description="平台名称"),
    book_id: str = Path(..., description="平台上的书籍ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    添加书籍到下载列表
    
    根据平台和书籍ID从API获取书籍详情，下载封面，获取章节列表，
    并将书籍添加到数据库。
    
    - **platform**: 平台名称 (fanqie/qimao/biquge)
    - **book_id**: 平台上的书籍ID
    """
    if platform not in ("fanqie", "qimao", "biquge"):
        raise HTTPException(status_code=400, detail="平台必须是 fanqie、qimao 或 biquge")
    
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        book = await book_service.add_book(
            platform=platform,
            book_id=book_id,
            download_cover=True,
            fetch_chapters=True,
        )
        
        book_response = BookResponse(
            id=book.id,
            platform=book.platform,
            book_id=book.book_id,
            title=book.title,
            author=book.author or "",
            cover_url=book.cover_url,
            cover_path=book.cover_path,
            epub_path=None,
            txt_path=None,
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
        
        return {
            "success": True,
            "message": f"书籍《{book.title}》添加成功",
            "book": book_response.model_dump(mode="json"),
        }
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="书籍在平台上不存在")
    except APIError as e:
        logger.error(f"Add book API error: {e}")
        raise HTTPException(status_code=502, detail=f"API请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"Add book error: {e}")
        raise HTTPException(status_code=500, detail=f"添加书籍失败: {str(e)}")


@router.get(
    "/",
    response_model=BookListResponse,
    summary="获取书籍列表",
    response_description="返回分页的书籍列表",
    responses={
        200: {"description": "获取成功"},
        500: {"description": "服务器内部错误"}
    }
)
async def list_books(
    platform: Optional[str] = Query(None, description="按平台筛选", pattern="^(fanqie|qimao|biquge)$"),
    status: Optional[str] = Query(None, description="按下载状态筛选", pattern="^(pending|downloading|completed|failed|partial)$"),
    search: Optional[str] = Query(None, description="搜索书名或作者", max_length=100),
    page: int = Query(0, ge=0, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> BookListResponse:
    """
    获取书籍列表
    
    支持按平台、状态筛选，以及按书名/作者搜索。
    
    - **platform**: 平台筛选 (fanqie/qimao/biquge)
    - **status**: 状态筛选 (pending/downloading/completed/failed)
    - **search**: 书名或作者关键词
    - **page**: 页码，从0开始
    - **limit**: 每页数量，最大100
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        result = book_service.list_books(
            platform=platform,
            status=status,
            search=search,
            page=page,
            limit=limit,
        )
        
        books = []
        for book in result["books"]:
            books.append(BookResponse(
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
            ))
        
        return BookListResponse(
            books=books,
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )
        
    except Exception as e:
        logger.error(f"List books error: {e}")
        raise HTTPException(status_code=500, detail=f"获取书籍列表失败: {str(e)}")


@router.get(
    "/{book_id}",
    response_model=BookDetailResponse,
    summary="获取书籍详情",
    response_description="返回书籍信息和统计数据",
    responses={
        200: {"description": "获取成功"},
        404: {"description": "书籍不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def get_book(
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> BookDetailResponse:
    """
    获取书籍详情
    
    返回书籍信息和统计数据（不再返回章节列表，需章节内容可使用阅读相关接口）。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        result = book_service.get_book_overview(book_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        book = result["book"]
        stats = result["statistics"]
        
        book_response = BookResponse(
            id=book.id,
            platform=book.platform,
            book_id=book.book_id,
            title=book.title,
            author=book.author or "",
            cover_url=book.cover_url,
            cover_path=book.cover_path,
            epub_path=str(storage.get_epub_path(book.title, book.id)) if storage.get_epub_path(book.title, book.id).exists() else None,
            txt_path=str(storage.get_txt_path(book.title, book.id)) if storage.get_txt_path(book.title, book.id).exists() else None,
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
        
        statistics = BookStatistics(
            total_chapters=stats.get("total_chapters", 0),
            completed_chapters=stats.get("completed_chapters", 0),
            failed_chapters=stats.get("failed_chapters", 0),
            pending_chapters=stats.get("pending_chapters", 0),
            progress=stats.get("progress", 0.0),
            exists=stats.get("exists", False),
            has_cover=stats.get("has_cover", False),
            chapter_count=stats.get("chapter_count", 0),
            size_bytes=stats.get("size_bytes", 0),
            size_mb=stats.get("size_mb", 0.0),
        )
        
        return BookDetailResponse(
            book=book_response,
            chapters=[],
            statistics=statistics,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get book error: {e}")
        raise HTTPException(status_code=500, detail=f"获取书籍详情失败: {str(e)}")
