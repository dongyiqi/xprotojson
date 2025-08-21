from fastapi import APIRouter

from .endpoints import health

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
