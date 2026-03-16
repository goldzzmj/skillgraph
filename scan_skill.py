#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to call the SkillGraph API to scan a skill."""

import requests
import json
import sys

# Read skill content
skill_path = r"C:\Users\GX\.claude\skills\daily-coding\SKILL.md"
with open(skill_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Prepare request
data = {
    "skill_content": content,
    "skill_name": "daily-coding"
}

# Call API
try:
    # 禁用代理
    session = requests.Session()
    session.trust_env["HTTP_PROXY"] = ""
    session.trust_env["HTTPS_PROXY"] = ""

    response = requests.post(
        "http://localhost:8000/api/v1/scan",
        json=data,
        timeout=30
    )

    print("=" * 50)
    print("Status Code:", response.status_code)
    print("\nResponse:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

except requests.exceptions.ProxyError as e:
    # 如果代理问题，    print("Proxy error, trying without proxy...")
    session = requests.Session()
    session.trust_env["HTTP_PROXY"] = ""
    session.trust_env["HTTPS_PROXY"] = ""

    response = requests.post(
        "http://localhost:8000/api/v1/scan",
        json=data,
        timeout=30
    )

    print("=" * 50)
    print("Status Code:", response.status_code)
    print("\nResponse:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
