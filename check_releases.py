#!/usr/bin/env python3
import requests
import json

try:
    # 获取最新release信息
    url = "https://api.github.com/repos/xpzouying/xiaohongshu-mcp/releases/latest"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    release = response.json()

    print("Latest Release Info:")
    print(f"Tag: {release.get('tag_name')}")
    print(f"Name: {release.get('name')}")
    print(f"Published: {release.get('published_at')}")
    print("\nAssets:")

    assets = release.get('assets', [])
    for asset in assets:
        print(f"  - {asset.get('name')}")
        print(f"    URL: {asset.get('browser_download_url')}")
        print(f"    Size: {asset.get('size')} bytes")
        print()

except Exception as e:
    print(f"Error: {str(e)}")
