#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import subprocess
import time
import os

def find_wechat_icons(image_path):
    """查找所有可能的微信图标位置"""
    img = Image.open(image_path)
    img_rgb = img.convert('RGB')
    width, height = img.size
    pixels = img_rgb.load()

    # 微信的典型绿色 (RGB: 7, 193, 96)
    WECHAT_GREEN = (7, 193, 96)
    TOLERANCE = 25

    green_positions = []
    for y in range(0, height, 10):  # 步长10
        for x in range(0, width, 10):
            r, g, b = pixels[x, y]

            if (abs(r - WECHAT_GREEN[0]) < TOLERANCE and
                abs(g - WECHAT_GREEN[1]) < TOLERANCE and
                abs(b - WECHAT_GREEN[2]) < TOLERANCE):
                green_positions.append((x, y))

    return green_positions

def try_launch_wechat():
    """尝试通过多种方式启动微信"""
    print("Trying to launch WeChat...")

    # 方法1: 通过注册表快捷方式
    try:
        os.system("start weixin://")
        print("Attempt 1: weixin:// protocol - executed")
        time.sleep(2)
    except:
        pass

    # 方法2: 通过桌面快捷方式
    try:
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        for filename in os.listdir(desktop):
            if 'wechat' in filename.lower() or '微信' in filename.lower():
                if filename.endswith('.lnk'):
                    shortcut_path = os.path.join(desktop, filename)
                    os.startfile(shortcut_path)
                    print(f"Attempt 2: Desktop shortcut {filename} - executed")
                    time.sleep(2)
                    break
    except:
        pass

    # 方法3: 通过开始菜单
    try:
        start_menu = os.path.join(os.environ['APPDATA'],
                                'Microsoft', 'Windows', 'Start Menu', 'Programs')
        if os.path.exists(start_menu):
            for filename in os.listdir(start_menu):
                if 'wechat' in filename.lower() or '微信' in filename.lower():
                    shortcut_path = os.path.join(start_menu, filename)
                    os.startfile(shortcut_path)
                    print(f"Attempt 3: Start menu {filename} - executed")
                    time.sleep(2)
                    break
    except:
        pass

def main():
    print("=== Smart WeChat Launcher ===\n")

    screenshot_path = r"F:\openclaw_data\xiaohongshu_login_20260211_202456.png"

    # 先尝试启动微信
    try_launch_wechat()

    # 等待微信启动
    time.sleep(3)

    # 截新图
    print("\nTaking new screenshot...")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_screenshot = f"F:\\openclaw_data\\wechat_check_{timestamp}.png"

    # 使用pyautogui截图
    screenshot = pyautogui.screenshot()
    screenshot.save(new_screenshot)
    print(f"Screenshot saved: {new_screenshot}")

    # 查找微信图标
    print("\nSearching for WeChat icons...")
    positions = find_wechat_icons(new_screenshot)

    if len(positions) > 0:
        print(f"Found {len(positions)} possible positions")

        # 计算最佳位置（按区域聚类）
        # 简单方法：找左上角的图标
        positions.sort(key=lambda p: p[0] + p[1])

        # 尝试点击前3个位置
        for i, (x, y) in enumerate(positions[:3], 1):
            print(f"\nAttempt {i}: Clicking at ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.3)
            pyautogui.click()
            time.sleep(1)

        print("\nClicking completed!")
    else:
        print("No WeChat icons found")
        print("WeChat may already be running")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
