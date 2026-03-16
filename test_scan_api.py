#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple API test script for SkillGraph security scan
"""

import requests
import json
import os

# Disable proxy
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['ALL_PROXY'] = ''

def main():
    print("=" * 60)
    print("SkillGraph API Scan Test")
    print("=" * 60)

    # Read skill file
    skill_path = r'C:\Users\GX\.claude\skills\daily-coding\SKILL.md'
    print(f"Reading skill file: {skill_path}")

    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    print(f"Skill content length: {len(skill_content)} characters")

    # Prepare request data
    data = {
        "skill_content": skill_content,
    }

    # Call API
    url = "http://localhost:8000/api/v1/scan"

    print(f"Calling API: {url}")
    print("Request data prepared")

    try:
        response = requests.post(url, json=data,        timeout=30)

        print(f"Response Status: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")


if __name__ == "__main__":
