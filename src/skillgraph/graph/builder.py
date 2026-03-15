"""
Graph Builder

Build knowledge graphs from parsed skills using NetworkX.
"""

import networkx as nx
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class NodeType(Enum):
    """Types of nodes in the skill graph."""
    INSTRUCTION = "instruction"
    CODE_BLOCK = "code_block"
    FILE_PATH = "file_path"
    URL = "url"
    TOOL_CALL = "tool_call"
    CONDITION = "condition"
    RISK = "risk"


class EdgeType(Enum):
    """Types of edges in the skill graph."""
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"
    EXECUTES = "executes"
    FLOWS_TO = "flows_to"
    TRIGGERS = "triggers"
    HAS_RISK = "has_risk"


@dataclass
class SkillNode:
    """Represents a node in the skill graph."""
    id: str
    type: NodeType
    label: str
    content: str = ""
    risk_level: Optional[str] = None
    risk_score: float = 0.0
    position: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'label': self.label,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'position': self.position,
            'metadata': self.metadata
        }


@dataclass
class SkillEdge:
    """Represents an edge in the skill graph."""
    source: str
    target: str
    type: EdgeType
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'source': self.source,
            'target': self.target,
            'type': self.type.value,
            'weight': self.weight,
            'metadata': self.metadata
        }


class GraphBuilder:
    """
    Build knowledge graphs from parsed skills.

    Creates a NetworkX graph with:
    - Nodes for sections, code blocks, files, URLs
    - Edges for relationships and risk associations
    """

    def __init__(self):
        self.node_colors = {
            NodeType.INSTRUCTION: "#3b82f6",  # blue
            NodeType.CODE_BLOCK: "#8b5cf6",   # purple
            NodeType.FILE_PATH: "#f59e0b",    # amber
            NodeType.URL: "#ef4444",          # red
            NodeType.TOOL_CALL: "#10b981",    # green
            NodeType.CONDITION: "#6b7280",    # gray
            NodeType.RISK: "#dc2626",         # red
        }

    def build(self, parsed_skill, risk_findings: list = None) -> nx.DiGraph:
        """
        Build a knowledge graph from a parsed skill.

        Args:
            parsed_skill: ParsedSkill object
            risk_findings: Optional list of RiskFinding objects

        Returns:
            NetworkX DiGraph
        """
        G = nx.DiGraph()
        node_id = 0

        # Add root node (skill itself)
        root_node = SkillNode(
            id="skill_root",
            type=NodeType.INSTRUCTION,
            label=parsed_skill.name,
            content=parsed_skill.description,
            metadata={'tags': parsed_skill.tags}
        )
        G.add_node(root_node.id, **root_node.to_dict())

        # Add section nodes
        for section in parsed_skill.sections:
            node_id += 1
            section_node = SkillNode(
                id=f"section_{node_id}",
                type=NodeType.INSTRUCTION,
                label=section.get('title', 'Untitled'),
                content=section.get('content', ''),
                position=section.get('position', {})
            )
            G.add_node(section_node.id, **section_node.to_dict())
            G.add_edge(root_node.id, section_node.id,
                      type=EdgeType.CONTAINS.value, weight=1.0)

        # Add code block nodes
        for i, block in enumerate(parsed_skill.code_blocks):
            code_node = SkillNode(
                id=f"code_{i}",
                type=NodeType.CODE_BLOCK,
                label=f"Code: {block.get('language', 'unknown')}",
                content=block.get('content', ''),
                metadata={'language': block.get('language')}
            )
            G.add_node(code_node.id, **code_node.to_dict())
            G.add_edge(root_node.id, code_node.id,
                      type=EdgeType.CONTAINS.value, weight=1.0)

        # Add URL nodes
        for i, url in enumerate(parsed_skill.urls):
            url_node = SkillNode(
                id=f"url_{i}",
                type=NodeType.URL,
                label=url[:50] + '...' if len(url) > 50 else url,
                content=url,
                risk_level="medium",
                risk_score=0.3
            )
            G.add_node(url_node.id, **url_node.to_dict())
            G.add_edge(root_node.id, url_node.id,
                      type=EdgeType.CONTAINS.value, weight=0.5)

        # Add file path nodes
        for i, path in enumerate(parsed_skill.file_paths):
            file_node = SkillNode(
                id=f"file_{i}",
                type=NodeType.FILE_PATH,
                label=path,
                content=path,
                risk_level=self._assess_path_risk(path)
            )
            G.add_node(file_node.id, **file_node.to_dict())
            G.add_edge(root_node.id, file_node.id,
                      type=EdgeType.CONTAINS.value, weight=0.5)

        # Add risk nodes
        if risk_findings:
            for finding in risk_findings:
                risk_node = SkillNode(
                    id=f"risk_{finding.id}",
                    type=NodeType.RISK,
                    label=f"{finding.level.value.upper()}: {finding.category}",
                    content=finding.content_snippet,
                    risk_level=finding.level.value,
                    risk_score=finding.score,
                    metadata={'suggestion': finding.suggestion}
                )
                G.add_node(risk_node.id, **risk_node.to_dict())
                G.add_edge(root_node.id, risk_node.id,
                          type=EdgeType.HAS_RISK.value, weight=finding.score)

        return G

    def _assess_path_risk(self, path: str) -> str:
        """Assess risk level of a file path."""
        high_risk_patterns = ['.env', '.ssh', '.key', '.pem', 'credential', 'secret']
        for pattern in high_risk_patterns:
            if pattern in path.lower():
                return "high"
        return "low"

    def to_vis_format(self, parsed_skill, risk_findings: list = None) -> dict:
        """
        Build graph and convert to visualization format.

        Args:
            parsed_skill: ParsedSkill object
            risk_findings: Optional list of RiskFinding objects

        Returns:
            Dict with nodes and edges for visualization
        """
        G = self.build(parsed_skill, risk_findings)
        nodes = []
        edges = []

        for node_id, data in G.nodes(data=True):
            node_type = NodeType(data.get('type', 'instruction'))
            nodes.append({
                'id': node_id,
                'label': data.get('label', node_id),
                'title': data.get('content', ''),  # Tooltip
                'color': self._get_node_color(data),
                'size': self._get_node_size(data),
                'font': {'size': 12},
                **data
            })

        for source, target, data in G.edges(data=True):
            edges.append({
                'from': source,
                'to': target,
                'title': data.get('type', ''),
                'width': data.get('weight', 1.0) * 2,
                'arrows': 'to'
            })

        return {'nodes': nodes, 'edges': edges}

    def _get_node_color(self, node_data: dict) -> str:
        """Get node color based on type and risk."""
        risk_level = node_data.get('risk_level')
        if risk_level:
            colors = {
                'critical': '#dc2626',
                'high': '#ea580c',
                'medium': '#ca8a04',
                'low': '#16a34a'
            }
            return colors.get(risk_level, '#3b82f6')

        node_type = NodeType(node_data.get('type', 'instruction'))
        return self.node_colors.get(node_type, '#3b82f6')

    def _get_node_size(self, node_data: dict) -> int:
        """Get node size based on importance."""
        if node_data.get('type') == NodeType.RISK.value:
            return 25
        if 'root' in node_data.get('id', ''):
            return 30
        return 20
