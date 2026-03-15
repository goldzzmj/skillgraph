#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time
from datetime import datetime

def try_multiple_positions():
    """尝试多个可能的位置"""
    print("Trying multiple positions for search result...")

    # 根据截图，搜索结果区域的大概范围
    width, height = pyautogui.size()

    # 搜索框在右上角，结果应该在下方
    # 尝试多个Y坐标
    base_x = width - 500  # 与搜索框相同的X
    y_positions = [160, 180, 200, 220, 240, 260]

    for i, y in enumerate(y_positions, 1):
        print(f"\nAttempt {i}: Clicking at ({base_x}, {y})")

        # 截图并标记
        screenshot = pyautogui.screenshot()
        img_rgb = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img_rgb)
        draw.ellipse([base_x-60, y-30, base_x+60, y+30],
                    outline='red', width=5)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        marked_path = f"F:\\openclaw_data\\click_attempt_{i}_{timestamp}.png"
        img_rgb.save(marked_path)

        print(f"Saved: {marked_path}")
        pyautogui.click(base_x, y)
        time.sleep(1.5)

    print("\nAll click attempts completed!")

def send_message_after_click():
    """点击后发送消息"""
    print("\n=== Sending Message ===")

    width, height = pyautogui.size()

    # 尝试多个可能的输入框位置
    input_y_positions = [height - 200, height - 150, height - 120, height - 100]
    input_x = width // 2

    for i, y in enumerate(input_y_positions, 1):
        print(f"\nAttempt {i}: Clicking input box at ({input_x}, {y})")

        # 截图并标记
        screenshot = pyautogui.screenshot()
        img_rgb = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img_rgb)
        draw.ellipse([input_x-80, y-40, input_x+80, y+40],
                    outline='red', width=5)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        marked_path = f"F:\\openclaw_data\\input_click_{i}_{timestamp}.png"
        img_rgb.save(marked_path)

        print(f"Saved: {marked_path}")
        pyautogui.click(input_x, y)
        time.sleep(0.5)

        # 尝试输入
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write('我是openclaw')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(1)

if __name__ == "__main__":
    print("=== Retry Clicking Search Result ===\n")

    try:
        # 尝试点击搜索结果
        try_multiple_positions()

        # 尝试发送消息
        send_message_after_click()

        print("\n=== All retry attempts completed! ===")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
