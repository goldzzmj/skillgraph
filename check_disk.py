import os
import shutil
from collections import defaultdict

# Get C drive space
disk_usage = shutil.disk_usage('C:\\')
total_gb = disk_usage.total / (1024**3)
used_gb = disk_usage.used / (1024**3)
free_gb = disk_usage.free / (1024**3)

print(f"C Drive Status:")
print(f"  Total: {total_gb:.2f} GB")
print(f"  Used:  {used_gb:.2f} GB")
print(f"  Free:  {free_gb:.2f} GB")
print(f"  Usage: {(used_gb/total_gb)*100:.1f}%")
print()

# Find large directories in C:\Users (common space hog)
print("Scanning C:\\Users\\ for large directories...")
print()

user_dirs = []
try:
    for root, dirs, files in os.walk('C:\\Users\\GX'):
        if 'AppData' in root or 'node_modules' in root or '.git' in root:
            continue
        try:
            size = sum(os.path.getsize(os.path.join(root, f)) for f in files if os.path.isfile(os.path.join(root, f)))
            if size > 100 * 1024 * 1024:  # > 100MB
                user_dirs.append((root, size))
        except (PermissionError, FileNotFoundError):
            continue

    # Sort by size
    user_dirs.sort(key=lambda x: x[1], reverse=True)

    for path, size in user_dirs[:20]:
        print(f"{size/(1024**2):6.1f} MB - {path}")
except Exception as e:
    print(f"Error: {e}")

print()
print("Scanning for common cleanup targets...")
print()

cleanup_candidates = {
    "Windows Temp": os.environ.get('TEMP', ''),
    "User Temp": os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp'),
    "Prefetch": os.path.join('C:\\', 'Windows', 'Prefetch'),
    "Recycle Bin": os.path.join('C:\\', '$Recycle.Bin'),
    "Windows Update Cache": os.path.join('C:\\', 'Windows', 'SoftwareDistribution', 'Download'),
}

for name, path in cleanup_candidates.items():
    if not path or not os.path.exists(path):
        continue
    try:
        total_size = 0
        count = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                    count += 1
                except (PermissionError, FileNotFoundError):
                    continue
        print(f"{name:25s}: {count:5d} files, {total_size/(1024**2):8.1f} MB")
    except (PermissionError, FileNotFoundError):
        print(f"{name:25s}: Cannot access")
