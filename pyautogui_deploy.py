"""
PyAutoGUI Deployment Helper - Install, check, and guide PyAutoGUI usage

Provides utilities for installing PyAutoGUI, checking installation status,
and providing usage examples and test scripts.
"""
import subprocess
import sys
import logging
from typing import Tuple, Optional


def setup_logging() -> None:
    """Configure logging for deployment operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def check_package_installed(package_name: str) -> bool:
    """
    Check if a Python package is installed.

    Args:
        package_name: Name of the package to check

    Returns:
        True if package is installed, False otherwise
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Failed to check package {package_name}: {e}")
        return False


def get_package_version(package_name: str) -> Optional[str]:
    """
    Get version of an installed package.

    Args:
        package_name: Name of the package

    Returns:
        Version string if package is installed, None otherwise
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()

        return None

    except Exception as e:
        logging.error(f"Failed to get version for {package_name}: {e}")
        return None


def install_package(package_name: str, extra_packages: Optional[list] = None) -> bool:
    """
    Install a Python package using pip.

    Args:
        package_name: Name of package to install
        extra_packages: Optional list of additional packages to install

    Returns:
        True if installation succeeded, False otherwise
    """
    packages = [package_name]
    if extra_packages:
        packages.extend(extra_packages)

    try:
        logging.info(f"Installing packages: {', '.join(packages)}")

        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + packages,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            logging.info(f"Successfully installed: {package_name}")
            return True
        else:
            logging.error(f"Installation failed for: {package_name}")
            logging.error(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"Installation timed out for: {package_name}")
        return False
    except Exception as e:
        logging.error(f"Installation error for {package_name}: {e}")
        return False


def check_pyautogui_installation() -> bool:
    """
    Check if PyAutoGUI is installed and functional.

    Returns:
        True if PyAutoGUI is installed and working, False otherwise
    """
    print("=" * 60)
    print("PyAutoGUI Installation Check")
    print("=" * 60)

    try:
        import pyautogui

        print("\n[OK] PyAutoGUI is installed")

        # Get version
        version = getattr(pyautogui, '__version__', 'Unknown')
        print(f"    Version: {version}")

        # Get location
        location = getattr(pyautogui, '__file__', 'Unknown')
        print(f"    Location: {location}")

        # Test basic functions
        print("\nTesting basic functions...")

        pos = pyautogui.position()
        print(f"    Current mouse position: {pos}")

        size = pyautogui.size()
        print(f"    Screen size: {size[0]} x {size[1]}")

        return True

    except ImportError as e:
        print("\n[NOT INSTALLED] PyAutoGUI is not installed")
        print(f"    Error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Failed to test PyAutoGUI: {e}")
        return False


def install_pyautogui() -> bool:
    """
    Install PyAutoGUI and its dependencies.

    Returns:
        True if installation succeeded, False otherwise
    """
    print("\n" + "=" * 60)
    print("Installing PyAutoGUI...")
    print("=" * 60)

    # Install PyAutoGUI with Pillow
    return install_package("pyautogui", extra_packages=["pillow"])


def print_usage_examples() -> None:
    """Print PyAutoGUI usage examples."""
    print("\n" + "=" * 60)
    print("PyAutoGUI Usage Examples")
    print("=" * 60)

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


def print_test_script() -> None:
    """Print a test script for PyAutoGUI."""
    print("\n" + "=" * 60)
    print("Test Script")
    print("=" * 60)

    script_content = """
#!/usr/bin/env python3
import pyautogui
import time

# Configure
pyautogui.PAUSE = 0.5  # Delay between actions
pyautogui.FAILSAFE = True  # Enable fail-safe (move mouse to corner to cancel)

print("Starting test...")
print(f"Screen size: {pyautogui.size()}")

# Move mouse to screen center
width, height = pyautogui.size()
center_x, center_y = width // 2, height // 2

print(f"Moving to center: ({center_x}, {center_y})")
pyautogui.moveTo(center_x, center_y, duration=1)
time.sleep(0.5)

# Click
print("Clicking...")
pyautogui.click()

# Type text
print("Typing 'Hello'...")
pyautogui.write("Hello")
time.sleep(0.5)

print("Test completed!")
"""

    print(script_content)


def print_deployment_summary(installed: bool) -> None:
    """
    Print deployment summary.

    Args:
        installed: Whether PyAutoGUI is installed
    """
    print("\n" + "=" * 60)
    print("Deployment Summary")
    print("=" * 60)

    print(f"\n[STATUS] PyAutoGUI: {'INSTALLED' if installed else 'NOT INSTALLED'}")
    print("[ENV] Python environment")
    print(f"[PYTHON] Using: {sys.executable}")

    print("\n[USAGE] Import in Python:")
    print("  import pyautogui")
    print("  pyautogui.write('Hello')")

    print("\n[NEXT STEPS]")
    print("  1. Test the test script above")
    print("  2. Use examples for your automation tasks")
    print("  3. Check documentation for advanced features")

    print("=" * 60)


def main() -> int:
    """
    Main function - run PyAutoGUI deployment check.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    setup_logging()

    # Check installation status
    installed = check_pyautogui_installation()

    # Install if not present
    if not installed:
        installed = install_pyautogui()

        # Recheck after installation
        if installed:
            print("\nRechecking installation...")
            installed = check_pyautogui_installation()

    # Print usage examples
    print_usage_examples()

    # Print test script
    print_test_script()

    # Print summary
    print_deployment_summary(installed)

    return 0 if installed else 1


if __name__ == "__main__":
    sys.exit(main())
