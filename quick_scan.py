import os
import shutil

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

# Quick scan of key directories
key_paths = {
    "Windows Temp": os.environ.get('TEMP', ''),
    "Conda Packages": r"D:\anaconda3\pkgs",
    "User Temp": os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp'),
    "Windows Update Cache": r"C:\Windows\SoftwareDistribution\Download",
    "Browser Cache": os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
}

def get_dir_size(path):
    try:
        if not os.path.exists(path):
            return 0, 0
        total_size = 0
        count = 0
        for entry in os.listdir(path):
            try:
                entry_path = os.path.join(path, entry)
                if os.path.isfile(entry_path):
                    total_size += os.path.getsize(entry_path)
                    count += 1
                elif os.path.isdir(entry_path):
                    # Count dir but don't recurse for speed
                    count += 1
            except (PermissionError, FileNotFoundError):
                continue
        return total_size, count
    except (PermissionError, FileNotFoundError):
        return 0, 0

print("Quick scan of common cleanup targets:")
print()
for name, path in key_paths.items():
    if not path:
        print(f"{name:25s}: Path not set")
        continue
    exists = os.path.exists(path)
    print(f"{name:25s}: {'Exists' if exists else 'Not found'}", end='')
    if exists:
        size, count = get_dir_size(path)
        print(f" - {count} files, {size/(1024**2):.1f} MB")
    else:
        print()

print()
print("Checking for large directories in user profile...")
print()

# Get top-level directories size
base_path = os.path.expanduser('~')
for item in os.listdir(base_path):
    try:
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            size = 0
            count = 0
            for entry in os.listdir(item_path):
                try:
                    entry_path = os.path.join(item_path, entry)
                    if os.path.isfile(entry_path):
                        size += os.path.getsize(entry_path)
                        count += 1
                except (PermissionError, FileNotFoundError):
                    continue
            if size > 50 * 1024 * 1024:  # > 50MB
                print(f"{item:30s}: {count:5d} files, {size/(1024**2):8.1f} MB")
    except (PermissionError, FileNotFoundError):
        continue
