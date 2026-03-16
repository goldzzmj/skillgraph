#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to test the SkillGraph scan API
"""

import requests
import json

# Skill file path
SKILL_PATH = r"C:\Users\GX\.claude\skills\daily-coding\SKILL.md"

# Read skill content
with open(SKILL_PATH, 'r', encoding='utf-8') as f:
    skill_content = f.read()

# API endpoint
url = "http://localhost:8000/api/v1/scan"

# Prepare request payload
payload = {
    "skill_content": skill_content,
    "skill_name": "daily-coding",
    "scan_options": {
        "use_graphrag": True,
        "include_community_detection": True
    }
}

try:
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})

    # Print response
    print("Status Code:", response.status_code)
    print("Response:")
    print(json.dumps(response.json(), indent=2)

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    sys.exit(1)
