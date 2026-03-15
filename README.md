# SkillGraph

> **Map the Hidden Risks** - Agent Skills Security Scanner

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/status-alpha-orange.svg" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

A security scanner for AI Agent Skills using **GraphRAG + GNN**. Detect hidden risks in downloaded skills before using them.

## Why SkillGraph?

When you download Agent Skills from the internet, they may contain:
- Hidden data exfiltration commands
- Credential theft instructions
- System destruction commands
- Security bypass attempts

SkillGraph helps you **see through** these risks with graph-based analysis.

## Features

- 🔍 **Skill Parser** - Parse Markdown skills into structured data
- ⚠️ **Risk Detection** - Pattern-based security risk identification
- 📊 **Graph Visualization** - Interactive knowledge graph display
- 💻 **CLI Tool** - Command-line interface for quick scanning
- 🌐 **Web UI** - Streamlit-based visualization app

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/goldzzmj/skillgraph.git
cd skillgraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### CLI Usage

```bash
# Scan a skill file
skillgraph scan path/to/skill.md

# Scan with JSON output
skillgraph scan skill.md -f json -o report.json

# Parse skill structure
skillgraph parse skill.md -o parsed.json
```

### Web UI

```bash
# Launch visualization app
skillgraph viz

# Or run directly
streamlit run src/skillgraph/viz/app.py
```

Open http://localhost:8501 in your browser.

## Risk Levels

| Level | Score | Description |
|-------|-------|-------------|
| 🔴 Critical | 0.8-1.0 | Data exfiltration, system destruction |
| 🟠 High | 0.6-0.8 | Sensitive access, network requests |
| 🟡 Medium | 0.4-0.6 | Code execution, config modification |
| 🟢 Low | 0.2-0.4 | General file operations |
| ✅ Safe | 0-0.2 | No risks detected |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   SkillGraph System                  │
├─────────────────────────────────────────────────────┤
│  Input Layer     │  Core Engine     │  Output Layer │
│  - Markdown      │  - Parser        │  - Web UI     │
│  - YAML          │  - Rules Engine  │  - CLI        │
│  - Scripts       │  - Graph Builder │  - API        │
└─────────────────────────────────────────────────────┘
```

## Project Structure

```
skillgraph/
├── src/skillgraph/
│   ├── parser/          # Markdown parsing
│   ├── rules/           # Risk detection rules
│   ├── graph/           # NetworkX graph builder
│   ├── viz/             # Streamlit visualization
│   └── cli.py           # Command-line interface
├── tests/               # Unit tests
├── examples/            # Example skill files
├── requirements.txt
└── setup.py
```

## Roadmap

- [x] MVP: Parser + Rules + CLI
- [x] Streamlit Visualization
- [ ] GraphRAG Integration
- [ ] GNN Risk Model
- [ ] FastAPI Service
- [ ] Claude Code Plugin

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**SkillGraph** - Map the Hidden Risks in your Agent Skills 🔍
