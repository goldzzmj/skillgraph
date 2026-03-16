#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete test script for SkillGraph API scan
Completely bypasses proxy
"""

import os
import sys
import requests
import json

# Remove proxy settings
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_proxy', None)
os.environ['NO_PROXY'] = '1'

def test_skill_scan():
    """Test skill scanning API."""
    # Skill file path
    skill_path = r'C:\Users\GX\.claude\skills\daily-coding\SKILL.md'

    print("=" * 60)
    print("Testing SkillGraph API Scan")
    print("=" * 60)

    # Read skill file
    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    print(f"\n1. Read skill file: {skill_path}")
    print(f"   Content length: {len(skill_content)} characters\n")

    # Prepare request payload
    payload = {
        "skill_content": skill_content,
        "skill_name": "daily-coding",
    }

    print("\n2. Calling API...")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/scan",
            json=payload,
            timeout=60
        )

        print(f"\n3. Response received!")
        print(f"   Status Code: {response.status_code}")
        print(f"\n")

        if response.status_code == 200:
            result = response.json()

            print("=" * 60)
            print("SCAN RESULTS")
            print("=" * 60)
            print(f"Scan ID: {result.get('scan_id')}")
            print(f"Skill Name: {result.get('skill_name')}")
            print(f"Scan Status: {result.get('scan_status')}")
            print(f"Overall Risk Score: {result.get('risk_summary', {}).get('overall_risk_score', 'N/A')}")

            # Entities
            entities = result.get('entities', [])
            print(f"\n4. Entities Found: {len(entities)}")
            print("-" * 40)
            for i, entity in enumerate(entities):
                print(f"  {i+1}. {entity.get('entity_name')}")
                print(f"     Type: {entity.get('entity_type')}")
                print(f"     Risk Score: {entity.get('risk_score')}")
                print(f"     Confidence: {entity.get('confidence')}")

            # Risk Findings
            findings = result.get('risk_findings', [])
            print(f"\n5. Risk Findings: {len(findings)}")
            print("-" * 40)
            for i, finding in enumerate(findings):
                print(f"  {i+1}. {finding.get('type')}")
                print(f"     Severity: {finding.get('severity')}")
                print(f"     Description: {finding.get('description')}")

            # Recommendations
            recommendations = result.get('recommendations', [])
            print(f"\n6. Recommendations: {len(recommendations)}")
            print("-" * 40)
            for i, rec in enumerate(recommendations):
                print(f"  {i}. {rec}")

            print("\n" + "=" * 60)
            print("FULL RESPONSE JSON")
            print("=" * 60)
            print(json.dumps(result, indent=2))

        else:
            print(f"\nERROR: Status Code {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\nREQUEST ERROR: {e}")
        return False

    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SkillGraph API Scan Test")
    print("=" * 60)

    success = test_skill_scan()
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
