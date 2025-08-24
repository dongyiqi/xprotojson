# """
# 简化演示端点 - 不依赖 Redis
# """
# from typing import Dict, Any
# from fastapi import APIRouter
# from fastapi.responses import HTMLResponse
# from app.services.dependencies import ConfigManagerDep

# router = APIRouter()


# @router.get("/simple", response_class=HTMLResponse, summary="简化演示页面")
# async def simple_demo(config_manager: ConfigManagerDep = None) -> str:
#     """
#     简化的演示页面，不依赖 Redis 缓存
#     """
#     sheets = config_manager.list_all_sheets()
#     groups = config_manager.list_all_groups()
    
#     html_content = f"""
# <!DOCTYPE html>
# <html lang="zh-CN">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>飞书表格数据服务 - 简化演示</title>
#     <style>
#         body {{
#             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
#             line-height: 1.6;
#             margin: 0;
#             padding: 20px;
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             min-height: 100vh;
#         }}
#         .container {{
#             max-width: 1000px;
#             margin: 0 auto;
#             background: white;
#             padding: 40px;
#             border-radius: 15px;
#             box-shadow: 0 10px 30px rgba(0,0,0,0.3);
#         }}
#         h1 {{
#             color: #333;
#             text-align: center;
#             font-size: 2.5em;
#             margin-bottom: 10px;
#         }}
#         .subtitle {{
#             text-align: center;
#             color: #666;
#             font-size: 1.1em;
#             margin-bottom: 40px;
#         }}
#         .stats {{
#             display: grid;
#             grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
#             gap: 20px;
#             margin: 30px 0;
#         }}
#         .stat-card {{
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             padding: 30px;
#             border-radius: 10px;
#             text-align: center;
#             box-shadow: 0 5px 15px rgba(0,0,0,0.2);
#         }}
#         .stat-number {{
#             font-size: 3em;
#             font-weight: bold;
#             display: block;
#         }}
#         .stat-label {{
#             font-size: 1.1em;
#             margin-top: 10px;
#         }}
#         .features {{
#             display: grid;
#             grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
#             gap: 25px;
#             margin: 40px 0;
#         }}
#         .feature-card {{
#             background: #f8f9fa;
#             padding: 25px;
#             border-radius: 10px;
#             border-left: 5px solid #667eea;
#             box-shadow: 0 3px 10px rgba(0,0,0,0.1);
#         }}
#         .feature-icon {{
#             font-size: 2.5em;
#             margin-bottom: 15px;
#         }}
#         .feature-title {{
#             font-size: 1.3em;
#             font-weight: bold;
#             color: #333;
#             margin-bottom: 10px;
#         }}
#         .feature-desc {{
#             color: #666;
#             line-height: 1.5;
#         }}
#         .config-section {{
#             margin: 40px 0;
#             padding: 30px;
#             background: #f8f9fa;
#             border-radius: 10px;
#         }}
#         .config-grid {{
#             display: grid;
#             grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
#             gap: 20px;
#             margin-top: 20px;
#         }}
#         .config-card {{
#             background: white;
#             padding: 20px;
#             border-radius: 8px;
#             border: 1px solid #e9ecef;
#             box-shadow: 0 2px 5px rgba(0,0,0,0.05);
#         }}
#         .config-name {{
#             font-weight: bold;
#             color: #667eea;
#             font-size: 1.1em;
#             margin-bottom: 8px;
#         }}
#         .config-info {{
#             color: #666;
#             font-size: 0.9em;
#         }}
#         .api-section {{
#             margin: 40px 0;
#             padding: 30px;
#             background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
#             color: white;
#             border-radius: 10px;
#         }}
#         .api-list {{
#             margin-top: 20px;
#         }}
#         .api-item {{
#             background: rgba(255,255,255,0.1);
#             padding: 15px;
#             margin: 10px 0;
#             border-radius: 8px;
#             font-family: 'Monaco', 'Consolas', monospace;
#         }}
#         .note {{
#             background: #fff3cd;
#             border: 1px solid #ffeaa7;
#             border-radius: 8px;
#             padding: 20px;
#             margin: 30px 0;
#             color: #856404;
#         }}
#         .note-title {{
#             font-weight: bold;
#             margin-bottom: 10px;
#         }}
#     </style>
# </head>
# <body>
#     <div class="container">
#         <h1>🚀 飞书表格数据服务</h1>
#         <div class="subtitle">基于 FastAPI + 飞书 API 的智能数据服务平台</div>
        
#         <div class="stats">
#             <div class="stat-card">
#                 <span class="stat-number">{len(sheets)}</span>
#                 <div class="stat-label">已配置表格</div>
#             </div>
#             <div class="stat-card">
#                 <span class="stat-number">{len(groups)}</span>
#                 <div class="stat-label">数据组</div>
#             </div>
#             <div class="stat-card">
#                 <span class="stat-number">∞</span>
#                 <div class="stat-label">无限扩展</div>
#             </div>
#         </div>
        
#         <div class="features">
#             <div class="feature-card">
#                 <div class="feature-icon">📊</div>
#                 <div class="feature-title">智能数据转换</div>
#                 <div class="feature-desc">
#                     自动将飞书表格转换为结构化 JSON，支持类型推断、数组解析和 JSON 字段处理
#                 </div>
#             </div>
#             <div class="feature-card">
#                 <div class="feature-icon">🔄</div>
#                 <div class="feature-title">懒加载缓存</div>
#                 <div class="feature-desc">
#                     首次请求时获取数据并缓存，后续请求直接返回缓存，支持强制刷新和 TTL 管理
#                 </div>
#             </div>
#             <div class="feature-card">
#                 <div class="feature-icon">🔀</div>
#                 <div class="feature-title">智能数据合并</div>
#                 <div class="feature-desc">
#                     自动识别并合并相关表格（如英雄+士兵），支持多种冲突策略和优先级设置
#                 </div>
#             </div>
#             <div class="feature-card">
#                 <div class="feature-icon">⚡</div>
#                 <div class="feature-title">高性能 API</div>
#                 <div class="feature-desc">
#                     基于 FastAPI + Redis 构建，支持异步处理、依赖注入和分布式缓存
#                 </div>
#             </div>
#         </div>
        
#         <div class="config-section">
#             <h2>📋 系统配置</h2>
#             <div class="config-grid">
# """

#     # 添加配置信息
#     for sheet_name in sheets:
#         config = config_manager.get_config(sheet_name)
#         if config:
#             html_content += f"""
#                 <div class="config-card">
#                     <div class="config-name">{sheet_name}</div>
#                     <div class="config-info">
#                         组: {config.group_name or 'None'}<br>
#                         子类型: {config.sub_type or 'None'}<br>
#                         主键: {config.schema.key_column}<br>
#                         缓存 TTL: {config.ttl}s
#                     </div>
#                 </div>
# """

#     html_content += f"""
#             </div>
#         </div>
        
#         <div class="api-section">
#             <h2>🛠 API 端点</h2>
#             <div class="api-list">
#                 <div class="api-item">GET /api/v1/data/configs - 获取配置信息</div>
#                 <div class="api-item">GET /api/v1/data/sheets/{{sheet_name}} - 获取表格数据</div>
#                 <div class="api-item">GET /api/v1/data/groups/{{group_name}} - 获取组合并数据</div>
#                 <div class="api-item">GET /api/v1/data/cache/stats - 获取缓存统计</div>
#                 <div class="api-item">POST /api/v1/data/sheets/{{sheet_name}}/refresh - 刷新表格</div>
#                 <div class="api-item">DELETE /api/v1/data/cache - 清理缓存</div>
#             </div>
#         </div>
        
#         <div class="note">
#             <div class="note-title">📝 注意事项</div>
#             <ul>
#                 <li>当前演示环境未启动 Redis，数据接口可能无法正常工作</li>
#                 <li>完整功能需要配置有效的飞书应用凭证和 Redis 服务</li>
#                 <li>支持的数据类型：int, float, bool, str, array, json</li>
#                 <li>表格命名格式：Config_Name(subtype) 或 Config_Name[subtype]</li>
#             </ul>
#         </div>
        
#         <div style="text-align: center; margin-top: 40px; color: #666;">
#             <p>🔗 API 文档: <a href="/docs" style="color: #667eea;">Swagger UI</a> | <a href="/redoc" style="color: #667eea;">ReDoc</a></p>
#             <p>📖 完整演示: <a href="/api/v1/demo/" style="color: #667eea;">功能演示页面</a></p>
#         </div>
#     </div>
# </body>
# </html>
# """
    
#     return html_content


# @router.get("/status", summary="系统状态")
# async def system_status(config_manager: ConfigManagerDep = None) -> Dict[str, Any]:
#     """
#     获取系统状态信息
#     """
#     sheets = config_manager.list_all_sheets()
#     groups = config_manager.list_all_groups()
    
#     return {
#         "service": "飞书表格数据服务",
#         "version": "1.0.0",
#         "status": "运行中",
#         "features": {
#             "智能数据转换": "✅ 正常",
#             "配置管理": "✅ 正常", 
#             "懒加载缓存": "⚠️ 需要 Redis",
#             "数据合并": "✅ 正常",
#             "API 接口": "✅ 正常"
#         },
#         "statistics": {
#             "configured_sheets": len(sheets),
#             "configured_groups": len(groups),
#             "supported_types": ["int", "float", "bool", "str", "array", "json"],
#             "cache_modes": ["Redis", "Memory (fallback)"]
#         },
#         "endpoints": {
#             "健康检查": "/api/v1/health",
#             "配置信息": "/api/v1/data/configs",
#             "演示页面": "/api/v1/demo/simple",
#             "API 文档": "/docs"
#         }
#     }
