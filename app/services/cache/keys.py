"""
缓存键生成规则
"""
import hashlib
from typing import Optional


class CacheKeys:
    """缓存键生成器"""
    
    # 键前缀
    PREFIX = "xpj"
    
    # 键模板
    STRUCTURED_DATA = "{prefix}:sheet:structured:{sheet_token}:{sheet_name}:{range_hash}"
    MERGED_DATA = "{prefix}:sheet:merged:{group_name}:{range_hash}"
    FOLDER_FILES = "{prefix}:folder:files:{folder_token}"
    SHEET_META = "{prefix}:sheet:meta:{sheet_token}"
    SHEET_SCHEMA = "{prefix}:sheet:schema:{sheet_token}:{sheet_name}"
    SHEET_SCHEMA_BY_NAME = "{prefix}:sheet:schema:{sheet_name}"
    SHEET_ROW = "{prefix}:sheet:row:{sheet_token}:{sheet_name}:{row_key}"
    ROW_CFGID = "{prefix}:cfgid:{row_key}"
    
    @classmethod
    def structured_key(
        cls,
        sheet_token: str,
        sheet_name: str,
        range_str: Optional[str] = None
    ) -> str:
        """
        生成结构化数据缓存键
        
        Args:
            sheet_token: 表格 token
            sheet_name: Sheet 名称
            range_str: 范围字符串
            
        Returns:
            缓存键
        """
        range_hash = cls._hash_range(range_str) if range_str else "full"
        return cls.STRUCTURED_DATA.format(
            prefix=cls.PREFIX,
            sheet_token=sheet_token,
            sheet_name=sheet_name,
            range_hash=range_hash
        )
    
    @classmethod
    def merged_key(
        cls,
        group_name: str,
        range_str: Optional[str] = None
    ) -> str:
        """
        生成合并数据缓存键
        
        Args:
            group_name: 组名
            range_str: 范围字符串
            
        Returns:
            缓存键
        """
        range_hash = cls._hash_range(range_str) if range_str else "full"
        return cls.MERGED_DATA.format(
            prefix=cls.PREFIX,
            group_name=group_name,
            range_hash=range_hash
        )
    
    @classmethod
    def folder_files_key(cls, folder_token: str) -> str:
        """生成文件夹文件列表缓存键"""
        return cls.FOLDER_FILES.format(
            prefix=cls.PREFIX,
            folder_token=folder_token
        )
    
    @classmethod
    def sheet_meta_key(cls, sheet_token: str) -> str:
        """生成表格元数据缓存键"""
        return cls.SHEET_META.format(
            prefix=cls.PREFIX,
            sheet_token=sheet_token
        )
    
    @classmethod
    def sheet_schema_key(cls, sheet_token: str, sheet_name: str) -> str:
        """生成表格 schema 的缓存键"""
        return cls.SHEET_SCHEMA.format(
            prefix=cls.PREFIX,
            sheet_token=sheet_token,
            sheet_name=sheet_name
        )
    
    @classmethod
    def sheet_row_key(cls, sheet_token: str, sheet_name: str, row_key: str) -> str:
        """生成单行数据缓存键"""
        return cls.SHEET_ROW.format(
            prefix=cls.PREFIX,
            sheet_token=sheet_token,
            sheet_name=sheet_name,
            row_key=row_key
        )

    @classmethod
    def row_cfgid_key(cls, row_key: str) -> str:
        """生成基于全局唯一 cfgid 的行键"""
        return cls.ROW_CFGID.format(
            prefix=cls.PREFIX,
            row_key=row_key
        )

    @classmethod
    def sheet_schema_by_name_key(cls, sheet_name: str) -> str:
        """仅基于 sheet 名称的 schema 键（便于跨 workbook 复用/合并）"""
        return cls.SHEET_SCHEMA_BY_NAME.format(
            prefix=cls.PREFIX,
            sheet_name=sheet_name
        )
    
    @staticmethod
    def _hash_range(range_str: str) -> str:
        """对范围字符串进行哈希，生成短键"""
        return hashlib.md5(range_str.encode()).hexdigest()[:8]
