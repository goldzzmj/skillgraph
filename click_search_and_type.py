#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time
from datetime import datetime

def find_and_click_search_box():
    """查找并点击搜索框"""
    print("Finding WeChat search box...")

    # 先截图
    width, height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    pixels = img_rgb.load()

    # 搜索框通常是浅灰色的
    LIGHT_GRAY = (240, 240, 240)
    TOLERANCE = 10

    search_positions = []

    # 在屏幕右上角区域搜索（微信搜索框通常在这里）
    for y in range(50, 150):
        for x in range(width - 800, width):
            r, g, b = pixels[x, y]
            if (abs(r - LIGHT_GRAY[0]) < TOLERANCE and
                abs(g - LIGHT_GRAY[1]) < TOLERANCE and
                abs(b - LIGHT_GRAY[2]) < TOLERANCE):
                search_positions.append((x, y))

    if len(search_positions) > 0:
        # 计算中心位置
        avg_x = sum(p[0] for p in search_positions) // len(search_positions)
        avg_y = sum(p[1] for p in search_positions) // len(search_positions)

        # 标记位置
        draw = ImageDraw.Draw(img_rgb)
        draw.ellipse([avg_x-80, avg_y-20, avg_x+80, avg_y+20],
                    outline='red', width=5)

        # 保存标记后的图片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        marked_path = f"F:\\openclaw_data\\search_box_marked_{timestamp}.png"
        img_rgb.save(marked_path)

        print(f"Found search box at: ({avg_x}, {avg_y})")
        print(f"Marked image: {marked_path}")

        # 点击搜索框
        print("Clicking search box...")
        pyautogui.click(avg_x, avg_y)
        time.sleep(0.5)

        return marked_path
    else:
        print("Search box not found, using default position")
        # 使用默认位置（右上角）
        default_x = width - 500
        default_y = 100

        # 截图并标记
        draw = ImageDraw.Draw(img_rgb)
        draw.ellipse([default_x-80, default_y-20, default_x+80, default_y+20],
                    outline='red', width=5)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        marked_path = f"F:\\openclaw_data\\search_box_marked_{timestamp}.png"
        img_rgb.save(marked_path)

        pyautogui.click(default_x, default_y)
        time.sleep(0.5)

        return marked_path

def type_search_text():
    """输入搜索文本"""
    print("\nTyping search text...")

    # 清空输入框
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)

    # 输入"郑政隆"
    search_text = "郑政隆"
    print(f"Typing: {search_text}")
    pyautogui.write(search_text)
    time.sleep(1)

    print("Text entered!")

if __name__ == "__main__":
    print("=== Click WeChat Search Box and Type ===\n")

    try:
        # Step 1: 找到并点击搜索框
        marked_path = find_and_click_search_box()

        # Step 2: 输入搜索文本
        type_search_text()

        print("\n=== Completed! ===")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
