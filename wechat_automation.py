#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time
from datetime import datetime

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
    filename = f"F:\\openclaw_data\\{label}_{timestamp}.png"
    img_rgb.save(filename)
    print(f"Saved: {filename}")
    return filename

def find_and_click_search():
    """1. 找到并点击搜索框"""
    print("\n=== Step 1: Find and Click Search Box ===")

    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    width, height = screenshot.size
    pixels = img_rgb.load()

    LIGHT_GRAY = (240, 240, 240)
    TOLERANCE = 10
    search_positions = []

    for y in range(50, 150):
        for x in range(width - 800, width):
            r, g, b = pixels[x, y]
            if (abs(r - LIGHT_GRAY[0]) < TOLERANCE and
                abs(g - LIGHT_GRAY[1]) < TOLERANCE and
                abs(b - LIGHT_GRAY[2]) < TOLERANCE):
                search_positions.append((x, y))

    if search_positions:
        avg_x = sum(p[0] for p in search_positions) // len(search_positions)
        avg_y = sum(p[1] for p in search_positions) // len(search_positions)
        screenshot_and_mark(avg_x, avg_y, 100, "Search_Box")
        pyautogui.click(avg_x, avg_y)
        time.sleep(1)
        return True
    return False

def search_contact():
    """2. 搜索联系人"""
    print("\n=== Step 2: Search for '郑政隆' ===")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.write('郑政隆')
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(2)
    print("Search completed")

def click_search_result():
    """3. 点击搜索结果"""
    print("\n=== Step 3: Click Search Result ===")
    width, height = pyautogui.size()
    result_x = width - 500
    result_y = 180
    screenshot_and_mark(result_x, result_y, 100, "Search_Result")
    pyautogui.click(result_x, result_y)
    time.sleep(2)

def send_message():
    """4. 发送消息"""
    print("\n=== Step 4: Send Message ===")
    width, height = pyautogui.size()
    input_x = width // 2
    input_y = height - 150
    screenshot_and_mark(input_x, input_y, 120, "Input_Box")

    pyautogui.click(input_x, input_y)
    time.sleep(0.5)

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.write('我是openclaw')
    time.sleep(0.5)

    screenshot_and_mark(input_x, input_y, 80, "Send")
    pyautogui.press('enter')
    time.sleep(1)

def main():
    print("=== WeChat Automation with desktop-control ===\n")

    try:
        find_and_click_search()
        search_contact()
        click_search_result()
        send_message()
        print("\n=== All steps completed! ===")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
