from fastapi.testclient import TestClient
import threading
import asyncio

from app.main import app
from app.web.websocket import get_connection_manager
from app.utils.database import SessionLocal
from app.models.book import Book
from app.models.task import DownloadTask
from app.config import get_settings
from itsdangerous import URLSafeTimedSerializer


def test_ws_task_progress_integration():
    """Integration test: connect to /ws/tasks/{task_id}, receive initial state, and receive broadcasted updates."""
    # prepare DB: create a book and a running task
    db = SessionLocal()
    book = Book(platform='fanqie', book_id='testbook', title='测试书籍')
    db.add(book)
    db.commit()
    db.refresh(book)

    task = DownloadTask(book_id=book.id, task_type='full_download', status='running', total_chapters=10, downloaded_chapters=0, progress=0.0)
    db.add(task)
    db.commit()
    db.refresh(task)

    manager = get_connection_manager()

    client = TestClient(app)
    # if app requires auth (app_password set), create signed auth_token cookie
    settings = get_settings()
    if settings.app_password:
        serializer = URLSafeTimedSerializer(settings.secret_key)
        token = serializer.dumps({"authenticated": True})
        client.cookies.set('auth_token', token)

    with client.websocket_connect(f"/ws/tasks/{task.id}") as websocket:
        # initial message should be sent immediately
        init_msg = websocket.receive_json()
        assert init_msg.get('type') == 'progress'
        assert init_msg['data']['task_id'] == task.id

        # broadcast a progress update from manager in background
        def send_progress():
            asyncio.run(manager.broadcast_progress(
                task_id=task.id,
                status='running',
                total_chapters=10,
                downloaded_chapters=2,
                failed_chapters=0,
                progress=20.0,
                error_message=None,
                book_title=book.title,
            ))

        t = threading.Thread(target=send_progress)
        t.start()
        t.join(timeout=5)

        msg = websocket.receive_json()
        assert msg.get('type') == 'progress'
        assert msg['data']['task_id'] == task.id
        assert msg['data']['progress'] == 20.0

    # cleanup
    try:
        db.delete(task)
        db.delete(book)
        db.commit()
    finally:
        db.close()
