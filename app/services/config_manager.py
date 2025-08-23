"""
配置管理器 - 管理 Sheet 的配置信息
"""
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path
from app.services.base import BaseService, ConfigNotFoundError
from app.services.transform.schema import SheetConfig, SheetSchema
from app.services.merge.rules import identify_group_and_sub


class ConfigManager(BaseService):
    """Sheet 配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        super().__init__("ConfigManager")
        self.configs: Dict[str, SheetConfig] = {}
        self.config_file = config_file or "sheet_configs.json"
        self.auto_discovery = True  # 是否自动发现配置
        
    def register_config(self, config: SheetConfig) -> None:
        """注册一个 Sheet 配置"""
        self.configs[config.sheet_name] = config
        self.log_info(f"注册配置: {config.sheet_name}")
    
    def register_from_dict(self, sheet_name: str, config_dict: Dict[str, Any]) -> SheetConfig:
        """从字典注册配置"""
        # 解析组名和子类型
        group_name, sub_type = identify_group_and_sub(sheet_name)
        
        # 构建 schema
        schema_dict = config_dict.get("schema", {})
        schema = SheetSchema(
            key_column=schema_dict.get("key_column", "ID"),
            type_mapping=schema_dict.get("type_hints", {}),  # 配置文件使用 type_hints，内部使用 type_mapping
            header_row=schema_dict.get("header_row", 1),
            data_start_row=schema_dict.get("data_start_row", 2),
            array_columns=schema_dict.get("array_columns", []),
            json_columns=schema_dict.get("json_columns", [])
        )
        
        # 创建配置
        config = SheetConfig(
            sheet_token=config_dict["sheet_token"],
            sheet_name=sheet_name,
            range_str=config_dict.get("range_str", ""),
            schema=schema,
            group_name=group_name,
            sub_type=sub_type
        )
        
        self.register_config(config)
        return config
    
    def get_config(self, sheet_name: str) -> Optional[SheetConfig]:
        """获取指定 Sheet 的配置"""
        config = self.configs.get(sheet_name)
        if not config and self.auto_discovery:
            # 如果配置不存在且启用了自动发现，尝试创建默认配置
            self.log_info(f"自动发现配置: {sheet_name}")
            config = self._create_default_config(sheet_name)
            if config:
                self.register_config(config)
        return config
    
    def get_config_required(self, sheet_name: str) -> SheetConfig:
        """获取配置，不存在则抛出异常"""
        config = self.get_config(sheet_name)
        if not config:
            raise ConfigNotFoundError(
                f"未找到 {sheet_name} 的配置",
                code="CONFIG_NOT_FOUND",
                details={"sheet_name": sheet_name}
            )
        return config
    
    def get_group_configs(self, group_name: str) -> List[SheetConfig]:
        """获取指定组的所有配置"""
        return [
            config for config in self.configs.values()
            if config.group_name == group_name
        ]
    
    def list_all_sheets(self) -> List[str]:
        """列出所有已配置的 Sheet"""
        return list(self.configs.keys())
    
    def list_all_groups(self) -> List[str]:
        """列出所有的组"""
        groups = set()
        for config in self.configs.values():
            if config.group_name:
                groups.add(config.group_name)
        return list(groups)
    
    def _create_default_config(self, sheet_name: str) -> Optional[SheetConfig]:
        """创建默认配置"""
        # 只有当 sheet token 已知时才能创建默认配置
        # 这里返回 None，实际使用时需要提供 sheet token
        return None
    
    def load_from_file(self, file_path: Optional[str] = None) -> None:
        """从文件加载配置"""
        path = file_path or self.config_file
        if not os.path.exists(path):
            self.log_warning(f"配置文件不存在: {path}")
            return
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载全局设置
            settings = data.get("settings", {})
            self.auto_discovery = settings.get("auto_discovery", True)
            
            # 加载 sheet 配置
            sheets = data.get("sheets", {})
            for sheet_name, config_dict in sheets.items():
                self.register_from_dict(sheet_name, config_dict)
                
            self.log_info(f"从 {path} 加载了 {len(sheets)} 个配置")
            
        except Exception as e:
            self.log_error(f"加载配置文件失败: {e}", error=e)
    
    def save_to_file(self, file_path: Optional[str] = None) -> None:
        """保存配置到文件"""
        path = file_path or self.config_file
        
        # 构建保存数据
        data = {
            "settings": {
                "auto_discovery": self.auto_discovery
            },
            "sheets": {}
        }
        
        for sheet_name, config in self.configs.items():
            data["sheets"][sheet_name] = {
                "sheet_token": config.sheet_token,
                "range_str": config.range_str,
                "schema": {
                    "key_column": config.schema.key_column,
                    "type_hints": config.schema.type_mapping,  # 使用正确的属性名
                    "array_columns": config.schema.array_columns,
                    "json_columns": config.schema.json_columns
                }
            }
        
        # 确保目录存在
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log_info(f"保存配置到 {path}")
        except Exception as e:
            self.log_error(f"保存配置文件失败: {e}", error=e)
    
    def create_from_sheet_list(self, sheets: List[Dict[str, Any]], default_token: str) -> None:
        """从 sheet 列表创建配置"""
        for sheet_info in sheets:
            sheet_name = sheet_info.get("name", "")
            sheet_token = sheet_info.get("sheet_token", default_token)
            
            if not sheet_name:
                continue
                
            # 跳过已存在的配置
            if sheet_name in self.configs:
                continue
            
            # 解析组名和子类型
            group_name, sub_type = identify_group_and_sub(sheet_name)
            
            # 创建默认 schema
            schema = SheetSchema(key_column="ID")
            
            # 创建配置
            config = SheetConfig(
                sheet_token=sheet_token,
                sheet_name=sheet_name,
                range_str="",  # 留空表示读取整个表
                schema=schema,
                group_name=group_name,
                sub_type=sub_type
            )
            
            self.register_config(config)
    
    def initialize_default_configs(self) -> None:
        """初始化默认示例配置"""
        # 示例配置
        example_configs = {
            "Config_Unit(hero)": {
                "sheet_token": "XUMasQlMYhOnMbt5htXc96h0nOg",
                "range_str": "",  # 读取整个表
                "schema": {
                    "key_column": "ID",
                    "type_hints": {
                        "ID": "int",
                        "Faction": "int",
                        "Gender": "int",
                        "Rarity": "int",
                        "DefaultMastery": "int",
                        "TroopClass": "int",
                        "FragmentItemId": "int"
                    },
                    "array_columns": ["Skills", "Talents"],
                    "json_columns": ["DuplicateRewardItemId"]
                }
            },
            "Config_Unit(soldier)": {
                "sheet_token": "XUMasQlMYhOnMbt5htXc96h0nOg",
                "range_str": "",
                "schema": {
                    "key_column": "ID",
                    "type_hints": {
                        "ID": "int",
                        "Level": "int",
                        "Attack": "int",
                        "Defense": "int",
                        "HP": "int"
                    },
                    "array_columns": ["Skills"],
                    "json_columns": []
                }
            },
            "Config_Skill": {
                "sheet_token": "XUMasQlMYhOnMbt5htXc96h0nOg",
                "range_str": "A1:Z1000",
                "schema": {
                    "key_column": "SkillID",
                    "type_hints": {
                        "SkillID": "int",
                        "Level": "int",
                        "CoolDown": "float",
                        "ManaCost": "int"
                    },
                    "array_columns": ["Effects"],
                    "json_columns": ["EffectParams"]
                }
            },
            "Config_Item": {
                "sheet_token": "XUMasQlMYhOnMbt5htXc96h0nOg", 
                "range_str": "",
                "schema": {
                    "key_column": "ItemID",
                    "type_hints": {
                        "ItemID": "int",
                        "ItemType": "int",
                        "Quality": "int",
                        "Price": "int",
                        "StackLimit": "int"
                    },
                    "array_columns": [],
                    "json_columns": ["Attributes", "Requirements"]
                }
            }
        }
        
        # 注册示例配置
        for sheet_name, config_dict in example_configs.items():
            try:
                self.register_from_dict(sheet_name, config_dict)
            except Exception as e:
                self.log_error(f"注册示例配置 {sheet_name} 失败: {e}", error=e)