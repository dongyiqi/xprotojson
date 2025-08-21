from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class TablesConfig:
    header_index_row: int = 1
    header_name_row: int = 2
    header_type_row: int = 3
    header_comment_row: int = 4
    data_start_row: int = 5

    @staticmethod
    def from_yaml(path: str | None) -> "TablesConfig":
        if not path:
            # 默认路径：相对当前包，回到 ../configs/xpj.feishu.yaml
            base = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(base, "configs", "xpj.feishu.yaml")
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}
        tables = data.get("tables", {}) or {}
        return TablesConfig(
            header_index_row=int(tables.get("header_index_row", 1)),
            header_name_row=int(tables.get("header_name_row", 2)),
            header_type_row=int(tables.get("header_type_row", 3)),
            header_comment_row=int(tables.get("header_comment_row", 4)),
            data_start_row=int(tables.get("data_start_row", 5)),
        )


