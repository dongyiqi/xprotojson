"""
数据 API 端点
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from app.services.dependencies import (
    ConfigManagerDep,
    RedisServiceDep,
    SheetSyncServiceDep,
    IndexBuilderDep,
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


class IdListResponse(BaseModel):
    total: int
    ids: List[int]


class GroupCountResponse(BaseModel):
    group: str
    counts: Dict[str, int]



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


@router.get("/tables/{table}/ids", response_model=IdListResponse, summary="分页获取表内 ID 列表")
async def get_table_ids(
    table: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    index: IndexBuilderDep = None,
):
    try:
        total = await index.ids_count(table)
        ids = await index.ids_range(table, offset, offset + limit - 1)
        return IdListResponse(total=total, ids=ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table}/ids/score", response_model=IdListResponse, summary="按 score 范围获取 ID")
async def get_table_ids_by_score(
    table: str,
    min_score: int = Query(0),
    max_score: int = Query(1 << 62),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    index: IndexBuilderDep = None,
):
    try:
        ids = await index.ids_by_score(table, min_score, max_score, limit=limit, offset=offset)
        total = await index.ids_count(table)
        return IdListResponse(total=total, ids=ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table}/groups/{group}/values/{value}/ids", response_model=IdListResponse, summary="分页获取分组值的 ID")
async def get_group_ids(
    table: str,
    group: str,
    value: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    index: IndexBuilderDep = None,
):
    try:
        ids = await index.group_ids_range(table, group, value, offset, offset + limit - 1)
        counts = await index.group_counts(table, group)
        total = counts.get(value, 0)
        return IdListResponse(total=total, ids=ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables/{table}/groups/{group}/counts", response_model=GroupCountResponse, summary="获取某分组的计数分布")
async def get_group_counts(
    table: str,
    group: str,
    index: IndexBuilderDep = None,
):
    try:
        counts = await index.group_counts(table, group)
        return GroupCountResponse(group=group, counts=counts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
