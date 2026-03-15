#!/usr/bin/env python3
import pyautogui
import time

# 读取保存的登录按钮位置
try:
    with open(r"F:\openclaw_data\login_position.txt", "r") as f:
        pos_str = f.read().strip()
        x, y = map(int, pos_str.split(','))
except:
    print("No saved position found!")
    print("Please run 'locate_login.py' first to set the login button position.")
    exit(1)

print(f"=== Clicking Login Button ===")
print(f"Target position: ({x}, {y})")
print(f"Screen size: {pyautogui.size()}")
print("\nMoving mouse to login button...")

# 移动鼠标到目标位置
pyautogui.moveTo(x, y, duration=1)
time.sleep(0.5)

print("Clicking...")
pyautogui.click()

print("\nDone!")
