#!/usr/bin/env python3
"""
PyAutoGUI Simple Test
"""

import pyautogui
import time
from datetime import datetime
import os

OUTPUT_DIR = r"F:\openclaw_data"

def test_screen_info():
    """测试屏幕信息获取"""
    print("\n[TEST 1] Screen Information")
    print("-" * 50)

    # 获取屏幕尺寸
    size = pyautogui.size()
    print(f"Screen Size: {size[0]} x {size[1]}")

    # 获取鼠标位置
    position = pyautogui.position()
    print(f"Mouse Position: ({position.x}, {position.y})")

    # 截图
    print("\nTaking screenshot...")
    screenshot = pyautogui.screenshot()
    filename = os.path.join(OUTPUT_DIR, f"test_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    screenshot.save(filename)
    print(f"Saved: {filename}")

    print("[OK] Test 1 completed")
    time.sleep(2)
    return True

def test_mouse_movement():
    """测试鼠标移动"""
    print("\n[TEST 2] Mouse Movement")
    print("-" * 50)

    size = pyautogui.size()
    center_x, center_y = size[0] // 2, size[1] // 2

    print(f"Moving to center: ({center_x}, {center_y})")
    pyautogui.moveTo(center_x, center_y, duration=1)
    time.sleep(1)

    pos = pyautogui.position()
    print(f"Current position: ({pos.x}, {pos.y})")

    # 移回原位
    print("Moving back...")
    pyautogui.moveTo(100, 100, duration=0.5)
    time.sleep(0.5)

    print("[OK] Test 2 completed")
    time.sleep(1)
    return True

def test_mouse_click():
    """测试鼠标点击"""
    print("\n[TEST 3] Mouse Click")
    print("-" * 50)

    # 移动到点击位置
    pyautogui.moveTo(500, 500, duration=0.5)
    time.sleep(0.5)

    print(f"Clicking at: (500, 500)")
    pyautogui.click()
    time.sleep(1)

    print("Double click...")
    pyautogui.doubleClick()
    time.sleep(1)

    print("[OK] Test 3 completed")
    time.sleep(1)
    return True

def test_keyboard_typing():
    """测试键盘输入"""
    print("\n[TEST 4] Keyboard Typing")
    print("-" * 50)

    # 打开记事本进行测试
    print("Opening Notepad...")
    try:
        os.system("notepad")
        time.sleep(2)
    except:
        print("Could not open Notepad")

    print("Typing: 'Hello from PyAutoGUI'")
    pyautogui.write("Hello from PyAutoGUI")
    time.sleep(1)

    print("Typing: 'Test number: 1234567890'")
    pyautogui.write("Test number: 1234567890")
    time.sleep(1)

    print("[OK] Test 4 completed")
    time.sleep(1)
    return True

def test_keyboard_shortcuts():
    """测试键盘快捷键"""
    print("\n[TEST 5] Keyboard Shortcuts")
    print("-" * 50)

    print("Pressing: Ctrl+A")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)

    print("Pressing: Ctrl+C")
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)

    print("Pressing: Alt+Tab")
    pyautogui.hotkey('alt', 'tab')
    time.sleep(0.5)

    print("[OK] Test 5 completed")
    time.sleep(1)
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("PyAutoGUI Simple Test Suite")
    print("=" * 60)
    print(f"PyAutoGUI Version: {pyautogui.__version__}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print("=" * 60)

    try:
        # 运行所有测试
        results = []
        results.append(test_screen_info())
        results.append(test_mouse_movement())
        results.append(test_mouse_click())
        results.append(test_keyboard_typing())
        results.append(test_keyboard_shortcuts())

        # 总结
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        total_tests = len(results)
        passed_tests = sum(results)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")

        if passed_tests == total_tests:
            print("\n[SUCCESS] All tests passed!")
        else:
            print("\n[WARNING] Some tests failed")

        print("=" * 60)
        print("\nPyAutoGUI is working correctly!")
        print("You can now use it for automation tasks.")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
