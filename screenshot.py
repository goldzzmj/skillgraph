#!/usr/bin/env python3
import os
from PIL import ImageGrab
from datetime import datetime

def take_screenshot(output_path):
    """Take a screenshot and save to file"""
    try:
        screenshot = ImageGrab.grab()
        screenshot.save(output_path)
        print(f"Screenshot saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"xiaohongshu_login_{timestamp}.png"
    filepath = os.path.join(r"F:\openclaw_data", filename)

    print("Taking screenshot...")
    if take_screenshot(filepath):
        size = os.path.getsize(filepath)
        print(f"File size: {size} bytes")
    else:
        print("Failed to take screenshot")
