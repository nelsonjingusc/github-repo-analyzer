"""
Command Line Interface for GitHub Repository Analysis Agent

This module provides a CLI for the GitHub repository analysis agent,
allowing users to chat with the AI agent and get repository insights.
"""

import asyncio
import sys
from typing import Optional
import logging
from datetime import datetime
import json

# Rich library for beautiful CLI output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ai_agent import GitHubAnalysisAgent


class CLIInterface:
    """
    command-line interface for the GitHub Analysis Agent
    """
    
    def __init__(self, github_token: Optional[str] = None, openai_api_key: Optional[str] = None, debug: bool = False, complete: bool = False):
        """
        Initialize the CLI interface
        
        Args:
            github_token: Optional GitHub token for API access
            openai_api_key: Optional OpenAI API key for advanced query parsing
            debug: Enable debug logging
            complete: Use OpenAI for response generation (--complete mode)
        """
        self.agent = GitHubAnalysisAgent(github_token, openai_api_key, use_openai_for_responses=complete)
        self.console = Console() if RICH_AVAILABLE else None
        self.debug = debug
        self.setup_logging()
        
        # CLI state  
        self.session_start = datetime.now()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('github_analyzer.log'),
                logging.StreamHandler() if self.debug else logging.NullHandler()
            ]
        )
        
        # Suppress verbose HTTP logs unless debug mode
        if not self.debug:
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
    
    
    def display_result(self, result: dict):
        """Display query result with rich formatting"""
        if not RICH_AVAILABLE:
            return self.display_result_simple(result)
        
        if result['success']:
            # Main response
            response_panel = Panel(
                Markdown(result['response']),
                title=f"🤖 Analysis Result (Intent: {result['intent']})",
                border_style="green"
            )
            self.console.print(response_panel)
            
            # Metadata
            if result.get('metadata'):
                meta = result['metadata']
                metadata_text = f"""
**Language:** {meta.get('language', 'N/A')} | **Repos Found:** {meta.get('repositories_found', 0)}
                """.strip()
                
                self.console.print(Panel(
                    Markdown(metadata_text),
                    title="Query Details",
                    border_style="blue",
                    padding=(0, 1)
                ))
        else:
            # Error handling
            error_panel = Panel(
                f"[red]{result['response']}[/red]",
                title="❌ Error",
                border_style="red"
            )
            self.console.print(error_panel)
            
            if result.get('suggestions'):
                suggestions_text = "\n".join(f"• {suggestion}" for suggestion in result['suggestions'])
                self.console.print(Panel(
                    suggestions_text,
                    title="💡 Suggestions",
                    border_style="yellow"
                ))
    
    def display_result_simple(self, result: dict):
        """Display result in simple text format"""
        print("\n" + "="*50)
        if result['success']:
            print("ANALYSIS RESULT:")
            print("-"*20)
            print(result['response'])
            print(f"\nIntent: {result['intent']}")
        else:
            print("ERROR:")
            print("-"*20)
            print(result['response'])
            if result.get('suggestions'):
                print("\nSuggestions:")
                for suggestion in result['suggestions']:
                    print(f"- {suggestion}")
        print("="*50 + "\n")
    
    

def main(github_token=None, openai_api_key=None, query=None, json_output=False, debug=False, complete=False):
    """
    Main CLI entry point - now accepts parameters instead of parsing arguments
    
    Args:
        github_token: GitHub personal access token
        openai_api_key: OpenAI API key for advanced query parsing
        query: Repository analysis query (required)
        json_output: Output results in JSON format
        debug: Enable debug logging
        complete: Use OpenAI for natural language responses
    """
    if not query:
        raise ValueError("Query parameter is required")
    
    # Create CLI interface
    cli = CLIInterface(github_token=github_token, openai_api_key=openai_api_key, debug=debug, complete=complete)
    
    try:
        # Single query mode
        async def run_single_query():
            result = await cli.agent.process_query(query)
            if json_output:
                print(json.dumps(result, indent=2, default=str))
            else:
                cli.display_result(result)
            return result['success']
        
        success = asyncio.run(run_single_query())
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Critical error: {e}")
        if debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()