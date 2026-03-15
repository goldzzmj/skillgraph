#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time

def find_and_click_search_box():
    """查找并点击搜索框"""
    print("Step 1: Finding search box...")

    # 先截图分析
    width, height = pyautogui.size()
    screenshot = pyautogui.screenshot()
    img_rgb = screenshot.convert('RGB')
    pixels = img_rgb.load()

    # 搜索框通常是浅灰色的
    LIGHT_GRAY = (240, 240, 240)
    TOLERANCE = 10

    search_positions = []

    # 在屏幕左上角区域搜索
    for y in range(50, 150):
        for x in range(50, width - 50):
            r, g, b = pixels[x, y]
            if (abs(r - LIGHT_GRAY[0]) < TOLERANCE and
                abs(g - LIGHT_GRAY[1]) < TOLERANCE and
                abs(b - LIGHT_GRAY[2]) < TOLERANCE):
                search_positions.append((x, y))

    if len(search_positions) > 0:
        # 计算中心位置
        avg_x = sum(p[0] for p in search_positions) // len(search_positions)
        avg_y = sum(p[1] for p in search_positions) // len(search_positions)

        print(f"Found search box at: ({avg_x}, {avg_y})")

        # 点击搜索框
        print("Clicking search box...")
        pyautogui.click(avg_x, avg_y)
        time.sleep(0.5)

        return True
    else:
        print("Could not find search box, using default position")
        # 使用默认位置（搜索框通常在右上角）
        pyautogui.click(width - 500, 100)
        time.sleep(0.5)
        return False

def search_contact():
    """搜索联系人"""
    print("\nStep 2: Searching for '郑政隆'...")

    # 清空搜索框
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)

    # 输入搜索内容
    search_text = "郑政隆"
    print(f"Typing: {search_text}")
    pyautogui.write(search_text)
    time.sleep(1)

    # 按回车确认
    print("Pressing Enter to confirm...")
    pyautogui.press('enter')
    time.sleep(2)

def click_contact_chat():
    """点击联系人进入聊天"""
    print("\nStep 3: Clicking contact to open chat...")

    # 搜索结果通常在搜索框下方
    # 根据之前截图，搜索框大约在右上角
    width, height = pyautogui.size()

    # 尝试点击搜索结果区域
    # 从搜索框向下
    result_x = width - 500  # 与搜索框相同的X坐标
    result_y = 180  # 搜索框下方

    print(f"Clicking search result at: ({result_x}, {result_y})")
    pyautogui.click(result_x, result_y)
    time.sleep(2)

def send_message():
    """发送消息"""
    print("\nStep 4: Sending message...")
    print("Locating input box...")

    # 输入框通常在聊天窗口底部
    width, height = pyautogui.size()

    input_y = height - 150  # 屏幕底部上方150像素
    input_x = width // 2  # 水平居中

    print(f"Clicking input box at: ({input_x}, {input_y})")
    pyautogui.click(input_x, input_y)
    time.sleep(0.5)

    # 清空并输入消息
    message = "我是openclaw"
    print(f"Typing: {message}")

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    pyautogui.write(message)
    time.sleep(0.5)

    # 发送
    print("Pressing Enter to send...")
    pyautogui.press('enter')

    print("\nMessage sent!")

if __name__ == "__main__":
    print("=== WeChat Search and Send Message ===\n")

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
