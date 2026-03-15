import os

def get_top_dirs(path, limit=20):
    """Get largest directories in path (non-recursive)"""
    results = []
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_dir(follow_symlinks=False):
                    # Get size by summing files in this dir only (not recursive for speed)
                    size = 0
                    count = 0
                    for subentry in os.scandir(entry.path):
                        try:
                            if subentry.is_file(follow_symlinks=False):
                                size += subentry.stat().st_size
                                count += 1
                        except (PermissionError, FileNotFoundError):
                            continue
                    results.append((entry.name, entry.path, size, count))
            except (PermissionError, FileNotFoundError):
                continue
    except (PermissionError, FileNotFoundError):
        pass
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:limit]

print("Scanning AppData\\Roaming for large directories...")
print()

roaming_path = r"C:\Users\GX\AppData\Roaming"
results = get_top_dirs(roaming_path, limit=30)

print("Top directories in AppData\\Roaming:")
print()
for name, path, size, count in results:
    if size > 50 * 1024 * 1024:  # > 50MB
        print(f"{size/(1024**3):8.3f} GB ({count:5d} files) - {name}")

print()
print("="*80)
print()

# Scan a few key directories recursively
print("Deep scan of selected large directories...")
print()

# Get top 3 largest for deep scan
top3 = results[:3]
for name, path, size, count in top3:
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
    print(f" {total/(1024**3):8.3f} GB ({file_count} files)")
