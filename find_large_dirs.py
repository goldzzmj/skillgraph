import os
from pathlib import Path

def get_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_size(entry.path)
    except (PermissionError, OSError):
        pass
    return total

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def scan_directory(base_path, depth=2):
    print(f"\nScanning {base_path} (depth={depth})...")
    large_dirs = []

    try:
        for entry in os.scandir(base_path):
            if entry.is_dir():
                try:
                    size = get_size(entry.path)
                    large_dirs.append((entry.name, entry.path, size))
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass

    # Sort by size (largest first)
    large_dirs.sort(key=lambda x: x[2], reverse=True)

    print(f"\nTop 20 largest directories in {base_path}:")
    print("-" * 80)
    print(f"{'Size':<15} {'Name':<30}")
    print("-" * 80)

    for name, path, size in large_dirs[:20]:
        print(f"{format_size(size):<15} {name[:30]:<30}")

if __name__ == "__main__":
    # Scan common user directories
    user_path = "C:\\Users\\GX"
    scan_directory(user_path)

    # Scan AppData
    appdata_path = os.path.join(user_path, "AppData")
    if os.path.exists(appdata_path):
        scan_directory(appdata_path)

    # Scan C: drive root (limited depth)
    print("\nScanning C:\\ drive (depth=1)...")
    large_dirs = []
    for entry in os.scandir("C:\\"):
        if entry.is_dir():
            try:
                size = get_size(entry.path)
                large_dirs.append((entry.name, entry.path, size))
            except (PermissionError, OSError):
                pass

    large_dirs.sort(key=lambda x: x[2], reverse=True)

    print(f"\nTop 10 largest directories on C:\\ drive:")
    print("-" * 80)
    print(f"{'Size':<15} {'Name':<30}")
    print("-" * 80)

    for name, path, size in large_dirs[:10]:
        print(f"{format_size(size):<15} {name[:30]:<30}")
