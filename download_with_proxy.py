#!/usr/bin/env python3
import requests
import os

# 尝试使用系统代理
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

success_count = 0

for file in files:
    print(f"Downloading: {file['url']}")
    print(f"Saving to: {file['path']}")

    try:
        # 使用requests，它会自动检测系统代理
        response = requests.get(file['url'], timeout=60, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(file['path'], 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"  Progress: {downloaded}/{total_size} bytes ({percent:.1f}%)")

        actual_size = os.path.getsize(file['path'])
        print(f"[OK] Downloaded: {os.path.basename(file['path'])} ({actual_size} bytes)\n")
        success_count += 1

    except Exception as e:
        print(f"[FAILED] Error: {str(e)}\n")

print(f"\nSummary: {success_count}/{len(files)} files downloaded")
