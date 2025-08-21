# 飞书Sheets API 迁移到 lark-oapi SDK

## 概述

`feishu_sheets.py` 已从纯 HTTP 调用迁移到使用官方 `lark-oapi` SDK，提供更好的稳定性、错误处理和维护性。

## 安装依赖

```bash
pip install lark-oapi
# 或者使用 requirements.txt
pip install -r requirements.txt
```

## 向后兼容性

✅ **完全向后兼容** - 现有代码无需修改即可继续工作。

### 旧的使用方式（仍然支持）
```python
from core.feishu_sheets import FeishuSheets

# 使用配置文件中的认证信息
client = FeishuSheets()
```

### 新的推荐方式
```python
from core.feishu_sheets import FeishuSheets

# 直接提供认证信息（推荐）
client = FeishuSheets(
    app_id="your_app_id",
    app_secret="your_app_secret"
)
```

## 主要改进

### 1. 使用官方 SDK
- 🔧 基于飞书官方 `lark-oapi` SDK
- 🛡️ 更稳定的错误处理和重试机制
- 📚 完整的类型提示和文档支持

### 2. 更好的错误处理
- 🚫 精确的错误分类（认证、权限、资源不存在等）
- 🔄 智能重试策略（只对可重试的错误进行重试）
- 📝 详细的错误日志和调试信息

### 3. 性能优化
- ⚡ SDK 内置连接池和请求优化
- 🎯 更精确的速率限制控制
- 📊 更好的请求监控和统计

## API 接口保持不变

所有公共方法的签名和返回格式完全保持一致：

```python
# 工作表查询
result = client.list_sheets(spreadsheet_token, page_size=200)

# 工作表详情
sheet_info = client.get_sheet(spreadsheet_token, sheet_id)

# 读取数据
rows = client.read_values(spreadsheet_token, "Sheet1!A1:Z100")

# 写入数据
response = client.update_values(spreadsheet_token, "Sheet1!A1:B3", values)

# 批量写入
response = client.batch_update_values(spreadsheet_token, ranges_data)
```

## 配置认证信息

### 方式1: 环境变量（推荐）
```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
```

### 方式2: 代码中直接指定
```python
client = FeishuSheets(
    app_id="your_app_id", 
    app_secret="your_app_secret"
)
```

### 方式3: 配置文件（向后兼容）
保持原有的 `configs/xpj.feishu.yaml` 配置文件格式不变。

## 运行测试

```bash
cd domino-framework/com.domino.xprotojson/python/test
python test.py
```

测试套件会自动检测可用的认证方式并选择最合适的初始化方法。

## 故障排除

### 1. 导入错误
如果遇到 `lark_oapi` 导入错误：
```bash
pip install lark-oapi>=1.0.0
```

### 2. 认证失败
- 确认 `app_id` 和 `app_secret` 正确
- 确认应用有相应的权限范围
- 检查网络连接和防火墙设置

### 3. 降级支持
如果 `lark-oapi` 不可用，系统会自动降级到传统的 HTTP 方式（需要保留 `feishu_auth.py`）。

## 迁移优势总结

| 特性 | 旧实现 | 新实现 |
|------|--------|--------|
| HTTP 处理 | 手动 requests | 官方 SDK |
| 错误处理 | 基础处理 | 精确分类 |
| 重试策略 | 简单退避 | 智能重试 |
| 类型安全 | 部分支持 | 完整支持 |
| 维护性 | 需要手动更新 | SDK 自动更新 |
| 文档支持 | 自维护 | 官方文档 |

## 相关链接

- [飞书开放平台 - lark-oapi SDK](https://open.feishu.cn/document/server-docs/getting-started/sdk-quick-start)
- [lark-oapi Python SDK 文档](https://github.com/larksuite/oapi-sdk-python)
