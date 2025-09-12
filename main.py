#!/usr/bin/env python3
"""
GitHub Repository Analysis Agent - Main Entry Point

A sophisticated AI agent that analyzes GitHub repository data to answer
questions about code trends, project activity, and repository comparisons.

This is the main entry point for the application. It can be run in
interactive mode or with single queries.

Author: GitHub Repository Analyzer Team
License: MIT
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from cli import main as cli_main
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you've installed the required dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def main():
    """
    Main application entry point with enhanced argument handling
    """
    parser = argparse.ArgumentParser(
        description="GitHub Repository Analysis Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
GitHub Repository Analysis Agent

Helps analyze GitHub repositories, find trending projects, and compare 
repositories through natural language queries.

Examples:
  python main.py
  python main.py --token YOUR_GITHUB_TOKEN
  python main.py --query "top 5 Python web frameworks"
  python main.py --query "compare React vs Vue" --json

Environment Variables:
  GITHUB_TOKEN    - GitHub personal access token for higher rate limits
        """
    )
    
    parser.add_argument(
        '--token', '-t',
        help='GitHub personal access token (or set GITHUB_TOKEN env var)',
        default=os.getenv('GITHUB_TOKEN')
    )
    
    parser.add_argument(
        '--openai-key', '-o', 
        help='OpenAI API key for advanced query parsing (or set OPENAI_API_KEY env var)',
        default=os.getenv('OPENAI_API_KEY')
    )
    
    parser.add_argument(
        '--query', '-q',
        help='Execute a single query and exit'
    )
    
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging and verbose output'
    )
    
    parser.add_argument(
        '--complete', '-c',
        action='store_true',
        help='Use OpenAI for natural language responses (requires --openai-key)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='GitHub Repository Analyzer 1.0.0'
    )
    
    # Check for help or version first
    if len(sys.argv) == 1:
        print("🚀 Starting GitHub Repository Analysis Agent in interactive mode...")
        print("Tip: Use --help to see all available options\n")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate GitHub token recommendation
    if not args.token:
        print("⚠️  Warning: No GitHub token provided.")
        print("   You can still use the agent, but with limited API rate limits.")
        print("   Get a token at: https://github.com/settings/tokens")
        print("   Set it with: export GITHUB_TOKEN=your_token_here\n")
    
    # Pass arguments to CLI main
    sys.argv = ['cli.py']  # Reset argv for cli module
    if args.token:
        sys.argv.extend(['--token', args.token])
    if args.openai_key:
        sys.argv.extend(['--openai-key', args.openai_key])
    if args.query:
        sys.argv.extend(['--query', args.query])
    if args.json:
        sys.argv.append('--json')
    if args.debug:
        sys.argv.append('--debug')
    if args.complete:
        sys.argv.append('--complete')
    
    try:
        cli_main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        if args.debug:
            raise
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()