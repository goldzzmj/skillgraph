#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time

def find_enter_button(image_path):
    """查找微信的"进入"绿色按钮"""
    img = Image.open(image_path)
    img_rgb = img.convert('RGB')
    width, height = img.size
    pixels = img_rgb.load()

    # 微信绿色按钮 RGB: (7, 193, 96)
    WECHAT_GREEN = (7, 193, 96)
    TOLERANCE = 30

    green_positions = []

    # 搜索整个屏幕
    for y in range(0, height, 5):
        for x in range(0, width, 5):
            r, g, b = pixels[x, y]

            # 检查是否是微信绿色
            if (abs(r - WECHAT_GREEN[0]) < TOLERANCE and
                abs(g - WECHAT_GREEN[1]) < TOLERANCE and
                abs(b - WECHAT_GREEN[2]) < TOLERANCE):

                green_positions.append((x, y))

    print(f"Found {len(green_positions)} green pixels")

    if len(green_positions) > 10:
        # 找到绿色像素较多的区域
        # 计算中心
        avg_x = sum(p[0] for p in green_positions) // len(green_positions)
        avg_y = sum(p[1] for p in green_positions) // len(green_positions)

        print(f"Button center estimated at: ({avg_x}, {avg_y})")

        # 标记位置
        marked_img = img_rgb.copy()
        draw = ImageDraw.Draw(marked_img)
        draw.ellipse([avg_x-80, avg_y-30, avg_x+80, avg_y+30],
                   outline='red', width=5)

        marked_path = image_path.replace('.png', '_button_marked.png')
        marked_img.save(marked_path)
        print(f"Marked image: {marked_path}")

        return avg_x, avg_y, marked_path

    return None, None, None

def main():
    print("=== WeChat Enter Button Clicker ===\n")

    screenshot_path = r"F:\openclaw_data\xiaohongshu_login_20260211_203600.png"

    x, y, marked_path = find_enter_button(screenshot_path)

    if x and y:
        print(f"\nFound button at: ({x}, {y})")
        print("Moving mouse...")
        pyautogui.moveTo(x, y, duration=1)
        time.sleep(0.5)

        print("Clicking...")
        pyautogui.click()

        print("\nClicked!")
    else:
        print("Could not find green button")
        print("Trying screen center click...")
        width, height = pyautogui.size()
        pyautogui.click(width//2, height//2 + 200)

if __name__ == "__main__":
    main()
