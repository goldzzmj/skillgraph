#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple API test for SkillGraph security scan"""

import requests
import json
import os

# Disable proxy
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

def main():
    print("=" * 60)
    print("SkillGraph API Scan Test")
    print("=" * 60)

    # Read skill file
    skill_path = r'C:\Users\GX\.claude\skills\daily-coding\SKILL.md'
    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    print(f"Skill file: {skill_path}")
    print(f"Content length: {len(skill_content)} chars")

    # Prepare request
    data = {"skill_content": skill_content}

    # Call API
    url = "http://localhost:8000/api/v1/scan"
    print(f"Calling: {url}")

    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
