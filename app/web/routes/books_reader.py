import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.schemas.service_schemas import (
    BookmarkCreateRequest,
    BookmarkResponse,
    CacheStatusResponse,
    ChapterContentResponse,
    ReaderProgressRequest,
    ReaderProgressResponse,
    ReaderTocChapter,
    ReaderTocResponse,
    ReadingHistoryResponse,
)
from app.services import ReaderService, StorageService, UserService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def _ensure_user(user_service: UserService, user_id: str):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def _ensure_book(reader_service: ReaderService, book_id: str):
    book = reader_service._get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return book


@router.get(
    "/{book_id}/toc",
    response_model=ReaderTocResponse,
    summary="获取阅读目录（需用户）",
)
async def get_reader_toc(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    page: int = Query(1, ge=1, description="页码(1-based)"),
    limit: int = Query(50, ge=1, le=500, description="每页数量"),
    anchor_id: Optional[str] = Query(None, description="希望包含的章节ID（根据该章节所在页返回数据）"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)

    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)

    toc = reader_service.get_toc(book_id, page=page, limit=limit, anchor_id=anchor_id)
    if not toc:
        raise HTTPException(status_code=404, detail="书籍不存在")

    chapters = [ReaderTocChapter(**item) for item in toc["chapters"]]
    return ReaderTocResponse(
        book_id=book_id,
        chapters=chapters,
        total=toc.get("total", len(chapters)),
        page=toc.get("page", page),
        limit=toc.get("limit", limit),
        pages=toc.get("pages", 0),
        has_more=toc.get("has_more", False),
    )


@router.get(
    "/{book_id}/chapters/{chapter_id}/content",
    response_model=ChapterContentResponse,
    summary="获取章节内容（缺失自动拉取）",
)
async def get_chapter_content(
    book_id: str = Path(..., description="书籍UUID"),
    chapter_id: str = Path(..., description="章节UUID"),
    user_id: str = Query(..., description="用户ID"),
    fmt: str = Query("html", pattern="^(html|text)$", description="返回格式"),
    range_dir: Optional[str] = Query(None, pattern="^(prev|next)$", description="获取相邻章节"),
    prefetch: int = Query(3, ge=0, le=5, description="自动预取后续章节数"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)

    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    try:
        result = await reader_service.get_chapter_content(
            book_id=book_id,
            chapter_id=chapter_id,
            fmt=fmt,
            fetch_range=range_dir,
            prefetch=prefetch,
            retries=3,
        )
        return ChapterContentResponse(**result)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Get chapter content error")
        raise HTTPException(status_code=500, detail=f"获取章节内容失败: {str(e)}")


@router.get(
    "/{book_id}/reader/progress",
    response_model=ReaderProgressResponse,
    responses={204: {"description": "暂无进度"}},
    summary="获取阅读进度（跨设备同步）",
)
async def get_reader_progress(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    device_id: Optional[str] = Query(None, description="设备ID（可选，不传则获取跨设备同步进度）"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    progress = reader_service.get_progress(user_id=user_id, book_id=book_id, device_id=device_id)
    if not progress:
        return Response(status_code=204)

    return ReaderProgressResponse(
        chapter_id=progress.chapter_id,
        offset_px=progress.offset_px,
        percent=progress.percent,
        device_id=progress.device_id,
        updated_at=progress.updated_at,
    )


@router.post(
    "/{book_id}/reader/progress",
    response_model=ReaderProgressResponse,
    summary="保存/更新阅读进度",
)
async def upsert_reader_progress(
    payload: ReaderProgressRequest,
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    chapter = reader_service._get_chapter(book_id, payload.chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    progress = reader_service.upsert_progress(
        user_id=user_id,
        book_id=book_id,
        chapter_id=payload.chapter_id,
        device_id=payload.device_id,
        offset_px=payload.offset_px,
        percent=payload.percent,
    )
    return ReaderProgressResponse(
        chapter_id=progress.chapter_id,
        offset_px=progress.offset_px,
        percent=progress.percent,
        device_id=progress.device_id,
        updated_at=progress.updated_at,
    )


@router.delete(
    "/{book_id}/reader/progress",
    summary="清空阅读进度（跨设备同步）",
)
async def clear_reader_progress(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    device_id: Optional[str] = Query(None, description="设备ID（可选，不传则清空所有设备进度）"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    if device_id:
        # 清空指定设备的进度（向后兼容）
        deleted = reader_service.clear_progress(user_id=user_id, book_id=book_id, device_id=device_id)
        if not deleted:
            return {"success": False, "message": "未找到进度"}
        return {"success": True, "message": "已清空指定设备进度"}
    else:
        # 清空所有设备进度（跨设备同步）
        all_progress = reader_service.get_all_device_progress(user_id=user_id, book_id=book_id)
        for progress in all_progress:
            reader_service.db.delete(progress)
        reader_service.db.commit()
        return {"success": True, "message": f"已清空所有设备进度，共{len(all_progress)}条记录"}


@router.get(
    "/{book_id}/reader/progress/devices",
    response_model=List[ReaderProgressResponse],
    summary="获取所有设备进度记录",
)
async def get_all_device_progress(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    progress_list = reader_service.get_all_device_progress(user_id=user_id, book_id=book_id)
    return [
        ReaderProgressResponse(
            chapter_id=progress.chapter_id,
            offset_px=progress.offset_px,
            percent=progress.percent,
            device_id=progress.device_id,
            updated_at=progress.updated_at,
        )
        for progress in progress_list
    ]


@router.get(
    "/{book_id}/reader/bookmarks",
    response_model=List[BookmarkResponse],
    summary="获取书签列表",
)
async def list_bookmarks(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    bookmarks = reader_service.list_bookmarks(user_id=user_id, book_id=book_id)
    return [BookmarkResponse.model_validate(bm) for bm in bookmarks]


@router.post(
    "/{book_id}/reader/bookmarks",
    response_model=BookmarkResponse,
    summary="创建书签",
)
async def create_bookmark(
    payload: BookmarkCreateRequest,
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    chapter = reader_service._get_chapter(book_id, payload.chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    bookmark = reader_service.add_bookmark(
        user_id=user_id,
        book_id=book_id,
        chapter_id=payload.chapter_id,
        offset_px=payload.offset_px,
        percent=payload.percent,
        note=payload.note,
    )
    return BookmarkResponse.model_validate(bookmark)


@router.delete(
    "/{book_id}/reader/bookmarks/{bookmark_id}",
    summary="删除书签",
)
async def delete_bookmark(
    book_id: str = Path(..., description="书籍UUID"),
    bookmark_id: str = Path(..., description="书签ID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    success = reader_service.delete_bookmark(user_id=user_id, book_id=book_id, bookmark_id=bookmark_id)
    if not success:
        raise HTTPException(status_code=404, detail="书签不存在")
    return {"success": True, "message": "书签已删除"}


@router.get(
    "/{book_id}/reader/history",
    response_model=List[ReadingHistoryResponse],
    summary="获取阅读历史",
)
async def list_history(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(50, ge=1, le=200, description="返回条数"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    history = reader_service.list_history(user_id=user_id, book_id=book_id, limit=limit)
    return [ReadingHistoryResponse.model_validate(h) for h in history]


@router.delete(
    "/{book_id}/reader/history",
    summary="清空阅读历史",
)
async def clear_history(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    _ensure_book(reader_service, book_id)

    deleted = reader_service.clear_history(user_id=user_id, book_id=book_id)
    return {"success": True, "deleted": deleted}


@router.get(
    "/{book_id}/cache/status",
    response_model=CacheStatusResponse,
    summary="获取缓存状态",
)
async def get_cache_status(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    book = _ensure_book(reader_service, book_id)

    status = reader_service.get_cache_status(book)
    return CacheStatusResponse(**status)


@router.post(
    "/{book_id}/cache/txt",
    summary="生成并下载TXT以缓存",
)
async def cache_txt(
    book_id: str = Path(..., description="书籍UUID"),
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db),
):
    user_service = UserService(db=db)
    _ensure_user(user_service, user_id)
    storage = StorageService()
    reader_service = ReaderService(db=db, storage=storage)
    book = _ensure_book(reader_service, book_id)

    try:
        txt_path = reader_service.ensure_txt_cached(book)
        return FileResponse(
            path=txt_path,
            filename=f"{book.title}.txt",
            media_type="text/plain",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Cache TXT failed")
        raise HTTPException(status_code=500, detail=f"生成TXT失败: {str(e)}")
