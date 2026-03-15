#!/usr/bin/env python3
import winreg
import os

# 常见的微信安装路径
common_paths = [
    r"C:\Program Files\Tencent\WeChat\WeChat.exe",
    r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
    r"D:\Program Files\Tencent\WeChat\WeChat.exe",
    r"D:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
    r"E:\Program Files\Tencent\WeChat\WeChat.exe",
    r"E:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
]

# 检查常见路径
for path in common_paths:
    if os.path.exists(path):
        print(f"Found: {path}")
        break
else:
    print("WeChat not found in common paths")

# 检查注册表
try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat")
    install_path = winreg.QueryValueEx(key, "InstallPath")[0]
    wechat_exe = os.path.join(install_path, "WeChat.exe")
    if os.path.exists(wechat_exe):
        print(f"Registry: {wechat_exe}")
    winreg.CloseKey(key)
except:
    pass
