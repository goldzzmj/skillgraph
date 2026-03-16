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
    # Read skill file
    skill_path = r'C:\Users\GX\.claude\skills\daily-coding\SKILL.md'
    print(f"Reading skill file: {skill_path}")

    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    print(f"Skill content length: {len(skill_content)} characters")

    # API endpoint
    url = "http://localhost:8000/api/v1/scan"

    # Prepare request
    payload = {
        "skill_content": skill_content,
    }

    headers = {
        "Content-Type": " "application/json"
    }

    print(f"Calling API: {url}")
    print(f"Payload size: {len(json.dumps(payload))} bytes")

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print("\n" + "=" * 60)
            print("SCAN RESULT:")
            print("=" * 60)
            print(json.dumps(result, indent=2,        else:
            print(f"\nERROR: Status {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SkillGraph API Scan Test")
    print("=" * 60)
