from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from core.feishu_client import FeishuClient


class ManifestService:
    """
    负责同步目标目录（Drive folder）下所有 workbook（file）及其 sheet（spreadsheets）的信息，生成 manifest。
    - manifest.json 提供差异化比对基础。
    """

    def __init__(self, client: FeishuClient, output_dir: str) -> None:
        self.client = client
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def build_manifest_for_folder(self, folder_token: str, manifest_name: str = "manifest.json") -> Dict[str, Any]:
        # 列表第一页
        page_token: str | None = None
        files: List[Dict[str, Any]] = []

        while True:
            data = self.client.list_drive_files(
                folder_token=folder_token,
                page_size=50,
                page_token=page_token,
                order_by="EditedTime",
                direction="DESC",
            )
            # lark response.data 可能是对象，尽量兼容 dict 访问
            items = []
            if isinstance(data, dict):
                items = data.get("files") or data.get("list") or []
                page_token = data.get("page_token") or None
                has_more = data.get("has_more") or False
            else:
                # 假设为 SDK 对象：data.files, data.next_page_token, data.has_more
                items = getattr(data, "files", []) or getattr(data, "list", []) or []
                page_token = getattr(data, "page_token", None)
                has_more = getattr(data, "has_more", False)

            for it in items:
                # 直接记录完整条目，尽量保留信息以用于差异化比对
                if isinstance(it, dict):
                    files.append(it)
                else:
                    # 将对象转为 dict（简化：仅取常见字段）
                    files.append({
                        "token": getattr(it, "token", None),
                        "name": getattr(it, "name", None),
                        "type": getattr(it, "type", None),
                        "url": getattr(it, "url", None),
                        "parent_token": getattr(it, "parent_token", None),
                        "owner_id": getattr(it, "owner_id", None),
                        "create_time": getattr(it, "create_time", None),
                        "edit_time": getattr(it, "edit_time", None),
                    })

            if not has_more or not page_token:
                break

        manifest = {
            "folder_token": folder_token,
            "file_count": len(files),
            "files": files,
        }

        out_path = os.path.join(self.output_dir, manifest_name)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        return manifest


