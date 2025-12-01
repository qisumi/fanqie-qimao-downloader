import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services import DownloadService, StorageService
from app.utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/quota/{platform}")
async def get_quota(
    platform: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    获取指定平台的配额使用情况
    
    - **platform**: 平台名称 (fanqie/qimao)
    """
    if platform not in ("fanqie", "qimao"):
        raise HTTPException(status_code=400, detail="平台必须是 fanqie 或 qimao")
    
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        usage = download_service.get_quota_usage(platform)
        return usage
        
    except Exception as e:
        logger.error(f"Get quota error: {e}")
        raise HTTPException(status_code=500, detail=f"获取配额信息失败: {str(e)}")


@router.get("/quota")
async def get_all_quota(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """获取所有平台的配额使用情况"""
    try:
        storage = StorageService()
        download_service = DownloadService(db=db, storage=storage)
        
        usage = download_service.get_all_quota_usage()
        return usage
        
    except Exception as e:
        logger.error(f"Get all quota error: {e}")
        raise HTTPException(status_code=500, detail=f"获取配额信息失败: {str(e)}")
