"""
Command Line Interface for GitHub Repository Analysis Agent

This module provides an interactive CLI for the GitHub repository analysis agent,
allowing users to chat with the AI agent and get repository insights.
"""

import asyncio
import argparse
import sys
import os
from typing import Optional
import logging
from datetime import datetime
import json

# Rich library for beautiful CLI output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Installing required dependencies...")
    os.system("pip install rich")
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich.table import Table
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from rich.prompt import Prompt, Confirm
        from rich.live import Live
        from rich.align import Align
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False

from ai_agent import GitHubAnalysisAgent


class CLIInterface:
    """
    Interactive command-line interface for the GitHub Analysis Agent
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
        self.query_count = 0
        self.running = True
        
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
    
    def print_welcome(self):
        """Display welcome message"""
        if RICH_AVAILABLE:
            welcome_text = """
# GitHub Repository Analysis Agent

Welcome to the GitHub repository analysis assistant!

## What I can help with:

• **Repository Rankings**: "Show me the top 5 Python web frameworks"
• **Project Comparisons**: "Compare React vs Vue.js activity" 
• **Trending Analysis**: "What are trending JavaScript projects this week?"
• **Smart Search**: "Find machine learning libraries for beginners"

## Tips:
- Be specific about programming languages for better results
- Ask follow-up questions to dive deeper into any topic
- Type 'help' for more commands or 'quit' to exit
"""
            
            self.console.print(Panel(
                Markdown(welcome_text),
                title="GitHub Repository Analyzer",
                border_style="blue",
                padding=(1, 2)
            ))
        else:
            print("\n" + "="*60)
            print("GitHub Repository Analysis Agent")
            print("="*60)
            print("Ask me about GitHub repositories, trends, and comparisons!")
            print("Type 'help' for commands or 'quit' to exit")
            print("="*60 + "\n")
    
    def print_help(self):
        """Display help information"""
        if RICH_AVAILABLE:
            help_text = """
## Available Commands:

• `help` - Show this help message
• `quit` / `exit` - Exit the application
• `history` - Show conversation history
• `clear` - Clear conversation history
• `stats` - Show session statistics
• `debug on/off` - Toggle debug mode

## Example Queries:

• "What are the most popular Python frameworks?"
• "Show me trending JavaScript projects"
• "Compare TensorFlow vs PyTorch repositories"
• "Find active machine learning projects"
• "Top 10 most starred Go projects this year"
"""
            
            self.console.print(Panel(
                Markdown(help_text),
                title="Help & Commands",
                border_style="green"
            ))
        else:
            print("\nAvailable Commands:")
            print("- help: Show this help")
            print("- quit/exit: Exit application")
            print("- history: Show conversation history")
            print("- clear: Clear history")
            print("- stats: Show session stats\n")
    
    def print_stats(self):
        """Display session statistics"""
        uptime = datetime.now() - self.session_start
        history_count = len(self.agent.get_conversation_history())
        
        if RICH_AVAILABLE:
            stats_table = Table(title="Session Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")
            
            stats_table.add_row("Queries Processed", str(self.query_count))
            stats_table.add_row("Conversation Items", str(history_count))
            stats_table.add_row("Session Uptime", str(uptime).split('.')[0])
            stats_table.add_row("Debug Mode", "Enabled" if self.debug else "Disabled")
            
            self.console.print(stats_table)
        else:
            print(f"\nSession Statistics:")
            print(f"- Queries: {self.query_count}")
            print(f"- History: {history_count} items")
            print(f"- Uptime: {str(uptime).split('.')[0]}")
    
    def print_history(self):
        """Display conversation history"""
        history = self.agent.get_conversation_history()
        
        if not history:
            if RICH_AVAILABLE:
                self.console.print("[yellow]No conversation history yet![/yellow]")
            else:
                print("No conversation history yet!")
            return
        
        if RICH_AVAILABLE:
            for i, item in enumerate(history[-5:], 1):  # Show last 5 items
                query_panel = Panel(
                    f"[bold blue]Q{i}:[/bold blue] {item['query']}\n"
                    f"[dim]Intent: {item['intent']} | Time: {item['timestamp'][:19]}[/dim]",
                    border_style="blue"
                )
                self.console.print(query_panel)
                
                response_panel = Panel(
                    Markdown(item['response']),
                    border_style="green",
                    title="Response"
                )
                self.console.print(response_panel)
                self.console.print()
        else:
            print("\nRecent Conversation History:")
            for i, item in enumerate(history[-3:], 1):
                print(f"\n{i}. Q: {item['query']}")
                print(f"   A: {item['response'][:100]}...")
    
    async def process_user_input(self, user_input: str) -> bool:
        """
        Process user input and return whether to continue
        
        Args:
            user_input: User's input string
            
        Returns:
            True to continue, False to exit
        """
        user_input = user_input.strip()
        
        # Handle special commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            return False
        elif user_input.lower() == 'help':
            self.print_help()
            return True
        elif user_input.lower() == 'history':
            self.print_history()
            return True
        elif user_input.lower() == 'clear':
            self.agent.clear_conversation_history()
            if RICH_AVAILABLE:
                self.console.print("[green]Conversation history cleared![/green]")
            else:
                print("Conversation history cleared!")
            return True
        elif user_input.lower() == 'stats':
            self.print_stats()
            return True
        elif user_input.lower().startswith('debug'):
            if 'on' in user_input.lower():
                self.debug = True
                logging.getLogger().setLevel(logging.DEBUG)
                print("Debug mode enabled")
            elif 'off' in user_input.lower():
                self.debug = False
                logging.getLogger().setLevel(logging.INFO)
                print("Debug mode disabled")
            return True
        elif not user_input:
            return True
        
        # Process as a query to the agent
        await self.handle_query(user_input)
        self.query_count += 1
        return True
    
    async def handle_query(self, query: str):
        """Handle a user query with the AI agent"""
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Analyzing repositories...", total=None)
                
                # Process the query
                result = await self.agent.process_query(query)
                progress.update(task, description="Processing complete!")
                
            # Display results
            self.display_result(result)
        else:
            print("Analyzing...")
            result = await self.agent.process_query(query)
            self.display_result_simple(result)
    
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
    
    async def run_interactive(self):
        """Run the interactive CLI session"""
        self.print_welcome()
        
        try:
            while self.running:
                try:
                    if RICH_AVAILABLE:
                        user_input = Prompt.ask(
                            "[bold cyan]Ask me anything about GitHub repositories[/bold cyan]",
                            default=""
                        )
                    else:
                        user_input = input("\n🔍 Ask me about repositories: ").strip()
                    
                    should_continue = await self.process_user_input(user_input)
                    if not should_continue:
                        break
                        
                except KeyboardInterrupt:
                    if RICH_AVAILABLE:
                        if Confirm.ask("\n[yellow]Are you sure you want to exit?[/yellow]"):
                            break
                    else:
                        print("\n\nGoodbye!")
                        break
                except EOFError:
                    # Handle EOF (Ctrl+D or non-interactive environment)
                    print("\n\nGoodbye!")
                    break
                except Exception as e:
                    if RICH_AVAILABLE:
                        self.console.print(f"[red]Unexpected error: {e}[/red]")
                    else:
                        print(f"Error: {e}")
                    
                    if self.debug:
                        raise
                    
        except Exception as e:
            print(f"Critical error: {e}")
            if self.debug:
                raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        if RICH_AVAILABLE:
            self.console.print("\n[green]Thanks for using GitHub Repository Analyzer! 🚀[/green]")
        else:
            print("\nThanks for using GitHub Repository Analyzer!")
        
        # Log session summary
        logging.info(f"Session ended. Processed {self.query_count} queries.")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="GitHub Repository Analysis Agent - Intelligent CLI for repository insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli --token YOUR_GITHUB_TOKEN
  python -m src.cli --debug
  python -m src.cli --query "top 5 Python web frameworks"
        """
    )
    
    parser.add_argument(
        '--token', '-t',
        help='GitHub personal access token for higher API rate limits',
        default=os.getenv('GITHUB_TOKEN')
    )
    
    parser.add_argument(
        '--openai-key', '-o',
        help='OpenAI API key for advanced query parsing (or set OPENAI_API_KEY env var)',
        default=os.getenv('OPENAI_API_KEY')
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--query', '-q',
        required=True,
        help='Repository analysis query (required)'
    )
    
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results in JSON format (for single queries)'
    )
    
    parser.add_argument(
        '--complete', '-c',
        action='store_true',
        help='Use OpenAI for natural language responses (requires --openai-key)'
    )
    
    args = parser.parse_args()
    
    # Create CLI interface
    cli = CLIInterface(github_token=args.token, openai_api_key=args.openai_key, debug=args.debug, complete=args.complete)
    
    try:
        # Single query mode (now the only mode)
        async def run_single_query():
            result = await cli.agent.process_query(args.query)
            if args.json:
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
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()