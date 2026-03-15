#!/usr/bin/env python3
"""
飞书（Feishu/Lark）MCP 配置助手
检查配置文件并提供配置指南
"""

import os
import json

LARK_MCP_PATH = r"C:\Users\GX\.agents\skills\lark-mcp"

def check_config_files():
    """检查配置文件"""
    print("=" * 60)
    print("检查飞书 MCP 配置文件...")
    print("=" * 60 + "\n")

    config_files = [
        "config.json",
        "settings.json",
        "lark-mcp.json",
        "mcp.json",
        ".env",
        "config.toml",
        "lark.toml"
    ]

    found_configs = []
    for filename in config_files:
        filepath = os.path.join(LARK_MCP_PATH, filename)
        if os.path.exists(filepath):
            found_configs.append(filepath)
            print(f"✅ 找到: {filename}")

            # 尝试读取内容
            try:
                if filename.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"   内容预览: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"   内容预览: {content[:200]}...")
            except Exception as e:
                print(f"   读取失败: {e}")

    if not found_configs:
        print("❌ 未找到配置文件")
    else:
        print(f"\n总共找到 {len(found_configs)} 个配置文件")

    return found_configs

def print_setup_guide():
    """打印配置指南"""
    print("\n" + "=" * 60)
    print("飞书 MCP 配置指南")
    print("=" * 60 + "\n")

    print("## 方式1: 使用用户身份（推荐，无需应用凭证）\n")

    print("飞书 MCP 支持用户身份操作（useUAT: true）")
    print("这种方式：")
    print("  ✅ 不需要飞书开放平台创建应用")
    print("  ✅ 不需要配置 app_id 和 app_secret")
    print("  ✅ 直接使用当前用户权限")
    print("  ✅ 创建的资源可以立即访问")

    print("\n## 方式2: 使用租户身份（需要开放平台应用）\n")

    print("如果需要更多权限或后台操作：")
    print("  1. 访问飞书开放平台：https://open.feishu.cn")
    print("  2. 创建应用并获取：")
    print("     - App ID")
    print("     - App Secret")
    print("  3. 配置环境变量或配置文件")

    print("\n## 可用的功能\n")

    features = [
        ("多维表格 (Bitable)", "创建、查询、更新、删除表格和数据"),
        ("文档 (Documents)", "搜索、创建、获取内容"),
        ("消息 (Messages)", "发送文本、图片、文件消息"),
        ("群组 (Groups)", "创建群组、管理成员"),
        ("权限 (Permissions)", "管理文档和表格访问权限"),
        ("联系人 (Contacts)", "查询用户信息"),
        ("Wiki (知识库)", "搜索和管理知识库内容")
    ]

    for feature, description in features:
        print(f"  • {feature:<20} - {description}")

    print("\n## 使用示例\n")

    print("""
1. 搜索文档：
   工具: mcp__lark-mcp__docx_builtin_search
   data:
     search_key: "项目报告"

2. 发送消息：
   工具: mcp__lark-mcp__im_v1_message_create
   data:
     receive_id: "oc_xxxxx"
     msg_type: "text"
     content: '{"text": "消息内容"}'
   params:
     receive_id_type: "chat_id"
   useUAT: true

3. 查询多维表格：
   工具: mcp__lark-mcp__bitable_v1_appTableRecord_search
   path:
     app_token: "bascnxxxxx"
     table_id: "tblxxxxx"
   params:
     page_size: 20
   data:
     filter:
       conjunction: "and"
       conditions:
         - field_name: "状态"
           operator: "is"
           value: ["已完成"]
   useUAT: true
""")

def main():
    """主函数"""
    check_config_files()
    print_setup_guide()

    print("\n" + "=" * 60)
    print("配置状态：")
    print("=" * 60)
    print("\n✅ 技能已安装：lark-mcp")
    print("✅ 技能路径：C:\\Users\\GX\\.agents\\skills\\lark-mcp")
    print("✅ 推荐方式：使用用户身份 (useUAT: true)")
    print("\n📝 下一步：")
    print("   1. 使用示例命令测试飞书功能")
    print("   2. 告诉我你想执行的具体操作")
    print("   3. 如需租户身份，请提供飞书开放平台应用凭证")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
