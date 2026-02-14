"""Read-side usecase for task querying endpoints."""

from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.repositories import DownloadTaskRepository


class TaskReadUseCase:
    """Application read usecase for listing and fetching tasks."""

    def __init__(self, db: Session):
        self.repo = DownloadTaskRepository(db)

    def list_tasks(
        self,
        book_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 0,
        limit: int = 20,
    ) -> Dict[str, object]:
        tasks, total = self.repo.list_tasks(
            book_id=book_id,
            status=status,
            page=page,
            limit=limit,
        )
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "limit": limit,
        }

    def get_task(self, task_id: str):
        return self.repo.get_by_id(task_id)
