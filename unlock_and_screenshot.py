import time
import os
from PIL import ImageGrab
import pyautogui

# Disable fail-safe
pyautogui.FAILSAFE = False

# Wake up screen
pyautogui.press('space')

# Wait for password field
time.sleep(1)

# Enter password
pyautogui.write('28944328')
pyautogui.press('enter')

# Wait for desktop to load
time.sleep(4)

# Try to take screenshot
os.chdir(r'C:\Users\GX\.openclaw\workspace')
try:
    img = ImageGrab.grab()
    img.save('screenshot_unlocked.png')
    print('Screenshot saved successfully')
except Exception as e:
    print(f'Error taking screenshot: {e}')
    # Try alternative: get pixel color to verify screen is active
    try:
        pixel = ImageGrab.grab(bbox=(0, 0, 1, 1)).getpixel((0, 0))
        print(f'Screen pixel color: {pixel}')
    except Exception as e2:
        print(f'Cannot access screen: {e2}')
