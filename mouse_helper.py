#!/usr/bin/env python3
import pyautogui
import time

def click_login_button():
    """帮助点击微信登录按钮"""
    print("Mouse Helper - Click Helper")
    print("=" * 40)

    # 获取当前鼠标位置
    current_pos = pyautogui.position()
    print(f"Current mouse position: {current_pos}")

    # 常见的微信登录按钮位置（需要根据实际调整）
    # 通常在屏幕中央或左上角
    print("\nClicking login button...")
    print("Please wait...")

    # 尝试点击常见的登录按钮位置
    # 这些坐标可能需要根据实际屏幕分辨率调整
    # 屏幕中央
    screen_width, screen_height = pyautogui.size()
    center_x, center_y = screen_width // 2, screen_height // 2

    # 尝试点击几个可能的位置
    click_positions = [
        (center_x, center_y),  # 屏幕中央
        (center_x - 200, center_y),  # 偏左
        (center_x + 200, center_y),  # 偏右
        (400, 300),  # 固定位置（可能需要调整）
    ]

    for i, (x, y) in enumerate(click_positions, 1):
        print(f"\nAttempt {i}: Clicking at ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(1)  # 等待1秒

    print("\nClick attempts completed!")
    print(f"Screen size: {screen_width}x{screen_height}")

if __name__ == "__main__":
    # 禁用故障保护（可选）
    # pyautogui.FAILSAFE = False

    try:
        click_login_button()
    except Exception as e:
        print(f"Error: {e}")
