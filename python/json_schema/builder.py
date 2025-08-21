from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .config import TablesConfig


@dataclass
class FieldDef:
    name: str
    type_spec: str
    comment: Optional[str] = None
    index: Optional[int] = None


@dataclass
class TableSchema:
    title: str
    fields: List[FieldDef]


class JsonSchemaBuilder:
    def parse_header_rows(self, rows: List[List[Any]], cfg: TablesConfig, title: str) -> TableSchema:
        # rows: A1:Z<header_comment_row> 区间
        # 将缺失的行补空
        def get_row(r: int) -> List[Any]:
            return rows[r - 1] if 1 <= r <= len(rows) else []

        idx_row = get_row(cfg.header_index_row)
        name_row = get_row(cfg.header_name_row)
        type_row = get_row(cfg.header_type_row)
        cmt_row = get_row(cfg.header_comment_row)

        max_len = max(len(name_row), len(type_row), len(cmt_row), len(idx_row))
        fields: List[FieldDef] = []
        for i in range(max_len):
            raw_name = (name_row[i] if i < len(name_row) else "") or ""
            raw_type = (type_row[i] if i < len(type_row) else "") or ""
            raw_cmt = (cmt_row[i] if i < len(cmt_row) else "") or None
            raw_idx = (idx_row[i] if i < len(idx_row) else None)

            name = str(raw_name).strip()
            type_spec = str(raw_type).strip()
            comment = str(raw_cmt).strip() if raw_cmt is not None else None
            try:
                index = int(raw_idx) if raw_idx not in (None, "") else None
            except Exception:
                index = None

            if not name:
                continue
            if not type_spec:
                type_spec = "string"  # 默认字符串
            fields.append(FieldDef(name=name, type_spec=type_spec, comment=comment, index=index))

        return TableSchema(title=title, fields=fields)

    def build_object_schema(self, table: TableSchema) -> Dict[str, Any]:
        # 使用第一列作为 key（通常为 id）
        if not table.fields:
            return {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": table.title,
                "type": "object",
                "additionalProperties": {"type": "object"},
            }

        key_field = table.fields[0]

        # 构建条目对象（不包含 key 字段本身）
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for f in table.fields[1:]:
            prop_schema, is_required = self._field_to_schema(f)
            prop_name = f.name.rstrip("?")
            properties[prop_name] = prop_schema
            if is_required:
                required.append(prop_name)

        item_schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            item_schema["required"] = required

        # 约束 key 形式：若 id 为整数类型，则使用数字键名（JSON 键为字符串，使用正则限制）
        key_type = key_field.type_spec.strip().lower().rstrip("?")
        property_names: Dict[str, Any] | None = None
        if key_type in {"int", "int32", "uint32", "int64", "integer"}:
            property_names = {"pattern": r"^\d+$"}

        schema: Dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": table.title,
            "type": "object",
            "additionalProperties": item_schema,
        }
        if property_names:
            schema["propertyNames"] = property_names

        return schema

    def _field_to_schema(self, field: FieldDef) -> (Dict[str, Any], bool):
        name = field.name
        type_spec = field.type_spec
        required = True

        # 可选标记
        if name.endswith("?"):
            required = False
        if type_spec.endswith("?"):
            required = False
            type_spec = type_spec[:-1]

        type_spec = type_spec.strip().lower()

        # # 数组类型
        # if type_spec.endswith("[]"):
        #     elem = type_spec[:-2]
        #     return {
        #         "type": "array",
        #         "items": self._primitive_type(elem)
        #     }, required

        # 原始类型
        return self._primitive_type(type_spec), required

    def _primitive_type(self, t: str) -> Dict[str, Any]:
        t = t.strip().lower()
        if t in {"int", "int32", "uint32", "integer"}:
            return {"type": "integer"}
        if t in {"float", "double", "number","fp32"}:
            return {"type": "number"}
        if t in {"bool", "boolean"}:
            return {"type": "boolean"}
        # if t in {"datetime", "date-time"}:
        #     return {"type": "string", "format": "date-time"}
        # if t in {"date"}:
        #     return {"type": "string", "format": "date"}
        # if t in {"time"}:
        #     return {"type": "string", "format": "time"}
        # 默认 string
        return {"type": "string"}


