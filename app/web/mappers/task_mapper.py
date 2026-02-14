"""Task response mappers."""

from app.schemas import TaskResponse


def to_task_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        book_id=task.book_id,
        task_type=task.task_type,
        status=task.status or "pending",
        total_chapters=task.total_chapters or 0,
        downloaded_chapters=task.downloaded_chapters or 0,
        failed_chapters=task.failed_chapters or 0,
        progress=task.progress or 0.0,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
    )
