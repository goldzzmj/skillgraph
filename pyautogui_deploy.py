#!/usr/bin/env python3
"""
PyAutoGUI 部署和使用指南
"""

import subprocess
import sys

def check_installation():
    """检查 PyAutoGUI 安装状态"""
    print("=" * 60)
    print("PyAutoGUI Installation Check")
    print("=" * 60 + "\n")

    try:
        import pyautogui
        print(f"[OK] PyAutoGUI is installed")
        print(f"    Version: {pyautogui.__version__}")
        print(f"    Location: {pyautogui.__file__}")

        # 测试基本功能
        print("\nTesting basic functions...")
        pos = pyautogui.position()
        print(f"    Current mouse position: {pos}")

        size = pyautogui.size()
        print(f"    Screen size: {size[0]} x {size[1]}")

        return True
    except ImportError:
        print("[NOT INSTALLED] PyAutoGUI is not installed")
        return False

def install_pyautogui():
    """安装 PyAutoGUI"""
    print("\n" + "=" * 60)
    print("Installing PyAutoGUI...")
    print("=" * 60 + "\n")

    try:
        # 使用 pip 安装
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyautogui", "pillow"],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("[SUCCESS] PyAutoGUI installed successfully!")
            return True
        else:
            print(f"[FAILED] Installation failed")
            print(f"Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def print_usage_examples():
    """打印使用示例"""
    print("\n" + "=" * 60)
    print("PyAutoGUI Usage Examples")
    print("=" * 60 + "\n")

    examples = {
        "Mouse Control": [
            "pyautogui.moveTo(x, y, duration=1)  # Move mouse",
            "pyautogui.click()  # Click at current position",
            "pyautogui.click(x, y)  # Click at position",
            "pyautogui.doubleClick()  # Double click",
            "pyautogui.rightClick()  # Right click",
            "pyautogui.scroll(10)  # Scroll up",
            "pyautogui.scroll(-10)  # Scroll down"
        ],
        "Keyboard Input": [
            "pyautogui.write('Hello World')  # Type text",
            "pyautogui.press('enter')  # Press key",
            "pyautogui.press('space')  # Press space",
            "pyautogui.hotkey('ctrl', 'c')  # Ctrl+C",
            "pyautogui.hotkey('ctrl', 'v')  # Ctrl+V",
            "pyautogui.hotkey('alt', 'tab')  # Alt+Tab"
        ],
        "Screen Functions": [
            "pyautogui.screenshot('screenshot.png')  # Take screenshot",
            "pyautogui.size()  # Get screen size",
            "pyautogui.position()  # Get mouse position"
        ],
        "Advanced Features": [
            "pyautogui.dragTo(x, y, duration=1)  # Drag mouse",
            "pyautogui.PAUSE = 0.5  # Set delay between actions",
            "pyautogui.FAILSAFE = True  # Enable fail-safe"
        ]
    }

    for category, commands in examples.items():
        print(f"\n{category}:")
        for cmd in commands:
            print(f"  {cmd}")

def print_test_script():
    """打印测试脚本"""
    print("\n" + "=" * 60)
    print("Test Script")
    print("=" * 60 + "\n")

    script_content = '''
#!/usr/bin/env python3
import pyautogui
import time

# 配置
pyautogui.PAUSE = 0.5  # 动作之间的延迟
pyautogui.FAILSAFE = True  # 启用故障保护（移动鼠标到角落取消）

print("Starting test...")
print(f"Screen size: {pyautogui.size()}")

# 移动鼠标到屏幕中央
width, height = pyautogui.size()
center_x, center_y = width // 2, height // 2

print(f"Moving to center: ({center_x}, {center_y})")
pyautogui.moveTo(center_x, center_y, duration=1)
time.sleep(0.5)

# 点击
print("Clicking...")
pyautogui.click()

# 输入文本
print("Typing 'Hello'...")
pyautogui.write("Hello")
time.sleep(0.5)

print("Test completed!")
'''

    print(script_content)

def main():
    """主函数"""
    # 检查安装状态
    installed = check_installation()

    # 如果未安装，则安装
    if not installed:
        installed = install_pyautogui()

        # 安装后重新检查
        if installed:
            print("\nRechecking installation...")
            check_installation()

    # 打印使用示例
    print_usage_examples()

    # 打印测试脚本
    print_test_script()

    print("\n" + "=" * 60)
    print("Deployment Summary")
    print("=" * 60)
    print(f"\n[STATUS] PyAutoGUI: {'INSTALLED' if installed else 'NOT INSTALLED'}")
    print("[ENV] Conda environment")
    print("[PYTHON] Using current Python interpreter")
    print("\n[USAGE] Import in Python:")
    print("  import pyautogui")
    print("  pyautogui.write('Hello')")
    print("\n[NEXT STEPS]")
    print("  1. Test the test script above")
    print("  2. Use examples for your automation tasks")
    print("  3. Check desktop-control skill for advanced features")
    print("=" * 60)

if __name__ == "__main__":
    main()
