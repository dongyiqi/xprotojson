from fastapi import APIRouter

from .endpoints import health, test

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(test.router)
