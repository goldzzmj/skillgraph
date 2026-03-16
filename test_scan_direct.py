#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct test script for SkillGraph API
No proxy issues
"""

import requests
import json

# Skill file path
SKILL_PATH = r"C:\Users\GX\.claude\skills\daily-coding\SKILL.md"

# Read skill content
with open(SKILL_PATH, 'r', encoding='utf-8') as f:
    skill_content = f.read()

# Disable proxy
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

# Call API
url = "http://localhost:8000/api/v1/scan"
data = {
    "skill_content": skill_content,
    "skill_name": "daily-coding",
    "scan_options": {
        "use_graphrag": True,
        "use_llm_extraction": False,
        "use_gat_risk_model": False,
        "include_community_detection": True,
        "include_embeddings": False,
        "output_format": "json"
    }
}

print("=" * 50)
print("Status Code:", response.status_code)
print("Response:")
print(json.dumps(response.json(), indent=2))
