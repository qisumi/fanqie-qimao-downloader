import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.schemas.service_schemas import (
    BookListResponse,
    BookResponse,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services import UserService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def _book_to_response(book) -> BookResponse:
    """将 Book ORM 对象转换为响应模型"""
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


@router.get(
    "",
    response_model=UserListResponse,
    summary="获取用户列表",
)
async def list_users(
    db: Session = Depends(get_db),
) -> UserListResponse:
    try:
        user_service = UserService(db=db)
        users = user_service.list_users()
        return UserListResponse(users=[UserResponse.model_validate(u) for u in users])
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="创建用户",
)
async def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    try:
        user_service = UserService(db=db)
        user = user_service.create_user(payload.username)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail="创建用户失败")


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="修改用户名",
)
async def rename_user(
    user_id: str = Path(..., description="用户ID"),
    payload: UserUpdateRequest = ...,
    db: Session = Depends(get_db),
) -> UserResponse:
    try:
        user_service = UserService(db=db)
        user = user_service.rename_user(user_id, payload.username if payload else "")
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rename user error: {e}")
        raise HTTPException(status_code=500, detail="更新用户失败")


@router.delete(
    "/{user_id}",
    summary="删除用户",
)
async def delete_user(
    user_id: str = Path(..., description="用户ID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        user_service = UserService(db=db)
        success = user_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"success": True, "message": "用户已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="删除用户失败")


@router.get(
    "/{user_id}/books",
    response_model=BookListResponse,
    summary="获取用户私人书架",
)
async def list_user_books(
    user_id: str = Path(..., description="用户ID"),
    platform: Optional[str] = Query(None, description="按平台筛选", pattern="^(fanqie|qimao)$"),
    status: Optional[str] = Query(None, description="按下载状态筛选", pattern="^(pending|downloading|completed|failed|partial)$"),
    search: Optional[str] = Query(None, description="搜索书名或作者", max_length=100),
    page: int = Query(0, ge=0, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> BookListResponse:
    try:
        user_service = UserService(db=db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        result = user_service.list_user_books(
            user_id=user_id,
            platform=platform,
            status=status,
            search=search,
            page=page,
            limit=limit,
        )

        books = [_book_to_response(b) for b in result["books"]]
        return BookListResponse(
            books=books,
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            pages=result["pages"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List user books error: {e}")
        raise HTTPException(status_code=500, detail="获取私人书架失败")


@router.post(
    "/{user_id}/books/{book_id}",
    summary="添加到私人书架",
)
async def add_book_to_user(
    user_id: str = Path(..., description="用户ID"),
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        user_service = UserService(db=db)
        link = user_service.add_book_to_user(user_id=user_id, book_id=book_id)
        book = _book_to_response(link.book)
        return {"success": True, "message": "已加入私人书架", "book": book.model_dump(mode="json")}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Add book to user error: {e}")
        raise HTTPException(status_code=500, detail="加入私人书架失败")


@router.delete(
    "/{user_id}/books/{book_id}",
    summary="从私人书架移除",
)
async def remove_book_from_user(
    user_id: str = Path(..., description="用户ID"),
    book_id: str = Path(..., description="书籍UUID"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    try:
        user_service = UserService(db=db)
        success = user_service.remove_book_from_user(user_id=user_id, book_id=book_id)
        if not success:
            raise HTTPException(status_code=404, detail="记录不存在")
        return {"success": True, "message": "已移出私人书架"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove book from user error: {e}")
        raise HTTPException(status_code=500, detail="移出私人书架失败")
