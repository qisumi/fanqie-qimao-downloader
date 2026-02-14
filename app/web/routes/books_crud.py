import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api.base import APIError, BookNotFoundError
from app.schemas import (
    BookDetailResponse,
    BookListResponse,
    BookMetadataUpdateRequest,
    BookResponse,
)
from app.usecases import BookUseCase
from app.utils.database import get_db
from app.web.mappers import to_book_detail_response, to_book_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put(
    "/{book_id}",
    response_model=BookResponse,
    summary="更新书籍元数据",
    response_description="返回更新后的书籍信息",
    responses={
        200: {"description": "更新成功"},
        404: {"description": "书籍不存在"},
        500: {"description": "服务器内部错误"}
    }
)
async def update_book_metadata(
    book_id: str = Path(..., description="书籍UUID"),
    payload: BookMetadataUpdateRequest = ...,
    db: Session = Depends(get_db),
) -> BookResponse:
    """
    更新书籍元数据
    
    手动更新书籍的书名、作者、连载状态和封面URL。
    主要用于修正本地上传书籍的信息。
    
    - **book_id**: 书籍UUID
    """
    try:
        usecase = BookUseCase(db=db)
        
        book = usecase.update_book_metadata(book_id=book_id, payload=payload)
        
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
            
        return to_book_response(book)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update book error: {e}")
        raise HTTPException(status_code=500, detail=f"更新书籍失败: {str(e)}")


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
        usecase = BookUseCase(db=db)
        
        book = await usecase.add_book(platform=platform, book_id=book_id)
        
        book_response = to_book_response(book)
        
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
        usecase = BookUseCase(db=db)
        
        result = usecase.list_books(
            platform=platform,
            status=status,
            search=search,
            page=page,
            limit=limit,
        )
        
        books = [to_book_response(book) for book in result["books"]]
        
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
        usecase = BookUseCase(db=db)
        
        result = usecase.get_book_overview(book_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        book = result["book"]
        stats = result["statistics"]

        return to_book_detail_response(
            book=book,
            statistics=stats,
            storage=usecase.storage,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get book error: {e}")
        raise HTTPException(status_code=500, detail=f"获取书籍详情失败: {str(e)}")
