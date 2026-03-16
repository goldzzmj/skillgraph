"""
Bandit Scanner Wrapper

Bandit scanner wrapper for Python security checks.
"""

import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class BanditScanner:
    """Bandit security scanner."""

    def __init__(self, bandit_path: Optional[str] = None):
        """
        Initialize Bandit scanner.

        Args:
            bandit_path: Path to bandit executable
        """
        self.bandit_path = bandit_path or self._find_bandit()
        
        if not self.bandit_path:
            raise FileNotFoundError("Bandit not found. Please install: pip install bandit")
        
        logger.info(f"Initialized Bandit scanner at: {self.bandit_path}")

    def _find_bandit(self) -> Optional[str]:
        """Find bandit executable."""
        # Try to find bandit in PATH
        try:
            result = subprocess.run(['where', 'bandit'], capture_output=True, text=True)
            if result.returncode == 0:
                bandit_path = result.stdout.strip()
                if os.path.exists(bandit_path):
                    return bandit_path
        except:
            pass
        
        # Try to find bandit in common locations
        common_paths = [
            r'C:\Program Files\bandit',
            r'C:\bandit',
            os.path.expanduser('~/.local/bin/bandit'),
            os.path.expanduser('~/AppData/Local/bandit')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """
        Scan a single file with Bandit.

        Args:
            file_path: Path to file to scan

        Returns:
            Dictionary with scan results
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        cmd = [
            self.bandit_path,
            'check',
            '--format', 'json',
            '-f', file_path
        ]
        
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
                    logger.error(f"Failed to parse Bandit output: {result.stdout}")
                    return {
                        "file": file_path,
                        "findings": [],
                        "status": "error",
                        "error": "Failed to parse Bandit output"
                    }
            else:
                logger.error(f"Bandit failed: {result.stderr}")
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

    def scan_directory(self, directory: str) -> Dict[str, Any]:
        """
        Scan a directory with Bandit.

        Args:
            directory: Path to directory to scan

        Returns:
            Dictionary with scan results
        """
        if not os.path.exists(directory):
            logger.error(f"Directory not found: {directory}")
            return {"error": f"Directory not found: {directory}"}
        
        cmd = [
            self.bandit_path,
            'check',
            '--format', 'json',
            '-r', directory
        ]
        
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
                    logger.error(f"Failed to parse Bandit output: {result.stdout}")
                    return {
                        "directory": directory,
                        "findings": [],
                        "status": "error",
                        "error": "Failed to parse Bandit output"
                    }
            else:
                logger.error(f"Bandit failed: {result.stderr}")
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

    def generate_report(self, scan_results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """
        Generate security report from Bandit scan results.

        Args:
            scan_results: List of scan results
            output_path: Path to output report file

        Returns:
            Dictionary with report generation results
        """
        total_findings = []
        findings_by_severity = {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "UNDEFINED": []
        }
        
        for result in scan_results:
            if result.get("status") == "success":
                findings = result.get("findings", {}).get("results", [])
                total_findings.extend(findings)
                
                for finding in findings:
                    severity = finding.get("issue_severity", "UNDEFINED")
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
    """Main function for Bandit integration testing."""
    print("=" * 60)
    print("Bandit Integration - Python Security Scanner")
    print("=" * 60)
    
    scanner = BanditScanner()
    
    # Test: Check installation
    print(f"Bandit installed at: {scanner.bandit_path}")
    
    # Test: Scan a file
    print("\nScanning a file...")
    scan_result = scanner.scan_file('src/skillgraph/llm/extractor.py')
    print(f"Status: {scan_result['status']}")
    print(f"Findings: {len(scan_result.get('findings', {}))}")
    
    print("\n" + "=" * 60)
    print("Bandit Integration Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
