#!/usr/bin/env python3
import urllib.request
import ssl
import os

# 禁用SSL验证（如果需要）
ssl_context = ssl._create_unverified_context()

files = [
    {
        "url": "https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-windows-amd64.exe",
        "path": r"C:\Users\GX\xiaohongshu-mcp\xiaohongshu-mcp-windows-amd64.exe"
    },
    {
        "url": "https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-windows-amd64.exe",
        "path": r"C:\Users\GX\xiaohongshu-mcp\xiaohongshu-login-windows-amd64.exe"
    }
]

for file in files:
    print(f"正在下载: {file['url']}")
    print(f"保存到: {file['path']}")

    try:
        # 使用代理（如果需要）
        # proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
        # opener = urllib.request.build_opener(proxy_handler)
        opener = urllib.request.build_opener()

        request = urllib.request.Request(file['url'])
        request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        response = opener.open(request, timeout=60)

        with open(file['path'], 'wb') as f:
            f.write(response.read())

        print(f"[OK] Downloaded: {os.path.basename(file['path'])}\n")
    except Exception as e:
        print(f"[FAILED] Error: {str(e)}\n")
