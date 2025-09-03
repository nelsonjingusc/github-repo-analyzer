"""
Query Parser for Natural Language Understanding

This module analyzes user queries to extract intent, entities, and parameters
for the GitHub repository analysis agent.
"""

import re
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Supported query intents"""
    RANKING = "ranking"          # "top 5 most starred"
    COMPARISON = "comparison"    # "compare React vs Vue"
    TRENDING = "trending"        # "trending projects"
    SEARCH = "search"           # "find projects about"
    UNKNOWN = "unknown"


class QueryParser:
    """
    Parses natural language queries to extract structured parameters
    for repository analysis.
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
        
        # Pattern definitions for different query types
        self.patterns = {
            'ranking': [
                r'top\s+(\d+)\s+(?:most\s+)?(starred|popular|used|forked)',
                r'(?:show me|list|find)\s+(?:the\s+)?top\s+(\d+)',
                r'most\s+(starred|popular|forked|active)\s+(\w+)',
                r'best\s+(\d+)?\s*(\w+)',
                r'(\d+)\s+most\s+(starred|popular)'
            ],
            'comparison': [
                r'compare\s+([\w\-\.]+)\s+(?:vs|and|with|to)\s+([\w\-\.]+)',
                r'([\w\-\.]+)\s+(?:vs|versus|compared to)\s+([\w\-\.]+)',
                r'how\s+(?:does\s+)?([\w\-\.]+)\s+compare\s+(?:to\s+)?([\w\-\.]+)',
                r'difference\s+between\s+([\w\-\.]+)\s+and\s+([\w\-\.]+)',
                r'which\s+is\s+better\s+([\w\-\.]+)\s+or\s+([\w\-\.]+)'
            ],
            'trending': [
                r'trending\s+(\w+)?\s*(?:projects|repositories|repos)',
                r'(?:show me|find)\s+trending',
                r'popular\s+(?:recently|this\s+(?:year|month|week))',
                r'hot\s+(?:projects|repositories)',
                r'rising\s+(?:projects|stars)'
            ],
            'search': [
                r'(?:find|search|show)\s+(?:me\s+)?(?:some\s+)?(\w+)',
                r'(?:projects|repositories|repos)\s+(?:about|for|with)',
                r'(?:any|some)\s+(?:good\s+)?(\w+)'
            ]
        }

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
            'limit': 10,
            'repositories': [],
            'filters': {},
            'original_query': query,
            'confidence': 0.0
        }
        
        # Detect intent and extract parameters
        intent_detected = False
        
        # Check for ranking queries
        for pattern in self.patterns['ranking']:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                result['intent'] = QueryIntent.RANKING
                result['confidence'] = 0.8
                intent_detected = True
                
                # Extract number if present
                numbers = re.findall(r'\d+', match.group(0))
                if numbers:
                    result['limit'] = min(int(numbers[0]), 50)  # Cap at 50
                
                # Extract sort criteria
                sort_keywords = ['starred', 'popular', 'forked', 'active']
                for keyword in sort_keywords:
                    if keyword in match.group(0):
                        if keyword in ['starred', 'popular']:
                            result['sort_by'] = 'stars'
                        elif keyword == 'forked':
                            result['sort_by'] = 'forks'
                        elif keyword == 'active':
                            result['sort_by'] = 'updated'
                break
        
        # Check for comparison queries
        if not intent_detected:
            for pattern in self.patterns['comparison']:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    result['intent'] = QueryIntent.COMPARISON
                    result['confidence'] = 0.9
                    result['repositories'] = [match.group(1), match.group(2)]
                    intent_detected = True
                    break
        
        # Check for trending queries
        if not intent_detected:
            for pattern in self.patterns['trending']:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    result['intent'] = QueryIntent.TRENDING
                    result['confidence'] = 0.7
                    result['filters']['days'] = 30  # Default to last 30 days
                    intent_detected = True
                    break
        
        # Default to search if no specific intent detected
        if not intent_detected:
            result['intent'] = QueryIntent.SEARCH
            result['confidence'] = 0.5
        
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
        # Check for exact matches first
        for lang in self.programming_languages:
            if f" {lang} " in f" {query} " or query.startswith(lang) or query.endswith(lang):
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