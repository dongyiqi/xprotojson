# Sheet 配置说明

本目录包含飞书表格的配置文件，用于定义如何解析和转换表格数据。

## 配置文件结构

```json
{
  "settings": {
    "auto_discovery": true,    // 是否自动发现新表格
    "cache_ttl": 3600,        // 缓存过期时间（秒）
    "default_key_column": "ID" // 默认主键列名
  },
  "sheets": {
    "表格名称": {
      "sheet_token": "飞书表格的 token",
      "range_str": "A1:Z100",  // 读取范围（空字符串表示整个表）
      "schema": {
        "key_column": "ID",    // 主键列名
        "type_hints": {        // 列类型定义
          "ID": "int",
          "Name": "str",
          "Level": "float",
          "IsActive": "bool"
        },
        "array_columns": ["Skills", "Tags"],      // 数组类型的列
        "json_columns": ["Attributes", "Config"]  // JSON 类型的列
      }
    }
  },
  "merge_rules": {
    "组名": {
      "conflict_strategy": "first_win", // 冲突策略: first_win, last_win, merge_fields
      "priority_order": ["hero", "soldier"], // 子类型优先级
      "merge_mode": "by_subtype"  // 合并模式
    }
  }
}
```

## 类型定义

### 基本类型
- `int`: 整数
- `float`: 浮点数
- `bool`: 布尔值
- `str`: 字符串（默认）

### 特殊类型
- `array_columns`: 数组类型的列，支持以下格式：
  - JSON 数组: `[1, 2, 3]`
  - 逗号分隔: `1,2,3`
  - 分号分隔: `1;2;3`
  
- `json_columns`: JSON 类型的列，支持：
  - 标准 JSON: `{"key": "value"}`
  - 简单键值对: `key:value, key2:value2`

## 表格命名规则

系统会自动识别表格的组名和子类型：

- `Config_Unit(hero)` → 组名: Config_Unit, 子类型: hero
- `Config_Unit(soldier)` → 组名: Config_Unit, 子类型: soldier
- `Config_Skill_magic` → 组名: Config_Skill, 子类型: magic
- `Config_Event[daily]` → 组名: Config_Event, 子类型: daily
- `Config_Item` → 组名: Config_Item, 子类型: None

## 合并规则

当多个表格属于同一组时，系统会根据合并规则进行处理：

### 冲突策略
- `first_win`: 保留第一个出现的数据
- `last_win`: 后面的数据覆盖前面的
- `merge_fields`: 字段级合并（数组会合并去重）

### 优先级
定义子类型的优先级顺序，用于解决跨子类型的主键冲突。

## 使用示例

1. 复制 `sheet_configs_example.json` 为 `sheet_configs.json`
2. 修改其中的 `sheet_token` 为实际的飞书表格 token
3. 根据实际表格结构调整 schema 定义
4. 启动服务后，配置会自动加载

## 注意事项

1. 主键列的值必须唯一
2. 表头默认在第一行，数据从第二行开始
3. 空单元格会被解析为 `null`
4. 类型转换失败时会保留原始字符串值
