#!/usr/bin/env python3
"""
使用 pywinauto 进行微信自动化
"""

from PIL import Image, ImageDraw
import pyautogui
import time
from datetime import datetime
from pywinauto import Application, keyboard

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

def main():
    print("=== Pywinauto WeChat Automation ===\n")

    try:
        # 获取微信窗口
        print("Step 1: Finding WeChat window...")
        app = Application(backend="uia").connect(title="WeChat", timeout=10)
        wechat = app.window(title="WeChat")

        print(f"Found WeChat window: {wechat}")

        # 激活窗口
        wechat.set_focus()
        time.sleep(1)

        # 获取窗口信息
        print(f"Window rectangle: {wechat.rectangle()}")
        rect = wechat.rectangle()

        # 计算搜索框位置（通常在窗口右上角）
        search_x = rect.right - 400
        search_y = rect.top + 80

        # 标记并点击搜索框
        print(f"\nStep 2: Clicking search box at ({search_x}, {search_y})")
        screenshot_and_mark(search_x, search_y, 100, "Search_Box")

        pyautogui.click(search_x, search_y)
        time.sleep(1)

        # 输入搜索内容
        print("\nStep 3: Typing search text...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write('郑政隆')
        time.sleep(1)

        # 标记回车位置
        screenshot_and_mark(search_x, search_y, 50, "Press_Enter")

        print("\nStep 4: Pressing Enter...")
        pyautogui.press('enter')
        time.sleep(2)

        # 点击搜索结果
        print("\nStep 5: Clicking search result...")
        result_x = search_x
        result_y = search_y + 80

        screenshot_and_mark(result_x, result_y, 100, "Click_Result")
        pyautogui.click(result_x, result_y)
        time.sleep(2)

        # 点击输入框
        print("\nStep 6: Clicking input box...")
        input_x = rect.left + rect.width() // 2
        input_y = rect.bottom - 200

        screenshot_and_mark(input_x, input_y, 120, "Input_Box")
        pyautogui.click(input_x, input_y)
        time.sleep(0.5)

        # 输入消息
        print("\nStep 7: Typing message...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write('我是openclaw')
        time.sleep(0.5)

        # 标记发送位置
        screenshot_and_mark(input_x, input_y, 80, "Send")
        print("\nStep 8: Sending...")

        # 发送消息
        pyautogui.press('enter')
        time.sleep(1)

        print("\n=== All steps completed! ===")
        print(f"\nWindow rectangle: {rect}")
        print(f"Search box: ({search_x}, {search_y})")
        print(f"Search result: ({result_x}, {result_y})")
        print(f"Input box: ({input_x}, {input_y})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

        # 回退方案：使用 pyautogui
        print("\nFalling back to pyautogui...")
        try_fallback()

def try_fallback():
    """回退方案：使用 pyautogui"""
    print("\n=== Fallback: Using pyautogui ===\n")

    # 获取屏幕尺寸
    width, height = pyautogui.size()

    # 搜索框
    print("Finding search box...")
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
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

        screenshot_and_mark(avg_x, avg_y, 100, "Search_Box_Fallback")
        pyautogui.click(avg_x, avg_y)
        time.sleep(1)

        # 搜索
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write('郑政隆')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)

        # 点击结果
        result_x = avg_x
        result_y = avg_y + 80
        screenshot_and_mark(result_x, result_y, 100, "Click_Result_Fallback")
        pyautogui.click(result_x, result_y)
        time.sleep(2)

        # 输入消息
        input_x = width // 2
        input_y = height - 150
        screenshot_and_mark(input_x, input_y, 120, "Input_Box_Fallback")

        pyautogui.click(input_x, input_y)
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write('我是openclaw')
        time.sleep(0.5)

        # 发送
        screenshot_and_mark(input_x, input_y, 80, "Send_Fallback")
        pyautogui.press('enter')
        time.sleep(1)

        print("\n=== Fallback completed! ===")

if __name__ == "__main__":
    main()
