"""
服务依赖注入模块
"""
from typing import Annotated
from fastapi import Depends, Request
from app.services.config_manager import ConfigManager
from app.services.feishu import DriveService, SheetService
from app.services.cache import RedisService
from app.services.transform import SheetTransformer
from app.services.merge import SheetMerger
from app.services.structured_service import StructuredSheetService
from app.clients.feishu import FeishuClient


# 全局服务实例
_config_manager = None
_redis_service = None
_transformer = None
_merger = None
_structured_service = None


def get_feishu_client(request: Request) -> FeishuClient:
    """获取 FeishuClient"""
    return request.app.state.feishu


def get_config_manager() -> ConfigManager:
    """获取配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        # 初始化默认配置
        _config_manager.initialize_default_configs()
        # 尝试加载配置文件
        _config_manager.load_from_file("config/sheet_configs.json")
    return _config_manager


def get_redis_service() -> RedisService:
    """获取 Redis 服务"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service


def get_transformer() -> SheetTransformer:
    """获取数据转换器"""
    global _transformer
    if _transformer is None:
        _transformer = SheetTransformer()
    return _transformer


def get_merger() -> SheetMerger:
    """获取合并器"""
    global _merger
    if _merger is None:
        _merger = SheetMerger()
    return _merger


def get_drive_service(feishu_client: Annotated[FeishuClient, Depends(get_feishu_client)]) -> DriveService:
    """获取 Drive 服务"""
    return DriveService(feishu_client)


def get_sheet_service(feishu_client: Annotated[FeishuClient, Depends(get_feishu_client)]) -> SheetService:
    """获取 Sheet 服务"""
    return SheetService(feishu_client)


def get_structured_service(
    sheet_service: Annotated[SheetService, Depends(get_sheet_service)],
    redis_service: Annotated[RedisService, Depends(get_redis_service)],
    transformer: Annotated[SheetTransformer, Depends(get_transformer)],
    merger: Annotated[SheetMerger, Depends(get_merger)],
    config_manager: Annotated[ConfigManager, Depends(get_config_manager)],
    drive_service: Annotated[DriveService, Depends(get_drive_service)]
) -> StructuredSheetService:
    """获取结构化数据服务"""
    global _structured_service
    if _structured_service is None:
        _structured_service = StructuredSheetService(
            sheet_service=sheet_service,
            redis_service=redis_service,
            transformer=transformer,
            merger=merger,
            config_manager=config_manager,
            drive_service=drive_service
        )
    return _structured_service


# 类型别名，方便在端点中使用
ConfigManagerDep = Annotated[ConfigManager, Depends(get_config_manager)]
RedisServiceDep = Annotated[RedisService, Depends(get_redis_service)]
SheetTransformerDep = Annotated[SheetTransformer, Depends(get_transformer)]
SheetMergerDep = Annotated[SheetMerger, Depends(get_merger)]
DriveServiceDep = Annotated[DriveService, Depends(get_drive_service)]
SheetServiceDep = Annotated[SheetService, Depends(get_sheet_service)]
StructuredServiceDep = Annotated[StructuredSheetService, Depends(get_structured_service)]
