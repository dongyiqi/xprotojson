import os
import json
import logging
from typing import Any, Dict, Optional, Tuple, List
from urllib.parse import quote

import lark_oapi as lark
from lark_oapi.api.sheets.v3 import (
	QuerySpreadsheetSheetRequest,
	QuerySpreadsheetSheetResponse,
)
from app.core.config import settings


class FeishuClient:
	"""
	最小实现：仅鉴权 + v3 Query 列表工作表 + v2 读值 + Drive v1 列表文件
	"""

	def __init__(
		self,
		app_id: Optional[str] = None,
		app_secret: Optional[str] = None,
		config_path: Optional[str] = None,
		log_level: lark.LogLevel = lark.LogLevel.DEBUG,
	) -> None:
		self._logger = logging.getLogger("xpj.feishu")
		app_id, app_secret = self._load_credentials(app_id, app_secret, config_path)
		self.client = (
			lark.Client.builder()
			.app_id(app_id)
			.app_secret(app_secret)
			.log_level(log_level)
			.build()
		)

	def _default_config_candidates(self) -> List[str]:
		"""
		返回可能存在的默认配置文件路径候选，按优先级排序。
		"""
		current_dir = os.path.dirname(__file__)
		candidates: List[str] = []
		# 1) app/configs/xpj.feishu.yaml
		candidates.append(os.path.abspath(os.path.join(current_dir, "..", "configs", "xpj.feishu.yaml")))
		# 2) python/configs/xpj.feishu.yaml（兼容旧目录，待废弃）
		candidates.append(os.path.abspath(os.path.join(current_dir, "..", "..", "python", "configs", "xpj.feishu.yaml")))
		return candidates

	def _load_credentials(
		self,
		app_id: Optional[str],
		app_secret: Optional[str],
		config_path: Optional[str],
	) -> Tuple[str, str]:
		# 1) Explicit params
		if app_id and app_secret:
			return app_id, app_secret
		# 2) From FastAPI settings (recommended)
		if settings.feishu_app_id and settings.feishu_app_secret:
			return settings.feishu_app_id, settings.feishu_app_secret
		# 3) Fallback to raw environment variables (compat)
		env_app_id = os.getenv("FEISHU_APP_ID") or os.getenv("XPJ_FEISHU_APP_ID")
		env_app_secret = os.getenv("FEISHU_APP_SECRET") or os.getenv("XPJ_FEISHU_APP_SECRET")
		if env_app_id and env_app_secret:
			return env_app_id, env_app_secret
		raise ValueError(
			"Feishu credentials not found. Configure XPJ_FEISHU_APP_ID/XPJ_FEISHU_APP_SECRET (or FEISHU_*), or pass app_id/app_secret explicitly."
		)

	# ---------- Drive v1：列出指定文件夹下的文件（单页） ----------
	def list_drive_files(
		self,
		folder_token: str,
		page_size: int = 50,
		page_token: Optional[str] = None,
		order_by: str = "EditedTime",
		direction: str = "DESC",
		user_id_type: str = "open_id",
	) -> Dict[str, Any]:
		"""
		使用 lark-oapi SDK 调用 Drive v1 列表接口，返回单页结果。
		如需翻页，请传入上页的 page_token。
		返回值为原生 response.data 对象（便于 lark.JSON.marshal 打印）。
		"""
		try:
			from lark_oapi.api.drive.v1 import ListFileRequest, ListFileResponse
		except ModuleNotFoundError as e:
			raise NotImplementedError(
				"当前 lark-oapi 版本未提供 drive.v1 file.list API。请升级到支持的版本（如 >=1.4.15）。"
			) from e

		builder = (
			ListFileRequest.builder()
			.page_size(page_size)
			.folder_token(folder_token)
			.order_by(order_by)
			.direction(direction)
			.user_id_type(user_id_type)
		)
		if page_token:
			builder = builder.page_token(page_token)
		request = builder.build()

		response: ListFileResponse = self.client.drive.v1.file.list(request)
		if not response.success():
			self._logger.error(
				f"client.drive.v1.file.list failed, code: {response.code}, msg: {response.msg}, "
				f"log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
			)
			raise RuntimeError(f"Drive list failed: {response.code} {response.msg}")

		return response.data if response.data is not None else {}

	# ---------- Sheets v3：列出工作表（返回原生响应对象） ----------
	def list_sheets(self, spreadsheet_token: str):
		request: QuerySpreadsheetSheetRequest = (
			QuerySpreadsheetSheetRequest.builder()
			.spreadsheet_token(spreadsheet_token)
			.build()
		)
		response: QuerySpreadsheetSheetResponse = (
			self.client.sheets.v3.spreadsheet_sheet.query(request)
		)
		if not response.success():
			self._logger.error(
				f"client.sheets.v3.spreadsheet_sheet.query failed, code: {response.code}, msg: {response.msg}, "
				f"log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
			)
			raise RuntimeError(f"Sheets query failed: {response.code} {response.msg}")
		try:
			self._logger.info(lark.JSON.marshal(response.data, indent=4))
		except Exception:
			pass
		# 与测试中的实现保持一致，直接返回原生响应对象
		return response

	# ---------- Sheets v2：读取指定范围的值（使用 lark 原生 BaseRequest 调用） ----------
	def read_range_values(
		self,
		spreadsheet_token: str,
		range_a1: str,
		value_render_option: str = "ToString",
		date_time_render_option: str = "FormattedString",
	) -> List[List[Any]]:
		"""
		使用 lark-oapi 的原生 BaseRequest 模式调用 v2 valueRange GET 接口。
		不回退到纯 HTTP。
		"""
		# URL 中的 range 需要进行 path 安全编码，但保留 '!' 和 ':'
		encoded_range = quote(range_a1, safe="!:")
		uri = f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{encoded_range}"

		request = (
			lark.BaseRequest.builder()
			.http_method(lark.HttpMethod.GET)
			.uri(uri)
			.token_types({lark.AccessTokenType.TENANT})
			.queries([
				("valueRenderOption", value_render_option),
				("dateTimeRenderOption", date_time_render_option),
			])
			.build()
		)

		response: lark.BaseResponse = self.client.request(request)
		if not response.success():
			raise RuntimeError(
				f"valueRange get failed: code={response.code}, msg={response.msg}, log_id={response.get_log_id()}"
			)

		try:
			body = json.loads(response.raw.content.decode("utf-8"))
		except Exception as ex:
			raise RuntimeError(f"invalid json body: {ex}")

		values = (
			(body or {}).get("data", {}).get("valueRange", {}).get("values", [])
			or []
		)
		# 统一返回二维数组
		return values