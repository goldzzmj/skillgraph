import os

def simple_dir_size(path):
    """Get simple dir size using du-like approach"""
    try:
        import subprocess
        result = subprocess.run(['powershell', '-Command',
            f"(Get-ChildItem -Path '{path}' -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum"],
            capture_output=True, text=True, timeout=30)
        if result.stdout.strip():
            size = float(result.stdout.strip())
            return size
    except:
        pass
    return 0

# Alternative: use os.walk but with timeout
def get_dir_size_limited(path, max_files=10000):
    """Get directory size with file limit"""
    total_size = 0
    count = 0
    try:
        for root, dirs, files in os.walk(path):
            for file in files[:100]:  # Limit per directory
                try:
                    total_size += os.path.getsize(os.path.join(root, file))
                    count += 1
                    if count >= max_files:
                        return total_size
                except (PermissionError, FileNotFoundError):
                    continue
    except (PermissionError, FileNotFoundError):
        pass
    return total_size

# Scan specific large directories
print("Scanning key directories (this may take a moment)...")
print()

key_dirs = [
    ("Conda packages", r"D:\anaconda3\pkgs"),
    ("Windows", r"C:\Windows"),
    ("Program Files", r"C:\Program Files"),
    ("Program Files (x86)", r"C:\Program Files (x86)"),
    ("User AppData Local", r"C:\Users\GX\AppData\Local"),
    ("User AppData Roaming", r"C:\Users\GX\AppData\Roaming"),
    ("User Documents", r"C:\Users\GX\Documents"),
    ("User Downloads", r"C:\Users\GX\Downloads"),
    ("ProgramData", r"C:\ProgramData"),
]

for name, path in key_dirs:
    if not os.path.exists(path):
        print(f"{name:30s}: Not found")
        continue
    print(f"{name:30s}: Scanning...", end='', flush=True)
    size = get_dir_size_limited(path, max_files=5000)
    if size > 0:
        print(f" ~{size/(1024**3):8.2f} GB")
    else:
        print(f" Cannot scan")
