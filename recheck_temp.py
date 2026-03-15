import os

temp_path = r"C:\Users\GX\AppData\Local\Temp"

print(f"Re-checking {temp_path}...")
print()

if not os.path.exists(temp_path):
    print("Directory does not exist!")
    exit(0)

# Check top-level directories
print("Top-level directories in Temp:")
total_size = 0
total_files = 0

for entry in os.scandir(temp_path):
    try:
        if entry.is_dir(follow_symlinks=False):
            size = 0
            count = 0
            for subentry in os.scandir(entry.path):
                try:
                    if subentry.is_file(follow_symlinks=False):
                        size += subentry.stat().st_size
                        count += 1
                except (PermissionError, FileNotFoundError):
                    continue
            total_size += size
            total_files += count
            if size > 10 * 1024 * 1024:  # > 10MB
                print(f"  {size/(1024**2):8.1f} MB ({count:5d} files) - {entry.name}")
        elif entry.is_file(follow_symlinks=False):
            total_size += entry.stat().st_size
            total_files += 1
    except (PermissionError, FileNotFoundError):
        continue

print()
print(f"Total: {total_size/(1024**3):.3f} GB, {total_files} files")
