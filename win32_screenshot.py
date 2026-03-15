import ctypes
from ctypes import wintypes
import time
import os
import pyautogui

# Disable fail-safe
pyautogui.FAILSAFE = False

# Wake up screen and unlock
pyautogui.press('space')
time.sleep(1)
pyautogui.write('28944328')
pyautogui.press('enter')
time.sleep(4)

# Try Windows API screenshot
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

try:
    # Get screen dimensions
    width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)

    # Create DC
    hwnd = user32.GetDesktopWindow()
    hdesktop = user32.GetWindowDC(hwnd)
    hdc = gdi32.CreateCompatibleDC(hdesktop)

    # Create bitmap
    hbmp = gdi32.CreateCompatibleBitmap(hdesktop, width, height)
    gdi32.SelectObject(hdc, hbmp)

    # Copy screen
    gdi32.BitBlt(hdc, 0, 0, width, height, hdesktop, left, top, 0x00CC0020)

    # Save to file using PIL
    import win32ui
    save_path = r'C:\Users\GX\.openclaw\workspace\screenshot_unlocked.png'
    obj = win32ui.CreateBitmapFromHandle(hbmp)
    obj.SaveBitmapFile(hdc, save_path)

    print('Screenshot saved successfully')

except ImportError as e:
    print(f'Module not available: {e}')
except Exception as e:
    print(f'Error: {e}')
finally:
    # Cleanup
    try:
        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc)
        user32.ReleaseDC(hwnd, hdesktop)
    except:
        pass
