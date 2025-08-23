"""
Sheet 同步服务：读取指定 spreadsheet_token 的首个（或指定）Sheet，
基于表格顶部前四行推断 JSON Schema，将每行数据解析为 JSON 并写入 Redis。
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.services.base import BaseService
from app.services.feishu import SheetService
from app.services.cache import RedisService, CacheKeys
from app.services.transform import SheetTransformer, SheetSchema
from app.core.config import settings


class SheetSyncService(BaseService):
    """Sheet 同步到 Redis 的服务"""

    def __init__(
        self,
        sheet_service: SheetService,
        redis_service: RedisService,
        transformer: SheetTransformer,
    ) -> None:
        super().__init__("SheetSyncService")
        self.sheet_service = sheet_service
        self.redis = redis_service
        self.transformer = transformer

    async def sync_sheet(
        self,
        spreadsheet_token: str,
    ) -> Dict[str, Any]:
        """同步指定表格的数据到 Redis。

        - 自动获取 Sheet 元信息（含行列数、revision 等）
        - 读取 A1 到末尾（按元信息行列数构造范围）
        - 依据前四行推断 Schema（表头与类型映射）
        - 从第 5 行开始逐行解析并写入 Redis
        - 同时写入 meta 与 schema
        """

        # 1) 列出工作簿内所有 sheet
        list_resp = await self._list_sheets(spreadsheet_token)
        sheets = list_resp.get("sheets", [])

        per_sheet_results: List[Dict[str, Any]] = []
        total_rows_written = 0
            
        for s in sheets:
            sheet_id = s.get("sheet_id") or s.get("sheetId") or ""
            sheet_title = s.get("title") or s.get("name") or sheet_id or "Sheet1"
            gp = s.get("grid_properties", {}) or {}
            rows = int(gp.get("row_count", 0) or 0)
            cols = int(gp.get("column_count", 0) or 0)
            rows = max(rows, 1)
            cols = max(cols, 1)

            a1_range_by_id = f"{sheet_id}!A1:{self._col_number_to_letters(cols)}{rows}"

            # 2) 读取数据（values）：只使用 sheet_id 形式，符合 Feishu API 标准
            raw = await self.sheet_service.get_sheet_values(
                spreadsheet_token=spreadsheet_token,
                range_str=a1_range_by_id,
            )
            values: List[List[Any]] = raw.get("valueRange", {}).get("values", [])

            # 3) 构建/推断 Schema（前四行）
            schema = self._infer_schema_from_top_rows(values)

            # 4) 解析行并批量写入 Redis
            row_count, written_keys = await self._write_rows_to_redis(
                spreadsheet_token=spreadsheet_token,
                sheet_name=sheet_title,
                values=values,
                schema=schema,
            )
            total_rows_written += row_count

          
            await self._write_schema_by_name(
                sheet_name=sheet_title,
                schema=schema,
            )

            per_sheet_results.append({
                "sheet_id": sheet_id,
                "sheet_name": sheet_title,
                "rows_written": row_count,
                "schema_key": CacheKeys.sheet_schema_by_name_key(sheet_title),
                "row_keys_sample": written_keys[:10],
            })
            

        # 5) 写入工作簿级别 meta（容器信息）
        await self._write_container_meta(
            spreadsheet_token=spreadsheet_token,
            sheets=[{"sheet_id": s.get("sheet_id"), "sheet_name": s.get("title")} for s in sheets],
            total_rows=total_rows_written,
        )

        return {
            "sheet_token": spreadsheet_token,
            "total_rows_written": total_rows_written,
            "sheets": per_sheet_results,
            "container_meta_key": CacheKeys.sheet_meta_key(spreadsheet_token),
        }

    async def _write_rows_to_redis(
        self,
        spreadsheet_token: str,
        sheet_name: str,
        values: List[List[Any]],
        schema: SheetSchema,
    ) -> Tuple[int, List[str]]:
        """将数据行写入 Redis，返回成功写入的行数和键样本。"""
        if not values:
            return 0, []

        # 以 transformer 解析为结构化字典 {key: row_data}
        structured = self.transformer.transform_to_structured(values, schema)
        if not structured:
            return 0, []

        written = 0
        keys_sample: List[str] = []

        async with self.redis.pipeline() as pipe:
            for row_key, row_data in structured.items():
                # 全局唯一键：xpj:cfgid:{row_key}
                redis_key = CacheKeys.row_cfgid_key(str(row_key))
                await pipe.set(redis_key, self.redis._serialize(row_data))
                written += 1
                if len(keys_sample) < 20:
                    keys_sample.append(redis_key)
            await pipe.execute()

        return written, keys_sample

    async def _write_schema_and_meta(
        self,
        spreadsheet_token: str,
        sheet_name: str,
        schema: SheetSchema,
        meta: Dict[str, Any],
    ) -> None:
        schema_key = CacheKeys.sheet_schema_key(spreadsheet_token, sheet_name)
        meta_key = CacheKeys.sheet_meta_key(spreadsheet_token)

        # 将 dataclass Schema 转为可序列化 dict
        schema_dict = {
            "key_column": schema.key_column,
            "headers": schema.headers,
            "header_row": schema.header_row,
            "data_start_row": schema.data_start_row,
            "type_mapping": schema.type_mapping,
            "array_columns": schema.array_columns,
            "json_columns": schema.json_columns,
        }
        await self.redis.set(schema_key, schema_dict)
        await self.redis.set(meta_key, meta)

    async def _write_schema(
        self,
        spreadsheet_token: str,
        sheet_name: str,
        schema: SheetSchema,
    ) -> None:
        schema_key = CacheKeys.sheet_schema_key(spreadsheet_token, sheet_name)
        schema_dict = {
            "key_column": schema.key_column,
            "headers": schema.headers,
            "header_row": schema.header_row,
            "data_start_row": schema.data_start_row,
            "type_mapping": schema.type_mapping,
            "array_columns": schema.array_columns,
            "json_columns": schema.json_columns,
        }
        await self.redis.set(schema_key, schema_dict)

    # 为兼容旧命名，提供 _write_schema_only 的别名
    _write_schema_only = _write_schema

    async def _write_schema_by_name(
        self,
        sheet_name: str,
        schema: SheetSchema,
    ) -> None:
        schema_key = CacheKeys.sheet_schema_by_name_key(sheet_name)
        schema_dict = {
            "key_column": schema.key_column,
            "headers": schema.headers,
            "header_row": schema.header_row,
            "data_start_row": schema.data_start_row,
            "type_mapping": schema.type_mapping,
            "array_columns": schema.array_columns,
            "json_columns": schema.json_columns,
        }
        await self.redis.set(schema_key, schema_dict)

    async def _write_container_meta(
        self,
        spreadsheet_token: str,
        sheets: List[Dict[str, Any]],
        total_rows: int,
    ) -> None:
        meta_key = CacheKeys.sheet_meta_key(spreadsheet_token)

        # 获取文件级别的创建/修改时间（数字时间戳）与名称
        created_ts = 0
        modified_ts = 0
        workbook_name = ""
        try:
            resp = await self._call_drive_get_file(spreadsheet_token)
            # 兼容属性/字典
            payload = resp
            if isinstance(resp, dict) and "data" in resp:
                payload = resp["data"]
            created_ts = self._extract_num_ts(payload, ["created_time", "create_time"]) or 0
            modified_ts = self._extract_num_ts(payload, ["modified_time", "update_time", "edited_time"]) or 0
            # 名称字段
            if isinstance(payload, dict):
                workbook_name = payload.get("name") or ""
            else:
                workbook_name = getattr(payload, "name", "") or ""
        except Exception:
            pass

        meta = {
            "generated_at": datetime.now().isoformat(),
            "revision": 0,
            "sheets": sheets,
            "total_rows": total_rows,
            "created_time": created_ts,
            "modified_time": modified_ts,
            "workbook_name": workbook_name,
        }
        await self.redis.set(meta_key, meta)

    async def _call_drive_get_file(self, file_token: str):
        # 参考 _call_list_sheets 的风格，使用底层 client
        loop = None
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except Exception:
            loop = None
        if loop and loop.is_running():
            return await loop.run_in_executor(None, self.sheet_service.feishu_client.get_drive_file, file_token)
        else:
            return self.sheet_service.feishu_client.get_drive_file(file_token)

    def _extract_num_ts(self, obj: Any, keys: List[str]) -> int:
        def _g(o: Any, k: str):
            if isinstance(o, dict):
                return o.get(k)
            return getattr(o, k, None)
        for k in keys:
            v = _g(obj, k)
            if v is None:
                continue
            try:
                return int(float(str(v)))
            except Exception:
                continue
        return 0

    def _infer_schema_from_top_rows(self, values: List[List[Any]]) -> SheetSchema:
        """基于配置行索引推断 Schema：
        - header 使用 settings.table.header_name_row（默认第 2 行）
        - 类型使用 settings.table.type_row（默认第 3 行）
        - 备注使用 settings.table.comment_row（默认第 4 行，不参与解析，仅预留）
        - 数据开始行使用 settings.table.data_start_row（默认第 5 行，0-based）
        - 主键列优先匹配 settings.table.default_key_column（默认 ID），否则第一列
        """
        cfg = settings.table
        header_row = cfg.header_name_row + 1  # storage uses 1-based for transformer
        data_start_row = cfg.data_start_row + 1

        headers: List[str] = []
        if values and len(values) > cfg.header_name_row:
            raw_headers = values[cfg.header_name_row]
            headers = []
            for cell in raw_headers:
                if self.transformer._is_empty_value(cell):
                    headers.append(f"Column{len(headers) + 1}")
                else:
                    import re
                    header = str(cell).strip()
                    header = re.sub(r'[^\w\u4e00-\u9fa5]', '_', header)
                    headers.append(header)

        # 采样行（类型行优先，其它行作为补充）
        samples: List[List[Any]] = []
        if len(values) > cfg.type_row:
            samples.append(values[cfg.type_row])
        for r in range(cfg.header_name_row + 1, min(len(values), cfg.comment_row + 1)):
            if r != cfg.type_row and r < len(values):
                samples.append(values[r])

        # 推断类型
        type_mapping: Dict[str, str] = {}
        array_columns: List[str] = []
        json_columns: List[str] = []

        for col_idx, header in enumerate(headers):
            inferred_type = self._infer_column_type([row[col_idx] if col_idx < len(row) else None for row in samples])
            type_mapping[header] = inferred_type
            if inferred_type == "array":
                array_columns.append(header)
            elif inferred_type == "json":
                json_columns.append(header)

        # 主键列
        key_column = cfg.default_key_column or "ID"
        if headers:
            lower_headers = [h.lower() for h in headers]
            dk = (cfg.default_key_column or "ID").lower()
            if dk in lower_headers:
                key_column = headers[lower_headers.index(dk)]
            else:
                key_column = headers[0]

        # 如果数据总行数不足，保证 data_start_row 至少大于 header_row
        if len(values) <= cfg.data_start_row:
            data_start_row = max(header_row + 1, len(values))

        return SheetSchema(
            key_column=key_column,
            headers=headers,
            header_row=header_row,
            data_start_row=data_start_row,
            type_mapping=type_mapping,
            array_columns=array_columns,
            json_columns=json_columns,
        )

    def _infer_column_type(self, samples: List[Any]) -> str:
        """根据样本值推断列类型。"""
        has_json = False
        has_array = False
        has_bool = False
        has_int = False
        has_float = False

        for v in samples:
            if v is None or (isinstance(v, str) and v.strip() == ""):
                continue
            s = str(v).strip()
            if s.startswith("{") and s.endswith("}"):
                has_json = True
                continue
            if s.startswith("[") and s.endswith("]"):
                has_array = True
                continue
            if "," in s or ";" in s:
                has_array = True
            lv = s.lower()
            if lv in ("true", "false", "1", "0", "yes", "no", "是", "否"):
                has_bool = True
                continue
            try:
                iv = int(float(s))
                fv = float(s)
                if float(iv) == fv:
                    has_int = True
                else:
                    has_float = True
                continue
            except Exception:
                try:
                    float(s)
                    has_float = True
                    continue
                except Exception:
                    pass

        if has_json:
            return "json"
        if has_array:
            return "array"
        if has_bool:
            return "bool"
        if has_int:
            return "int"
        if has_float:
            return "float"
        return "str"

    def _col_number_to_letters(self, col_number: int) -> str:
        """1 -> A, 26 -> Z, 27 -> AA ..."""
        result = ""
        n = max(col_number, 1)
        while n > 0:
            n, rem = divmod(n - 1, 26)
            result = chr(65 + rem) + result
        return result

    async def _list_sheets(self, spreadsheet_token: str) -> Dict[str, Any]:
        """列出工作簿内的所有 sheet，返回简化的 dict 结构。
        兼容 lark 响应对象与 dict。
        返回形如：{"sheets": [{"sheet_id": str, "title": str, "grid_properties": {"row_count": int, "column_count": int}}]}
        """
        # 直接使用底层 client，避免重复封装
        resp = await self._call_list_sheets(spreadsheet_token)
        payload = resp
        if isinstance(resp, dict):
            payload = resp.get("data", resp)
        else:
            # lark Response 对象
            try:
                payload = resp.data
            except Exception:
                payload = resp

        sheets_obj = []
        if isinstance(payload, dict):
            sheets_obj = payload.get("sheets", [])
        else:
            try:
                sheets_obj = getattr(payload, "sheets", [])
            except Exception:
                sheets_obj = []

        def _to_dict(s: Any) -> Dict[str, Any]:
            if isinstance(s, dict):
                sheet_id = s.get("sheet_id") or s.get("sheetId") or ""
                title = s.get("title") or s.get("name") or ""
                gp = s.get("grid_properties") or {}
                if not isinstance(gp, dict) and gp is not None:
                    gp = {
                        "row_count": getattr(gp, "row_count", 0),
                        "column_count": getattr(gp, "column_count", 0),
                    }
                return {
                    "sheet_id": sheet_id,
                    "title": title,
                    "grid_properties": {
                        "row_count": int((gp or {}).get("row_count", 0) or 0),
                        "column_count": int((gp or {}).get("column_count", 0) or 0),
                    },
                }
            else:
                sheet_id = getattr(s, "sheet_id", "")
                title = getattr(s, "title", "") or getattr(s, "name", "")
                gp = getattr(s, "grid_properties", None)
                row_count = 0
                col_count = 0
                if gp is not None:
                    row_count = getattr(gp, "row_count", 0) or 0
                    col_count = getattr(gp, "column_count", 0) or 0
                return {
                    "sheet_id": sheet_id,
                    "title": title,
                    "grid_properties": {
                        "row_count": int(row_count),
                        "column_count": int(col_count),
                    },
                }

        return {"sheets": [_to_dict(s) for s in (sheets_obj or [])]}

    async def _call_list_sheets(self, spreadsheet_token: str):
        # 使用 SheetService 内部 feishu_client
        # list_sheets 为同步方法，外层以 run_in_executor 调用也可；但这里直接复用 SheetService 逻辑更简单。
        # 由于 SheetService.get_sheet_meta 已经验证可调用，我们直接调用 client 方法并返回原始响应。
        loop = None
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except Exception:
            loop = None
        if loop and loop.is_running():
            return await loop.run_in_executor(None, self.sheet_service.feishu_client.list_sheets, spreadsheet_token)
        else:
            return self.sheet_service.feishu_client.list_sheets(spreadsheet_token)


