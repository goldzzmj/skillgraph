"""
Screenshot Utility - Capture and save screenshots

Provides utilities for taking screenshots with automatic naming,
directory creation, and metadata recording.
"""
import os
import logging
from datetime import datetime
from typing import Optional, Tuple
from PIL import ImageGrab


def setup_logging() -> None:
    """Configure logging for screenshot operations."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def ensure_directory(path: str) -> bool:
    """
    Ensure directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {path}: {e}")
        return False


def generate_filename(
    prefix: str = "screenshot",
    extension: str = "png",
    timestamp: Optional[str] = None
) -> str:
    """
    Generate a filename with timestamp.

    Args:
        prefix: Filename prefix
        extension: File extension (without dot)
        timestamp: Optional timestamp string, defaults to current time

    Returns:
        Generated filename
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{prefix}_{timestamp}.{extension}"


def take_screenshot(
    output_path: str,
    region: Optional[Tuple[int, int, int, int]] = None
) -> bool:
    """
    Take a screenshot and save to file.

    Args:
        output_path: Full path where screenshot will be saved
        region: Optional tuple (left, top, width, height) for partial screenshot

    Returns:
        True if screenshot was saved successfully, False otherwise
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(output_path)
        if parent_dir and not os.path.exists(parent_dir):
            if not ensure_directory(parent_dir):
                return False

        # Capture screenshot
        if region:
            screenshot = ImageGrab.grab(bbox=region)
        else:
            screenshot = ImageGrab.grab()

        # Save screenshot
        screenshot.save(output_path)
        file_size = os.path.getsize(output_path)
        width, height = screenshot.size

        logging.info(f"Screenshot saved: {output_path}")
        logging.info(f"Size: {width}x{height}, File size: {file_size:,} bytes")

        return True

    except Exception as e:
        logging.error(f"Failed to take screenshot: {e}")
        return False


def take_screenshot_to_dir(
    directory: str,
    prefix: str = "screenshot",
    extension: str = "png",
    region: Optional[Tuple[int, int, int, int]] = None
) -> Optional[str]:
    """
    Take screenshot and save to directory with auto-generated filename.

    Args:
        directory: Target directory
        prefix: Filename prefix
        extension: File extension (without dot)
        region: Optional tuple (left, top, width, height) for partial screenshot

    Returns:
        Full path of saved screenshot, or None if failed
    """
    try:
        # Ensure directory exists
        if not ensure_directory(directory):
            return None

        # Generate filename
        filename = generate_filename(prefix, extension)
        output_path = os.path.join(directory, filename)

        # Take screenshot
        if take_screenshot(output_path, region):
            return output_path
        else:
            return None

    except Exception as e:
        logging.error(f"Failed to take screenshot to directory: {e}")
        return None


def get_screen_info() -> Tuple[int, int]:
    """
    Get current screen resolution.

    Returns:
        Tuple of (width, height)
    """
    try:
        screenshot = ImageGrab.grab()
        return screenshot.size
    except Exception as e:
        logging.error(f"Failed to get screen info: {e}")
        return (0, 0)


def main() -> int:
    """
    Main function - demonstrates screenshot capture.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    setup_logging()

    logging.info("=" * 60)
    logging.info("Screenshot Utility")
    logging.info("=" * 60)

    # Get screen info
    width, height = get_screen_info()
    logging.info(f"Screen resolution: {width}x{height}")

    # Configuration
    output_dir = r"F:\openclaw_data"
    prefix = "screenshot"

    logging.info(f"Output directory: {output_dir}")
    logging.info("Taking screenshot...")

    # Take screenshot
    output_path = take_screenshot_to_dir(output_dir, prefix)

    if output_path:
        logging.info("=" * 60)
        logging.info(f"Success! Screenshot saved to:")
        logging.info(f"  {output_path}")
        logging.info("=" * 60)
        return 0
    else:
        logging.error("Failed to take screenshot")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
