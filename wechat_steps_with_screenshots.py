#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time
from datetime import datetime

def mark_and_save_region(x, y, radius=50, label=""):
    """标记区域并保存截图"""
    # 截图
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')

    # 标记位置
    draw = ImageDraw.Draw(img_rgb)
    draw.ellipse([x-radius, y-radius, x+radius, y+radius],
                outline='red', width=5)

    if label:
        draw.text((x-radius, y-radius-30), label, fill='red')

    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"F:\\openclaw_data\\step_{timestamp}_{label.replace(' ', '_')}.png"
    img_rgb.save(filename)

    print(f"Screenshot saved: {filename}")
    return filename

def find_and_click_search_box():
    """查找并点击搜索框"""
    print("\n=== Step 1: Finding Search Box ===")

    width, height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    pixels = img_rgb.load()

    # 搜索框通常是浅灰色的
    LIGHT_GRAY = (240, 240, 240)
    TOLERANCE = 10

    search_positions = []

    for y in range(50, 150):
        for x in range(50, width - 50):
            r, g, b = pixels[x, y]
            if (abs(r - LIGHT_GRAY[0]) < TOLERANCE and
                abs(g - LIGHT_GRAY[1]) < TOLERANCE and
                abs(b - LIGHT_GRAY[2]) < TOLERANCE):
                search_positions.append((x, y))

    if len(search_positions) > 0:
        avg_x = sum(p[0] for p in search_positions) // len(search_positions)
        avg_y = sum(p[1] for p in search_positions) // len(search_positions)

        print(f"Found at: ({avg_x}, {avg_y})")

        # 截图并标记
        mark_and_save_region(avg_x, avg_y, 100, "Search Box")

        # 点击
        print("Clicking...")
        pyautogui.click(avg_x, avg_y)
        time.sleep(1)

        return avg_x, avg_y
    else:
        print("Not found, using default")
        default_x, default_y = width - 500, 100
        mark_and_save_region(default_x, default_y, 100, "Search Box (default)")
        pyautogui.click(default_x, default_y)
        time.sleep(1)
        return default_x, default_y

def search_contact():
    """搜索联系人"""
    print("\n=== Step 2: Searching for '郑政隆' ===")

    # 输入前截图
    width, height = pyautogui.size()
    input_x, input_y = width - 500, 100
    mark_and_save_region(input_x, input_y, 150, "Input Area")

    # 输入搜索词
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.write('郑政隆')
    time.sleep(1)

    # 标记回车位置
    mark_and_save_region(input_x, input_y, 50, "Press Enter")

    # 按回车
    print("Pressing Enter...")
    pyautogui.press('enter')
    time.sleep(2)

def click_contact_chat():
    """点击联系人"""
    print("\n=== Step 3: Clicking Contact ===")

    width, height = pyautogui.size()
    result_x = width - 500
    result_y = 180

    # 标记并点击
    mark_and_save_region(result_x, result_y, 80, "Search Result")
    print(f"Clicking at: ({result_x}, {result_y})")
    pyautogui.click(result_x, result_y)
    time.sleep(2)

def send_message():
    """发送消息"""
    print("\n=== Step 4: Sending Message ===")

    width, height = pyautogui.size()
    input_x = width // 2
    input_y = height - 150

    # 标记输入框位置
    mark_and_save_region(input_x, input_y, 100, "Input Box")

    # 点击输入框
    print("Clicking input box...")
    pyautogui.click(input_x, input_y)
    time.sleep(0.5)

    # 输入消息
    message = "我是openclaw"
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.write(message)
    time.sleep(1)

    # 标记发送位置
    mark_and_save_region(input_x, input_y, 50, "Press Enter to Send")

    # 发送
    print("Sending...")
    pyautogui.press('enter')
    time.sleep(2)

if __name__ == "__main__":
    print("=== WeChat Search and Send - With Screenshots ===")

    try:
        # Step 1: 找到并点击搜索框
        find_and_click_search_box()

        # Step 2: 搜索联系人
        search_contact()

        # Step 3: 点击联系人
        click_contact_chat()

        # Step 4: 发送消息
        send_message()

        print("\n=== All steps completed! ===")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
