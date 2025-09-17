"""
Query Parser for Natural Language Understanding

This module analyzes user queries to extract intent, entities, and parameters
for the GitHub repository analysis agent.
"""

import re
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
import json

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Supported query intents"""
    RANKING = "ranking"          # "top 5 most starred"
    COMPARISON = "comparison"    # "compare React vs Vue"
    TRENDING = "trending"        # "trending projects"
    SEARCH = "search"           # "find projects about"
    UNKNOWN = "unknown"


class OpenAIQueryParser:
    """
    Advanced query parser using OpenAI GPT models for natural language understanding.
    Provides more accurate parsing for complex queries.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-5"):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse query using OpenAI GPT for advanced understanding"""
        try:
            prompt = self._create_parsing_prompt(query)
            
            # Try GPT-5 first, fallback to GPT-4o if not available
            try:
                response = self.client.chat.completions.create(
                    model="gpt-5",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_completion_tokens=300  # GPT-5 uses max_completion_tokens
                )
            except Exception as model_error:
                logger.warning(f"GPT-5 not available for parsing: {model_error}. Using GPT-4o")
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=300  # GPT-4o still uses max_tokens
                )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response - clean markdown code blocks if present
            try:
                # Remove markdown code block formatting
                if result_text.strip().startswith('```'):
                    lines = result_text.strip().split('\n')
                    result_text = '\n'.join(lines[1:-1])  # Remove first and last lines
                
                result = json.loads(result_text)
                
                # Ensure all required fields are present with defaults
                defaults = {
                    'intent': QueryIntent.UNKNOWN,
                    'language': None,
                    'project_type': None,
                    'sort_by': 'stars',
                    'limit': 20,
                    'repositories': [],
                    'domain_keywords': [],
                    'filters': {},
                    'original_query': query,
                    'confidence': 0.9
                }
                
                # Fill in missing fields with defaults
                for key, default_value in defaults.items():
                    if key not in result:
                        result[key] = default_value
                
                # Convert intent string to enum
                if 'intent' in result and isinstance(result['intent'], str):
                    try:
                        result['intent'] = QueryIntent(result['intent'])
                    except ValueError:
                        result['intent'] = QueryIntent.UNKNOWN
                
                logger.info(f"OpenAI parsed query with intent: {result['intent']}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI JSON response: {e}")
                logger.error(f"Raw response: {result_text}")
                # Fall back to rule-based parsing
                return self._fallback_parse(query)
                
        except Exception as e:
            logger.error(f"OpenAI parsing failed: {e}")
            # Fall back to rule-based parsing
            return self._fallback_parse(query)
    
    def _create_parsing_prompt(self, query: str) -> str:
        """Create prompt for OpenAI query parsing"""
        return f"""
Parse this GitHub repository query into structured JSON format:

Query: "{query}"

Extract these fields and return ONLY valid JSON:

{{
    "intent": "ranking|comparison|trending|search",
    "language": "programming language name or null",
    "project_type": "library|framework|tool|application or null", 
    "limit": number (if mentioned, max 50, default 20),
    "repositories": ["owner/repo1", "owner/repo2"] (for comparisons only),
    "domain_keywords": ["keyword1", "keyword2"] (important domain terms like "trading", "machine learning", etc.),
    "sort_by": "stars|forks|updated"
}}

Intent rules:
- "ranking": queries like "top 5", "best", "most popular"  
- "comparison": queries with "vs", "compare", "difference between"
- "trending": queries with "trending", "hot", "rising"
- "search": general search queries like "find", "show me"

IMPORTANT: For comparison queries, convert repository names to full owner/repo format using the most popular/official repositories:
- "React" → "facebook/react"
- "Vue" → "vuejs/vue"
- "Angular" → "angular/angular"
- "Django" → "django/django"
- "Flask" → "pallets/flask"
- "TensorFlow" → "tensorflow/tensorflow"
- "PyTorch" → "pytorch/pytorch"
- "jQuery" → "jquery/jquery"
- "Bootstrap" → "twbs/bootstrap"
- "Express" → "expressjs/express"

Examples:
"top 5 python web frameworks" → {{"intent": "ranking", "language": "python", "project_type": "framework", "limit": 5, "domain_keywords": ["web"]}}
"compare React vs Vue" → {{"intent": "comparison", "repositories": ["facebook/react", "vuejs/vue"], "domain_keywords": []}}
"find machine learning libraries" → {{"intent": "search", "domain_keywords": ["machine", "learning"], "project_type": "library"}}

Return only JSON, no explanations:
"""
    
    def _fallback_parse(self, query: str) -> Dict[str, Any]:
        """Fallback to rule-based parsing if OpenAI fails"""
        logger.info("Falling back to rule-based parsing")
        parser = QueryParser()
        return parser.parse_query(query)
    
    def validate_query(self, parsed_query: Dict[str, Any]) -> bool:
        """Validate if the parsed query has sufficient information to process"""
        # Delegate to rule-based parser for validation
        parser = QueryParser()
        return parser.validate_query(parsed_query)
    
    def get_suggested_clarifications(self, parsed_query: Dict[str, Any]) -> List[str]:
        """Generate suggestions to clarify ambiguous queries"""
        # Delegate to rule-based parser for suggestions
        parser = QueryParser()
        return parser.get_suggested_clarifications(parsed_query)


class QueryParser:
    """
    Rule-based query parser for natural language understanding.
    Fast and reliable fallback when OpenAI is not available.
    """
    
    def __init__(self):
        self.programming_languages = {
            'python', 'javascript', 'java', 'typescript', 'go', 'rust', 'c++', 'c#', 
            'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'shell',
            'html', 'css', 'sql', 'dart', 'lua', 'perl', 'haskell', 'clojure',
            'js', 'ts', 'cpp', 'c', 'objective-c', 'vue', 'react', 'angular'
        }
        
        self.project_types = {
            'framework', 'frameworks', 'library', 'libraries', 'tool', 'tools',
            'package', 'packages', 'module', 'modules', 'plugin', 'plugins',
            'extension', 'extensions', 'sdk', 'api', 'service', 'app', 'application'
        }
        
        self.sort_criteria = {
            'star', 'stars', 'starred', 'fork', 'forks', 'forked', 
            'activity', 'active', 'recent', 'updated', 'commit', 'commits',
            'issue', 'issues', 'contributor', 'contributors', 'watcher', 'watchers'
        }
        
        # Flexible keyword-based patterns instead of rigid regex
        self.ranking_keywords = {'top', 'best', 'most', 'popular', 'starred', 'forked'}
        self.comparison_keywords = {'vs', 'versus', 'compare', 'comparison', 'difference', 'better'}
        self.trending_keywords = {'trending', 'hot', 'rising', 'popular', 'recent'}
        self.search_keywords = {'find', 'show', 'search', 'get', 'about', 'projects', 'repositories'}

    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query into structured parameters.
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary containing parsed query parameters
        """
        query_lower = query.lower().strip()
        logger.info(f"Parsing query: {query}")
        
        # Initialize result structure
        result = {
            'intent': QueryIntent.UNKNOWN,
            'language': None,
            'project_type': None,
            'sort_by': 'stars',
            'limit': 20,
            'repositories': [],
            'filters': {},
            'original_query': query,
            'confidence': 0.0
        }
        
        # Flexible intent detection based on keywords
        query_words = set(query_lower.split())
        
        # Calculate intent scores
        ranking_score = len(query_words & self.ranking_keywords)
        comparison_score = len(query_words & self.comparison_keywords)  
        trending_score = len(query_words & self.trending_keywords)
        search_score = len(query_words & self.search_keywords)
        
        # Also check for numbers (indicates ranking)
        numbers = re.findall(r'\d+', query_lower)
        if numbers:
            ranking_score += 1
            result['limit'] = min(int(numbers[0]), 50)
        
        # Check for comparison indicators (vs, versus, compare X and Y)
        if re.search(r'\b(vs|versus)\b', query_lower) or re.search(r'compare.*\b(and|with)\b', query_lower):
            comparison_score += 2
            
        # Extract potential comparison items - more flexible patterns
        comparison_patterns = [
            r'(\w+)\s+(?:vs|versus)\s+(\w+)',           # X vs Y
            r'(\w+)\s+(?:and|with)\s+(\w+)',           # X and Y, X with Y  
            r'(\w+)\s+or\s+(\w+)',                     # X or Y
            r'compare\s+(\w+)\s+(?:and|with|to)\s+(\w+)', # compare X and Y
            r'between\s+(\w+)\s+and\s+(\w+)'          # between X and Y
        ]
        
        for pattern in comparison_patterns:
            comparison_match = re.search(pattern, query_lower)
            if comparison_match:
                result['repositories'] = [comparison_match.group(1), comparison_match.group(2)]
                comparison_score += 1
                break
        
        # Determine intent based on highest score
        max_score = max(ranking_score, comparison_score, trending_score, search_score)
        
        if max_score == 0:
            result['intent'] = QueryIntent.SEARCH
            result['confidence'] = 0.3
        elif comparison_score == max_score:
            result['intent'] = QueryIntent.COMPARISON
            result['confidence'] = min(0.9, 0.6 + comparison_score * 0.1)
        elif ranking_score == max_score:
            result['intent'] = QueryIntent.RANKING  
            result['confidence'] = min(0.9, 0.6 + ranking_score * 0.1)
        elif trending_score == max_score:
            result['intent'] = QueryIntent.TRENDING
            result['confidence'] = min(0.8, 0.5 + trending_score * 0.1)
            result['filters']['days'] = 30
        else:
            result['intent'] = QueryIntent.SEARCH
            # For search queries, confidence should be based on presence of meaningful technical terms
            tech_word_count = len([word for word in query_lower.split() 
                                 if word.strip('.,!?') in {'framework', 'frameworks', 'library', 'libraries', 
                                                          'tool', 'tools', 'microservice', 'microservices', 
                                                          'api', 'web', 'database', 'testing', 'machine', 
                                                          'learning', 'docker', 'kubernetes'}])
            has_language = result['language'] is not None
            base_confidence = 0.4 + search_score * 0.1 + tech_word_count * 0.1
            if has_language:
                base_confidence += 0.2
            result['confidence'] = min(0.8, base_confidence)
        
        # Extract programming language
        detected_language = self._extract_language(query_lower)
        if detected_language:
            result['language'] = detected_language
            result['confidence'] += 0.1
        
        # Extract project type
        detected_type = self._extract_project_type(query_lower)
        if detected_type:
            result['project_type'] = detected_type
            result['confidence'] += 0.1
        
        # Extract additional filters
        result['filters'].update(self._extract_filters(query_lower))
        
        logger.info(f"Parsed query with intent: {result['intent']}, confidence: {result['confidence']}")
        return result
    
    def _extract_language(self, query: str) -> Optional[str]:
        """Extract programming language from query"""
        # Check for exact matches first - need word boundaries to avoid false matches
        import re
        for lang in self.programming_languages:
            # Use word boundary matching to avoid matching 'c' in 'recent'
            if len(lang) == 1:  # Single letter languages like 'c' need special handling
                pattern = r'\b' + re.escape(lang.upper()) + r'\b|\b' + re.escape(lang.lower()) + r'\b'
                if re.search(pattern, query):
                    # Additional check for context - avoid common words
                    if lang == 'c' and re.search(r'\b[Cc]\+\+\b', query):
                        return 'c++'
                    elif lang == 'c' and not re.search(r'\b[Cc]( language| programming)\b', query):
                        continue  # Skip standalone 'c' unless clearly referring to language
                    return lang
            else:
                # For multi-character languages, use word boundaries
                pattern = r'\b' + re.escape(lang) + r'\b'
                if re.search(pattern, query, re.IGNORECASE):
                    # Handle special cases
                    if lang == 'js':
                        return 'javascript'
                    elif lang == 'ts':
                        return 'typescript'
                    elif lang == 'cpp':
                        return 'c++'
                    return lang
        
        # Check for language-specific keywords
        if 'node' in query or 'npm' in query:
            return 'javascript'
        elif 'pip' in query or 'django' in query or 'flask' in query:
            return 'python'
        elif 'gem' in query or 'rails' in query:
            return 'ruby'
        elif 'maven' in query or 'gradle' in query:
            return 'java'
        
        return None
    
    def _extract_project_type(self, query: str) -> Optional[str]:
        """Extract project type from query"""
        for project_type in self.project_types:
            if project_type in query:
                # Normalize to singular form
                if project_type.endswith('s'):
                    # Handle special cases for irregular plurals
                    if project_type == 'libraries':
                        return 'library'
                    elif project_type == 'frameworks':
                        return 'framework'
                    else:
                        return project_type[:-1]
                return project_type
        return None
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract additional filters from query"""
        filters = {}
        
        # Time-based filters
        if 'this year' in query:
            filters['days'] = 365
        elif 'this month' in query:
            filters['days'] = 30
        elif 'this week' in query:
            filters['days'] = 7
        elif 'recent' in query:
            filters['days'] = 30
        
        # Activity filters
        if 'high activity' in query or 'very active' in query:
            filters['min_stars'] = 100
        elif 'active' in query:
            filters['min_stars'] = 10
        
        # Size filters
        if 'small' in query:
            filters['max_size'] = 1000
        elif 'large' in query:
            filters['min_size'] = 10000
        
        return filters
    
    def validate_query(self, parsed_query: Dict[str, Any]) -> bool:
        """
        Validate if the parsed query has sufficient information to process.
        
        Args:
            parsed_query: Result from parse_query()
            
        Returns:
            True if query can be processed, False otherwise
        """
        # Check if we have a clear intent
        if parsed_query['intent'] == QueryIntent.UNKNOWN:
            return False
        
        # For comparison queries, we need at least one repository
        if parsed_query['intent'] == QueryIntent.COMPARISON:
            return len(parsed_query['repositories']) >= 1
        
        # For ranking and trending, we should have some context
        if parsed_query['intent'] in [QueryIntent.RANKING, QueryIntent.TRENDING]:
            return (parsed_query['language'] is not None or 
                   parsed_query['project_type'] is not None or
                   parsed_query['confidence'] > 0.6)
        
        return True
    
    def get_suggested_clarifications(self, parsed_query: Dict[str, Any]) -> List[str]:
        """
        Generate suggestions to clarify ambiguous queries.
        
        Args:
            parsed_query: Result from parse_query()
            
        Returns:
            List of clarification suggestions
        """
        suggestions = []
        
        if not self.validate_query(parsed_query):
            suggestions.append("Could you be more specific about what you're looking for?")
        
        if parsed_query['intent'] == QueryIntent.RANKING and not parsed_query['language']:
            suggestions.append("Which programming language are you interested in?")
        
        if parsed_query['intent'] == QueryIntent.COMPARISON and len(parsed_query['repositories']) < 2:
            suggestions.append("Which repositories would you like to compare?")
        
        if parsed_query['confidence'] < 0.5:
            suggestions.append("I'm not sure I understood correctly. Could you rephrase your question?")
        
        return suggestions