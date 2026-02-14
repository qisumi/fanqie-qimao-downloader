"""Export usecase layer for EPUB/TXT workflows."""

import logging
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.services import BookService, EPUBService, ExportTaskService, StorageService, TXTService
from app.utils.database import SessionLocal

logger = logging.getLogger(__name__)


class ExportUseCase:
    """Coordinates export task orchestration and file readiness checks."""

    def __init__(self, db: Optional[Session] = None):
        self.storage = StorageService()
        self.book_service = BookService(db=db, storage=self.storage) if db else None
        self.epub_service = EPUBService(db=db, storage=self.storage) if db else None
        self.txt_service = TXTService(db=db, storage=self.storage) if db else None
        self.export_task_service = ExportTaskService(db=db) if db else None

    def get_epub_status(self, book_id: str) -> Dict[str, Any]:
        if not self.export_task_service:
            raise RuntimeError("Database session is required")
        return self.export_task_service.get_status_dict(book_id=book_id, export_type="epub")

    @staticmethod
    async def _generate_epub_async(book_id: str):
        db = SessionLocal()
        try:
            storage = StorageService()
            book_service = BookService(db=db, storage=storage)
            epub_service = EPUBService(db=db, storage=storage)
            export_task_service = ExportTaskService(db=db)
            export_task_service.set_status(
                book_id=book_id,
                export_type="epub",
                status="running",
                progress=0,
                message="正在生成EPUB...",
            )

            result = book_service.get_book_with_chapters(book_id)
            if not result:
                raise ValueError("书籍不存在")

            book = result["book"]
            chapters = result["chapters"]
            completed_chapters = [ch for ch in chapters if ch.download_status == "completed"]

            if not completed_chapters:
                raise ValueError("没有已下载的章节可生成EPUB")

            export_task_service.set_status(
                book_id=book_id,
                export_type="epub",
                status="running",
                progress=30,
                message=f"准备生成EPUB，共{len(completed_chapters)}章",
            )

            epub_path = epub_service.generate_epub(book, completed_chapters)

            export_task_service.set_status(
                book_id=book_id,
                export_type="epub",
                status="completed",
                progress=100,
                message="EPUB生成成功",
                file_path=epub_path,
                error=None,
            )
        except Exception as exc:
            logger.error(f"EPUB generation error: {exc}")
            ExportTaskService(db=db).set_status(
                book_id=book_id,
                export_type="epub",
                status="failed",
                progress=0,
                message=str(exc),
                file_path=None,
                error=str(exc),
            )
        finally:
            db.close()

    def start_epub_generation(
        self,
        book_id: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        if not self.book_service or not self.export_task_service:
            raise RuntimeError("Database session is required")

        book = self.book_service.get_book(book_id)
        if not book:
            raise ValueError("书籍不存在")

        current = self.export_task_service.get_status_dict(book_id=book_id, export_type="epub")
        if current.get("status") in ("running", "queued"):
            return {
                "success": True,
                "message": "EPUB生成任务已在进行中",
                "status": current,
            }

        self.export_task_service.set_status(
            book_id=book_id,
            export_type="epub",
            status="queued",
            progress=0,
            message="EPUB生成任务已排队",
        )
        background_tasks.add_task(self._generate_epub_async, book_id)
        return {
            "success": True,
            "message": "EPUB生成任务已启动",
            "book_id": book_id,
        }

    def ensure_epub_download_ready(
        self,
        book_id: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        if not self.book_service or not self.epub_service or not self.export_task_service:
            raise RuntimeError("Database session is required")

        book = self.book_service.get_book(book_id)
        if not book:
            raise ValueError("书籍不存在")

        epub_path = self.storage.get_epub_path(book.title, book.id)
        result = self.book_service.get_book_with_chapters(book_id)
        if not result:
            raise ValueError("书籍不存在")

        chapters = result["chapters"]
        completed_chapters = [ch for ch in chapters if ch.download_status == "completed"]
        if not completed_chapters:
            raise FileNotFoundError("没有已下载的章节可生成EPUB")

        if not epub_path.exists():
            if self.export_task_service.is_active(book_id=book_id, export_type="epub"):
                return {"type": "queued", "detail": "EPUB正在生成中，请稍后再试", "status_code": 202}

            self.export_task_service.set_status(
                book_id=book_id,
                export_type="epub",
                status="queued",
                progress=0,
                message="EPUB生成任务已排队",
            )
            background_tasks.add_task(self._generate_epub_async, book_id)
            return {"type": "queued", "detail": "EPUB生成任务已启动，请稍后再试下载", "status_code": 202}

        info = self.epub_service.get_epub_info(str(epub_path))
        epub_chapter_count = info.get("chapter_count") if info else None
        if epub_chapter_count is None or epub_chapter_count < len(completed_chapters):
            if self.export_task_service.is_active(book_id=book_id, export_type="epub"):
                return {"type": "queued", "detail": "EPUB正在重新生成中，请稍后再试", "status_code": 202}

            self.export_task_service.set_status(
                book_id=book_id,
                export_type="epub",
                status="queued",
                progress=0,
                message="EPUB重新生成任务已排队",
            )
            background_tasks.add_task(self._generate_epub_async, book_id)
            return {"type": "queued", "detail": "EPUB重新生成任务已启动，请稍后再试下载", "status_code": 202}

        return {
            "type": "file",
            "path": str(epub_path),
            "filename": f"{book.title}.epub",
        }

    def get_txt_status(self, book_id: str) -> Dict[str, Any]:
        if not self.export_task_service:
            raise RuntimeError("Database session is required")
        return self.export_task_service.get_status_dict(book_id=book_id, export_type="txt")

    @staticmethod
    async def _generate_txt_async(book_id: str):
        db = SessionLocal()
        try:
            storage = StorageService()
            book_service = BookService(db=db, storage=storage)
            txt_service = TXTService(db=db, storage=storage)
            export_task_service = ExportTaskService(db=db)
            export_task_service.set_status(
                book_id=book_id,
                export_type="txt",
                status="running",
                progress=0,
                message="正在生成TXT...",
            )

            result = book_service.get_book_with_chapters(book_id)
            if not result:
                raise ValueError("书籍不存在")

            book = result["book"]
            chapters = result["chapters"]
            completed_chapters = [ch for ch in chapters if ch.download_status == "completed"]
            if not completed_chapters:
                raise ValueError("没有已下载的章节可生成TXT")

            export_task_service.set_status(
                book_id=book_id,
                export_type="txt",
                status="running",
                progress=30,
                message=f"准备生成TXT，共{len(completed_chapters)}章",
            )

            txt_path = txt_service.generate_txt(book, completed_chapters)
            export_task_service.set_status(
                book_id=book_id,
                export_type="txt",
                status="completed",
                progress=100,
                message="TXT生成成功",
                file_path=txt_path,
                error=None,
            )
        except Exception as exc:
            logger.error(f"TXT generation error: {exc}")
            ExportTaskService(db=db).set_status(
                book_id=book_id,
                export_type="txt",
                status="failed",
                progress=0,
                message=str(exc),
                file_path=None,
                error=str(exc),
            )
        finally:
            db.close()

    def start_txt_generation(
        self,
        book_id: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        if not self.book_service or not self.export_task_service:
            raise RuntimeError("Database session is required")

        book = self.book_service.get_book(book_id)
        if not book:
            raise ValueError("书籍不存在")

        current = self.export_task_service.get_status_dict(book_id=book_id, export_type="txt")
        if current.get("status") in ("running", "queued"):
            return {
                "success": True,
                "message": "TXT生成任务已在进行中",
                "status": current,
            }

        self.export_task_service.set_status(
            book_id=book_id,
            export_type="txt",
            status="queued",
            progress=0,
            message="TXT生成任务已排队",
        )
        background_tasks.add_task(self._generate_txt_async, book_id)
        return {
            "success": True,
            "message": "TXT生成任务已启动",
            "book_id": book_id,
        }

    def ensure_txt_download_ready(
        self,
        book_id: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        if not self.book_service or not self.txt_service or not self.export_task_service:
            raise RuntimeError("Database session is required")

        book = self.book_service.get_book(book_id)
        if not book:
            raise ValueError("书籍不存在")

        txt_path = self.storage.get_txt_path(book.title, book.id)
        if txt_path.exists():
            return {
                "type": "file",
                "path": str(txt_path),
                "filename": f"{book.title}.txt",
            }

        if self.export_task_service.is_active(book_id=book_id, export_type="txt"):
            return {"type": "queued", "detail": "TXT正在生成中，请稍后再试", "status_code": 202}

        self.export_task_service.set_status(
            book_id=book_id,
            export_type="txt",
            status="queued",
            progress=0,
            message="TXT生成任务已排队",
        )
        background_tasks.add_task(self._generate_txt_async, book_id)
        return {"type": "queued", "detail": "TXT生成任务已启动，请稍后再试下载", "status_code": 202}
