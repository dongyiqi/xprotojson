from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.feishu_client import FeishuClient
from .config import TablesConfig
from .builder import JsonSchemaBuilder
from core.cache import DiskCache


class FeishuSchemaService:
    def __init__(self, client: FeishuClient, tables_cfg: TablesConfig | None = None, cache_dir: str | None = None) -> None:
        self.client = client
        self.cfg = tables_cfg or TablesConfig.from_yaml(None)
        self.builder = JsonSchemaBuilder()
        self.cache = DiskCache(cache_dir) if cache_dir else None

    def build_schema_for_spreadsheet(self, spreadsheet_token: str, sheet_id: str, header_max_col: str = "Z") -> Dict[str, Any]:
        # 读取表头行（1 ~ header_comment_row）
        range_a1 = f"{sheet_id}!A1:{header_max_col}{self.cfg.header_comment_row}"
        header_rows = self.client.read_range_values(spreadsheet_token, range_a1)

        # 规范化：按行对齐，不足列位填空
        normalized: list[list[Any]] = header_rows

        table = self.builder.parse_header_rows(normalized, self.cfg, title=sheet_id)
        schema = self.builder.build_object_schema(table)
        if self.cache:
            try:
                self.cache.write_schema(f"{spreadsheet_token}-{sheet_id}", schema)
            except Exception:
                pass
        return schema

    def get_cached_schema(self, spreadsheet_token: str) -> Dict[str, Any] | None:
        if not self.cache:
            return None
        if not self.cache.has_schema(spreadsheet_token):
            return None
        try:
            return self.cache.read_schema(spreadsheet_token)
        except Exception:
            return None

    def build_schema_for_workbook(self, spreadsheet_token: str, header_max_col: str = "Z") -> Dict[str, Any]:
        """
        为整个 workbook（电子表格）构建包含所有 sheet 的 JSON Schema 集合。
        返回结构：
        {
          "spreadsheet_token": str,
          "sheet_count": int,
          "sheets": [
             {"sheet_id": str, "title": str, "schema": {...}}, ...
          ]
        }
        若启用 cache，则将组合后的结果以 spreadsheet_token 为 key 写入磁盘。
        """
        # 获取 sheet 列表（兼容 dict 与 SDK 对象）
        resp = self.client.list_sheets(spreadsheet_token)
        sheet_items = getattr(resp, "data", None)
        sheet_items = getattr(sheet_items, "sheets", []) if sheet_items else []

        result: Dict[str, Any] = {
            "spreadsheet_token": spreadsheet_token,
            "sheet_count": len(sheet_items),
            "sheets": []
        }

        for s in sheet_items:
            if isinstance(s, dict):
                sheet_id = s.get("sheet_id")
                title = s.get("title")
            else:
                sheet_id = getattr(s, "sheet_id", None)
                title = getattr(s, "title", None)
            if not sheet_id:
                continue

            schema = self.build_schema_for_spreadsheet(spreadsheet_token, sheet_id, header_max_col)
            result["sheets"].append({
                "sheet_id": sheet_id,
                "title": title,
                "schema": schema,
            })

        return result

    def build_items_for_sheet(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        header_max_col: str = "Z",
        data_max_col: Optional[str] = None,
        data_max_rows: int = 5000,
    ) -> Dict[str, Any]:
        """
        将指定 sheet 下的数据按之前的 schema 约定转换为对象：
        {
          "<id>": { "id": <id>, "field1": v1, ... },
          ...
        }
        - 第一列为 id/key
        - 头部行范围：1 ~ header_comment_row
        - 数据范围：从 data_start_row 起至 data_max_rows/列上限
        """
        # 1) 读取头部，提取字段名与类型
        header_range = f"{sheet_id}!A1:{header_max_col}{self.cfg.header_comment_row}"
        header_rows = self.client.read_range_values(spreadsheet_token, header_range)
        table = self.builder.parse_header_rows(header_rows, self.cfg, title=sheet_id)
        field_names: List[str] = [f.name.rstrip("?") for f in table.fields]

        if not field_names:
            return {}

        # 2) 读取数据区域
        last_col = data_max_col or header_max_col
        data_range = f"{sheet_id}!A{self.cfg.data_start_row}:{last_col}{data_max_rows}"
        data_rows = self.client.read_range_values(spreadsheet_token, data_range)

        # 3) 构造 items
        items: Dict[str, Any] = {}
        for row in data_rows:
            if not row or len(row) == 0:
                continue
            key = str(row[0]).strip()
            if key == "" or key.lower() == "none":
                continue

            obj: Dict[str, Any] = {}
            # 填充各字段（包括 id）
            for idx, name in enumerate(field_names):
                val = row[idx] if idx < len(row) else None
                obj[name] = val
            items[key] = obj

        return items


