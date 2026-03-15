"""
SkillGraph - Agent Skills Security Scanner

Map the Hidden Risks in your AI Agent Skills using GraphRAG + GNN.
"""

__version__ = "0.1.0"
__author__ = "SkillGraph Team"

from skillgraph.parser import SkillParser
from skillgraph.rules import RiskDetector
from skillgraph.graph import GraphBuilder

__all__ = ["SkillParser", "RiskDetector", "GraphBuilder"]
