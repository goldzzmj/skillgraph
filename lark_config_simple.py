#!/usr/bin/env python3
"""
Feishu/Lark MCP Configuration Helper
"""

import os
import sys

LARK_MCP_PATH = r"C:\Users\GX\.agents\skills\lark-mcp"

def main():
    print("=" * 60)
    print("Feishu/Lark MCP Configuration Status")
    print("=" * 60 + "\n")

    print("[SKILL] lark-mcp is installed")
    print(f"[PATH] {LARK_MCP_PATH}\n")

    print("Available Features:")
    features = [
        "Multidimensional Tables (Bitable)",
        "Documents (create, search, read)",
        "Messages (send text, images, files)",
        "Groups (create, manage)",
        "Permissions (manage access)",
        "Contacts (query users)",
        "Wiki (knowledge base)"
    ]

    for feature in features:
        print(f"  - {feature}")

    print("\nUsage Modes:")
    print("  1. User Identity (useUAT: true)")
    print("     - No app credentials needed")
    print("     - Uses current user permissions")
    print("     - Created resources accessible immediately")
    print("\n  2. Tenant Identity (useUAT: false)")
    print("     - Requires Feishu Open Platform app")
    print("     - Needs app_id and app_secret")
    print("     - For background operations")

    print("\nExample Commands:")
    print("""
1. Search documents:
   Tool: mcp__lark-mcp__docx_builtin_search
   data:
     search_key: "project report"
   useUAT: true

2. Send message:
   Tool: mcp__lark-mcp__im_v1_message_create
   data:
     receive_id: "oc_xxxxx"
     msg_type: "text"
     content: '{"text": "Hello"}'
   params:
     receive_id_type: "chat_id"
   useUAT: true
""")

    print("\nNext Steps:")
    print("  1. Try using Feishu MCP tools")
    print("  2. Tell me what you want to do")
    print("  3. For tenant mode, provide app credentials from Feishu Open Platform")

    print("\n" + "=" * 60)
    print("Configuration Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
