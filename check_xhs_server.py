#!/usr/bin/env python3
import requests
import time

def check_server():
    """检查小红书MCP服务器状态"""
    url = "http://localhost:18060/api/v1/login/status"

    try:
        print(f"Connecting to {url}...")
        response = requests.get(url, timeout=30)
        print(f"Status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")

            login_info = data.get("data", {})
            if login_info.get("is_logged_in"):
                print(f"\n[OK] Logged in as: {login_info.get('username', 'Unknown')}")
                return True
            else:
                print("\n[NOT LOGGED IN] Please login via xiaohongshu-login tool")
                return False
        else:
            print(f"\n[ERROR] Server returned: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to server at localhost:18060")
        print("Make sure xiaohongshu-mcp is running")
        return False
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Xiaohongshu MCP Server Check ===\n")
    check_server()
