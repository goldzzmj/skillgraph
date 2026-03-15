import os

roaming_path = r"C:\Users\GX\AppData\Roaming"

print("All directories in AppData\\Roaming with sizes (top level only):")
print()

results = []
for entry in os.scandir(roaming_path):
    try:
        if entry.is_dir(follow_symlinks=False):
            # Get size of files in this directory only
            size = 0
            count = 0
            for subentry in os.scandir(entry.path):
                try:
                    if subentry.is_file(follow_symlinks=False):
                        size += subentry.stat().st_size
                        count += 1
                except (PermissionError, FileNotFoundError):
                    continue
            results.append((entry.name, size, count))
    except (PermissionError, FileNotFoundError):
        continue

results.sort(key=lambda x: x[1], reverse=True)

for name, size, count in results:
    if size > 1 * 1024 * 1024:  # > 1MB
        print(f"{size/(1024**2):8.1f} MB ({count:5d} files) - {name}")

print()
print("="*80)
print()

# Now do recursive scan for top 5
print("Recursive scan of top 5 largest directories:")
print()

for name, size, count in results[:5]:
    path = os.path.join(roaming_path, name)
    print(f"Scanning {name}...", end='', flush=True)
    total = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    total += os.path.getsize(os.path.join(root, file))
                    file_count += 1
                except (PermissionError, FileNotFoundError):
                    continue
    except (PermissionError, FileNotFoundError):
        pass
    print(f" {total/(1024**2):8.1f} MB ({file_count} files)")
