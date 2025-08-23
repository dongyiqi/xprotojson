"""
演示页面 API
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.services.dependencies import (
    StructuredServiceDep,
    ConfigManagerDep
)

router = APIRouter()


@router.get("/", response_class=HTMLResponse, summary="演示主页")
async def demo_page(
    request: Request,
    config_manager: ConfigManagerDep = None
) -> str:
    """
    返回演示页面的 HTML
    """
    sheets = config_manager.list_all_sheets()
    groups = config_manager.list_all_groups()
    
    # 构建示例 URL
    base_url = str(request.url).rstrip('/')
    api_base = base_url.replace('/demo', '/data')
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>飞书表格数据服务演示</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .api-section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .api-item {{
            margin: 15px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border: 1px solid #e9ecef;
        }}
        .method {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
        }}
        .get {{ background: #d4edda; color: #155724; }}
        .post {{ background: #d1ecf1; color: #0c5460; }}
        .delete {{ background: #f8d7da; color: #721c24; }}
        .url {{
            font-family: 'Monaco', 'Consolas', monospace;
            background: #f1f3f4;
            padding: 8px;
            border-radius: 4px;
            margin: 5px 0;
            word-break: break-all;
        }}
        .description {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        .config-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .config-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #e9ecef;
        }}
        .config-name {{
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }}
        .config-details {{
            font-size: 12px;
            color: #666;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-item {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            display: block;
        }}
        .try-button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 12px;
            margin-left: 10px;
        }}
        .try-button:hover {{
            background: #0056b3;
        }}
        .features {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .feature {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            text-align: center;
        }}
        .feature-icon {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 飞书表格数据服务演示</h1>
        
        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">{len(sheets)}</span>
                已配置表格
            </div>
            <div class="stat-item">
                <span class="stat-number">{len(groups)}</span>
                数据组
            </div>
            <div class="stat-item">
                <span class="stat-number">∞</span>
                懒加载缓存
            </div>
        </div>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">📊</div>
                <h3>智能数据转换</h3>
                <p>自动将飞书表格转换为结构化 JSON，支持类型推断和数组/JSON 列解析</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔄</div>
                <h3>懒加载缓存</h3>
                <p>首次请求时获取数据并缓存，后续请求直接返回缓存，支持强制刷新</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🔀</div>
                <h3>数据合并</h3>
                <p>自动识别并合并相关表格（如英雄+士兵），支持多种冲突策略</p>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <h3>高性能 API</h3>
                <p>基于 FastAPI + Redis，支持异步处理和分布式缓存</p>
            </div>
        </div>

        <div class="api-section">
            <h2>📡 数据接口</h2>
            
            <div class="api-item">
                <span class="method get">GET</span>
                <strong>获取表格数据</strong>
                <div class="url">{api_base}/sheets/{{sheet_name}}?force_refresh=false</div>
                <div class="description">获取单个表格的结构化数据，支持懒加载和缓存</div>
                {"".join([f'<a href="{api_base}/sheets/{sheet}?force_refresh=false" class="try-button" target="_blank">试试 {sheet}</a>' for sheet in sheets[:3]])}
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span>
                <strong>获取组合并数据</strong>
                <div class="url">{api_base}/groups/{{group_name}}?force_refresh=false</div>
                <div class="description">获取组的合并数据，自动合并同组下的所有表格</div>
                {"".join([f'<a href="{api_base}/groups/{group}" class="try-button" target="_blank">试试 {group}</a>' for group in groups[:3]])}
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span>
                <strong>获取配置信息</strong>
                <div class="url">{api_base}/configs</div>
                <div class="description">查看所有已配置的表格和组信息</div>
                <a href="{api_base}/configs" class="try-button" target="_blank">查看配置</a>
            </div>
            
            <div class="api-item">
                <span class="method get">GET</span>
                <strong>缓存统计</strong>
                <div class="url">{api_base}/cache/stats</div>
                <div class="description">查看缓存使用统计信息</div>
                <a href="{api_base}/cache/stats" class="try-button" target="_blank">查看统计</a>
            </div>
            
            <div class="api-item">
                <span class="method post">POST</span>
                <strong>刷新表格</strong>
                <div class="url">{api_base}/sheets/{{sheet_name}}/refresh</div>
                <div class="description">强制刷新指定表格的缓存数据</div>
            </div>
            
            <div class="api-item">
                <span class="method delete">DELETE</span>
                <strong>清理缓存</strong>
                <div class="url">{api_base}/cache?pattern=xpj:*</div>
                <div class="description">清理缓存数据，支持模式匹配</div>
            </div>
        </div>

        <div class="api-section">
            <h2>📋 已配置表格</h2>
            <div class="config-list">
"""
    
    # 添加配置表格信息
    for sheet_name in sheets:
        config = config_manager.get_config(sheet_name)
        if config:
            html_content += f"""
                <div class="config-item">
                    <div class="config-name">{sheet_name}</div>
                    <div class="config-details">
                        组: {config.group_name or 'None'} | 
                        子类型: {config.sub_type or 'None'} | 
                        主键: {config.schema.key_column}
                    </div>
                    <a href="{api_base}/sheets/{sheet_name}" class="try-button" target="_blank">获取数据</a>
                </div>
"""
    
    html_content += """
            </div>
        </div>

        <div class="api-section">
            <h2>🔧 API 文档</h2>
            <p>
                完整的 API 文档请访问：
                <a href="/docs" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold;">Swagger UI</a>
                或 
                <a href="/redoc" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold;">ReDoc</a>
            </p>
        </div>

        <div class="api-section">
            <h2>💡 使用说明</h2>
            <ol>
                <li><strong>懒加载</strong>：首次请求表格数据时，系统会从飞书获取并缓存，后续请求直接返回缓存</li>
                <li><strong>强制刷新</strong>：添加 <code>?force_refresh=true</code> 参数可以强制重新获取最新数据</li>
                <li><strong>数据合并</strong>：同组表格（如 Config_Unit(hero) 和 Config_Unit(soldier)）会自动合并</li>
                <li><strong>类型转换</strong>：根据配置自动进行类型转换（int, float, bool, array, json）</li>
                <li><strong>缓存管理</strong>：可以查看缓存统计和清理缓存数据</li>
            </ol>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content


@router.get("/api-docs", summary="API 使用说明")
async def api_docs() -> Dict[str, Any]:
    """
    返回 API 使用说明
    """
    return {
        "title": "飞书表格数据服务 API",
        "version": "1.0.0",
        "description": "基于懒加载和缓存的飞书表格数据服务",
        "features": [
            "智能数据转换：自动将表格数据转换为结构化 JSON",
            "懒加载缓存：首次请求时获取并缓存，提高响应速度",
            "数据合并：支持同组表格的自动合并",
            "类型推断：支持 int, float, bool, array, json 类型",
            "缓存管理：提供缓存统计和清理功能"
        ],
        "endpoints": {
            "GET /api/v1/data/sheets/{sheet_name}": "获取表格数据",
            "GET /api/v1/data/groups/{group_name}": "获取组合并数据",
            "GET /api/v1/data/configs": "获取配置信息",
            "GET /api/v1/data/cache/stats": "获取缓存统计",
            "POST /api/v1/data/sheets/{sheet_name}/refresh": "刷新表格",
            "DELETE /api/v1/data/cache": "清理缓存"
        },
        "examples": {
            "获取英雄数据": "/api/v1/data/sheets/Config_Unit(hero)",
            "获取单位组数据": "/api/v1/data/groups/Config_Unit",
            "强制刷新": "/api/v1/data/sheets/Config_Skill?force_refresh=true"
        }
    }
