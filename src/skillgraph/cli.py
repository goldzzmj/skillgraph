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
from skillgraph.graphrag import KnowledgeGraph
import yaml


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

    # GraphRAG init command
    graphrag_init_parser = subparsers.add_parser('graphrag-init', help='Initialize GraphRAG for a skill')
    graphrag_init_parser.add_argument('file', type=str, help='Path to skill file')
    graphrag_init_parser.add_argument('-o', '--output', type=str, default='output/graphrag', help='Output directory')
    graphrag_init_parser.add_argument('-c', '--config', type=str, help='Path to config file')

    # GraphRAG extract command
    graphrag_extract_parser = subparsers.add_parser('graphrag-extract', help='Extract entities and relationships')
    graphrag_extract_parser.add_argument('file', type=str, help='Path to skill file')
    graphrag_extract_parser.add_argument('-o', '--output', type=str, help='Output JSON file')
    graphrag_extract_parser.add_argument('-c', '--config', type=str, help='Path to config file')

    # GraphRAG query command
    graphrag_query_parser = subparsers.add_parser('graphrag-query', help='Query the knowledge graph')
    graphrag_query_parser.add_argument('file', type=str, help='Path to skill file or pre-built graph')
    graphrag_query_parser.add_argument('query', type=str, help='Query string')
    graphrag_query_parser.add_argument('-c', '--config', type=str, help='Path to config file')

    # GraphRAG analyze command
    graphrag_analyze_parser = subparsers.add_parser('graphrag-analyze', help='Full GraphRAG analysis')
    graphrag_analyze_parser.add_argument('file', type=str, help='Path to skill file')
    graphrag_analyze_parser.add_argument('-o', '--output', type=str, default='output/analysis.json', help='Output JSON file')
    graphrag_analyze_parser.add_argument('-f', '--format', choices=['json', 'gexf', 'graphml'], default='json', help='Export format')
    graphrag_analyze_parser.add_argument('-c', '--config', type=str, help='Path to config file')
    graphrag_analyze_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.command == 'scan':
        cmd_scan(args)
    elif args.command == 'viz':
        cmd_viz(args)
    elif args.command == 'parse':
        cmd_parse(args)
    elif args.command == 'graphrag-init':
        cmd_graphrag_init(args)
    elif args.command == 'graphrag-extract':
        cmd_graphrag_extract(args)
    elif args.command == 'graphrag-query':
        cmd_graphrag_query(args)
    elif args.command == 'graphrag-analyze':
        cmd_graphrag_analyze(args)
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


def _load_config(config_path: Optional[str]) -> dict:
    """Load GraphRAG configuration."""
    default_config = {
        'model': {
            'provider': 'openai',
            'model_name': 'gpt-4-turbo-preview',
            'embedding_model': 'text-embedding-3-small',
            'api_key': ''
        },
        'entity_extraction': {
            'enabled': True,
            'chunk_size': 2000,
            'chunk_overlap': 200
        },
        'community_detection': {
            'enabled': True,
            'algorithm': 'leiden',
            'resolution': 1.0
        },
        'embeddings': {
            'enabled': True,
            'batch_size': 100
        },
        'retrieval': {
            'strategy': 'hybrid',
            'top_k_entities': 10,
            'top_k_communities': 5
        }
    }

    if config_path:
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge configs
                return {**default_config, **user_config}
        except Exception as e:
            print(f"Warning: Failed to load config, using defaults: {e}", file=sys.stderr)

    return default_config


def cmd_graphrag_init(args):
    """Initialize GraphRAG for a skill file."""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Load config
    config = _load_config(args.config)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Initializing GraphRAG for {args.file}...")

    try:
        # Parse skill
        parser = SkillParser()
        skill = parser.parse_file(str(file_path))

        # Build knowledge graph
        kg = KnowledgeGraph(config)
        analysis = kg.build(skill)

        # Export to JSON
        json_path = output_dir / 'knowledge_graph.json'
        kg.export_to_json(str(json_path))

        # Export to GEXF for visualization
        gexf_path = output_dir / 'knowledge_graph.gexf'
        kg.export_to_gexf(str(gexf_path))

        print(f"\n✅ GraphRAG initialization complete!")
        print(f"   Entities: {len(analysis.entities)}")
        print(f"   Relationships: {len(analysis.relationships)}")
        print(f"   Communities: {len(analysis.communities)}")
        print(f"\nOutput:")
        print(f"   JSON: {json_path}")
        print(f"   GEXF: {gexf_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_graphrag_extract(args):
    """Extract entities and relationships from skill file."""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Load config
    config = _load_config(args.config)

    print(f"Extracting entities and relationships from {args.file}...")

    try:
        # Parse skill
        parser = SkillParser()
        skill = parser.parse_file(str(file_path))

        # Build knowledge graph (only extraction)
        kg = KnowledgeGraph(config)

        # Extract entities and relationships
        entities = kg.entity_extractor.extract(
            '',
            skill.sections if hasattr(skill, 'sections') else [],
            skill.code_blocks if hasattr(skill, 'code_blocks') else []
        )
        relationships = kg._extract_relationships()

        # Prepare output
        result = {
            'skill_name': skill.name,
            'entities': [e.to_dict() for e in entities],
            'relationships': [r.to_dict() for r in relationships],
            'summary': {
                'entity_count': len(entities),
                'relationship_count': len(relationships),
                'entity_types': list(set(e.type.value for e in entities))
            }
        }

        output = json.dumps(result, indent=2, ensure_ascii=False)

        if args.output:
            Path(args.output).write_text(output)
            print(f"\n✅ Extraction complete!")
            print(f"   Entities: {len(entities)}")
            print(f"   Relationships: {len(relationships)}")
            print(f"   Saved to: {args.output}")
        else:
            print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_graphrag_query(args):
    """Query the knowledge graph."""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Load config
    config = _load_config(args.config)

    print(f"Querying knowledge graph...")
    print(f"Query: {args.query}\n")

    try:
        # Check if file is a skill or pre-built graph
        if file_path.suffix == '.json':
            # Load pre-built graph
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Reconstruct analysis from data
            from skillgraph.graphrag.models import (
                Entity, Relationship, Community, GraphRAGAnalysis
            )

            entities = [Entity.from_dict(e) for e in data.get('entities', [])]
            communities = [Community.from_dict(c) for c in data.get('communities', [])]

            analysis = GraphRAGAnalysis(
                entities=entities,
                relationships=[],
                communities=communities,
                risk_findings=data.get('risk_findings', []),
                summary=data.get('summary', '')
            )
        else:
            # Build graph from skill file
            parser = SkillParser()
            skill = parser.parse_file(str(file_path))

            kg = KnowledgeGraph(config)
            analysis = kg.build(skill)

        # Perform query
        result = kg.retriever.retrieve(args.query, analysis)

        # Display results
        print(f"{'='*60}")
        print(f"Query Results")
        print(f"{'='*60}")
        print(f"\n{result.reasoning}\n")

        if result.entities:
            print(f"{'─'*60}")
            print(f"Retrieved Entities ({len(result.entities)}):")
            print(f"{'─'*60}")

            for i, (entity, score) in enumerate(zip(result.entities, result.entity_scores), 1):
                risk_emoji = '🔴' if entity.risk_score > 0.6 else '🟡' if entity.risk_score > 0.4 else '🟢'
                print(f"\n{i}. {risk_emoji} [{entity.type.value}] {entity.name}")
                print(f"   Description: {entity.description[:80]}...")
                print(f"   Similarity: {score:.3f}")
                print(f"   Risk Score: {entity.risk_score:.2f}")

        if result.communities:
            print(f"\n{'─'*60}")
            print(f"Retrieved Communities ({len(result.communities)}):")
            print(f"{'─'*60}")

            for i, (community, score) in enumerate(zip(result.communities, result.community_scores), 1):
                risk_emoji = '🔴' if community.risk_score > 0.6 else '🟡' if community.risk_score > 0.4 else '🟢'
                print(f"\n{i}. {risk_emoji} {community.description}")
                print(f"   Size: {len(community.entities)} entities")
                print(f"   Similarity: {score:.3f}")
                print(f"   Risk Score: {community.risk_score:.2f}")

        print(f"\n{'='*60}")
        print(f"Total Score: {result.total_score:.3f}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_graphrag_analyze(args):
    """Full GraphRAG analysis of a skill file."""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Load config
    config = _load_config(args.config)

    print(f"Running GraphRAG analysis on {args.file}...\n")

    try:
        # Parse skill
        parser = SkillParser()
        skill = parser.parse_file(str(file_path))

        # Build knowledge graph
        kg = KnowledgeGraph(config)
        analysis = kg.build(skill)

        # Display summary
        print(f"{'='*60}")
        print(f"GraphRAG Analysis Results")
        print(f"{'='*60}")
        print(f"\n{analysis.summary}\n")

        if args.verbose:
            # Display entities by type
            print(f"{'─'*60}")
            print(f"Entities by Type:")
            print(f"{'─'*60}")

            entity_types = {}
            for entity in analysis.entities:
                entity_types[entity.type.value] = entity_types.get(entity.type.value, 0) + 1

            for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {entity_type}: {count}")

            # Display high-risk entities
            high_risk_entities = kg.get_high_risk_entities(threshold=0.6)
            if high_risk_entities:
                print(f"\n{'─'*60}")
                print(f"High-Risk Entities (risk >= 0.6):")
                print(f"{'─'*60}")

                for entity in high_risk_entities[:10]:
                    print(f"  🔴 [{entity.type.value}] {entity.name} (risk: {entity.risk_score:.2f})")

            # Display communities
            if analysis.communities:
                print(f"\n{'─'*60}")
                print(f"Detected Communities:")
                print(f"{'─'*60}")

                for community in analysis.communities[:5]:
                    risk_emoji = '🔴' if community.risk_score > 0.6 else '🟡' if community.risk_score > 0.4 else '🟢'
                    print(f"  {risk_emoji} {community.description}")
                    print(f"     Size: {len(community.entities)} | Level: {community.level}")

        # Export results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.format == 'json':
            kg.export_to_json(str(output_path))
        elif args.format == 'gexf':
            kg.export_to_gexf(str(output_path))
        elif args.format == 'graphml':
            kg.export_to_graphml(str(output_path))

        print(f"\n{'='*60}")
        print(f"✅ Analysis complete!")
        print(f"Output saved to: {output_path}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
