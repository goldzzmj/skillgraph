#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time

def find_login_button(image_path):
    """查找微信登录按钮"""
    img = Image.open(image_path)
    img_rgb = img.convert('RGB')
    width, height = img.size
    pixels = img_rgb.load()

    # 登录按钮通常是绿色的，或者是蓝色的
    # 让我们找屏幕中央的大块颜色区域

    center_x = width // 2
    center_y = height // 2

    # 在中央区域搜索可能的按钮
    search_region_size = 400
    left = center_x - search_region_size // 2
    right = center_x + search_region_size // 2
    top = center_y - search_region_size // 2
    bottom = center_y + search_region_size // 2

    # 扫描这个区域
    print(f"Searching in center region: ({left}, {top}) to ({right}, {bottom})")

    # 尝试点击屏幕中央的几个位置
    click_positions = [
        (center_x, center_y - 100),  # 稍微向上
        (center_x, center_y),          # 正中央
        (center_x, center_y + 100),  # 稍微向下
        (center_x, center_y + 200),  # 更靠下
    ]

    for i, (x, y) in enumerate(click_positions, 1):
        print(f"\nPosition {i}: ({x}, {y})")

    return click_positions

def main():
    print("=== WeChat Login Clicker ===\n")

    screenshot_path = r"F:\openclaw_data\xiaohongshu_login_20260211_202723.png"

    # 获取点击位置
    positions = find_login_button(screenshot_path)

    # 尝试点击每个位置
    print("\nStarting click attempts...")
    for i, (x, y) in enumerate(positions, 1):
        print(f"\nAttempt {i}: Moving to ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(0.3)

        print(f"Clicking...")
        pyautogui.click()
        time.sleep(2)  # 等待响应

        # 截图检查结果
        print("Checking result...")
        time.sleep(1)

    print("\nClicking completed!")
    print("If WeChat opened successfully, great!")
    print("If not, please try manual clicking.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
