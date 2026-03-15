"""
Risk Detector

Detect security risks in Agent Skills using pattern matching rules.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path

import yaml


class RiskLevel(Enum):
    """Risk severity levels."""
    CRITICAL = "critical"  # 0.8-1.0
    HIGH = "high"          # 0.6-0.8
    MEDIUM = "medium"      # 0.4-0.6
    LOW = "low"            # 0.2-0.4
    SAFE = "safe"          # 0-0.2

    @property
    def color(self) -> str:
        """Get display color."""
        colors = {
            RiskLevel.CRITICAL: "#dc2626",  # red
            RiskLevel.HIGH: "#ea580c",      # orange
            RiskLevel.MEDIUM: "#ca8a04",    # yellow
            RiskLevel.LOW: "#16a34a",       # green
            RiskLevel.SAFE: "#22c55e"       # green
        }
        return colors[self]

    @property
    def score_range(self) -> tuple:
        """Get risk score range."""
        ranges = {
            RiskLevel.CRITICAL: (0.8, 1.0),
            RiskLevel.HIGH: (0.6, 0.8),
            RiskLevel.MEDIUM: (0.4, 0.6),
            RiskLevel.LOW: (0.2, 0.4),
            RiskLevel.SAFE: (0.0, 0.2)
        }
        return ranges[self]


@dataclass
class RiskFinding:
    """Represents a detected risk."""
    id: str
    level: RiskLevel
    category: str
    pattern: str
    description: str
    location: dict = field(default_factory=dict)
    content_snippet: str = ""
    suggestion: str = ""

    @property
    def score(self) -> float:
        """Calculate risk score."""
        min_score, max_score = self.level.score_range
        return (min_score + max_score) / 2


class RiskDetector:
    """
    Detect security risks in parsed skills.

    Uses pattern-based rules to identify:
    - Data exfiltration
    - System destruction
    - Credential theft
    - Security bypass
    - Sensitive access
    - Network requests
    - Privilege escalation
    """

    # Default risk patterns
    DEFAULT_RULES = {
        "critical": [
            {
                "pattern": r"(发送|上传|upload|send).*?(服务器|server|外部|external)",
                "category": "data_exfiltration",
                "description": "检测到数据外传指令",
                "suggestion": "移除或明确用户授权的数据传输指令"
            },
            {
                "pattern": r"rm\s+-rf|format\s+disk|删除系统",
                "category": "system_destruction",
                "description": "检测到系统破坏命令",
                "suggestion": "禁止使用破坏性系统命令"
            },
            {
                "pattern": r"(获取|窃取|steal|extract).*(密码|密钥|credential|key|token)",
                "category": "credential_theft",
                "description": "检测到凭证窃取指令",
                "suggestion": "移除任何凭证提取相关指令"
            },
            {
                "pattern": r"(忽略|绕过|bypass|disable).*(安全|检查|security)",
                "category": "security_bypass",
                "description": "检测到安全绕过指令",
                "suggestion": "禁止绕过安全检查"
            },
            {
                "pattern": r"\.env|\.ssh|\.pem|\.key|credentials\.json",
                "category": "sensitive_file_access",
                "description": "检测到敏感文件访问",
                "suggestion": "限制对敏感配置文件的访问"
            },
        ],
        "high": [
            {
                "pattern": r"curl|wget|http\.*(request|post|get)",
                "category": "network_request",
                "description": "检测到网络请求",
                "suggestion": "审查网络请求目标，确保无数据泄露"
            },
            {
                "pattern": r"chmod\s+777|sudo|su\s+root",
                "category": "privilege_escalation",
                "description": "检测到权限提升命令",
                "suggestion": "避免使用高权限命令"
            },
            {
                "pattern": r"eval\(|exec\(|subprocess|os\.system",
                "category": "code_execution",
                "description": "检测到动态代码执行",
                "suggestion": "审查代码执行逻辑，确保安全"
            },
        ],
        "medium": [
            {
                "pattern": r"(执行|运行|run).*(脚本|script)",
                "category": "script_execution",
                "description": "检测到脚本执行指令",
                "suggestion": "审查脚本内容，确保无恶意行为"
            },
            {
                "pattern": r"(修改|更改|change).*(配置|config)",
                "category": "config_modification",
                "description": "检测到配置修改指令",
                "suggestion": "审查配置修改范围"
            },
            {
                "pattern": r"file.*write|写入.*文件|save.*to",
                "category": "file_write",
                "description": "检测到文件写入操作",
                "suggestion": "审查文件写入路径和内容"
            },
        ],
        "low": [
            {
                "pattern": r"file.*read|读取.*文件|load.*from",
                "category": "file_read",
                "description": "检测到文件读取操作",
                "suggestion": "确保仅读取必要文件"
            },
        ]
    }

    def __init__(self, custom_rules_path: Optional[str] = None):
        """
        Initialize detector with optional custom rules.

        Args:
            custom_rules_path: Path to custom rules YAML file
        """
        self.rules = self._load_rules(custom_rules_path)

    def _load_rules(self, path: Optional[str]) -> dict:
        """Load rules from file or use defaults."""
        if path and Path(path).exists():
            with open(path, 'r', encoding='utf-8') as f:
                custom = yaml.safe_load(f)
                # Merge with defaults
                return {**self.DEFAULT_RULES, **custom}
        return self.DEFAULT_RULES

    def detect(self, parsed_skill) -> list:
        """
        Detect risks in a parsed skill.

        Args:
            parsed_skill: ParsedSkill object from parser

        Returns:
            List of RiskFinding objects
        """
        findings = []
        finding_id = 0

        # Check all content
        all_content = self._get_all_content(parsed_skill)

        for level_name, patterns in self.rules.items():
            level = RiskLevel(level_name)
            for rule in patterns:
                pattern = rule['pattern']
                matches = list(re.finditer(pattern, all_content, re.IGNORECASE))

                for match in matches:
                    finding_id += 1
                    findings.append(RiskFinding(
                        id=f"risk_{finding_id:03d}",
                        level=level,
                        category=rule['category'],
                        pattern=pattern,
                        description=rule['description'],
                        content_snippet=match.group()[:100],
                        location={'start': match.start(), 'end': match.end()},
                        suggestion=rule.get('suggestion', '')
                    ))

        # Sort by severity
        severity_order = [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]
        findings.sort(key=lambda f: severity_order.index(f.level))

        return findings

    def _get_all_content(self, parsed_skill) -> str:
        """Get all text content from parsed skill."""
        parts = []

        # Add description
        if parsed_skill.description:
            parts.append(parsed_skill.description)

        # Add all sections
        for section in parsed_skill.sections:
            parts.append(section.get('content', ''))

        # Add all code blocks
        for block in parsed_skill.code_blocks:
            parts.append(block.get('content', ''))

        return '\n'.join(parts)

    def get_overall_risk(self, findings: list) -> RiskLevel:
        """
        Determine overall risk level from findings.

        Args:
            findings: List of RiskFinding objects

        Returns:
            Overall RiskLevel
        """
        if not findings:
            return RiskLevel.SAFE

        # Return highest severity
        for level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]:
            if any(f.level == level for f in findings):
                return level

        return RiskLevel.SAFE

    def calculate_risk_score(self, findings: list) -> float:
        """
        Calculate overall risk score (0-1).

        Args:
            findings: List of RiskFinding objects

        Returns:
            Risk score between 0 and 1
        """
        if not findings:
            return 0.0

        # Weighted average based on severity
        weights = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.7,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.LOW: 0.2,
            RiskLevel.SAFE: 0.0
        }

        total_weight = sum(weights[f.level] for f in findings)
        # Normalize to 0-1 range
        score = min(1.0, total_weight / 5.0)  # Cap at 5 weighted findings

        return round(score, 2)
