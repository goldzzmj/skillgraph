"""
Tests for Skill Parser
"""

import pytest
from pathlib import Path

from skillgraph.parser import SkillParser, ParsedSkill


class TestSkillParser:
    """Test cases for SkillParser."""

    @pytest.fixture
    def parser(self):
        return SkillParser()

    @pytest.fixture
    def normal_skill_path(self):
        return Path(__file__).parent.parent / "examples" / "normal_skill.md"

    @pytest.fixture
    def malicious_skill_path(self):
        return Path(__file__).parent.parent / "examples" / "malicious_skill.md"

    def test_parse_basic_content(self, parser):
        """Test parsing basic markdown content."""
        content = """# Test Skill\n\nSome content here."""
        result = parser.parse(content)

        assert isinstance(result, ParsedSkill)
        assert result.name == "Test Skill"

    def test_parse_with_frontmatter(self, parser):
        """Test parsing content with YAML frontmatter."""
        content = """---
name: My Skill
description: Test description
tags: [test, demo]
---

# My Skill

Content here.
"""
        result = parser.parse(content)

        assert result.name == "My Skill"
        assert result.description == "Test description"
        assert "test" in result.tags

    def test_parse_file(self, parser, normal_skill_path):
        """Test parsing from file."""
        if not normal_skill_path.exists():
            pytest.skip("Example file not found")

        result = parser.parse_file(str(normal_skill_path))

        assert result.name == "Code Review Helper"
        assert len(result.sections) > 0
        assert len(result.code_blocks) > 0

    def test_extract_code_blocks(self, parser):
        """Test code block extraction."""
        content = """# Skill

```python
print("hello")
```

```bash
echo "world"
```
"""
        result = parser.parse(content)

        assert len(result.code_blocks) == 2
        assert result.code_blocks[0]['language'] == 'python'
        assert result.code_blocks[1]['language'] == 'bash'

    def test_extract_urls(self, parser):
        """Test URL extraction."""
        content = """# Skill

Visit https://example.com for more info.
Also check http://test.org/page
"""
        result = parser.parse(content)

        assert len(result.urls) >= 2
        assert any('example.com' in url for url in result.urls)

    def test_to_dict(self, parser):
        """Test conversion to dictionary."""
        content = "# Test\n\nContent"
        result = parser.parse(content)

        d = result.to_dict()

        assert isinstance(d, dict)
        assert 'name' in d
        assert 'sections' in d

    def test_to_json(self, parser):
        """Test conversion to JSON."""
        content = "# Test\n\nContent"
        result = parser.parse(content)

        json_str = result.to_json()

        assert isinstance(json_str, str)
        assert '"name"' in json_str
