"""Task orchestration utilities for download/update workflows."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from app.models.task import DownloadTask
from app.repositories import BookRepository, DownloadTaskRepository
from app.services import BookService, DownloadService, QuotaReachedError, StorageService, TaskCancelledError
from app.utils.database import SessionLocal
from app.web.websocket import get_connection_manager

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Coordinates running async download tasks and websocket callbacks."""

    _running_downloads: Dict[str, asyncio.Task] = {}

    @classmethod
    def has_active_download(cls, book_id: str) -> bool:
        task = cls._running_downloads.get(book_id)
        if not task:
            return False
        if task.done():
            cls._running_downloads.pop(book_id, None)
            return False
        return True

    @classmethod
    def get_running_downloads(cls) -> Dict[str, asyncio.Task]:
        return cls._running_downloads

    @classmethod
    def start_background_task(
        cls,
        book_id: str,
        task_type: str,
        task_id: str,
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
    ) -> asyncio.Task:
        # Keep one active background task per book.
        async_task = asyncio.create_task(
            cls.run_download_task(
                book_id=book_id,
                task_type=task_type,
                task_id=task_id,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
            )
        )
        cls._running_downloads[book_id] = async_task
        return async_task

    @classmethod
    def cancel_background_task(cls, book_id: str):
        task = cls._running_downloads.get(book_id)
        if task:
            task.cancel()
            cls._running_downloads.pop(book_id, None)

    @classmethod
    async def run_download_task(
        cls,
        book_id: str,
        task_type: str,
        task_id: str,
        start_chapter: int = 0,
        end_chapter: Optional[int] = None,
    ):
        db = SessionLocal()
        try:
            storage = StorageService()
            download_service = DownloadService(db=db, storage=storage)

            if task_type == "update":
                book_service = BookService(db=db, storage=storage)
                new_count = await book_service.add_new_chapters(book_id)
                logger.info(f"Found {new_count} new chapters for book {book_id}")
                await download_service.update_book(book_id, task_id=task_id)
            else:
                await download_service.download_book(
                    book_uuid=book_id,
                    task_type=task_type,
                    start_chapter=start_chapter,
                    end_chapter=end_chapter,
                    task_id=task_id,
                    skip_completed=True,
                )
        except QuotaReachedError as exc:
            logger.warning(f"Download quota reached: {exc}")
        except TaskCancelledError:
            logger.info(f"Download task cancelled: {book_id}")
        except asyncio.CancelledError:
            logger.info(f"Download task was cancelled by user: {book_id}")
            try:
                book_repo = BookRepository(db)
                task_repo = DownloadTaskRepository(db)
                book = book_repo.get_by_id(book_id)
                task = task_repo.get_by_id(task_id)
                if book and book.download_status == "downloading":
                    book.download_status = "partial" if book.downloaded_chapters > 0 else "pending"
                if task and task.status == "running":
                    task.status = "cancelled"
                    task.completed_at = datetime.now(timezone.utc)
                db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update status after cancel: {update_error}")
        except Exception as exc:
            logger.error(f"Download task error: {exc}", exc_info=True)
        finally:
            db.close()
            cls._running_downloads.pop(book_id, None)
            logger.debug(f"Cleaned up download task for book {book_id}")

    @staticmethod
    def build_ws_progress_callback(
        book_title: str,
        completed_message: str = "下载完成",
        failed_message: str = "下载失败",
    ) -> Callable[[DownloadTask], None]:
        manager = get_connection_manager()

        def sync_callback(updated_task: DownloadTask):
            async def broadcast():
                try:
                    if updated_task.status in ("completed", "failed", "cancelled"):
                        await manager.broadcast_completed(
                            task_id=updated_task.id,
                            success=updated_task.status == "completed",
                            message=updated_task.error_message or (
                                completed_message if updated_task.status == "completed"
                                else "任务已取消" if updated_task.status == "cancelled"
                                else failed_message
                            ),
                            book_title=book_title,
                        )
                    else:
                        await manager.broadcast_progress(
                            task_id=updated_task.id,
                            status=updated_task.status,
                            total_chapters=updated_task.total_chapters or 0,
                            downloaded_chapters=updated_task.downloaded_chapters or 0,
                            failed_chapters=updated_task.failed_chapters or 0,
                            progress=updated_task.progress or 0.0,
                            error_message=updated_task.error_message,
                            book_title=book_title,
                        )
                except Exception as exc:
                    logger.warning(f"WebSocket callback error: {exc}")

            asyncio.create_task(broadcast())

        return sync_callback

    @staticmethod
    def ensure_progress_callback(
        download_service: DownloadService,
        task_id: str,
        callback: Callable[[DownloadTask], None],
    ) -> bool:
        callbacks = download_service._progress_callbacks.get(task_id, set())
        if callbacks:
            logger.info(f"Task {task_id} already has {len(callbacks)} callback(s), reusing existing ones")
            return False
        download_service.register_progress_callback(task_id, callback)
        logger.info(f"Registered progress callback for task {task_id}")
        return True
