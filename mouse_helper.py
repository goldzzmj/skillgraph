"""
Mouse Helper - Mouse position and click automation utilities

Provides utilities for mouse position tracking and click automation.
Designed to work with various screen resolutions.
"""
import pyautogui
import time
from typing import Tuple, List
import logging


def setup_logging() -> None:
    """Configure logging for mouse operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def get_mouse_position() -> Tuple[int, int]:
    """
    Get current mouse cursor position.

    Returns:
        Tuple of (x, y) coordinates
    """
    return pyautogui.position()


def get_screen_size() -> Tuple[int, int]:
    """
    Get screen resolution.

    Returns:
        Tuple of (width, height)
    """
    return pyautogui.size()


def safe_click(x: int, y: int, delay: float = 0.1) -> bool:
    """
    Safely click at given coordinates.

    Args:
        x: X coordinate
        y: Y coordinate
        delay: Delay in seconds before click

    Returns:
        True if click succeeded, False otherwise
    """
    try:
        if delay > 0:
            time.sleep(delay)
        pyautogui.click(x, y)
        return True
    except Exception as e:
        logging.error(f"Click failed at ({x}, {y}): {e}")
        return False


def click_positions(positions: List[Tuple[int, int]], delay: float = 1.0) -> int:
    """
    Click at multiple positions sequentially.

    Args:
        positions: List of (x, y) coordinate tuples
        delay: Delay in seconds between clicks

    Returns:
        Number of successful clicks
    """
    success_count = 0

    for i, (x, y) in enumerate(positions, 1):
        logging.info(f"Attempt {i}: Clicking at ({x}, {y})")
        if safe_click(x, y, delay=0):
            success_count += 1
            time.sleep(delay)
        else:
            logging.warning(f"Failed to click at ({x}, {y})")

    return success_count


def generate_click_positions(strategy: str = 'grid') -> List[Tuple[int, int]]:
    """
    Generate click positions based on strategy.

    Args:
        strategy: Strategy name ('grid', 'center', 'scan')

    Returns:
        List of (x, y) coordinate tuples
    """
    width, height = get_screen_size()
    positions = []

    if strategy == 'center':
        # Screen center and slight offsets
        center_x, center_y = width // 2, height // 2
        positions = [
            (center_x, center_y),
            (center_x - 200, center_y),
            (center_x + 200, center_y),
            (center_x, center_y - 100),
            (center_x, center_y + 100),
        ]

    elif strategy == 'scan':
        # 3x3 grid scan
        x_positions = [width // 4, width // 2, width * 3 // 4]
        y_positions = [height // 4, height // 2, height * 3 // 4]
        positions = [(x, y) for x in x_positions for y in y_positions]

    else:  # 'grid' or default
        # 2x2 grid
        positions = [
            (width // 4, height // 4),
            (width * 3 // 4, height // 4),
            (width // 4, height * 3 // 4),
            (width * 3 // 4, height * 3 // 4),
        ]

    return positions


def show_mouse_info() -> None:
    """Display mouse and screen information."""
    pos = get_mouse_position()
    width, height = get_screen_size()

    logging.info("=" * 60)
    logging.info("Mouse Helper - Information")
    logging.info("=" * 60)
    logging.info(f"Screen size: {width}x{height}")
    logging.info(f"Current mouse position: {pos}")
    logging.info("=" * 60)


def demo_click_helper() -> int:
    """
    Demo: Click helper for common button positions.

    Returns:
        Number of successful clicks
    """
    logging.info("Mouse Helper - Click Helper Demo")
    logging.info("=" * 60)

    show_mouse_info()

    # Generate click positions
    positions = generate_click_positions(strategy='center')
    logging.info(f"\nGenerated {len(positions)} click positions")
    logging.info("Starting click attempts...")

    # Execute clicks
    success_count = click_positions(positions, delay=1.0)

    logging.info("=" * 60)
    logging.info(f"Click attempts completed!")
    logging.info(f"Successful: {success_count}/{len(positions)}")

    return success_count


def main() -> int:
    """
    Main function - runs mouse helper demo.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    setup_logging()

    try:
        demo_click_helper()
        return 0
    except KeyboardInterrupt:
        logging.info("\nInterrupted by user")
        return 0
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
