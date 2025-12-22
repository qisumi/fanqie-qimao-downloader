import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.services.book_service import BookService
from app.utils.database import get_db
from app.schemas.service_schemas import BookResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=BookResponse)
async def upload_book(
    title: str = Form(None),
    author: str = Form(None),
    regex: str = Form(default=r"第[0-9一二三四五六七八九十百千]+章\s+.+"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = file.filename.lower()
    if not (filename.endswith('.txt') or filename.endswith('.epub')):
        raise HTTPException(status_code=400, detail="Only .txt and .epub files are supported")
        
    try:
        service = BookService(db)
        content_bytes = await file.read()
        
        if filename.endswith('.txt'):
            # Try decoding with utf-8, fallback to gbk/gb18030
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = content_bytes.decode('gb18030')
                except UnicodeDecodeError:
                     raise HTTPException(status_code=400, detail="Could not decode file. Please ensure it is UTF-8 or GBK.")

            book = await service.upload_txt_book(
                title=title or file.filename.rsplit('.', 1)[0],
                author=author or "Unknown",
                content=content,
                regex_pattern=regex
            )
        else: # .epub
            book = await service.upload_epub_book(
                title=title,
                author=author,
                file_content=content_bytes
            )
            
        return book
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
