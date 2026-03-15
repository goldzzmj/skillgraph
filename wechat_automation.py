"""
WeChat Automation - Automate WeChat message sending

Provides automation for WeChat operations including searching contacts
and sending messages with screenshot debugging support.
"""
import os
import logging
import time
from datetime import datetime
from typing import Tuple, List, Optional
from PIL import Image, ImageDraw
import pyautogui


def setup_logging() -> None:
    """Configure logging for WeChat automation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def get_output_directory() -> str:
    """
    Get output directory for screenshots.

    Returns:
        Output directory path
    """
    return r"F:\openclaw_data"


def ensure_output_directory(path: str) -> bool:
    """
    Ensure output directory exists.

    Args:
        path: Directory path

    Returns:
        True if directory exists or was created
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False


def screenshot_and_mark(
    x: int,
    y: int,
    radius: int = 80,
    label: str = ""
) -> Optional[str]:
    """
    Take screenshot and mark a position with ellipse.

    Args:
        x: X coordinate to mark
        y: Y coordinate to mark
        radius: Radius of the marking ellipse
        label: Label text to add to the screenshot

    Returns:
        Path to saved screenshot, or None if failed
    """
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot()
        img_rgb = screenshot.convert('RGB')
        draw = ImageDraw.Draw(img_rgb)

        # Draw ellipse at position
        draw.ellipse(
            [x - radius, y - radius // 2, x + radius, y + radius // 2],
            outline='red',
            width=5
        )

        # Add label if provided
        if label:
            draw.text((x - radius, y - radius - 40), label, fill='red')

        # Save screenshot
        output_dir = get_output_directory()
        if not ensure_output_directory(output_dir):
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{label}_{timestamp}.png" if label else f"marked_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        img_rgb.save(filepath)
        logging.info(f"Saved screenshot: {filepath}")
        return filepath

    except Exception as e:
        logging.error(f"Failed to take screenshot: {e}")
        return None


def find_color_in_screenshot(
    target_color: Tuple[int, int, int],
    tolerance: int = 10,
    x_range: Optional[Tuple[int, int]] = None,
    y_range: Optional[Tuple[int, int]] = None
) -> List[Tuple[int, int]]:
    """
    Find pixels of a specific color in screenshot.

    Args:
        target_color: Target RGB color tuple
        tolerance: Color matching tolerance
        x_range: Optional tuple (min_x, max_x) to limit search area
        y_range: Optional tuple (min_y, max_y) to limit search area

    Returns:
        List of (x, y) coordinate tuples
    """
    try:
        screenshot = pyautogui.screenshot()
        img_rgb = screenshot.convert('RGB')
        width, height = screenshot.size
        pixels = img_rgb.load()

        # Default ranges
        if x_range is None:
            x_range = (0, width)
        if y_range is None:
            y_range = (0, height)

        positions = []

        for y in range(y_range[0], y_range[1]):
            for x in range(x_range[0], x_range[1]):
                r, g, b = pixels[x, y]
                if (abs(r - target_color[0]) < tolerance and
                    abs(g - target_color[1]) < tolerance and
                    abs(b - target_color[2]) < tolerance):
                    positions.append((x, y))

        return positions

    except Exception as e:
        logging.error(f"Failed to find color: {e}")
        return []


def find_and_click_search() -> bool:
    """
    Find and click WeChat search box.

    Returns:
        True if search box was found and clicked, False otherwise
    """
    logging.info("=== Step 1: Find and Click Search Box ===")

    try:
        # Get screen dimensions
        width, height = pyautogui.size()

        # Define search area (top-right corner)
        x_range = (width - 800, width)
        y_range = (50, 150)

        # Light gray color (search box background)
        LIGHT_GRAY = (240, 240, 240)
        TOLERANCE = 10

        # Find search box pixels
        search_positions = find_color_in_screenshot(
            LIGHT_GRAY,
            TOLERANCE,
            x_range,
            y_range
        )

        if not search_positions:
            logging.warning("Search box not found")
            return False

        # Calculate average position
        avg_x = sum(p[0] for p in search_positions) // len(search_positions)
        avg_y = sum(p[1] for p in search_positions) // len(search_positions)

        logging.info(f"Found search box at ({avg_x}, {avg_y})")

        # Take screenshot and mark position
        screenshot_and_mark(avg_x, avg_y, 100, "Search_Box")

        # Click search box
        pyautogui.click(avg_x, avg_y)
        time.sleep(1)

        return True

    except Exception as e:
        logging.error(f"Failed to find and click search box: {e}")
        return False


def search_contact(contact_name: str = "郑政隆") -> bool:
    """
    Search for a contact in WeChat.

    Args:
        contact_name: Name of contact to search for

    Returns:
        True if search was completed, False otherwise
    """
    logging.info(f"=== Step 2: Search for '{contact_name}' ===")

    try:
        # Clear existing text and type contact name
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write(contact_name)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)

        logging.info(f"Search completed for '{contact_name}'")
        return True

    except Exception as e:
        logging.error(f"Failed to search contact: {e}")
        return False


def click_search_result() -> bool:
    """
    Click on search result.

    Returns:
        True if click was successful, False otherwise
    """
    logging.info("=== Step 3: Click Search Result ===")

    try:
        # Calculate search result position
        width, height = pyautogui.size()
        result_x = width - 500
        result_y = 180

        # Take screenshot and mark position
        screenshot_and_mark(result_x, result_y, 100, "Search_Result")

        # Click search result
        pyautogui.click(result_x, result_y)
        time.sleep(2)

        return True

    except Exception as e:
        logging.error(f"Failed to click search result: {e}")
        return False


def send_message(message: str = "我是openclaw") -> bool:
    """
    Send a message to current chat.

    Args:
        message: Message text to send

    Returns:
        True if message was sent, False otherwise
    """
    logging.info(f"=== Step 4: Send Message '{message}' ===")

    try:
        # Calculate input box position
        width, height = pyautogui.size()
        input_x = width // 2
        input_y = height - 150

        # Take screenshot and mark input box
        screenshot_and_mark(input_x, input_y, 120, "Input_Box")

        # Click input box
        pyautogui.click(input_x, input_y)
        time.sleep(0.5)

        # Clear existing text and type message
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.write(message)
        time.sleep(0.5)

        # Send message
        pyautogui.press('enter')
        time.sleep(1)

        logging.info("Message sent successfully")
        return True

    except Exception as e:
        logging.error(f"Failed to send message: {e}")
        return False


def main() -> int:
    """
    Main function - run WeChat automation workflow.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    setup_logging()

    logging.info("=" * 60)
    logging.info("WeChat Automation Started")
    logging.info("=" * 60)

    try:
        # Run automation workflow
        success = True

        if not find_and_click_search():
            success = False

        if not search_contact():
            success = False

        if not click_search_result():
            success = False

        if not send_message():
            success = False

        logging.info("=" * 60)
        if success:
            logging.info("All steps completed successfully!")
        else:
            logging.warning("Some steps failed. Check logs for details.")
        logging.info("=" * 60)

        return 0 if success else 1

    except Exception as e:
        logging.error(f"Automation failed with error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
