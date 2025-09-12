"""
AI Agent for GitHub Repository Analysis

This module implements an intelligent agent that can understand natural language
queries about GitHub repositories and provide detailed analysis using GitHub API data.

The agent uses local LLM capabilities (Ollama) for conversation and integrates
with custom GitHub analysis tools.

Note: This was quite a fun project to build! Spent a lot of time fine-tuning
the natural language understanding part.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
import aiohttp
from dataclasses import dataclass

from github_tool import GitHubRepositoryTool, GitHubAPIError
from query_parser import QueryParser, OpenAIQueryParser, QueryIntent, OPENAI_AVAILABLE

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Maintains conversation state and context"""
    user_id: str = "default"
    last_query: Optional[str] = None
    last_intent: Optional[QueryIntent] = None
    last_language: Optional[str] = None
    conversation_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


class LLMProvider:
    """
    Abstract base for LLM providers with fallback mechanisms.
    Supports OpenAI API, Ollama (local), and basic template responses.
    """
    
    def __init__(self, openai_client=None, use_complete_mode=False):
        self.ollama_available = False
        self.openai_available = False
        self.openai_client = openai_client
        self.use_complete_mode = use_complete_mode
        if openai_client:
            self.openai_available = True
            logger.info("OpenAI client available for response generation")
        # Note: _check_availability will be called asynchronously when needed
    
    async def _check_availability(self):
        """Check which LLM providers are available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/version", timeout=2) as response:
                    if response.status == 200:
                        self.ollama_available = True
                        logger.info("Ollama LLM provider available")
        except:
            logger.info("Ollama not available, will use template responses")
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Generate response using available LLM provider with intelligent fallbacks
        Priority: --complete + OpenAI > Ollama > Template (default)
        """
        # Only use OpenAI if both --complete flag and API key are available
        if self.use_complete_mode and self.openai_available:
            return await self._openai_generate(prompt, context)
        elif self.ollama_available:
            return await self._ollama_generate(prompt, context)
        else:
            return self._template_generate(prompt, context or {})
    
    async def _openai_generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate response using OpenAI GPT"""
        try:
            # Try GPT-5 first, fallback to GPT-4o if not available
            try:
                model = "gpt-5"
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful GitHub repository analysis expert. Provide clear, informative responses about repositories, programming trends, and code analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_completion_tokens=800  # GPT-5 uses max_completion_tokens
                )
                logger.info("Generated response using OpenAI GPT-5")
            except Exception as model_error:
                # Fallback to GPT-4o if GPT-5 is not available
                logger.warning(f"GPT-5 not available: {model_error}. Falling back to GPT-4o")
                model = "gpt-4o"
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a helpful GitHub repository analysis expert. Provide clear, informative responses about repositories, programming trends, and code analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800  # GPT-4o still uses max_tokens
                )
                logger.info("Generated response using OpenAI GPT-4o")
            
            result = response.choices[0].message.content.strip()
            return result
            
        except Exception as e:
            logger.warning(f"OpenAI response generation failed: {e}")
            # Fall back to template generation
            return self._template_generate(prompt, context or {})
    
    async def _ollama_generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate response using Ollama local LLM"""
        try:
            payload = {
                "model": "llama2",  # or "mistral", "codellama"
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "").strip()
                    else:
                        logger.warning(f"Ollama request failed: {response.status}")
                        return self._template_generate(prompt, context or {})
                        
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
            return self._template_generate(prompt, context or {})
    
    def _template_generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Fallback template-based response generation for when LLMs are unavailable.
        This provides intelligent responses based on the analysis results.
        """
        intent = context.get('intent')
        data = context.get('data', [])
        language = context.get('language', 'repositories')
        
        if intent == QueryIntent.RANKING:
            return self._format_ranking_response(data, context)
        elif intent == QueryIntent.COMPARISON:
            return self._format_comparison_response(data, context)
        elif intent == QueryIntent.TRENDING:
            return self._format_trending_response(data, context)
        else:
            return self._format_search_response(data, context)
    
    def _format_ranking_response(self, data: List[Dict], context: Dict) -> str:
        """Format ranking query responses"""
        if not data:
            return f"I couldn't find any {context.get('language', '')} repositories matching your criteria."
        
        language = context.get('language', 'repositories')
        limit = min(len(data), context.get('limit', 5))
        
        response = f"Here are the top {limit} most starred {language} repositories:\n\n"
        
        for i, repo in enumerate(data[:limit], 1):
            name = repo.get('name', 'Unknown')
            full_name = repo.get('full_name', name)
            stars = repo.get('stargazers_count', 0)
            description = (repo.get('description') or 'No description available')[:100]
            
            response += f"{i}. **{full_name}** ⭐ {stars:,}\n"
            full_description = repo.get('description') or ''
            response += f"   {description}{'...' if len(full_description) > 100 else ''}\n\n"
        
        return response
    
    def _format_comparison_response(self, data: Dict, context: Dict) -> str:
        """Format repository comparison responses"""
        if not data:
            return "I couldn't retrieve comparison data for the requested repositories."
        
        response = "## Repository Comparison\n\n"
        
        for repo_name, repo_data in data.items():
            response += f"### {repo_name}\n"
            response += f"- **Stars**: {repo_data.get('stars', 0):,}\n"
            response += f"- **Forks**: {repo_data.get('forks', 0):,}\n"
            response += f"- **Language**: {repo_data.get('language', 'Unknown')}\n"
            response += f"- **Recent Commits**: {repo_data.get('recent_commits', 0)}\n"
            response += f"- **Contributors**: {repo_data.get('contributors_count', 0)}\n"
            response += f"- **Last Updated**: {repo_data.get('updated_at', 'Unknown')[:10]}\n\n"
        
        # Add analysis
        if len(data) == 2:
            repos = list(data.values())
            star_leader = "first" if repos[0]['stars'] > repos[1]['stars'] else "second"
            activity_leader = "first" if repos[0]['recent_commits'] > repos[1]['recent_commits'] else "second"
            
            response += f"**Analysis**: The {star_leader} repository has more stars, "
            response += f"while the {activity_leader} repository shows more recent activity."
        
        return response
    
    def _format_trending_response(self, data: List[Dict], context: Dict) -> str:
        """Format trending repositories responses"""
        if not data:
            return "I couldn't find any trending repositories matching your criteria."
        
        language = context.get('language', '')
        response = f"## Trending {language.title() + ' ' if language else ''}Repositories\n\n"
        
        for i, repo in enumerate(data[:10], 1):
            name = repo.get('full_name', repo.get('name', 'Unknown'))
            stars = repo.get('stargazers_count', 0)
            language_info = repo.get('language', 'Multiple')
            updated = repo.get('updated_at', '')[:10] if repo.get('updated_at') else 'Unknown'
            
            response += f"{i}. **{name}** ({language_info})\n"
            response += f"   ⭐ {stars:,} stars | Updated: {updated}\n"
            
            if repo.get('description'):
                desc = repo['description'][:80]
                response += f"   {desc}{'...' if len(repo['description']) > 80 else ''}\n"
            response += "\n"
        
        return response
    
    def _format_search_response(self, data: List[Dict], context: Dict) -> str:
        """Format general search responses"""
        if not data:
            return "I couldn't find any repositories matching your search criteria."
        
        query = context.get('original_query', 'your query')
        response = f"Found {len(data)} repositories related to '{query}':\n\n"
        
        for i, repo in enumerate(data[:8], 1):
            name = repo.get('full_name', repo.get('name', 'Unknown'))
            stars = repo.get('stargazers_count', 0)
            language_info = repo.get('language', 'Multiple')
            
            response += f"{i}. **{name}** ({language_info}) - ⭐ {stars:,}\n"
            
            if repo.get('description'):
                desc = repo['description'][:100]
                response += f"   {desc}{'...' if len(repo['description']) > 100 else ''}\n"
            response += "\n"
        
        return response


class GitHubAnalysisAgent:
    """
    Main AI agent for GitHub repository analysis.
    
    This agent combines natural language understanding, GitHub API integration,
    and intelligent response generation to provide comprehensive repository analysis.
    """
    
    def __init__(self, github_token: Optional[str] = None, openai_api_key: Optional[str] = None, use_openai_for_responses: bool = False):
        """
        Initialize the GitHub Analysis Agent
        
        Args:
            github_token: Optional GitHub token for higher rate limits
            openai_api_key: Optional OpenAI API key for advanced query parsing
            use_openai_for_responses: Whether to use OpenAI for response generation (--complete mode)
        """
        self.github_tool = GitHubRepositoryTool(github_token)
        
        # Initialize OpenAI client for both parsing and response generation
        openai_client = None
        if openai_api_key and OPENAI_AVAILABLE:
            try:
                from openai import OpenAI
                openai_client = OpenAI(api_key=openai_api_key)
                self.query_parser = OpenAIQueryParser(openai_api_key)
                logger.info("Using OpenAI for both query parsing and response generation")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.query_parser = QueryParser()
                logger.info("Falling back to rule-based query parser")
        else:
            self.query_parser = QueryParser()
            if openai_api_key and not OPENAI_AVAILABLE:
                logger.warning("OpenAI API key provided but openai library not installed. Using rule-based parser.")
            else:
                logger.info("Using rule-based query parser")
        
        self.llm_provider = LLMProvider(openai_client, use_complete_mode=use_openai_for_responses)
        self.context = ConversationContext()
        
        logger.info("GitHub Analysis Agent initialized")
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query and return comprehensive analysis
        
        Args:
            user_query: Natural language query from the user
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            logger.info(f"Processing query: {user_query}")
            
            # Parse the query to understand intent
            parsed_query = self.query_parser.parse_query(user_query)
            
            # Validate query
            if not self.query_parser.validate_query(parsed_query):
                suggestions = self.query_parser.get_suggested_clarifications(parsed_query)
                return {
                    "response": "I need more information to help you. " + " ".join(suggestions),
                    "success": False,
                    "suggestions": suggestions,
                    "intent": parsed_query['intent'].value
                }
            
            # Update context
            self.context.last_query = user_query
            self.context.last_intent = parsed_query['intent']
            self.context.last_language = parsed_query['language']
            
            # Execute the appropriate analysis based on intent
            analysis_result = await self._execute_analysis(parsed_query)
            
            # Generate intelligent response
            response = await self._generate_response(parsed_query, analysis_result)
            
            # Update conversation history
            self.context.conversation_history.append({
                "query": user_query,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "intent": parsed_query['intent'].value
            })
            
            return {
                "response": response,
                "success": True,
                "intent": parsed_query['intent'].value,
                "data": analysis_result,
                "confidence": parsed_query['confidence'],
                "metadata": {
                    "language": parsed_query['language'],
                    "repositories_found": len(analysis_result) if isinstance(analysis_result, list) else len(analysis_result) if isinstance(analysis_result, dict) else 0,
                    "processing_time": "< 1s"
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": f"I encountered an error while processing your query: {str(e)}",
                "success": False,
                "error": str(e),
                "intent": "error"
            }
    
    async def _execute_analysis(self, parsed_query: Dict[str, Any]) -> Any:
        """Execute the appropriate GitHub analysis based on query intent"""
        intent = parsed_query['intent']
        
        try:
            if intent == QueryIntent.RANKING:
                return await self._handle_ranking_query(parsed_query)
            elif intent == QueryIntent.COMPARISON:
                return await self._handle_comparison_query(parsed_query)
            elif intent == QueryIntent.TRENDING:
                return await self._handle_trending_query(parsed_query)
            elif intent == QueryIntent.SEARCH:
                return await self._handle_search_query(parsed_query)
            else:
                return []
                
        except GitHubAPIError as e:
            logger.error(f"GitHub API error during analysis: {e}")
            raise Exception(f"GitHub API error: {e}")
    
    async def _handle_ranking_query(self, parsed_query: Dict) -> List[Dict]:
        """Handle repository ranking queries"""
        query_parts = []
        
        # Build search query
        if parsed_query['project_type']:
            query_parts.append(parsed_query['project_type'])
        
        if parsed_query['language']:
            query_parts.append(parsed_query['language'])
        
        # Extract additional domain-specific keywords from the original query
        original_query = parsed_query['original_query'].lower()
        domain_keywords = []
        
        # Common domain keywords that should be included in search
        important_terms = {
            'trading', 'finance', 'financial', 'option', 'options', 'covered', 'calls',
            'machine', 'learning', 'neural', 'network', 'deep', 'ai', 'artificial',
            'web', 'http', 'rest', 'api', 'microservice', 'microservices',
            'database', 'sql', 'nosql', 'orm', 'cache', 'redis',
            'testing', 'test', 'unit', 'integration', 'mock',
            'auth', 'authentication', 'security', 'crypto', 'encryption',
            'docker', 'kubernetes', 'cloud', 'aws', 'gcp', 'azure'
        }
        
        # Check if OpenAI parser provided domain keywords
        if 'domain_keywords' in parsed_query and parsed_query['domain_keywords']:
            domain_keywords = parsed_query['domain_keywords'][:3]  # Use OpenAI keywords
        else:
            # Extract meaningful domain terms from the query (fallback)
            words = original_query.replace("'", "").split()
            for word in words:
                clean_word = word.strip('.,!?')
                if clean_word in important_terms:
                    domain_keywords.append(clean_word)
        
        # Add domain keywords to search query
        if domain_keywords:
            query_parts.extend(domain_keywords[:3])  # Limit to 3 most important terms
        
        search_query = " ".join(query_parts) if query_parts else "stars:>100"
        
        # Get repositories
        repositories = self.github_tool.search_repositories(
            query=search_query,
            language=parsed_query['language'],
            sort=parsed_query['sort_by'],
            order="desc",
            per_page=parsed_query['limit']
        )
        
        return repositories
    
    async def _handle_comparison_query(self, parsed_query: Dict) -> Dict:
        """Handle repository comparison queries"""
        repos_to_compare = []
        
        for repo_name in parsed_query['repositories']:
            # Try to find the repository
            if '/' in repo_name:
                owner, name = repo_name.split('/', 1)
                repos_to_compare.append((owner, name))
            else:
                # Check if it's a language comparison (like "Java vs Python")
                programming_languages = {'java', 'python', 'javascript', 'go', 'rust', 'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin'}
                
                if repo_name.lower() in programming_languages:
                    # For language comparisons, search for the most popular repository in that language
                    search_results = self.github_tool.search_repositories(
                        query="",  # Empty query to get top repos
                        language=repo_name.lower(),
                        sort="stars",
                        order="desc",
                        per_page=1
                    )
                    if search_results:
                        full_name = search_results[0]['full_name']
                        owner, name = full_name.split('/', 1)
                        repos_to_compare.append((owner, name))
                else:
                    # Search for the repository by name
                    search_results = self.github_tool.search_repositories(
                        query=repo_name,
                        per_page=1
                    )
                    if search_results:
                        full_name = search_results[0]['full_name']
                        owner, name = full_name.split('/', 1)
                        repos_to_compare.append((owner, name))
        
        if repos_to_compare:
            return self.github_tool.compare_repositories(repos_to_compare)
        else:
            return {}
    
    async def _handle_trending_query(self, parsed_query: Dict) -> List[Dict]:
        """Handle trending repositories queries"""
        days = parsed_query['filters'].get('days', 30)
        min_stars = parsed_query['filters'].get('min_stars', 10)
        
        return self.github_tool.find_trending_repositories(
            language=parsed_query['language'],
            days=days,
            min_stars=min_stars
        )
    
    async def _handle_search_query(self, parsed_query: Dict) -> List[Dict]:
        """Handle general search queries"""
        # Extract search terms from the original query with better NLP
        original_query = parsed_query['original_query'].lower()
        
        # Expanded stop words for better filtering
        stop_words = {
            'find', 'show', 'me', 'some', 'any', 'projects', 'repositories', 'repos', 
            'about', 'for', 'with', 'that', 'are', 'is', 'am', 'looking', 'search',
            'get', 'help', 'i', 'im', 'want', 'need', 'decent', 'good', 
            'nice', 'best', 'top', 'popular', 'which', 'what', 'how', 'where',
            'arent', 'too', 'very', 'really', 'quite', 'pretty', 'heavyweight',
            'light', 'heavy', 'small', 'large', 'simple', 'complex'
        }
        
        # Look for technical keywords that are more meaningful
        tech_keywords = {
            'framework', 'frameworks', 'library', 'libraries', 'tool', 'tools',
            'microservice', 'microservices', 'api', 'rest', 'web', 'http',
            'database', 'db', 'orm', 'sql', 'nosql', 'cache', 'redis',
            'testing', 'auth', 'authentication', 'security', 'crypto',
            'machine', 'learning', 'ml', 'ai', 'neural', 'deep',
            'docker', 'kubernetes', 'cloud', 'aws', 'gcp', 'azure'
        }
        
        # Extract words and find meaningful ones
        words = original_query.replace("'", "").split()
        meaningful_words = []
        
        # First pass: look for technical keywords
        for word in words:
            clean_word = word.strip('.,!?')
            if clean_word in tech_keywords:
                meaningful_words.append(clean_word)
        
        # Second pass: add other significant words not in stop words
        for word in words:
            clean_word = word.strip('.,!?')
            if (clean_word not in stop_words and 
                len(clean_word) > 2 and 
                clean_word not in meaningful_words):
                meaningful_words.append(clean_word)
        
        # If we found meaningful words, use them; otherwise fall back to original logic
        if meaningful_words:
            search_query = " ".join(meaningful_words[:3])
        else:
            # Fallback: just use project type or language if available
            if parsed_query['project_type']:
                search_query = parsed_query['project_type']
            elif parsed_query['language']:
                search_query = f"{parsed_query['language']} framework"
            else:
                search_query = "popular projects"
        
        return self.github_tool.search_repositories(
            query=search_query,
            language=parsed_query['language'],
            sort="stars",
            order="desc",
            per_page=20
        )
    
    async def _generate_response(self, parsed_query: Dict, analysis_result: Any) -> str:
        """Generate intelligent natural language response"""
        # Prepare context for LLM
        context = {
            'intent': parsed_query['intent'],
            'language': parsed_query['language'],
            'original_query': parsed_query['original_query'],
            'data': analysis_result,
            'limit': parsed_query.get('limit', 10)
        }
        
        # Create prompt for LLM
        prompt = self._create_response_prompt(parsed_query, analysis_result)
        
        # Generate response
        response = await self.llm_provider.generate_response(prompt, context)
        
        return response
    
    def _create_response_prompt(self, parsed_query: Dict, analysis_result: Any) -> str:
        """Create prompt for LLM response generation"""
        intent = parsed_query['intent'].value
        query = parsed_query['original_query']
        
        prompt = f"""
You are a GitHub repository analysis expert. A user asked: "{query}"

The query intent is: {intent}
Programming language: {parsed_query.get('language', 'Not specified')}

Analysis results: {json.dumps(analysis_result, default=str)[:1000]}

Provide a clear, informative response that:
1. Directly answers the user's question
2. Highlights the most important findings
3. Uses markdown formatting for readability
4. Includes specific metrics (stars, forks, activity)
5. Keeps response under 500 words

Response:
"""
        return prompt
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.context.conversation_history
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.context.conversation_history = []
        self.context.last_query = None
        self.context.last_intent = None
        self.context.last_language = None
        
        logger.info("Conversation history cleared")