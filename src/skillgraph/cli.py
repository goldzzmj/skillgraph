#!/usr/bin/env python3
"""
SkillGraph CLI

Command-line interface for skill security scanning.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from skillgraph.parser import SkillParser
from skillgraph.rules import RiskDetector
from skillgraph.graph import GraphBuilder


def main():
    parser = argparse.ArgumentParser(
        prog='skillgraph',
        description='SkillGraph - Agent Skills Security Scanner'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan a skill file')
    scan_parser.add_argument('file', type=str, help='Path to skill file')
    scan_parser.add_argument('-o', '--output', type=str, help='Output file for report')
    scan_parser.add_argument('-f', '--format', choices=['text', 'json'], default='text',
                            help='Output format')
    scan_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    # Visualize command
    viz_parser = subparsers.add_parser('viz', help='Launch visualization app')
    viz_parser.add_argument('-p', '--port', type=int, default=8501, help='Port number')
    viz_parser.add_argument('file', type=str, nargs='?', help='Optional skill file to visualize')

    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse a skill file')
    parse_parser.add_argument('file', type=str, help='Path to skill file')
    parse_parser.add_argument('-o', '--output', type=str, help='Output JSON file')

    args = parser.parse_args()

    if args.command == 'scan':
        cmd_scan(args)
    elif args.command == 'viz':
        cmd_viz(args)
    elif args.command == 'parse':
        cmd_parse(args)
    else:
        parser.print_help()


def cmd_scan(args):
    """Execute scan command."""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Parse and analyze
    parser = SkillParser()
    detector = RiskDetector()

    try:
        skill = parser.parse_file(str(file_path))
        findings = detector.detect(skill)
        overall_risk = detector.get_overall_risk(findings)
        risk_score = detector.calculate_risk_score(findings)

        if args.format == 'json':
            result = {
                'file': str(file_path),
                'skill_name': skill.name,
                'overall_risk': overall_risk.value,
                'risk_score': risk_score,
                'findings_count': len(findings),
                'findings': [
                    {
                        'id': f.id,
                        'level': f.level.value,
                        'category': f.category,
                        'description': f.description,
                        'suggestion': f.suggestion
                    }
                    for f in findings
                ]
            }
            output = json.dumps(result, indent=2)

            if args.output:
                Path(args.output).write_text(output)
                print(f"Report saved to {args.output}")
            else:
                print(output)

        else:  # text format
            print(f"\n{'='*60}")
            print(f"SkillGraph Security Report")
            print(f"{'='*60}")
            print(f"\nFile: {file_path}")
            print(f"Skill: {skill.name}")
            print(f"\nOverall Risk: {overall_risk.value.upper()}")
            print(f"Risk Score: {risk_score:.2f}")
            print(f"Findings: {len(findings)}")

            if findings:
                print(f"\n{'─'*60}")
                print("Risk Findings:")
                print(f"{'─'*60}")

                for f in findings:
                    level_emoji = {
                        'critical': '🔴',
                        'high': '🟠',
                        'medium': '🟡',
                        'low': '🟢'
                    }
                    emoji = level_emoji.get(f.level.value, '⚪')
                    print(f"\n{emoji} [{f.level.value.upper()}] {f.category}")
                    print(f"   Pattern: {f.pattern}")
                    if args.verbose:
                        print(f"   Content: {f.content_snippet[:80]}...")
                    print(f"   Suggestion: {f.suggestion}")
            else:
                print(f"\n✅ No security risks detected!")

            print(f"\n{'='*60}\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_viz(args):
    """Execute visualization command."""
    print(f"Starting SkillGraph visualization on port {args.port}...")
    print("Open http://localhost:{}".format(args.port))

    from skillgraph.viz import run_app
    run_app(port=args.port)


def cmd_parse(args):
    """Execute parse command."""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    parser = SkillParser()

    try:
        skill = parser.parse_file(str(file_path))
        output = skill.to_json()

        if args.output:
            Path(args.output).write_text(output)
            print(f"Parsed data saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
