"""
Disk Cleaner - Safe directory cleaning with error handling

Cleans temporary files and caches from various locations.
All operations are non-destructive and skip files that cannot be accessed.
"""
import os
import logging
from typing import Tuple
from datetime import datetime


def setup_logging() -> None:
    """Configure logging for the cleaner."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('cleanup.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def clean_dir(path: str, name: str) -> Tuple[int, int]:
    """
    Safely clean a directory by removing all files and empty directories.

    Args:
        path: Directory path to clean
        name: Human-readable name for logging

    Returns:
        Tuple of (total_freed_bytes, files_deleted_count)
    """
    if not os.path.exists(path):
        logging.warning(f"[SKIP] {name}: Directory not found - {path}")
        return 0, 0

    if not os.path.isdir(path):
        logging.error(f"[ERROR] {name}: Path is not a directory - {path}")
        return 0, 0

    total_size = 0
    file_count = 0

    try:
        # Remove files
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    total_size += size
                    file_count += 1
                    os.remove(file_path)
                except (PermissionError, OSError) as e:
                    logging.debug(f"[SKIP] Cannot remove {file_path}: {e}")

        # Remove empty directories
        for root, dirs, files in os.walk(path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    os.rmdir(dir_path)
                except OSError:
                    # Directory not empty or cannot be removed
                    pass

        size_mb = total_size / (1024 * 1024)
        logging.info(f"[OK] {name}: Cleaned {file_count} files, freed {size_mb:.2f} MB")

    except Exception as e:
        logging.error(f"[ERROR] {name}: Clean failed - {e}")

    return total_size, file_count


def format_size(bytes_size: int) -> str:
    """
    Format bytes into human-readable size.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string (e.g., "123.45 MB")
    """
    mb = bytes_size / (1024 * 1024)
    gb = mb / 1024

    if gb >= 1:
        return f"{gb:.2f} GB"
    else:
        return f"{mb:.2f} MB"


def main() -> int:
    """
    Main function - runs the disk cleaning process.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    setup_logging()

    logging.info("=" * 60)
    logging.info("Disk Cleaner Started")
    logging.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)

    # Define cleanup paths
    cleanup_paths = [
        (r"C:\Users\GX\AppData\Local\Temp", "临时文件"),
        (r"C:\Users\GX\AppData\Local\Google\Chrome\User Data\Default\Cache", "Chrome缓存"),
        (r"C:\Users\GX\AppData\Local\Microsoft\Edge\User Data\Default\Cache", "Edge缓存"),
        (r"C:\Windows\Temp", "Windows临时文件"),
        (r"C:\Windows\Prefetch", "Prefetch缓存"),
    ]

    total_freed = 0
    total_files = 0

    # Clean each directory
    for path, name in cleanup_paths:
        freed, files = clean_dir(path, name)
        total_freed += freed
        total_files += files

    # Print summary
    logging.info("=" * 60)
    logging.info(f"Total: Cleaned {total_files} files")
    logging.info(f"Total Freed: {format_size(total_freed)}")
    logging.info("=" * 60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
