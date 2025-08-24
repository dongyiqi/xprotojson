"""
数据 API 端点
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from app.services.dependencies import (
    ConfigManagerDep,
    RedisServiceDep,
    SheetSyncServiceDep,
)
from app.services.cache import CacheKeys

router = APIRouter()


class DataResponse(BaseModel):
    """统一的数据响应格式"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    metadata: Optional[Dict[str, Any]] = None


class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    total_keys: int
    sheet_keys: int
    group_keys: int
    folder_keys: int


class SyncResponse(BaseModel):
    """同步响应"""
    success: bool
    message: str = ""
    details: Optional[Dict[str, Any]] = None



@router.post("/sheets/{sheet_token}/sync", response_model=SyncResponse, summary="同步指定表格到 Redis")
async def sync_sheet_to_redis(
    sheet_token: str = Path(..., description="飞书 spreadsheet token"),
    sync_service: SheetSyncServiceDep = None,
) -> SyncResponse:
    try:
        result = await sync_service.sync_sheet(sheet_token)
        return SyncResponse(success=True, message="同步完成", details=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# 清理缓存等 StructuredSheetService 相关能力已下线或迁移；保留接口占位时可在此实现新逻辑
