from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


class MemoryCache:
    def __init__(self, ttl_seconds: Optional[float] = None) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._meta: Dict[str, Dict[str, float]] = {}
        self._ttl = ttl_seconds

    def _now(self) -> float:
        return time.time()

    def _expired(self, category: str, key: str) -> bool:
        if self._ttl is None:
            return False
        ts = self._meta.get(category, {}).get(key)
        if ts is None:
            return False
        return (self._now() - ts) > self._ttl

    def has_json(self, category: str, key: str) -> bool:
        if category not in self._store:
            return False
        if key not in self._store[category]:
            return False
        if self._expired(category, key):
            self.invalidate(category, key)
            return False
        return True

    def read_json(self, category: str, key: str) -> Dict[str, Any]:
        if not self.has_json(category, key):
            raise KeyError(f"memory cache miss: {category}:{key}")
        return self._store[category][key]

    def write_json(self, category: str, key: str, data: Dict[str, Any]) -> None:
        self._store.setdefault(category, {})[key] = data
        if self._ttl is not None:
            self._meta.setdefault(category, {})[key] = self._now()

    def invalidate(self, category: str, key: str) -> None:
        if category in self._store and key in self._store[category]:
            del self._store[category][key]
        if category in self._meta and key in self._meta[category]:
            del self._meta[category][key]


class DiskCache:
    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _safe_key(self, key: str) -> str:
        return key.replace("/", "_")

    def _path(self, category: str, key: str) -> str:
        cat_dir = os.path.join(self.cache_dir, category)
        os.makedirs(cat_dir, exist_ok=True)
        return os.path.join(cat_dir, f"{self._safe_key(key)}.json")

    def has_json(self, category: str, key: str) -> bool:
        return os.path.isfile(self._path(category, key))

    def read_json(self, category: str, key: str) -> Dict[str, Any]:
        with open(self._path(category, key), "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, category: str, key: str, data: Dict[str, Any]) -> None:
        with open(self._path(category, key), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # schema/manifest 便捷方法
    def has_schema(self, spreadsheet_token: str) -> bool:
        return self.has_json("schema", spreadsheet_token)

    def read_schema(self, spreadsheet_token: str) -> Dict[str, Any]:
        return self.read_json("schema", spreadsheet_token)

    def write_schema(self, spreadsheet_token: str, schema: Dict[str, Any]) -> None:
        self.write_json("schema", spreadsheet_token, schema)


class LayeredCache:
    def __init__(self, memory: MemoryCache, disk: DiskCache | None = None) -> None:
        self.mem = memory
        self.disk = disk

    def has_json(self, category: str, key: str) -> bool:
        if self.mem.has_json(category, key):
            return True
        if self.disk and self.disk.has_json(category, key):
            data = self.disk.read_json(category, key)
            self.mem.write_json(category, key, data)
            return True
        return False

    def read_json(self, category: str, key: str) -> Dict[str, Any]:
        if self.mem.has_json(category, key):
            return self.mem.read_json(category, key)
        if self.disk and self.disk.has_json(category, key):
            data = self.disk.read_json(category, key)
            self.mem.write_json(category, key, data)
            return data
        raise KeyError(f"cache miss: {category}:{key}")

    def write_json(self, category: str, key: str, data: Dict[str, Any]) -> None:
        self.mem.write_json(category, key, data)
        if self.disk:
            self.disk.write_json(category, key, data)

    # schema/manifest 便捷方法
    def write_schema(self, spreadsheet_token: str, schema: Dict[str, Any]) -> None:
        self.write_json("schema", spreadsheet_token, schema)

    def read_schema(self, spreadsheet_token: str) -> Dict[str, Any]:
        return self.read_json("schema", spreadsheet_token)

    def has_schema(self, spreadsheet_token: str) -> bool:
        return self.has_json("schema", spreadsheet_token)

    def write_manifest(self, folder_token: str, manifest: Dict[str, Any]) -> None:
        self.write_json("manifest", folder_token, manifest)

    def read_manifest(self, folder_token: str) -> Dict[str, Any]:
        return self.read_json("manifest", folder_token)

    def has_manifest(self, folder_token: str) -> bool:
        return self.has_json("manifest", folder_token)


