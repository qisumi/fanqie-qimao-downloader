"""
书籍API路由

提供书籍相关的RESTful API端点:
- 搜索书籍
- 添加书籍
- 获取书籍列表
- 获取书籍详情
- 删除书籍
- 生成EPUB
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.services import (
    StorageService,
    BookService,
    DownloadService,
    EPUBService,
    DownloadError,
    QuotaReachedError,
)
from app.schemas.service_schemas import (
    BookCreate,
    BookResponse,
    BookListResponse,
    BookDetailResponse,
    BookStatistics,
    ChapterResponse,
    TaskResponse,
    SuccessResponse,
    ErrorResponseModel,
)
from app.api.base import BookNotFoundError, APIError

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 搜索书籍 ============

@router.get("/search")
async def search_books(
    q: str = Query(..., description="搜索关键词"),
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


# ============ 添加书籍 ============

@router.post("/{platform}/{book_id}", response_model=Dict[str, Any])
async def add_book(
    platform: str,
    book_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    添加书籍到下载列表
    
    根据平台和书籍ID从API获取书籍详情，下载封面，获取章节列表，
    并将书籍添加到数据库。
    
    - **platform**: 平台名称 (fanqie/qimao)
    - **book_id**: 平台上的书籍ID
    """
    if platform not in ("fanqie", "qimao"):
        raise HTTPException(status_code=400, detail="平台必须是 fanqie 或 qimao")
    
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        # 添加书籍
        book = await book_service.add_book(
            platform=platform,
            book_id=book_id,
            download_cover=True,
            fetch_chapters=True,
        )
        
        # 转换为响应格式
        book_response = BookResponse(
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
        
        return {
            "success": True,
            "message": f"书籍《{book.title}》添加成功",
            "book": book_response.model_dump(mode="json"),
        }
        
    except ValueError as e:
        # 书籍已存在
        raise HTTPException(status_code=409, detail=str(e))
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="书籍在平台上不存在")
    except APIError as e:
        logger.error(f"Add book API error: {e}")
        raise HTTPException(status_code=502, detail=f"API请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"Add book error: {e}")
        raise HTTPException(status_code=500, detail=f"添加书籍失败: {str(e)}")


# ============ 获取书籍列表 ============

@router.get("/", response_model=BookListResponse)
async def list_books(
    platform: Optional[str] = Query(None, description="按平台筛选"),
    status: Optional[str] = Query(None, description="按下载状态筛选"),
    search: Optional[str] = Query(None, description="搜索书名或作者"),
    page: int = Query(0, ge=0, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
) -> BookListResponse:
    """
    获取书籍列表
    
    支持按平台、状态筛选，以及按书名/作者搜索。
    
    - **platform**: 平台筛选 (fanqie/qimao)
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
        
        # 转换为响应格式
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


# ============ 获取书籍详情 ============

@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book(
    book_id: str,
    db: Session = Depends(get_db),
) -> BookDetailResponse:
    """
    获取书籍详情
    
    返回书籍信息、章节列表和统计数据。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        result = book_service.get_book_with_chapters(book_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        book = result["book"]
        chapters = result["chapters"]
        stats = result["statistics"]
        
        # 转换书籍
        book_response = BookResponse(
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
        
        # 转换章节
        chapter_responses = []
        for ch in chapters:
            chapter_responses.append(ChapterResponse(
                id=ch.id,
                book_id=ch.book_id,
                item_id=ch.item_id,
                title=ch.title,
                volume_name=ch.volume_name,
                chapter_index=ch.chapter_index,
                word_count=ch.word_count,
                content_path=ch.content_path,
                download_status=ch.download_status or "pending",
                downloaded_at=ch.downloaded_at,
                created_at=ch.created_at,
            ))
        
        # 转换统计
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
            chapters=chapter_responses,
            statistics=statistics,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get book error: {e}")
        raise HTTPException(status_code=500, detail=f"获取书籍详情失败: {str(e)}")


# ============ 删除书籍 ============

@router.delete("/{book_id}", response_model=SuccessResponse)
async def delete_book(
    book_id: str,
    delete_files: bool = Query(True, description="是否同时删除本地文件"),
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
        
        # 获取书籍信息
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        title = book.title
        
        # 删除书籍
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


# ============ 刷新书籍元数据 ============

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


# ============ 检查新章节 ============

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
        
        # 检查书籍是否存在
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


# ============ EPUB生成 (异步) ============

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
        # 创建新的数据库会话
        from app.utils.database import SessionLocal
        db = SessionLocal()
        
        try:
            storage = StorageService()
            book_service = BookService(db=db, storage=storage)
            epub_service = EPUBService(db=db, storage=storage)
            
            # 获取书籍和章节
            result = book_service.get_book_with_chapters(book_id)
            if not result:
                raise ValueError("书籍不存在")
            
            book = result["book"]
            chapters = result["chapters"]
            
            # 只使用已完成的章节
            completed_chapters = [
                ch for ch in chapters 
                if ch.download_status == "completed"
            ]
            
            if not completed_chapters:
                raise ValueError("没有已下载的章节可生成EPUB")
            
            _epub_tasks[book_id]["progress"] = 30
            _epub_tasks[book_id]["message"] = f"准备生成EPUB，共{len(completed_chapters)}章"
            
            # 生成EPUB
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


@router.post("/{book_id}/epub")
async def generate_epub(
    book_id: str,
    background_tasks: BackgroundTasks,
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
        
        # 检查书籍是否存在
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查是否已有正在进行的任务
        if book_id in _epub_tasks and _epub_tasks[book_id].get("status") == "running":
            return {
                "success": True,
                "message": "EPUB生成任务已在进行中",
                "status": _epub_tasks[book_id],
            }
        
        # 启动后台任务
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


@router.get("/{book_id}/epub/status")
async def get_epub_status(
    book_id: str,
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
    db: Session = Depends(get_db),
):
    """
    下载EPUB文件
    
    如果EPUB文件已生成，返回文件下载。
    如果尚未生成，返回404错误。
    
    - **book_id**: 书籍UUID
    """
    try:
        storage = StorageService()
        book_service = BookService(db=db, storage=storage)
        
        # 检查书籍是否存在
        book = book_service.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 检查EPUB文件是否存在
        epub_path = storage.get_epub_path(book.title, book.id)
        
        if not epub_path.exists():
            # 检查是否有生成任务
            if book_id in _epub_tasks:
                status = _epub_tasks[book_id]
                if status.get("status") == "running":
                    raise HTTPException(status_code=202, detail="EPUB正在生成中，请稍后再试")
                elif status.get("status") == "failed":
                    raise HTTPException(status_code=500, detail=f"EPUB生成失败: {status.get('error')}")
            
            raise HTTPException(status_code=404, detail="EPUB文件不存在，请先生成")
        
        # 返回文件下载
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