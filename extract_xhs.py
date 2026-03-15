#!/usr/bin/env python3
import zipfile
import os

zip_path = r"C:\Users\GX\xiaohongshu-mcp\server.zip"
extract_path = r"C:\Users\GX\xiaohongshu-mcp"

print("Extracting zip file...")
print(f"From: {zip_path}")
print(f"To: {extract_path}\n")

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        print("Files in zip:")
        for file in zip_ref.namelist():
            print(f"  - {file}")

        print("\nExtracting...")
        zip_ref.extractall(extract_path)

        print("\nExtraction complete!")

    # 列出解压后的文件
    print("\nExtracted files:")
    for root, dirs, files in os.walk(extract_path):
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            print(f"  - {file} ({size} bytes)")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
