### 项目简介

一个围绕飞书 Lark Sheets 的工具与服务集合：
- **核心库**：最小可用的 `FeishuClient`，基于 `lark-oapi` 实现鉴权、Drive 列表、Sheets 读范围值等；
- **JSON Schema 生成**：从飞书表格表头约定解析出 JSON Schema，并将数据区按 Schema 规范化为对象集合；
- **Manifest 构建**：扫描指定 Drive 文件夹下的文件，生成用于差异化比对的 `manifest.json`；
- **FastAPI 服务**：提供基础 API（示例健康检查），可扩展为对外的自动化/智能化接口。

### 目录结构

```
app/                # FastAPI 应用（/api/v1）
  api/v1/endpoints/ # 示例：健康检查
  main.py           # 入口
python/             # Python 核心库
  core/feishu_client.py         # 飞书客户端封装
  json_schema/feishu_service.py # 从表头生成 JSON Schema & 读取数据
  json_schema/manifest_service.py# 生成 manifest.json
  configs/xpj.feishu.yaml       # 运行所需配置（可从环境变量注入）
sample/             # 示例与附加资源
```

### 快速开始

1) 安装依赖（建议 Python 3.10+）

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
pip install -r python/requirements.txt
```

2) 配置凭证（任选其一）

- 环境变量：

```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
```

- 或编辑文件 `python/configs/xpj.feishu.yaml`：

```yaml
auth:
  app_id: "your_app_id"
  app_secret: "your_app_secret"
```

3) 启动服务

```bash
uvicorn app.main:app --reload
# 浏览器访问： http://127.0.0.1:8000/api/v1/health
```

### 库用法示例

确保将项目根目录加入 `PYTHONPATH`：

```bash
export PYTHONPATH=$PWD:$PYTHONPATH
```

读取表头生成 JSON Schema，并按约定读取数据：

```python
from python.core.feishu_client import FeishuClient
from python.json_schema.feishu_service import FeishuSchemaService

client = FeishuClient()
svc = FeishuSchemaService(client)

schema = svc.build_schema_for_spreadsheet(
    spreadsheet_token="your_spreadsheet_token",
    sheet_id="your_sheet_id",
)

items = svc.build_items_for_sheet(
    spreadsheet_token="your_spreadsheet_token",
    sheet_id="your_sheet_id",
)
print(schema)
print(items)
```

构建某个 Drive 文件夹的清单 `manifest.json`：

```python
from python.core.feishu_client import FeishuClient
from python.json_schema.manifest_service import ManifestService

client = FeishuClient()
manifest = ManifestService(client, output_dir="./out").build_manifest_for_folder(
    folder_token="your_folder_token"
)
print(manifest)
```

### Roadmap（后续计划）

- JSON ↔ 飞书表格互转
  - 从 JSON/JSON Schema 生成飞书表格（字段、类型、注释）
  - 从飞书表格批量导出/更新 JSON（含类型、可选项校验）
- 提供 MCP/AI Agent 服务
  - 基于 FastAPI 封装为 MCP 兼容服务，暴露“表格读取/写入、Schema 生成、清单同步”等能力
  - 集成 Agent（如函数调用/工具插件）驱动飞书数据读写与校验
- 增强的配置与缓存
  - 支持多环境与多租户配置；磁盘/Redis 缓存 Schema 与数据片段
- 任务编排与增量同步
  - 根据 `manifest.json` 做差异比对与增量同步；支持定时/回调触发
- Web UI
  - 提供简单的可视化来预览 Schema、数据与同步计划

### 许可

可自由用于学习与内部项目，生产使用前请完善鉴权、审计与异常处理。

