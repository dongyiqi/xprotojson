from typing import Optional

from fastapi import APIRouter
from app.dependencies import FeishuClientDep

router = APIRouter()


@router.get("/test/ping", summary="Ping")
def ping():
	return {"pong": True}


@router.get("/test/page", summary="测试页面")
def test_page():
	return {
		"title": "XPJ Test Page",
		"message": "This is a test endpoint under /api/v1/test/page",
	}


@router.get("/test/drive", summary="测试获取目录列表")
def test_drive(
	folder_token: str,
	page_size: int = 50,
	page_token: Optional[str] = None,
	client: FeishuClientDep = None,
):
	data = client.list_drive_files(
		folder_token=folder_token,
		page_size=page_size,
		page_token=page_token,
	)
	return data

