#!/usr/bin/env python3
import subprocess
import os

# 搜索微信.exe文件
print("Searching for WeChat.exe...")
result = subprocess.run(
    ['powershell', '-Command',
     'Get-ChildItem -Path C:\\,D:\\,E:\\ -Recurse -Filter "WeChat.exe" -ErrorAction SilentlyContinue | Select-Object FullName -First 5'],
    capture_output=True, text=True, timeout=60
)

if result.stdout:
    print(result.stdout)
else:
    print("WeChat.exe not found on C, D, E drives")

# 尝试通过快捷方式启动
print("\nTrying to launch via WeChat shortcut...")
subprocess.run(['powershell', '-Command',
                '(New-Object -ComObject WScript.Shell).Run("weixin://")'],
                capture_output=True)
