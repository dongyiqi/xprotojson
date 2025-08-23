from fastapi import APIRouter

from .endpoints import health, test, data, demo, simple_demo

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["健康检查"])
api_v1_router.include_router(test.router, tags=["测试"])
api_v1_router.include_router(data.router, prefix="/data", tags=["数据接口"])
api_v1_router.include_router(demo.router, prefix="/demo", tags=["演示页面"])
api_v1_router.include_router(simple_demo.router, prefix="/demo", tags=["简化演示"])
