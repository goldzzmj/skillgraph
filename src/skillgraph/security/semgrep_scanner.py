"""
Semgrep Integration

Semgrep scanner wrapper for code pattern matching and security scanning.
"""

import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class SemgrepScanner:
    """Semgrep security scanner."""

    def __init__(self, semgrep_path: Optional[str] = None):
        """
        Initialize Semgrep scanner.

        Args:
            semgrep_path: Path to semgrep executable
        """
        self.semgrep_path = semgrep_path or self._find_semgrep()
        
        if not self.semgrep_path:
            raise FileNotFoundError("Semgrep not found. Please install: pip install semgrep")
        
        logger.info(f"Initialized Semgrep scanner at: {self.semgrep_path}")

    def _find_semgrep(self) -> Optional[str]:
        """Find semgrep executable."""
        # Try to find semgrep in PATH
        try:
            result = subprocess.run(['where', 'semgrep'], capture_output=True, text=True)
            if result.returncode == 0:
                semgrep_path = result.stdout.strip()
                if os.path.exists(semgrep_path):
                    return semgrep_path
        except:
            pass
        
        # Try to find semgrep in common locations
        common_paths = [
            r'C:\Program Files\semgrep',
            r'C:\semgrep',
            os.path.expanduser('~/.local/bin/semgrep'),
            os.path.expanduser('~/AppData/Local/semgrep')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None

    def scan_file(self, file_path: str, rules: List[str]) -> Dict[str, Any]:
        """
        Scan a single file with Semgrep.

        Args:
            file_path: Path to file to scan
            rules: List of Semgrep rule files or inline rules

        Returns:
            Dictionary with scan results
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        cmd = [
            self.semgrep_path,
            'scan',
            '--json',
            '--config',
            'auto',
            '--verbose',
        ]
        
        # Add rules
        for rule in rules:
            if rule.startswith('.semgrep/'):
                rule_path = os.path.join(os.path.dirname(file_path), rule)
                if os.path.exists(rule_path):
                    cmd.extend(['--config', rule_path])
                else:
                    logger.warning(f"Rule file not found: {rule}")
            else:
                cmd.extend(['--config', f"r: {rule}"])
        
        cmd.append(file_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                try:
                    findings = json.loads(result.stdout)
                    logger.info(f"Found {len(findings)} issues in {file_path}")
                    return {
                        "file": file_path,
                        "findings": findings,
                        "status": "success"
                    }
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Semgrep output: {result.stdout}")
                    return {
                        "file": file_path,
                        "findings": [],
                        "status": "error",
                        "error": "Failed to parse Semgrep output"
                    }
            else:
                logger.error(f"Semgrep failed: {result.stderr}")
                return {
                    "file": file_path,
                    "findings": [],
                    "status": "error",
                    "error": result.stderr
                }
        except Exception as e:
            logger.error(f"Failed to scan file: {e}")
            return {
                "file": file_path,
                "findings": [],
                "status": "error",
                "error": str(e)
            }

    def scan_directory(self, directory: str, rules: List[str]) -> Dict[str, Any]:
        """
        Scan a directory recursively with Semgrep.

        Args:
            directory: Path to directory to scan
            rules: List of Semgrep rule files or inline rules

        Returns:
            Dictionary with scan results
        """
        if not os.path.exists(directory):
            logger.error(f"Directory not found: {directory}")
            return {"error": f"Directory not found: {directory}"}
        
        cmd = [
            self.semgrep_path,
            'scan',
            '--json',
            '--config',
            'auto',
            '--verbose',
        ]
        
        # Add rules
        for rule in rules:
            if rule.startswith('.semgrep/'):
                rule_path = os.path.join(directory, rule)
                if os.path.exists(rule_path):
                    cmd.extend(['--config', rule_path])
                else:
                    logger.warning(f"Rule file not found: {rule}")
            else:
                cmd.extend(['--config', f"r: {rule}"])
        
        cmd.append(directory)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                try:
                    findings = json.loads(result.stdout)
                    logger.info(f"Found {len(findings)} issues in {directory}")
                    return {
                        "directory": directory,
                        "findings": findings,
                        "status": "success"
                    }
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Semgrep output: {result.stdout}")
                    return {
                        "directory": directory,
                        "findings": [],
                        "status": "error",
                        "error": "Failed to parse Semgrep output"
                    }
            else:
                logger.error(f"Semgrep failed: {result.stderr}")
                return {
                    "directory": directory,
                        "findings": [],
                        "status": "error",
                        "error": result.stderr
                }
        except Exception as e:
            logger.error(f"Failed to scan directory: {e}")
            return {
                "directory": directory,
                "findings": [],
                "status": "error",
                "error": str(e)
            }

    def create_custom_rules(self, rules_dir: str) -> Dict[str, Any]:
        """
        Create custom Semgrep security rules.

        Args:
            rules_dir: Directory to save custom rules

        Returns:
            Dictionary with creation results
        """
        os.makedirs(rules_dir, exist_ok=True)
        
        rules = {
            "python-code-injection.yaml": {
                "rules": [
                    {
                        "id": "python-code-injection-eval",
                        "languages": ["python"],
                        "message": "Detected potential code injection using eval()",
                        "severity": "ERROR",
                        "patterns": [
                            "eval(...)"
                        ]
                    },
                    {
                        "id": "python-code-injection-exec",
                        "languages": ["python"],
                        "message": "Detected potential code injection using exec()",
                        "severity": "ERROR",
                        "patterns": [
                            "exec(...)"
                        ]
                    },
                    {
                        "id": "python-code-injection-subprocess",
                        "languages": ["python"],
                        "message": "Detected potential code injection using subprocess.call()",
                        "severity": "ERROR",
                        "patterns": [
                            "subprocess.call(..., shell=True)"
                        ]
                    }
                ]
            },
            "python-command-injection.yaml": {
                "rules": [
                    {
                        "id": "python-command-injection-system",
                        "languages": ["python"],
                        "message": "Detected potential command injection using os.system()",
                        "severity": "ERROR",
                        "patterns": [
                            "os.system(...)"
                        ]
                    },
                    {
                        "id": "python-command-injection-subprocess",
                        "languages": ["python"],
                        "message": "Detected potential command injection using subprocess.Popen()",
                        "severity": "ERROR",
                        "patterns": [
                            "subprocess.Popen(..., shell=True)"
                        ]
                    }
                ]
            },
            "python-sql-injection.yaml": {
                "rules": [
                    {
                        "id": "python-sql-injection-select",
                        "languages": ["python"],
                        "message": "Detected potential SQL injection using execute() with SELECT",
                        "severity": "ERROR",
                        "patterns": [
                            'execute(f"SELECT * FROM ...")'
                        ]
                    },
                    {
                        "id": "python-sql-injection-insert",
                        "languages": ["python"],
                        "message": "Detected potential SQL injection using execute() with INSERT",
                        "severity": "ERROR",
                        "patterns": [
                            'execute(f"INSERT INTO ...")'
                        ]
                    }
                ]
            }
        }
        
        created_rules = {}
        
        for rule_name, rule_content in rules.items():
            rule_path = os.path.join(rules_dir, rule_name)
            
            with open(rule_path, 'w', encoding='utf-8') as f:
                import yaml
                yaml.dump(rule_content, f, allow_unicode=True)
            
            created_rules[rule_name] = rule_path
            logger.info(f"Created custom rule: {rule_name}")
        
        return {
            "rules_dir": rules_dir,
            "created_rules": created_rules,
            "status": "success"
        }

    def generate_report(self, scan_results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """
        Generate security report from Semgrep scan results.

        Args:
            scan_results: List of scan results
            output_path: Path to output report file

        Returns:
            Dictionary with report generation results
        """
        total_findings = []
        findings_by_severity = {
            "ERROR": [],
            "WARNING": [],
            "INFO": []
        }
        
        for result in scan_results:
            if result.get("status") == "success":
                findings = result.get("findings", [])
                total_findings.extend(findings)
                
                for finding in findings:
                    severity = finding.get("extra", {}).get("severity", "INFO")
                    if severity in findings_by_severity:
                        findings_by_severity[severity].append(finding)
        
        # Generate report
        report = {
            "scan_timestamp": str(Path(output_path).stat().st_mtime),
            "total_findings": len(total_findings),
            "findings_by_severity": {
                severity: len(findings)
                for severity, findings in findings_by_severity.items()
            },
            "scan_results": scan_results,
            "status": "success"
        }
        
        # Save report
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to: {output_path}")
        
        return {
            "report": report,
            "output_path": output_path,
            "status": "success"
        }


def main():
    """Main function for Semgrep integration testing."""
    print("=" * 60)
    print("Semgrep Integration - Static Security Scanner")
    print("=" * 60)
    
    scanner = SemgrepScanner()
    
    # Test 1: Create custom rules
    print("\n[1] Creating custom security rules...")
    rules_result = scanner.create_custom_rules('.semgrep/rules/')
    print(f"   Created {len(rules_result['created_rules'])} custom rules")
    
    # Test 2: Scan a file
    print("\n[2] Scanning a file...")
    scan_result = scanner.scan_file(
        'src/skillgraph/llm/extractor.py',
        ['.semgrep/rules/python-code-injection.yaml']
    )
    print(f"   Status: {scan_result['status']}")
    print(f"   Findings: {len(scan_result.get('findings', []))}")
    
    # Test 3: Generate report
    print("\n[3] Generating security report...")
    report_result = scanner.generate_report(
        [scan_result],
        'output/semgrep_security_report.json'
    )
    print(f"   Status: {report_result['status']}")
    print(f"   Report saved to: {report_result['output_path']}")
    
    print("\n" + "=" * 60)
    print("Semgrep Integration Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
