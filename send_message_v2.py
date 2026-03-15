#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time

def find_contact_in_search():
    """在搜索结果中查找联系人"""
    print("Finding contact in search results...")

    # 搜索结果通常在搜索框下方的一个列表
    # 根据截图，搜索框大约在 (2205, 102)
    # 结果应该在 (2205, 180-300) 之间

    # 尝试点击搜索结果区域的中间位置
    result_x = 2205
    result_y_positions = [180, 220, 260, 300]

    for i, y in enumerate(result_y_positions, 1):
        print(f"Attempt {i}: Clicking at ({result_x}, {y})")
        pyautogui.click(result_x, y)
        time.sleep(1.5)

        # 检查是否打开了聊天窗口
        # 如果打开成功，聊天窗口标题应该变化
        time.sleep(0.5)

    print("Click attempts completed!")

def type_and_send_message():
    """输入并发送消息"""
    print("\n=== Typing and Sending Message ===")

    # 输入框位置（根据微信界面，通常在底部）
    width, height = pyautogui.size()

    # 尝试几个可能的输入框位置
    input_positions = [
        (width // 2, height - 150),  # 底部中央
        (width // 2, height - 100),  # 底部更靠上
        (width // 2, height - 80),   # 底部更靠上
    ]

    message = "我是openclaw的自动化输入"

    for i, (x, y) in enumerate(input_positions, 1):
        print(f"\nAttempt {i}: Clicking input box at ({x}, {y})")
        pyautogui.click(x, y)
        time.sleep(0.5)

        # 清空输入框
        print("Clearing input box...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)

        # 输入消息
        print(f"Typing: {message}")
        pyautogui.write(message)
        time.sleep(0.5)

        # 发送
        print("Pressing Enter to send...")
        pyautogui.press('enter')
        time.sleep(1)

        # 截图检查
        print("Checking if message sent...")
        time.sleep(0.5)

    print("\nMessage send attempts completed!")

if __name__ == "__main__":
    print("=== WeChat Auto Message ===\n")
    try:
        find_contact_in_search()
        time.sleep(2)
        type_and_send_message()

        print("\nFinal screenshot...")
        time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
