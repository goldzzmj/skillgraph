#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final test script for SkillGraph API scan
Completely bypass proxy
"""

import os
import sys

# Remove proxy settings
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_proxy', None)
os.environ['NO_PROXY'] = '1'

import requests
import json

# Read skill file
skill_path = r'C:\Users\GX\.claude\skills\daily-coding\SKILL.md'
with open(skill_path, 'r', encoding='utf-8') as f:
    skill_content = f.read()

print("Skill content read successfully")

# Prepare request
data = {
    "skill_content": skill_content,
    "skill_name": "daily-coding"
}

# Call API
print("Calling API...")
try:
    response = requests.post(
        "http://localhost:8000/api/v1/scan",
        json=data,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
