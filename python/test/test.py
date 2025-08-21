import os
import sys
import time
import json
import logging
from typing import Dict, Any, List

# 允许在 test 目录下直接运行：python test.py
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.feishu_client import FeishuClient
from json_schema import FeishuSchemaService, TablesConfig
import lark_oapi as lark
from lark_oapi.api.sheets.v3 import (
    QuerySpreadsheetSheetRequest,
    QuerySpreadsheetSheetResponse,
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class FeishuSheetsTestSuite:
    """飞书表格API最小测试套件（仅测试 v3 列表工作表）"""
    
    def __init__(self, spreadsheet_token: str, app_id: str = None, app_secret: str = None):
        self.spreadsheet_token = spreadsheet_token
        
        # 最小依赖：直接使用 FeishuClient
        self.client = FeishuClient(app_id=app_id, app_secret=app_secret)
            
        self.test_sheet_id = None
        
    def run_all_tests(self):
        """运行所有测试用例"""
        print("=" * 60)
        print("飞书Sheets API 完整测试套件")
        print("=" * 60)
        
        try:
            # 0. 测试获取目录文件列表（Drive v1）
            #self.test_list_drive_files()
            
            # 1. 测试工作表查询功能（v3）
            # self.test_list_sheets()
            # 2. 读取首个工作表前四行（若 SDK 支持）
            #self.test_read_first_four_rows()
            # 3. 基于表头生成 JSON Schema
            #self.test_build_json_schema()
            # 4. 为整个 workbook 生成所有 sheet 的 JSON Schema 并聚合
            self.test_build_workbook_schema()
            # 5. 生成当前 sheet 的数据条目（以第一列 id 作为 key）
            self.test_build_items_for_sheet()
            
            # 其余接口暂不测试（最小依赖）
            
            
            print("\n" + "=" * 60)
            print("✅ 所有测试完成!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            raise
    
    def test_list_drive_files(self):
        """测试获取指定目录下的文件列表（单页）。"""
        print("\n📁 测试目录文件列表...")
        try:
            folder_token = "HXU6fGxVNl1THgdh5wMcjRSznHd"
            data = self.client.list_drive_files(folder_token=folder_token, page_size=20)
            try:
                # 原生对象用 lark 的 JSON 工具打印
                print(lark.JSON.marshal(data, indent=2))
            except Exception:
                # 如果是 dict
                print(json.dumps(data if isinstance(data, dict) else {}, ensure_ascii=False, indent=2))
            print("✅ 目录文件列表获取成功")
        except NotImplementedError as nie:
            print(f"⚠️  SDK 不支持 Drive v1 列表API，已跳过：{nie}")
        except Exception as e:
            print(f"❌ 目录文件列表获取失败: {e}")
            raise
    
    def test_list_sheets(self):
        """测试工作表列表查询"""
        print("\n📋 测试工作表列表查询...")
        try:
            # 使用 client 的封装接口
            response = self.client.list_sheets(self.spreadsheet_token)

            # 直接打印原生数据结构
            try:
                print(lark.JSON.marshal(response.data, indent=2))
            except Exception:
                pass

            sheets = response.data.sheets or []
            print(f"   - 工作表数量: {len(sheets)}")
            if len(sheets) > 0:
                self.test_sheet_id = sheets[0].sheet_id
                print(f"   - 第一个工作表: {sheets[0].title}")
                print(f"   - Sheet ID: {self.test_sheet_id}")
                
        except Exception as e:
            print(f"❌ 工作表列表查询失败: {e}")
            raise

    def test_read_first_four_rows(self):
        """读取首个工作表的前四行（A1:Z4），使用 lark SDK。若不支持则跳过。"""
        print("\n📖 读取首个工作表前四行...")
        try:
            if not self.test_sheet_id:
                print("⚠️  未找到有效的 sheet_id，跳过读取")
                return
            # 使用 sheet_id 而非标题，避免 90215 not found sheetId 错误
            range_a1 = f"{self.test_sheet_id}!A1:Z4"
            rows = self.client.read_range_values(self.spreadsheet_token, range_a1)
            print(f"✅ 成功读取，行数={len(rows)}")
            for r in rows[:4]:
                print(r)
        except NotImplementedError as nie:
            print(f"⚠️  SDK 不支持读取值API（v2 valueRange），已跳过：{nie}")
        except Exception as e:
            print(f"❌ 读取前四行失败: {e}")
            raise

    def test_build_json_schema(self):
        """基于首个工作表头部行生成 JSON Schema。"""
        print("\n🧩 生成 JSON Schema...")
        try:
            if not self.test_sheet_id:
                print("⚠️  未找到有效的 sheet_id，跳过生成 JSON Schema")
                return
            cfg = TablesConfig.from_yaml(None)
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cache/schema"))
            svc = FeishuSchemaService(self.client, cfg, cache_dir=cache_dir)
            schema = svc.build_schema_for_spreadsheet(self.spreadsheet_token, self.test_sheet_id, header_max_col="Z")
            print(json.dumps(schema, ensure_ascii=False, indent=2))
            # 磁盘缓存验证
            cached = svc.get_cached_schema(self.spreadsheet_token)
            if cached:
                print("✅ 发现缓存的 JSON Schema（磁盘缓存验证成功）")
        except Exception as e:
            print(f"❌ 生成 JSON Schema 失败: {e}")
            raise

    def test_build_workbook_schema(self):
        """为整个 workbook 生成所有 sheet 的 JSON Schema 并聚合。"""
        print("\n📚 生成 Workbook 级 JSON Schema 聚合...")
        try:
            cfg = TablesConfig.from_yaml(None)
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cache/schema"))
            svc = FeishuSchemaService(self.client, cfg, cache_dir=cache_dir)
            result = svc.build_schema_for_workbook(self.spreadsheet_token, header_max_col="Z")
            print(f"✅ 聚合完成：sheet_count={result.get('sheet_count')}\n")
            sheets = result.get("sheets", [])
            for s in sheets[:2]:
                print(f"   - sheet: {s.get('title')} ({s.get('sheet_id')})")
        except Exception as e:
            print(f"❌ 生成 Workbook 级 JSON Schema 失败: {e}")
            raise

    def test_build_items_for_sheet(self):
        """将当前 sheet 的数据转为 items（key 为第一列 id）。"""
        print("\n🧾 生成当前 Sheet 的数据 items...")
        try:
            if not self.test_sheet_id:
                # 若未显式查询 list_sheets，则尝试查询一次以获取首个 sheet_id
                resp = self.client.list_sheets(self.spreadsheet_token)
                sheets = resp.data.sheets or []
                if sheets:
                    self.test_sheet_id = sheets[0].sheet_id
            if not self.test_sheet_id:
                print("⚠️  未找到有效的 sheet_id，跳过 items 生成")
                return
            cfg = TablesConfig.from_yaml(None)
            svc = FeishuSchemaService(self.client, cfg)
            items = svc.build_items_for_sheet(self.spreadsheet_token, self.test_sheet_id, header_max_col="Z")
            print(f"✅ items 数量: {len(items)}")
            # 打印前 2 条
            cnt = 0
            for k, v in items.items():
                print(f"   - {k}: {v}")
                cnt += 1
                if cnt >= 2:
                    break
        except Exception as e:
            print(f"❌ 生成 items 失败: {e}")
            raise

def demo_list_sheets(spreadsheet_token: str, app_id: str = None, app_secret: str = None) -> None:
    client = FeishuClient(app_id=app_id, app_secret=app_secret)
    data = client.list_sheets(spreadsheet_token)
    print("data keys:", list(data.keys()) if isinstance(data, dict) else type(data))


def demo_write(*args, **kwargs):
    print("写入演示已停用（最小依赖模式）")


if __name__ == "__main__":
    # 使用前请设置环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET
    # 或在 configs/xpj.feishu.yaml 内配置
    test_spreadsheet_token = "EWbhsZrIdhdEzdtvaIDcI2E5nIe"

    # 自动读取环境变量（或配置文件）并直接运行最小测试套件
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    print("=" * 60)
    print("飞书Sheets API 测试工具 - 自动模式")
    print("=" * 60)
    if app_id and app_secret:
        print(f"✅ 检测到环境变量中的认证信息 (APP_ID: {app_id[:8]}***)")
    else:
        print("ℹ️  将尝试使用配置文件中的认证信息")

    # 直接运行测试
    suite = FeishuSheetsTestSuite(test_spreadsheet_token, app_id, app_secret)
    suite.run_all_tests()


