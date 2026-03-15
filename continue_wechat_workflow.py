#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time
from datetime import datetime

def click_search_result():
    """点击搜索结果中的联系人"""
    print("Step 1: Clicking search result...")

    # 搜索结果在搜索框下方
    width, height = pyautogui.size()
    result_x = width - 500
    result_y = 180

    # 截图并标记
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    draw = ImageDraw.Draw(img_rgb)
    draw.ellipse([result_x-100, result_y-40, result_x+100, result_y+40],
                outline='red', width=5)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    marked_path = f"F:\\openclaw_data\\click_result_{timestamp}.png"
    img_rgb.save(marked_path)

    print(f"Clicking at: ({result_x}, {result_y})")
    print(f"Marked: {marked_path}")
    pyautogui.click(result_x, result_y)
    time.sleep(2)

    return marked_path

def send_message():
    """发送消息"""
    print("\nStep 2: Sending message...")

    width, height = pyautogui.size()
    input_x = width // 2
    input_y = height - 150

    # 截图并标记输入框
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    draw = ImageDraw.Draw(img_rgb)
    draw.ellipse([input_x-120, input_y-50, input_x+120, input_y+50],
                outline='red', width=5)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    marked_path1 = f"F:\\openclaw_data\\input_box_{timestamp}.png"
    img_rgb.save(marked_path1)

    print(f"Clicking input box: ({input_x}, {input_y})")
    print(f"Marked: {marked_path1}")
    pyautogui.click(input_x, input_y)
    time.sleep(0.5)

    # 输入消息
    message = "我是openclaw"
    print(f"Typing: {message}")

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.write(message)
    time.sleep(0.5)

    # 标记发送位置
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    draw = ImageDraw.Draw(img_rgb)
    draw.ellipse([input_x-60, input_y-40, input_x+60, input_y+40],
                outline='red', width=5)

    timestamp2 = datetime.now().strftime("%Y%m%d_%H%M%S")
    marked_path2 = f"F:\\openclaw_data\\send_{timestamp2}.png"
    img_rgb.save(marked_path2)

    print(f"Sending... Marked: {marked_path2}")
    pyautogui.press('enter')
    time.sleep(1)

    return marked_path1, marked_path2

if __name__ == "__main__":
    print("=== Continue WeChat Workflow ===\n")

    try:
        # Step 1: 点击搜索结果
        img1 = click_search_result()

        # Step 2: 发送消息
        img2, img3 = send_message()

        print("\n=== Completed! ===")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
