#!/usr/bin/env python3
import pyautogui
import time

print("Testing mouse control...")
print(f"Screen size: {pyautogui.size()}")
print(f"Current position: {pyautogui.position()}")

# 移动鼠标到屏幕中心
x, y = pyautogui.size()
center_x, center_y = x // 2, y // 2

print(f"Moving to center: ({center_x}, {center_y})")
pyautogui.moveTo(center_x, center_y, duration=1)
time.sleep(0.5)

print(f"Current position: {pyautogui.position()}")

# 点击一次
print("Clicking...")
pyautogui.click()

print("Test completed!")
