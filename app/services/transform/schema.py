"""
表格 Schema 和配置模型定义
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import re


@dataclass
class SheetSchema:
    """表格 Schema 定义，描述如何解析表格数据"""
    key_column: str  # 主键列名，如 "ID"
    headers: List[str] = field(default_factory=list)  # 列名列表，可选（自动从表头提取）
    header_row: int = 1  # 表头所在行（1-based）
    data_start_row: int = 2  # 数据开始行（1-based）
    type_mapping: Dict[str, str] = field(default_factory=dict)  # 列类型映射 {"ID": "int", "Name": "str"}
    array_columns: List[str] = field(default_factory=list)  # 数组类型的列
    json_columns: List[str] = field(default_factory=list)  # JSON 类型的列
    
    def get_type_for_column(self, column: str) -> str:
        """获取列的类型，默认为 str"""
        return self.type_mapping.get(column, "str")
    
    def validate(self) -> bool:
        """验证 Schema 是否有效"""
        if not self.key_column:
            return False
        if self.header_row < 1 or self.data_start_row < 1:
            return False
        if self.data_start_row <= self.header_row:
            return False
        return True


@dataclass
class SheetRange:
    """表格范围定义"""
    sheet_id: Optional[str] = None  # Sheet ID（可选）
    start_row: int = 1  # 起始行（1-based）
    end_row: Optional[int] = None  # 结束行（None 表示到最后）
    start_col: str = "A"  # 起始列
    end_col: Optional[str] = None  # 结束列（None 表示到最后）
    
    def to_a1_notation(self, sheet_name: Optional[str] = None) -> str:
        """
        转换为 A1 表示法
        
        Args:
            sheet_name: Sheet 名称
            
        Returns:
            A1 表示法字符串，如 "Sheet1!A1:Z100"
        """
        # 构建范围字符串
        range_str = f"{self.start_col}{self.start_row}"
        
        if self.end_col and self.end_row:
            range_str += f":{self.end_col}{self.end_row}"
        elif self.end_col:
            range_str += f":{self.end_col}"
        elif self.end_row:
            range_str += f":{self.start_col}{self.end_row}"
        
        # 添加 sheet 名称
        if sheet_name:
            # 如果 sheet 名称包含特殊字符，需要用单引号包裹
            if any(char in sheet_name for char in [' ', '!', '(', ')']):
                sheet_name = f"'{sheet_name}'"
            range_str = f"{sheet_name}!{range_str}"
        
        return range_str
    
    @classmethod
    def from_a1_notation(cls, a1_str: str) -> 'SheetRange':
        """从 A1 表示法创建 SheetRange"""
        # 分离 sheet 名称和范围
        sheet_name = None
        range_part = a1_str
        
        if '!' in a1_str:
            sheet_name, range_part = a1_str.split('!', 1)
            # 去除可能的引号
            sheet_name = sheet_name.strip("'")
        
        # 解析范围
        pattern = r'^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$'
        match = re.match(pattern, range_part)
        
        if not match:
            raise ValueError(f"无效的 A1 表示法: {a1_str}")
        
        start_col, start_row, end_col, end_row = match.groups()
        
        return cls(
            sheet_id=sheet_name,
            start_row=int(start_row),
            end_row=int(end_row) if end_row else None,
            start_col=start_col,
            end_col=end_col
        )


@dataclass
class SheetConfig:
    """表格配置，包含获取和解析表格所需的所有信息"""
    sheet_token: str  # 表格 token
    sheet_name: str  # Sheet 名称
    range_str: str  # 范围字符串，如 "A1:Z1000"
    schema: SheetSchema  # 表格 Schema
    group_name: Optional[str] = None  # 组名，如 "Config_Unit"
    sub_type: Optional[str] = None  # 子类型，如 "hero"、"soldier"
    ttl: int = 1800  # 缓存 TTL（秒），默认 30 分钟
    
    def get_full_range(self) -> str:
        """获取完整的范围字符串，包含 sheet 名称"""
        if '!' in self.range_str:
            return self.range_str
        return f"{self.sheet_name}!{self.range_str}"
