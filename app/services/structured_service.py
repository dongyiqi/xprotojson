"""
结构化数据服务 - 提供懒加载的结构化 Sheet 数据
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.services.base import BaseService, ConfigNotFoundError
from app.services.feishu import SheetService, DriveService
from app.services.cache import RedisService, CacheKeys
from app.services.transform import SheetTransformer, SheetConfig
from app.services.merge import SheetMerger
from app.services.config_manager import ConfigManager


class StructuredSheetService(BaseService):
    """结构化 Sheet 数据服务，实现懒加载和缓存"""
    
    def __init__(
        self,
        sheet_service: SheetService,
        redis_service: RedisService,
        transformer: SheetTransformer,
        merger: SheetMerger,
        config_manager: ConfigManager,
        drive_service: Optional[DriveService] = None
    ):
        """
        初始化服务
        
        Args:
            sheet_service: 飞书 Sheet 服务
            redis_service: Redis 缓存服务
            transformer: 数据转换器
            merger: 数据合并器
            config_manager: 配置管理器
            drive_service: 飞书 Drive 服务（可选）
        """
        super().__init__("StructuredSheetService")
        self.sheet_service = sheet_service
        self.redis = redis_service
        self.transformer = transformer
        self.merger = merger
        self.config_manager = config_manager
        self.drive_service = drive_service
    
    async def get_structured_data(
        self,
        sheet_name: str,
        force_refresh: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取结构化的 Sheet 数据（懒加载）
        
        Args:
            sheet_name: Sheet 名称
            force_refresh: 是否强制刷新
            
        Returns:
            结构化数据 {"key": {"field": value}}
        """
        self.log_info(f"获取结构化数据: {sheet_name}, force_refresh={force_refresh}")
        
        try:
            # 1. 获取配置
            config = self.config_manager.get_config(sheet_name)
            
            # 2. 生成缓存键
            cache_key = CacheKeys.structured_key(
                sheet_token=config.sheet_token,
                sheet_name=sheet_name,
                range_str=config.range_str
            )
            
            # 3. 如果不是强制刷新，尝试从缓存获取
            if not force_refresh:
                cached_data = await self.redis.get(cache_key)
                if cached_data is not None:
                    self.log_info(f"缓存命中: {sheet_name}")
                    self.record_metric("cache_hit", 1)
                    # 返回数据部分（去除元数据包装）
                    return cached_data.get("data", cached_data)
            
            # 4. 缓存未命中，从飞书获取
            self.log_info(f"缓存未命中，从飞书获取: {sheet_name}")
            self.record_metric("cache_miss", 1)
            
            # 使用 get_or_set 避免缓存击穿
            structured_data = await self.redis.get_or_set(
                key=cache_key,
                fetch_func=lambda: self._fetch_and_transform(config),
                ttl=config.ttl
            )
            
            return structured_data.get("data", structured_data)
            
        except ConfigNotFoundError:
            self.log_error(f"未找到 {sheet_name} 的配置")
            raise
        except Exception as e:
            self.log_error(f"获取结构化数据失败: {sheet_name}", error=e)
            raise
    
    async def get_merged_data(
        self,
        group_name: str,
        force_refresh: bool = False
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        获取合并后的数据
        
        Args:
            group_name: 组名
            force_refresh: 是否强制刷新
            
        Returns:
            合并数据 {"sub_type": {"key": {"field": value}}}
        """
        self.log_info(f"获取合并数据: {group_name}, force_refresh={force_refresh}")
        
        # 1. 生成缓存键
        cache_key = CacheKeys.merged_key(group_name=group_name)
        
        # 2. 如果不是强制刷新，尝试从缓存获取
        if not force_refresh:
            cached_data = await self.redis.get(cache_key)
            if cached_data is not None:
                self.log_info(f"合并数据缓存命中: {group_name}")
                return cached_data.get("data", cached_data)
        
        # 3. 获取该组的所有配置
        configs = self.config_manager.get_group_configs(group_name)
        if not configs:
            self.log_warning(f"未找到组 {group_name} 的任何配置")
            return {}
        
        # 4. 使用 merger 合并数据
        merged_data = await self.merger.merge_group(
            group_name=group_name,
            configs=configs,
            fetch_structured=self.get_structured_data
        )
        
        # 5. 添加元数据并缓存
        wrapped_data = self._add_metadata(
            data=merged_data,
            revision=0,  # 合并数据没有单一的 revision
            sheet_name=f"merged_{group_name}"
        )
        
        # 使用最长的 TTL
        max_ttl = max(config.ttl for config in configs) if configs else 3600
        await self.redis.set(cache_key, wrapped_data, ttl=max_ttl)
        
        return merged_data
    
    async def _fetch_and_transform(
        self,
        config: SheetConfig
    ) -> Dict[str, Any]:
        """从飞书获取并转换数据"""
        try:
            # 1. 从飞书获取原始数据
            raw_response = await self.sheet_service.get_sheet_values(
                spreadsheet_token=config.sheet_token,
                range_str=config.get_full_range()
            )
            
            # 2. 提取数据
            values = raw_response.get("valueRange", {}).get("values", [])
            revision = raw_response.get("revision", 0)
            
            if not values:
                self.log_warning(f"Sheet {config.sheet_name} 数据为空")
                return self._add_metadata({}, revision, config.sheet_name)
            
            # 3. 使用 transformer 转换数据
            structured_data = self.transformer.transform_to_structured(
                raw_values=values,
                schema=config.schema
            )
            
            # 4. 添加元数据
            return self._add_metadata(structured_data, revision, config.sheet_name)
            
        except Exception as e:
            self.log_error(f"获取并转换数据失败: {config.sheet_name}", error=e)
            raise
    
    def _add_metadata(
        self,
        data: Dict[str, Any],
        revision: int,
        sheet_name: str
    ) -> Dict[str, Any]:
        """添加元数据"""
        return {
            "data": data,
            "metadata": {
                "revision": revision,
                "sheet_name": sheet_name,
                "generated_at": datetime.now().isoformat(),
                "schema_version": "1.0",
                "row_count": len(data)
            }
        }
    
    async def get_folder_sheets(
        self,
        folder_token: str,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取文件夹下所有表格的信息
        
        Args:
            folder_token: 文件夹 token
            force_refresh: 是否强制刷新
            
        Returns:
            表格信息列表
        """
        if not self.drive_service:
            raise RuntimeError("DriveService 未初始化")
        
        # 生成缓存键
        cache_key = CacheKeys.folder_files_key(folder_token)
        
        # 尝试从缓存获取
        if not force_refresh:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return cached_data
        
        # 从飞书获取
        sheet_files = await self.drive_service.get_sheets_in_folder(folder_token)
        
        # 转换为字典列表（保持与飞书 API 时间戳一致为数字）
        result = [
            {
                "token": f.token,
                "name": f.name,
                "created_time": f.created_time,
                "modified_time": f.modified_time
            }
            for f in sheet_files
        ]
        
        # 缓存结果
        await self.redis.set(cache_key, result, ttl=300)  # 5分钟缓存
        
        return result
    
    async def refresh_sheet(self, sheet_name: str) -> Dict[str, Dict[str, Any]]:
        """
        强制刷新指定 sheet 的数据
        
        Args:
            sheet_name: Sheet 名称
            
        Returns:
            刷新后的数据
        """
        return await self.get_structured_data(sheet_name, force_refresh=True)
    
    async def refresh_group(self, group_name: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        强制刷新指定组的数据
        
        Args:
            group_name: 组名
            
        Returns:
            刷新后的合并数据
        """
        return await self.get_merged_data(group_name, force_refresh=True)
    
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        清除缓存
        
        Args:
            pattern: 键模式，不提供则清除所有
            
        Returns:
            清除的键数量
        """
        if pattern:
            return await self.redis.clear_pattern(pattern)
        else:
            # 清除所有 xpj 前缀的键
            return await self.redis.clear_pattern(f"{CacheKeys.PREFIX}:*")
