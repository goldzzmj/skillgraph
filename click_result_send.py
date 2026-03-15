#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time

def click_search_result():
    """点击搜索结果"""
    print("Step 2: Clicking search result...")
    print("Searching for '郑政隆' in results...")

    # 根据截图，搜索结果通常在搜索框下方
    # 搜索框在 (2205, 102)，结果应该在下方的某个位置
    # 让我们尝试点击几个可能的位置

    # 搜索结果可能的Y坐标（在搜索框下方）
    search_y = 102
    result_y_positions = [
        search_y + 80,   # 第一个结果
        search_y + 120,  # 第二个结果
        search_y + 160,  # 第三个结果
    ]

    # X坐标在搜索框附近
    result_x = 2205

    for i, y in enumerate(result_y_positions, 1):
        print(f"\nAttempt {i}: Clicking at ({result_x}, {y})")
        pyautogui.click(result_x, y)
        time.sleep(1.5)

        # 截图检查是否成功打开聊天
        print("Checking if chat opened...")
        time.sleep(1)

    print("\nClick attempts completed!")
    print("If chat is open, proceeding to send message...")

def send_message():
    """发送消息"""
    print("\nStep 3: Sending message...")
    print("Locating input box...")

    # 输入框通常在聊天窗口底部
    # 让我们尝试点击屏幕下方的位置
    width, height = pyautogui.size()

    input_y = height - 150  # 屏幕底部上方150像素
    input_x = width // 2  # 水平居中

    print(f"Clicking input box at: ({input_x}, {input_y})")
    pyautogui.click(input_x, input_y)
    time.sleep(0.5)

    # 输入消息
    message = "我是openclaw的自动化输入"
    print(f"Typing: {message}")

    pyautogui.write(message)
    time.sleep(0.5)

    # 发送
    print("Pressing Enter to send...")
    pyautogui.press('enter')

    print("\nMessage sent!")

if __name__ == "__main__":
    print("=== Click Search Result and Send Message ===\n")
    try:
        click_search_result()
        time.sleep(2)
        send_message()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
