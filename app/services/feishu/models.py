"""
飞书相关数据模型
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class FileInfo:
    """文件信息模型"""
    token: str  # 文件 token
    name: str  # 文件名
    type: str  # 文件类型 (sheet, doc, folder 等)
    parent_token: str  # 父文件夹 token
    created_time: datetime  # 创建时间
    modified_time: datetime  # 修改时间
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'FileInfo':
        """从飞书 API 响应创建实例"""
        return cls(
            token=data.get("token", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            parent_token=data.get("parent_token", ""),
            created_time=datetime.fromtimestamp(data.get("created_time", 0)),
            modified_time=datetime.fromtimestamp(data.get("modified_time", 0))
        )
    
    def is_sheet(self) -> bool:
        """判断是否为表格文件"""
        return self.type.lower() in ["sheet", "spreadsheet", "bitable"]


@dataclass
class SheetMeta:
    """表格元数据模型"""
    sheet_id: str  # Sheet ID
    sheet_name: str  # Sheet 名称
    revision: int  # 版本号
    last_modified: datetime  # 最后修改时间
    dimensions: Dict[str, int]  # 维度信息 {"rows": 100, "cols": 26}
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'SheetMeta':
        """从飞书 API 响应创建实例"""
        sheet_info = data.get("sheet", {})
        properties = sheet_info.get("properties", {})
        
        return cls(
            sheet_id=sheet_info.get("sheet_id", ""),
            sheet_name=properties.get("title", ""),
            revision=data.get("revision", 0),
            last_modified=datetime.now(),  # 飞书 API 可能不返回此字段
            dimensions={
                "rows": properties.get("row_count", 0),
                "cols": properties.get("column_count", 0)
            }
        )


@dataclass
class SheetValueRange:
    """表格值范围"""
    range: str  # 范围字符串，如 "A1:Z100"
    major_dimension: str  # 主要维度 ROWS/COLUMNS
    values: List[List[Any]]  # 二维数组数据
    revision: int  # 数据版本号
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'SheetValueRange':
        """从飞书 API 响应创建实例"""
        value_range = data.get("valueRange", {})
        
        return cls(
            range=value_range.get("range", ""),
            major_dimension=value_range.get("majorDimension", "ROWS"),
            values=value_range.get("values", []),
            revision=value_range.get("revision", data.get("revision", 0))
        )
    
    def is_empty(self) -> bool:
        """判断数据是否为空"""
        return not self.values or all(not row for row in self.values)
    
    def get_row_count(self) -> int:
        """获取行数"""
        return len(self.values)
    
    def get_col_count(self) -> int:
        """获取列数"""
        if not self.values:
            return 0
        return max(len(row) for row in self.values)


@dataclass 
class DriveListResponse:
    """Drive 文件列表响应"""
    files: List[FileInfo]
    has_more: bool
    next_page_token: Optional[str]
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'DriveListResponse':
        """从飞书 API 响应创建实例"""
        files = []
        for file_data in data.get("files", []):
            files.append(FileInfo.from_api_response(file_data))
        
        return cls(
            files=files,
            has_more=data.get("has_more", False),
            next_page_token=data.get("next_page_token")
        )
