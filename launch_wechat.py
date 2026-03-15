#!/usr/bin/env python3
import subprocess
import os

# 只搜索用户目录
print("Searching for WeChat.exe in user directories...")
result = subprocess.run(
    ['powershell', '-Command',
     'Get-ChildItem -Path $env:USERPROFILE -Recurse -Filter "WeChat.exe" -ErrorAction SilentlyContinue | Select-Object FullName -First 3'],
    capture_output=True, text=True, timeout=30
)

if result.stdout and "FullName" in result.stdout:
    print("Found WeChat.exe:")
    print(result.stdout)

    # 提取路径并启动
    lines = result.stdout.split('\n')
    for line in lines:
        if "C:\\" in line and ".exe" in line:
            path = line.split('-')[0].strip()
            print(f"\nLaunching: {path}")
            os.startfile(path)
            break
else:
    print("WeChat.exe not found in user directories")
    print("\nTrying URI scheme launch...")
    os.system("start weixin://")
