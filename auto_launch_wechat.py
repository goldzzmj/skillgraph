#!/usr/bin/env python3
"""
自动打开桌面微信并点击登录
"""

import pyautogui
import time
import os
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw

OUTPUT_DIR = r"F:\openclaw_data"
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

def screenshot_and_mark(x, y, radius=80, label=""):
    """截图并标记位置"""
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    draw = ImageDraw.Draw(img_rgb)
    draw.ellipse([x-radius, y-radius//2, x+radius, y+radius//2],
                outline='red', width=5)
    if label:
        draw.text((x-radius, y-radius-40), label, fill='red')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{timestamp}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    img_rgb.save(filepath)
    print(f"[SCREENSHOT] Saved: {filename}")
    return filepath

def find_wechat_icon():
    """查找桌面上的微信图标"""
    print("\n[STEP 1] Finding WeChat icon on Desktop...")

    # 截取桌面区域（屏幕左侧通常是图标所在区域）
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    width, height = screenshot.size
    pixels = img_rgb.load()

    # 微信图标通常是绿色的
    WECHAT_GREEN = (7, 193, 96)
    TOLERANCE = 30

    green_positions = []

    # 在屏幕左侧区域搜索（桌面图标通常在左侧）
    for y in range(0, height):
        for x in range(0, width // 3):  # 只搜索屏幕左侧1/3
            r, g, b = pixels[x, y]
            if (abs(r - WECHAT_GREEN[0]) < TOLERANCE and
                abs(g - WECHAT_GREEN[1]) < TOLERANCE and
                abs(b - WECHAT_GREEN[2]) < TOLERANCE):
                green_positions.append((x, y))

    if green_positions:
        # 找到最左上角的绿色图标
        min_pos = min(green_positions, key=lambda p: p[0] + p[1] * 10)
        avg_x = min_pos[0]
        avg_y = min_pos[1]

        print(f"[OK] Found WeChat icon at: ({avg_x}, {avg_y})")
        screenshot_and_mark(avg_x, avg_y, 100, "WeChat_Icon")
        return avg_x, avg_y
    else:
        print("[NOT FOUND] WeChat icon not found, trying default position")
        # 默认位置：图标通常在桌面左上角区域
        return 300, 300

def double_click_wechat(x, y):
    """双击微信图标"""
    print(f"\n[STEP 2] Double clicking WeChat icon at: ({x}, {y})")

    # 移动鼠标到图标
    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(0.3)

    # 双击打开
    pyautogui.doubleClick()
    time.sleep(0.5)

    print("[OK] Double clicked WeChat icon")

def wait_for_wechat_launch():
    """等待微信启动"""
    print("\n[STEP 3] Waiting for WeChat to launch...")

    # 等待5-10秒让微信启动
    wait_time = 8
    print(f"Waiting {wait_time} seconds...")
    time.sleep(wait_time)

    print("[OK] Wait completed")

def find_and_click_login_button():
    """查找并点击登录按钮"""
    print("\n[STEP 4] Finding login button...")

    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    width, height = screenshot.size
    pixels = img_rgb.load()

    # 登录按钮通常是绿色的
    WECHAT_GREEN = (7, 193, 96)
    TOLERANCE = 30

    green_positions = []

    # 搜索整个屏幕
    for y in range(0, height):
        for x in range(0, width):
            r, g, b = pixels[x, y]
            if (abs(r - WECHAT_GREEN[0]) < TOLERANCE and
                abs(g - WECHAT_GREEN[1]) < TOLERANCE and
                abs(b - WECHAT_GREEN[2]) < TOLERANCE):
                green_positions.append((x, y))

    if green_positions:
        # 计算绿色区域的中心
        avg_x = sum(p[0] for p in green_positions) // len(green_positions)
        avg_y = sum(p[1] for p in green_positions) // len(green_positions)

        print(f"[OK] Found login button at: ({avg_x}, {avg_y})")
        print(f"        Found {len(green_positions)} green pixels")
        screenshot_and_mark(avg_x, avg_y, 120, "Login_Button")

        # 点击登录按钮
        print("\n[STEP 5] Clicking login button...")
        pyautogui.click(avg_x, avg_y)
        time.sleep(1)

        print("[OK] Login button clicked")
        return True
    else:
        print("[NOT FOUND] Login button not found")
        print("[INFO] WeChat may have different login state")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Automatic WeChat Login Launcher")
    print("=" * 60)

    try:
        # Step 1: 找到微信图标
        icon_x, icon_y = find_wechat_icon()

        # Step 2: 双击打开微信
        double_click_wechat(icon_x, icon_y)

        # Step 3: 等待微信启动
        wait_for_wechat_launch()

        # Step 4: 找到并点击登录按钮
        login_clicked = find_and_click_login_button()

        # 最终截图
        print("\n[FINAL] Taking final screenshot...")
        time.sleep(2)
        width, height = pyautogui.size()
        screenshot_and_mark(width//2, height//2, 150, "Final_State")

        print("\n" + "=" * 60)
        if login_clicked:
            print("[SUCCESS] WeChat launch and login click completed!")
        else:
            print("[PARTIAL] WeChat launched, but login button not found")
        print("=" * 60)
        print("\n[INFO] Please use your phone to scan the QR code if shown")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
