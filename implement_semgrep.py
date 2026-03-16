"""
Task 2.1 Implementation - Semgrep Integration

Implement Semgrep scanner and create custom security rules.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skillgraph.security import SemgrepScanner


def create_custom_rules():
    """Create custom Semgrep security rules."""
    print("=" * 60)
    print("Creating Custom Semgrep Security Rules")
    print("=" * 60)
    
    scanner = SemgrepScanner()
    
    # Create rules directory
    rules_dir = Path('.semgrep/rules/')
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    # Create custom rules
    print("\n[1] Creating custom security rules...")
    rules_result = scanner.create_custom_rules(str(rules_dir))
    
    print(f"\nCreated {len(rules_result['created_rules'])} custom rules:")
    for rule_name, rule_path in rules_result['created_rules'].items():
        print(f"  ✓ {rule_name}: {rule_path}")
    
    return rules_result


def scan_codebase():
    """Scan codebase with Semgrep."""
    print("\n[2] Scanning codebase with Semgrep...")
    
    scanner = SemgrepScanner()
    
    # Scan Python files
    python_files = list(Path('.').rglob('**/*.py'))
    
    # Skip test files and venv
    python_files = [f for f in python_files if 'tests/' not in str(f) and 'venv/' not in str(f)]
    
    print(f"   Found {len(python_files)} Python files to scan")
    
    # Scan each file
    scan_results = []
    rules = ['.semgrep/rules/python-code-injection.yaml',
              '.semgrep/rules/python-command-injection.yaml',
              '.semgrep/rules/python-sql-injection.yaml']
    
    for file_path in python_files[:10]:  # Scan first 10 files for testing
        print(f"   Scanning: {file_path}")
        result = scanner.scan_file(str(file_path), rules)
        scan_results.append(result)
    
    # Generate report
    print("\n[3] Generating security report...")
    report_result = scanner.generate_report(scan_results, 'output/semgrep_scan_report.json')
    
    print(f"   Total findings: {report_result['report']['total_findings']}")
    print(f"   Report saved to: {report_result['output_path']}")
    
    return scan_results, report_result


def main():
    """Main function for Task 2.1 implementation."""
    print("=" * 60)
    print("Task 2.1: Semgrep Integration Implementation")
    print("=" * 60)
    print("Phase 5 v1.0.1 - Static Security Tools Integration")
    print("=" * 60)
    
    try:
        # Create custom rules
        rules_result = create_custom_rules()
        
        # Scan codebase
        scan_results, report_result = scan_codebase()
        
        print("\n" + "=" * 60)
        print("Task 2.1 Implementation Complete!")
        print("=" * 60)
        print("\nResults:")
        print(f"  ✓ Custom rules created: {len(rules_result['created_rules'])}")
        print(f"  ✓ Files scanned: {len(scan_results)}")
        print(f"  ✓ Total findings: {report_result['report']['total_findings']}")
        print(f"  ✓ Report saved")
        
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("  1. Review security report")
        print("  2. Fix critical findings")
        print("  3. Integrate into CI/CD")
        print("=" * 60)
        
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
