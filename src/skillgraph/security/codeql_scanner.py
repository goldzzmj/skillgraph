"""
CodeQL Scanner Wrapper

CodeQL scanner wrapper for deep code analysis.
"""

import subprocess
import json
import logging
from typing import Dict, Any, List, Optional
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeQLScanner:
    """CodeQL deep analysis scanner."""

    def __init__(self, codeql_path: Optional[str] = None):
        """
        Initialize CodeQL scanner.

        Args:
            codeql_path: Path to codeql executable
        """
        self.codeql_path = codeql_path or self._find_codeql()
        
        if not self.codeql_path:
            raise FileNotFoundError("CodeQL not found. Please install from GitHub")
        
        logger.info(f"Initialized CodeQL scanner at: {self.codeql_path}")

    def _find_codeql(self) -> Optional[str]:
        """Find codeql executable."""
        # Try to find codeql in PATH
        try:
            result = subprocess.run(['where', 'codeql'], capture_output=True, text=True)
            if result.returncode == 0:
                codeql_path = result.stdout.strip()
                if os.path.exists(codeql_path):
                    return codeql_path
        except:
            pass
        
        # Try to find codeql in common locations
        common_paths = [
            r'C:\Program Files\codeql',
            r'C:\codeql',
            os.path.expanduser('~/.local/bin/codeql'),
            os.path.expanduser('~/AppData/Local/codeql')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None

    def scan_file(self, file_path: str, query_path: str) -> Dict[str, Any]:
        """
        Scan a single file with CodeQL.

        Args:
            file_path: Path to file to scan
            query_path: Path to CodeQL query file

        Returns:
            Dictionary with scan results
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        if not os.path.exists(query_path):
            logger.error(f"Query file not found: {query_path}")
            return {"error": f"Query file not found: {query_path}"}
        
        cmd = [
            self.codeql_path,
            'query',
            'run',
            '--database=python',
            f'--source-root={os.path.dirname(file_path)}',
            query_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"CodeQL scan completed for {file_path}")
                return {
                    "file": file_path,
                    "query": query_path,
                    "status": "success"
                }
            else:
                logger.error(f"CodeQL failed: {result.stderr}")
                return {
                    "file": file_path,
                    "query": query_path,
                    "status": "error",
                    "error": result.stderr
                }
        except Exception as e:
            logger.error(f"Failed to scan file: {e}")
            return {
                "file": file_path,
                "query": query_path,
                "status": "error",
                "error": str(e)
            }

    def generate_report(self, scan_results: List[Dict[str, Any]], output_path: str) -> Dict[str, Any]:
        """
        Generate security report from CodeQL scan results.

        Args:
            scan_results: List of scan results
            output_path: Path to output report file

        Returns:
            Dictionary with report generation results
        """
        total_scans = len(scan_results)
        successful_scans = len([r for r in scan_results if r.get('status') == 'success'])
        
        # Generate report
        report = {
            "scan_timestamp": str(Path(output_path).stat().st_mtime),
            "total_scans": total_scans,
            "successful_scans": successful_scans,
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
    """Main function for CodeQL integration testing."""
    print("=" * 60)
    print("CodeQL Integration - Deep Code Analysis Scanner")
    print("=" * 60)
    
    scanner = CodeQLScanner()
    
    # Test: Check installation
    print(f"CodeQL installed at: {scanner.codeql_path}")
    
    # Test: Create sample query
    print("\nCreating sample CodeQL query...")
    query_path = '.codeql/queries/python-code-injection.ql'
    
    # Create directory
    os.makedirs('.codeql/queries', exist_ok=True)
    
    # Create sample query
    query = """
import python
from CodeQL

select * where exists(
    eval($expr),
    exec($expr)
)
"""
    
    with open(query_path, 'w', encoding='utf-8') as f:
        f.write(query)
    
    print(f"Created sample query: {query_path}")
    
    # Test: Scan a file
    print("\nScanning a file...")
    scan_result = scanner.scan_file('src/skillgraph/llm/extractor.py', query_path)
    print(f"Status: {scan_result['status']}")
    
    print("\n" + "=" * 60)
    print("CodeQL Integration Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
