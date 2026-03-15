#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time
from datetime import datetime

def click_send_button():
    """点击发送按钮"""
    print("=== Clicking Send Button ===")

    width, height = pyautogui.size()

    # 发送按钮通常在输入框右侧
    # 或者使用回车键发送
    print("Option 1: Pressing Enter...")
    pyautogui.press('enter')
    time.sleep(1)

    # Option 2: 点击发送按钮（绿色按钮）
    # 发送按钮通常在输入框右侧
    send_x = width - 800  # 输入框右侧
    send_y = height - 150  # 与输入框相同的Y坐标

    # 截图并标记
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    draw = ImageDraw.Draw(img_rgb)
    draw.ellipse([send_x-60, send_y-30, send_x+60, send_y+30],
                outline='red', width=5)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    marked_path = f"F:\\openclaw_data\\send_button_{timestamp}.png"
    img_rgb.save(marked_path)

    print(f"\nOption 2: Clicking send button at: ({send_x}, {send_y})")
    print(f"Marked: {marked_path}")
    pyautogui.click(send_x, send_y)
    time.sleep(1)

    return marked_path

if __name__ == "__main__":
    print("=== Click Send Button ===\n")

    try:
        click_send_button()

        print("\n=== Completed! ===")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
