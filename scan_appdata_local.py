import os
import time

def scan_directory(path, max_depth=2):
    """Scan directory with depth limit"""
    results = []
    try:
        for root, dirs, files in os.walk(path):
            depth = root.replace(path, '').count(os.sep)
            if depth > max_depth:
                dirs[:] = []  # Don't go deeper
                continue

            size = 0
            file_count = 0
            for file in files:
                try:
                    size += os.path.getsize(os.path.join(root, file))
                    file_count += 1
                except (PermissionError, FileNotFoundError):
                    continue

            if size > 10 * 1024 * 1024:  # > 10MB
                rel_path = os.path.relpath(root, path)
                results.append((rel_path, size, file_count))
    except (PermissionError, FileNotFoundError):
        pass
    results.sort(key=lambda x: x[1], reverse=True)
    return results

print("Scanning AppData\\Local (this will take a while)...")
print()

local_path = r"C:\Users\GX\AppData\Local"
start_time = time.time()

results = scan_directory(local_path, max_depth=3)

elapsed = time.time() - start_time
print(f"Scan completed in {elapsed:.1f} seconds")
print()

print("Top directories in AppData\\Local (>10MB):")
print()

for rel_path, size, count in results[:30]:
    print(f"{size/(1024**2):8.1f} MB ({count:6d} files) - {rel_path}")

print()
print("="*80)
print()
print(f"Total scanned: {len(results)} directories")
print()
print("Now doing deeper scan of top 5 directories...")
print()

top5 = results[:5]
for rel_path, size, count in top5:
    full_path = os.path.join(local_path, rel_path)
    print(f"Deep scanning {rel_path}...", end='', flush=True)
    total = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(full_path):
            for file in files:
                try:
                    total += os.path.getsize(os.path.join(root, file))
                    file_count += 1
                except (PermissionError, FileNotFoundError):
                    continue
    except (PermissionError, FileNotFoundError):
        pass
    print(f" {total/(1024**2):8.1f} MB ({file_count} files)")
