#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import os

# 微信的典型绿色 (RGB: 7, 193, 96)
WECHAT_GREEN = (7, 193, 96)
TOLERANCE = 30

def find_wechat_icon(image_path):
    """在截图中查找微信图标"""
    print(f"Analyzing: {image_path}")

    # 打开图片
    img = Image.open(image_path)
    width, height = img.size

    print(f"Image size: {width}x{height}")

    # 转换为RGB
    img_rgb = img.convert('RGB')
    pixels = img_rgb.load()

    # 查找绿色区域
    green_positions = []
    for y in range(0, height, 5):  # 步长5减少计算量
        for x in range(0, width, 5):
            r, g, b = pixels[x, y]

            # 检查是否是微信绿色
            if (abs(r - WECHAT_GREEN[0]) < TOLERANCE and
                abs(g - WECHAT_GREEN[1]) < TOLERANCE and
                abs(b - WECHAT_GREEN[2]) < TOLERANCE):

                # 只取屏幕上半部分（图标通常在顶部或左侧）
                if y < height * 0.6:
                    green_positions.append((x, y))

    print(f"Found {len(green_positions)} green pixel positions")

    if green_positions:
        # 计算中心位置
        avg_x = sum(p[0] for p in green_positions) // len(green_positions)
        avg_y = sum(p[1] for p in green_positions) // len(green_positions)

        print(f"WeChat icon estimated at: ({avg_x}, {avg_y})")

        # 标记位置并保存
        marked_img = img_rgb.copy()
        draw = ImageDraw.Draw(marked_img)

        # 画一个圈标记位置
        draw.ellipse([avg_x-50, avg_y-50, avg_x+50, avg_y+50],
                   outline='red', width=5)
        draw.ellipse([avg_x-10, avg_y-10, avg_x+10, avg_y+10],
                   fill='red')

        # 保存标记后的图片
        marked_path = image_path.replace('.png', '_marked.png')
        marked_img.save(marked_path)
        print(f"Marked image saved: {marked_path}")

        return avg_x, avg_y, marked_path
    else:
        print("No WeChat green found")
        return None, None, None

if __name__ == "__main__":
    screenshot_path = r"F:\openclaw_data\xiaohongshu_login_20260211_201722.png"

    x, y, marked_path = find_wechat_icon(screenshot_path)

    if x and y:
        print(f"\n=== Ready to click ===")
        print(f"Position: ({x}, {y})")
        print(f"Moving mouse...")

        import time
        pyautogui.moveTo(x, y, duration=1)
        time.sleep(0.5)

        print("Clicking...")
        pyautogui.click()

        print("Done!")
    else:
        print("\nCould not find WeChat icon automatically.")
        print("Please use the manual positioning method:")
        print("python C:\\Users\\GX\\.openclaw\\workspace\\locate_login.py")
