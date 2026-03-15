import os
import shutil
import glob

def clean_dir(path, name):
    """清理指定目录"""
    if not os.path.exists(path):
        print(f"[ERROR] {name}: Directory not found - {path}")
        return 0

    total_size = 0
    file_count = 0

    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    total_size += size
                    file_count += 1
                    os.remove(file_path)
                except (PermissionError, OSError) as e:
                    pass  # Skip files we can't access

        # Try to remove empty directories
        for root, dirs, files in os.walk(path, topdown=False):
            for dir in dirs:
                try:
                    os.rmdir(os.path.join(root, dir))
                except OSError:
                    pass  # Skip directories we can't remove

        size_mb = total_size / (1024 * 1024)
        print(f"[OK] {name}: Cleaned {file_count} files, freed {size_mb:.2f} MB")

    except Exception as e:
        print(f"[ERROR] {name}: Clean failed - {e}")

    return total_size

def main():
    print("开始清理...")
    print("=" * 60)

    total_freed = 0

    # 清理临时文件
    total_freed += clean_dir(r"C:\Users\GX\AppData\Local\Temp", "临时文件")

    # 清理Chrome缓存
    chrome_cache = r"C:\Users\GX\AppData\Local\Google\Chrome\User Data\Default\Cache"
    total_freed += clean_dir(chrome_cache, "Chrome缓存")

    # 清理Edge缓存
    edge_cache = r"C:\Users\GX\AppData\Local\Microsoft\Edge\User Data\Default\Cache"
    total_freed += clean_dir(edge_cache, "Edge缓存")

    # 清理Windows临时文件
    total_freed += clean_dir(r"C:\Windows\Temp", "Windows临时文件")

    # 清理Prefetch
    total_freed += clean_dir(r"C:\Windows\Prefetch", "Prefetch缓存")

    print("=" * 60)
    total_mb = total_freed / (1024 * 1024)
    print(f"总计释放: {total_mb:.2f} MB ({total_mb/1024:.2f} GB)")

if __name__ == "__main__":
    main()
