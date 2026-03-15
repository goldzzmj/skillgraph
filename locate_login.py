#!/usr/bin/env python3
import pyautogui
import time

print("=== Login Button Locator ===")
print(f"Screen size: {pyautogui.size()}")
print("\nInstructions:")
print("1. Move your mouse to the WeChat login button")
print("2. Press Ctrl+C in this terminal after 5 seconds...")
print("   The script will record the mouse position")
print("\nCounting down...")

for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

# 记录鼠标位置
pos = pyautogui.position()
print(f"\nLogin button position: ({pos.x}, {pos.y})")
print("This position has been saved for clicking.")

# 保存位置到文件
with open(r"F:\openclaw_data\login_position.txt", "w") as f:
    f.write(f"{pos.x},{pos.y}")

print("Position saved to: F:\\openclaw_data\\login_position.txt")
print("\nYou can now run 'click_login.py' to click this position.")
