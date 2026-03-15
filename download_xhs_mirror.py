#!/usr/bin/env python3
import urllib.request
import os

# 尝试多个镜像源
mirrors = [
    "",  # 原始GitHub
    "https://mirror.ghproxy.com/",
    "https://ghproxy.com/",
    "https://ghproxy.net/",
]

base_url = "https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/"
files = [
    "xiaohongshu-mcp-windows-amd64.exe",
    "xiaohongshu-login-windows-amd64.exe"
]

success_count = 0

for file in files:
    downloaded = False
    for mirror in mirrors:
        if mirror:
            url = mirror + base_url + file
        else:
            url = base_url + file

        print(f"Trying mirror: {mirror or 'GitHub original'}")
        print(f"URL: {url}")

        try:
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            response = urllib.request.urlopen(request, timeout=30)

            path = rf"C:\Users\GX\xiaohongshu-mcp\{file}"
            with open(path, 'wb') as f:
                f.write(response.read())

            size = os.path.getsize(path)
            print(f"[OK] Downloaded: {file} ({size} bytes)\n")
            downloaded = True
            success_count += 1
            break
        except Exception as e:
            print(f"[FAILED] {str(e)}\n")
            continue

    if not downloaded:
        print(f"[ERROR] Could not download {file} from any mirror\n")

print(f"\nSummary: {success_count}/{len(files)} files downloaded")
