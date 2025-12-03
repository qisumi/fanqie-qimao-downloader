import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.base import APIError
from app.services import BookService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/search",
    summary="搜索书籍",
    response_description="返回搜索结果列表",
    responses={
        200: {
            "description": "搜索成功",
            "content": {
                "application/json": {
                    "example": {
                        "books": [
                            {
                                "book_id": "7384886245497586234",
                                "title": "第一序列",
                                "author": "爱潜水的乌贼",
                                "cover_url": "https://example.com/cover.jpg",
                                "abstract": "小说简介...",
                                "word_count": 1234567,
                                "creation_status": "连载中"
                            }
                        ],
                        "total": 10,
                        "page": 0
                    }
                }
            }
        },
        400: {"description": "参数错误，平台必须是 fanqie 或 qimao"},
        502: {"description": "API请求失败，上游服务不可用"},
        500: {"description": "服务器内部错误"}
    }
)
async def search_books(
    q: str = Query(..., description="搜索关键词", min_length=1, max_length=100),
    platform: str = Query("fanqie", description="平台: fanqie 或 qimao"),
    page: int = Query(0, ge=0, description="页码 (从0开始)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    搜索书籍
    
    调用API搜索指定平台的书籍，返回搜索结果列表。
    
    - **q**: 搜索关键词
    - **platform**: 平台名称 (fanqie/qimao)
    - **page**: 页码，从0开始
    """
    if platform not in ("fanqie", "qimao"):
        raise HTTPException(status_code=400, detail="平台必须是 fanqie 或 qimao")
    
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        result = await book_service.search_books(platform, q, page)
        return result
    except APIError as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(status_code=502, detail=f"API请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
