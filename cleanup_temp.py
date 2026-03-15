import os
import shutil

temp_path = r"C:\Users\GX\AppData\Local\Temp"

print("Starting cleanup of Temp directory...")
print(f"Path: {temp_path}")
print()

# Check if directory exists
if not os.path.exists(temp_path):
    print("Temp directory does not exist!")
    exit(0)

# Get size before cleanup
print("Calculating size before cleanup...")
size_before = 0
count_before = 0
for root, dirs, files in os.walk(temp_path):
    for file in files:
        try:
            size_before += os.path.getsize(os.path.join(root, file))
            count_before += 1
        except (PermissionError, FileNotFoundError):
            continue

print(f"Before: {size_before/(1024**3):.2f} GB, {count_before} files")
print()

# Delete files (skip directories that are in use)
print("Deleting files...")
deleted_count = 0
deleted_size = 0
errors = 0

for root, dirs, files in os.walk(temp_path, topdown=False):
    for file in files:
        try:
            file_path = os.path.join(root, file)
            size = os.path.getsize(file_path)
            os.remove(file_path)
            deleted_size += size
            deleted_count += 1
            if deleted_count % 1000 == 0:
                print(f"  Deleted {deleted_count} files ({deleted_size/(1024**3):.2f} GB)...")
        except (PermissionError, FileNotFoundError, OSError) as e:
            errors += 1
            continue

    # Try to delete empty directories
    for dir_name in dirs:
        try:
            dir_path = os.path.join(root, dir_name)
            os.rmdir(dir_path)
        except:
            continue

print()
print(f"Cleanup completed!")
print(f"Deleted: {deleted_count} files, {deleted_size/(1024**3):.2f} GB")
print(f"Errors: {errors} (files in use)")
print()

# Get size after cleanup
print("Calculating size after cleanup...")
size_after = 0
count_after = 0
for root, dirs, files in os.walk(temp_path):
    for file in files:
        try:
            size_after += os.path.getsize(os.path.join(root, file))
            count_after += 1
        except (PermissionError, FileNotFoundError):
            continue

print(f"After: {size_after/(1024**3):.2f} GB, {count_after} files")
print()
print(f"Freed space: {(size_before - size_after)/(1024**3):.2f} GB")
