#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time

def find_search_box(image_path):
    """查找微信搜索框"""
    img = Image.open(image_path)
    img_rgb = img.convert('RGB')
    width, height = img.size
    pixels = img_rgb.load()

    # 搜索框通常是浅灰色的
    LIGHT_GRAY = (240, 240, 240)
    TOLERANCE = 10

    search_positions = []

    # 在屏幕左上角区域搜索（搜索框通常在这里）
    search_region_y = range(50, 150)
    search_region_x = range(50, width - 50)

    for y in search_region_y:
        for x in search_region_x:
            r, g, b = pixels[x, y]

            if (abs(r - LIGHT_GRAY[0]) < TOLERANCE and
                abs(g - LIGHT_GRAY[1]) < TOLERANCE and
                abs(b - LIGHT_GRAY[2]) < TOLERANCE):
                search_positions.append((x, y))

    if len(search_positions) > 0:
        # 计算中心
        avg_x = sum(p[0] for p in search_positions) // len(search_positions)
        avg_y = sum(p[1] for p in search_positions) // len(search_positions)

        # 标记位置
        marked_img = img_rgb.copy()
        draw = ImageDraw.Draw(marked_img)
        draw.rectangle([avg_x-150, avg_y-20, avg_x+150, avg_y+20],
                     outline='red', width=3)

        marked_path = image_path.replace('.png', '_search_marked.png')
        marked_img.save(marked_path)

        return avg_x, avg_y, marked_path

    return None, None, None

def search_and_chat():
    """搜索用户并发送消息"""
    screenshot_path = r"F:\openclaw_data\xiaohongshu_login_20260211_204651.png"

    # 1. 找到搜索框
    print("Step 1: Finding search box...")
    x, y, marked_path = find_search_box(screenshot_path)

    if x and y:
        print(f"Found search box at: ({x}, {y})")

        # 点击搜索框
        print("Clicking search box...")
        pyautogui.click(x, y)
        time.sleep(0.5)

        # 清空并输入搜索内容
        print("Typing search text...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write('郑政隆')
        time.sleep(1)

        # 按回车搜索
        print("Pressing Enter to search...")
        pyautogui.press('enter')
        time.sleep(2)

        print("\nSearch completed!")
        print("Please manually:")
        print("1. Click on '郑政隆' from search results")
        print("2. Type: 我是openclaw的自动化输入")
        print("3. Press Enter to send")

        return True
    else:
        print("Could not find search box")
        print("Trying alternative approach...")

        # 尝试直接搜索
        # 微信快捷键通常是 Ctrl+F
        print("Pressing Ctrl+F...")
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)

        print("Typing search text...")
        pyautogui.write('郑政隆')
        time.sleep(1)

        print("Pressing Enter...")
        pyautogui.press('enter')
        time.sleep(2)

        print("\nSearch completed!")
        return False

if __name__ == "__main__":
    print("=== WeChat Search and Chat ===\n")
    try:
        search_and_chat()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
