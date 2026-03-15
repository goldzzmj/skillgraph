"""
SkillGraph - Agent Skills Security Scanner

Map the Hidden Risks in your AI Agent Skills.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="skillgraph",
    version="0.1.0",
    author="SkillGraph Team",
    author_email="",
    description="Agent Skills Security Scanner using GraphRAG + GNN",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/goldzzmj/skillgraph",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "markdown>=3.5",
        "PyYAML>=6.0",
        "networkx>=3.2",
        "streamlit>=1.30",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4",
            "pytest-cov>=4.1",
            "black>=24.0",
            "ruff>=0.1",
            "mypy>=1.8",
        ],
        "gnn": [
            "torch>=2.0",
            "torch-geometric>=2.4",
        ],
        "llm": [
            "langchain>=0.1.0",
            "anthropic>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "skillgraph=skillgraph.cli:main",
        ],
    },
)
