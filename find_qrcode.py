#!/usr/bin/env python3
from PIL import Image, ImageDraw
import pyautogui
import time

def find_qr_code_region(image_path):
    """查找二维码区域（黑白方块区域）"""
    img = Image.open(image_path)
    img_rgb = img.convert('RGB')
    width, height = img.size
    pixels = img_rgb.load()

    # 二维码通常是黑白的，有明显的黑白对比
    # 我们可以通过找黑白交界处来定位

    # 扫描图像，寻找黑白对比强烈的区域
    high_contrast_positions = []

    # 只扫描屏幕中央区域（二维码通常在窗口中央）
    center_x = width // 2
    center_y = height // 2
    region_size = 600

    left = max(0, center_x - region_size)
    right = min(width, center_x + region_size)
    top = max(0, center_y - region_size)
    bottom = min(height, center_y + region_size)

    print(f"Scanning region: ({left}, {top}) to ({right}, {bottom})")

    for y in range(top, bottom, 10):
        for x in range(left, right, 10):
            r, g, b = pixels[x, y]

            # 检查是否是黑色或白色（二维码的颜色）
            if (r < 50 and g < 50 and b < 50) or (r > 200 and g > 200 and b > 200):
                high_contrast_positions.append((x, y))

    print(f"Found {len(high_contrast_positions)} black/white pixels")

    if len(high_contrast_positions) > 0:
        # 计算中心位置
        avg_x = sum(p[0] for p in high_contrast_positions) // len(high_contrast_positions)
        avg_y = sum(p[1] for p in high_contrast_positions) // len(high_contrast_positions)

        print(f"QR code estimated center: ({avg_x}, {avg_y})")

        # 标记位置
        marked_img = img_rgb.copy()
        draw = ImageDraw.Draw(marked_img)
        draw.ellipse([avg_x-100, avg_y-100, avg_x+100, avg_y+100],
                   outline='red', width=5)

        marked_path = image_path.replace('.png', '_qr_marked.png')
        marked_img.save(marked_path)
        print(f"Marked image: {marked_path}")

        return avg_x, avg_y, marked_path

    return None, None, None

def main():
    print("=== QR Code Finder ===\n")

    screenshot_path = r"F:\openclaw_data\xiaohongshu_login_20260211_203101.png"

    x, y, marked_path = find_qr_code_region(screenshot_path)

    if x and y:
        print(f"\nFound QR code at: ({x}, {y})")
        print("This is for WeChat login - use your phone to scan")

        # 发送标记后的图片
        print(f"\nMarked image: {marked_path}")
    else:
        print("Could not find QR code region")

if __name__ == "__main__":
    main()
