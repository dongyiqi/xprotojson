"""
数据 API 端点
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
from app.services.dependencies import (
    StructuredServiceDep,
    ConfigManagerDep,
    RedisServiceDep
)

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


@router.get("/sheets/{sheet_name}", response_model=DataResponse, summary="获取表格数据")
async def get_sheet_data(
    sheet_name: str = Path(..., description="表格名称，如 Config_Unit(hero)"),
    force_refresh: bool = Query(False, description="是否强制刷新缓存"),
    structured_service: StructuredServiceDep = None
) -> DataResponse:
    """
    获取单个表格的结构化数据
    
    支持懒加载：首次请求时从飞书获取并缓存，后续请求直接从缓存返回
    """
    try:
        data = await structured_service.get_structured_data(
            sheet_name=sheet_name,
            force_refresh=force_refresh
        )
        
        # 提取元数据
        metadata = {}
        if isinstance(data, dict) and "metadata" in data:
            metadata = data.pop("metadata", {})
        
        return DataResponse(
            success=True,
            data=data,
            message=f"成功获取表格 {sheet_name} 的数据",
            metadata=metadata
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取表格数据失败: {str(e)}"
        )


@router.get("/groups/{group_name}", response_model=DataResponse, summary="获取组合并数据")
async def get_group_data(
    group_name: str = Path(..., description="组名，如 Config_Unit"),
    force_refresh: bool = Query(False, description="是否强制刷新缓存"),
    structured_service: StructuredServiceDep = None
) -> DataResponse:
    """
    获取组的合并数据
    
    会自动合并同组下的所有表格（如 Config_Unit(hero) + Config_Unit(soldier)）
    """
    try:
        data = await structured_service.get_merged_data(
            group_name=group_name,
            force_refresh=force_refresh
        )
        
        return DataResponse(
            success=True,
            data=data,
            message=f"成功获取组 {group_name} 的合并数据"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取组数据失败: {str(e)}"
        )


@router.get("/folders/{folder_token}", response_model=DataResponse, summary="获取目录下的表格列表")
async def get_folder_sheets(
    folder_token: str = Path(..., description="飞书目录 token"),
    force_refresh: bool = Query(False, description="是否强制刷新缓存"),
    structured_service: StructuredServiceDep = None
) -> DataResponse:
    """
    获取指定目录下的所有表格信息
    """
    try:
        data = await structured_service.get_folder_sheets(
            folder_token=folder_token,
            force_refresh=force_refresh
        )
        
        return DataResponse(
            success=True,
            data={"sheets": data},
            message=f"成功获取目录 {folder_token} 下的表格列表"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取目录表格失败: {str(e)}"
        )


@router.post("/sheets/{sheet_name}/refresh", response_model=DataResponse, summary="刷新表格数据")
async def refresh_sheet(
    sheet_name: str = Path(..., description="表格名称"),
    structured_service: StructuredServiceDep = None
) -> DataResponse:
    """
    强制刷新指定表格的数据
    """
    try:
        data = await structured_service.refresh_sheet(sheet_name)
        
        return DataResponse(
            success=True,
            data=data,
            message=f"成功刷新表格 {sheet_name}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"刷新表格失败: {str(e)}"
        )


@router.post("/groups/{group_name}/refresh", response_model=DataResponse, summary="刷新组数据")
async def refresh_group(
    group_name: str = Path(..., description="组名"),
    structured_service: StructuredServiceDep = None
) -> DataResponse:
    """
    强制刷新指定组的数据
    """
    try:
        data = await structured_service.refresh_group(group_name)
        
        return DataResponse(
            success=True,
            data=data,
            message=f"成功刷新组 {group_name}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"刷新组数据失败: {str(e)}"
        )


@router.get("/configs", response_model=DataResponse, summary="获取配置信息")
async def get_configs(
    config_manager: ConfigManagerDep = None
) -> DataResponse:
    """
    获取所有已配置的表格信息
    """
    try:
        sheets = config_manager.list_all_sheets()
        groups = config_manager.list_all_groups()
        
        configs_info = {}
        for sheet_name in sheets:
            config = config_manager.get_config(sheet_name)
            if config:
                configs_info[sheet_name] = {
                    "sheet_token": config.sheet_token,
                    "group_name": config.group_name,
                    "sub_type": config.sub_type,
                    "range_str": config.range_str,
                    "key_column": config.schema.key_column,
                    "ttl": config.ttl
                }
        
        return DataResponse(
            success=True,
            data={
                "sheets": configs_info,
                "groups": groups,
                "total_sheets": len(sheets),
                "total_groups": len(groups)
            },
            message="成功获取配置信息"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取配置失败: {str(e)}"
        )


@router.get("/cache/stats", response_model=CacheStatsResponse, summary="获取缓存统计")
async def get_cache_stats(
    redis_service: RedisServiceDep = None
) -> CacheStatsResponse:
    """
    获取缓存统计信息
    """
    try:
        # 获取所有 xpj 相关的键
        all_keys = await redis_service.keys("xpj:*")
        sheet_keys = await redis_service.keys("xpj:sheet:*")
        group_keys = await redis_service.keys("xpj:sheet:merged:*")
        folder_keys = await redis_service.keys("xpj:folder:*")
        
        return CacheStatsResponse(
            total_keys=len(all_keys),
            sheet_keys=len(sheet_keys),
            group_keys=len(group_keys),
            folder_keys=len(folder_keys)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取缓存统计失败: {str(e)}"
        )


@router.delete("/cache", response_model=DataResponse, summary="清理缓存")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="缓存键模式，不提供则清理所有 xpj 缓存"),
    structured_service: StructuredServiceDep = None
) -> DataResponse:
    """
    清理缓存数据
    """
    try:
        cleared_count = await structured_service.clear_cache(pattern)
        
        return DataResponse(
            success=True,
            data={"cleared_count": cleared_count},
            message=f"成功清理 {cleared_count} 个缓存键"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清理缓存失败: {str(e)}"
        )
