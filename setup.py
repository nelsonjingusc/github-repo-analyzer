"""
Setup configuration for GitHub Repository Analysis Agent

This setup.py file enables professional package distribution and installation.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f.readlines() 
            if line.strip() and not line.startswith('#') and not line.startswith('-')
        ]
else:
    requirements = [
        "requests>=2.31.0",
        "aiohttp>=3.9.0", 
        "rich>=13.7.0",
        "python-dateutil>=2.8.2",
        "typing-extensions>=4.8.0"
    ]

setup(
    name="github-repo-analyzer",
    version="1.0.0",
    author="Nelson Jing",
    author_email="nelson.jingusc@gmail.com",
    description="AI agent for intelligent GitHub repository analysis and trends discovery",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nelsonjingusc/github-repo-analyzer",
    project_urls={
        "Bug Tracker": "https://github.com/nelsonjingusc/github-repo-analyzer/issues",
        "Documentation": "https://github.com/nelsonjingusc/github-repo-analyzer#readme",
        "Source Code": "https://github.com/nelsonjingusc/github-repo-analyzer",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: English",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0", 
            "pytest-cov>=4.1.0",
            "black>=23.9.0",
            "flake8>=6.1.0",
            "mypy>=1.6.0",
        ],
        "llm": [
            "ollama-python>=0.1.7",
            "transformers>=4.35.0",
        ],
        "nlp": [
            "spacy>=3.7.0",
            "nltk>=3.8.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "github-analyzer=main:main",
            "repo-analyzer=main:main",
        ],
    },
    keywords=[
        "github", "repository", "analysis", "ai", "agent", "trends", 
        "machine-learning", "nlp", "api", "cli", "open-source"
    ],
    include_package_data=True,
    zip_safe=False,
)