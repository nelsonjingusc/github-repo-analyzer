#!/usr/bin/env python3
"""
GitHub Repository Analysis Agent - Demo Queries

This script demonstrates various query types and capabilities of the agent.
Run this to see example interactions and test the system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from ai_agent import GitHubAnalysisAgent


class DemoRunner:
    """Runs demonstration queries to showcase agent capabilities"""
    
    def __init__(self, github_token=None):
        self.agent = GitHubAnalysisAgent(github_token)
        self.demo_queries = [
            "What are the top 5 most starred Python web frameworks?",
            "Show me trending JavaScript projects this month",
            "Compare React vs Vue.js repository activity",
            "Find popular machine learning libraries in Python",
            "What are the most active Go projects?",
            "Show me trending AI repositories",
            "Compare TensorFlow vs PyTorch",
            "Find beginner-friendly web development projects",
            "What are the top Node.js frameworks?",
            "Show me popular data visualization libraries"
        ]
    
    async def run_demo_query(self, query: str):
        """Run a single demo query and display results"""
        print(f"\n{'='*60}")
        print(f"🔍 DEMO QUERY: {query}")
        print('='*60)
        
        try:
            result = await self.agent.process_query(query)
            
            if result['success']:
                print(f"✅ SUCCESS (Intent: {result['intent']})")
                print(f"📊 Confidence: {result.get('confidence', 0):.2f}")
                print(f"📈 Repos Analyzed: {result.get('metadata', {}).get('repositories_analyzed', 0)}")
                print("\n📋 RESPONSE:")
                print(result['response'])
                
                if result.get('metadata'):
                    meta = result['metadata']
                    print(f"\n🔍 METADATA:")
                    print(f"  Language: {meta.get('language', 'N/A')}")
                    print(f"  Processing Time: {meta.get('processing_time', 'N/A')}")
            else:
                print(f"❌ ERROR: {result['response']}")
                if result.get('suggestions'):
                    print("💡 Suggestions:")
                    for suggestion in result['suggestions']:
                        print(f"  • {suggestion}")
                        
        except Exception as e:
            print(f"💥 EXCEPTION: {e}")
        
        print(f"{'='*60}\n")
    
    async def run_all_demos(self):
        """Run all demonstration queries"""
        print("🚀 GitHub Repository Analysis Agent - Demo Mode")
        print(f"Running {len(self.demo_queries)} demonstration queries...\n")
        
        for i, query in enumerate(self.demo_queries, 1):
            print(f"Demo {i}/{len(self.demo_queries)}")
            await self.run_demo_query(query)
            
            # Small delay between queries to be nice to GitHub API
            await asyncio.sleep(1)
        
        print("✨ Demo completed! All queries have been processed.")
    
    async def run_interactive_demo(self):
        """Run interactive demo where user can select queries"""
        print("🎯 Interactive Demo Mode")
        print("Select queries to run:\n")
        
        while True:
            print("Available demo queries:")
            for i, query in enumerate(self.demo_queries, 1):
                print(f"  {i}. {query}")
            
            print(f"  0. Run all queries")
            print(f"  q. Quit")
            
            try:
                choice = input("\nSelect a query number (or 'q' to quit): ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == '0':
                    await self.run_all_demos()
                    break
                else:
                    query_num = int(choice)
                    if 1 <= query_num <= len(self.demo_queries):
                        await self.run_demo_query(self.demo_queries[query_num - 1])
                    else:
                        print("Invalid query number!")
                        
            except (ValueError, KeyboardInterrupt):
                if choice != 'q':
                    print("Invalid input! Please enter a number or 'q'.")
                break
    
    def print_capabilities_overview(self):
        """Print overview of agent capabilities"""
        print("""
🎯 AGENT CAPABILITIES OVERVIEW

The GitHub Repository Analysis Agent can handle these types of queries:

1. 📊 RANKING QUERIES
   • "Top N most starred repositories"
   • "Most popular Python frameworks" 
   • "Best machine learning libraries"
   
2. 📈 TRENDING ANALYSIS
   • "Trending JavaScript projects this week"
   • "Hot repositories in artificial intelligence"
   • "Rising stars in web development"
   
3. ⚖️ REPOSITORY COMPARISONS  
   • "Compare React vs Vue.js vs Angular"
   • "TensorFlow vs PyTorch analysis"
   • "Django vs Flask vs FastAPI"
   
4. 🔍 SMART SEARCH
   • "Find beginner-friendly Python projects"
   • "Show me blockchain projects in Go"
   • "Search for data visualization tools"

5. 🏗️ TECHNICAL FEATURES
   • Natural language understanding
   • Intelligent response generation
   • GitHub API integration with caching
   • Rate limit handling
   • Async processing for performance
   • Rich CLI formatting
        """)


async def main():
    """Main demo function"""
    print("GitHub Repository Analysis Agent - Demo Script")
    
    # Get GitHub token from environment
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️  No GitHub token found. API rate limits will be lower.")
        print("   Set GITHUB_TOKEN environment variable for better performance.")
    
    demo = DemoRunner(github_token)
    
    # Check arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            await demo.run_all_demos()
        elif sys.argv[1] == '--interactive':
            demo.print_capabilities_overview()
            await demo.run_interactive_demo()
        elif sys.argv[1] == '--help':
            print("""
Demo Script Usage:
  python demo_queries.py                # Interactive mode
  python demo_queries.py --all          # Run all demos
  python demo_queries.py --interactive  # Interactive selection
  python demo_queries.py --help         # Show this help
            """)
        else:
            # Treat argument as a custom query
            custom_query = " ".join(sys.argv[1:])
            await demo.run_demo_query(custom_query)
    else:
        # Default to interactive mode
        demo.print_capabilities_overview()
        await demo.run_interactive_demo()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"💥 Demo failed with error: {e}")
        sys.exit(1)