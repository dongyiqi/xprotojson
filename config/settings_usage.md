# Settings 配置使用说明

## 概述

已将 ConfigManager 移除，统一使用 `core/config.py` 中的 Settings 来管理所有配置。

## 文件夹配置

### 环境变量配置

```bash
# 设置默认文件夹
export XPJ_FOLDERS__DEFAULT=fldcnVaJ6ltyVOJOHXtl6Ug6nOc

# 设置配置文件夹
export XPJ_FOLDERS__CONFIG=fldcnVaJ6ltyVOJOHXtl6Ug6nOc

# 设置测试文件夹
export XPJ_FOLDERS__TEST=fldcnVaJ6ltyVOJOHXtl6Ug6nOc
```

### 代码中使用

```python
from app.core.config import settings

# 获取默认文件夹 token
default_folder = settings.folders.default

# 获取配置文件夹 token
config_folder = settings.folders.config

# 获取测试文件夹 token
test_folder = settings.folders.test
```

## 其他配置

### Feishu 配置
```bash
export XPJ_FEISHU__AUTH__APP_ID=your_app_id
export XPJ_FEISHU__AUTH__APP_SECRET=your_app_secret
```

### Redis 配置
```bash
export XPJ_REDIS__URL=redis://localhost:6379/0
```

### 表格解析配置
```bash
export XPJ_TABLE__DEFAULT_KEY_COLUMN=ID
export XPJ_TABLE__DATA_START_ROW=4
```

## 优势

1. **统一管理**：所有配置集中在 settings 中
2. **环境变量支持**：支持环境变量和 .env 文件
3. **类型验证**：Pydantic 自动类型检查
4. **文档化**：每个配置都有描述
5. **无需文件**：不需要额外的 JSON 配置文件

## 迁移说明

- **旧方式**：`config_manager.get_folder_token("default")`
- **新方式**：`settings.folders.default`

配置更简单，类型更安全！
