from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.services.book_service import BookService
from app.utils.database import get_db
from app.schemas.service_schemas import BookResponse

router = APIRouter()

@router.post("/upload", response_model=BookResponse)
async def upload_book(
    title: str = Form(...),
    author: str = Form(None),
    regex: str = Form(default=r"第[0-9一二三四五六七八九十百千]+章\s+.+"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
        
    try:
        content_bytes = await file.read()
        # Try decoding with utf-8, fallback to gbk/gb18030
        try:
            content = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = content_bytes.decode('gb18030')
            except UnicodeDecodeError:
                 raise HTTPException(status_code=400, detail="Could not decode file. Please ensure it is UTF-8 or GBK.")

        service = BookService(db)
        book = await service.upload_txt_book(
            title=title,
            author=author or "Unknown",
            content=content,
            regex_pattern=regex
        )
        return book
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
