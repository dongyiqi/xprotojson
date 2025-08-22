"""
依赖注入模块 - 提供各种服务依赖
"""
from typing import Annotated
from fastapi import Depends, Request
from app.clients.feishu import FeishuClient


def get_feishu_client(request: Request) -> FeishuClient:
	"""获取全局 feishu client"""
	return request.app.state.feishu


# 类型别名，方便在端点中使用
FeishuClientDep = Annotated[FeishuClient, Depends(get_feishu_client)]
