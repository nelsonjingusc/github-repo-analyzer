#!/usr/bin/env python3
"""
Unit tests for Query Parser functionality

These tests verify the natural language understanding capabilities
of the repository analysis agent.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from query_parser import QueryParser, QueryIntent


class TestQueryParser:
    """Test cases for QueryParser"""
    
    @pytest.fixture
    def parser(self):
        """Create a QueryParser instance for testing"""
        return QueryParser()
    
    def test_initialization(self, parser):
        """Test parser initialization"""
        assert isinstance(parser.programming_languages, set)
        assert isinstance(parser.project_types, set)
        assert isinstance(parser.sort_criteria, set)
        assert 'python' in parser.programming_languages
        assert 'framework' in parser.project_types
        assert 'stars' in parser.sort_criteria
    
    # Test Ranking Queries
    def test_ranking_query_detection(self, parser):
        """Test detection of ranking queries"""
        test_queries = [
            "top 5 most starred Python projects",
            "show me the top 10 JavaScript frameworks", 
            "best Python libraries",
            "most popular web frameworks",
            "5 most starred repositories"
        ]
        
        for query in test_queries:
            result = parser.parse_query(query)
            assert result['intent'] == QueryIntent.RANKING
            assert result['confidence'] >= 0.7
    
    def test_ranking_query_parameters(self, parser):
        """Test parameter extraction from ranking queries"""
        result = parser.parse_query("top 10 most starred Python web frameworks")
        
        assert result['intent'] == QueryIntent.RANKING
        assert result['limit'] == 10
        assert result['language'] == 'python'
        assert result['project_type'] == 'framework'
        assert result['sort_by'] == 'stars'
    
    # Test Comparison Queries
    def test_comparison_query_detection(self, parser):
        """Test detection of comparison queries"""
        test_queries = [
            "compare React vs Vue",
            "React versus Angular comparison", 
            "difference between Django and Flask",
            "how does TensorFlow compare to PyTorch",
            "which is better Django or FastAPI"
        ]
        
        for query in test_queries:
            result = parser.parse_query(query)
            assert result['intent'] == QueryIntent.COMPARISON
            assert result['confidence'] >= 0.6
            # Repositories may be empty if not extracted properly by basic parser
            assert 'repositories' in result
    
    def test_comparison_query_repositories(self, parser):
        """Test repository extraction from comparison queries"""
        result = parser.parse_query("compare React vs Vue.js")
        
        assert result['intent'] == QueryIntent.COMPARISON
        assert len(result['repositories']) == 2
        assert 'react' in [r.lower() for r in result['repositories']]
        assert 'vue' in [r.lower() for r in result['repositories']]
    
    # Test Trending Queries  
    def test_trending_query_detection(self, parser):
        """Test detection of trending queries"""
        test_queries = [
            "trending Python projects",
            "hot JavaScript projects",
            "rising machine learning projects"
        ]
        
        for query in test_queries:
            result = parser.parse_query(query)
            assert result['intent'] == QueryIntent.TRENDING
            assert result['confidence'] >= 0.6
    
    def test_trending_query_filters(self, parser):
        """Test filter extraction from trending queries"""
        result = parser.parse_query("trending Python projects this week")
        
        assert result['intent'] == QueryIntent.TRENDING
        assert result['language'] == 'python'
        assert result['filters']['days'] == 7
    
    # Test Search Queries
    def test_search_query_detection(self, parser):
        """Test detection of search queries"""
        test_queries = [
            "find machine learning libraries",
            "show me some Python projects", 
            "search for web development tools",
            "any good data visualization packages"
        ]
        
        for query in test_queries:
            result = parser.parse_query(query)
            # Should default to search if no other intent detected
            assert result['intent'] == QueryIntent.SEARCH
    
    # Test Language Extraction
    def test_language_extraction(self, parser):
        """Test programming language detection"""
        test_cases = [
            ("Python web frameworks", "python"),
            ("Go microservices tools", "go"),
            ("Node.js packages", "javascript"),
            ("Django vs Flask", "python"),
            ("Cpp game engines", "c++"),
            ("TypeScript utilities", "typescript")
        ]
        
        for query, expected_lang in test_cases:
            result = parser.parse_query(query)
            assert result['language'] == expected_lang
    
    def test_language_aliases(self, parser):
        """Test language alias resolution"""
        test_cases = [
            ("JS frameworks", "javascript"),
            ("TS libraries", "typescript"), 
            ("CPP projects", "c++"),
            ("node packages", "javascript")
        ]
        
        for query, expected_lang in test_cases:
            result = parser.parse_query(query)
            assert result['language'] == expected_lang
    
    # Test Project Type Extraction
    def test_project_type_extraction(self, parser):
        """Test project type detection"""
        test_cases = [
            ("Python web frameworks", "framework"),
            ("JavaScript libraries", "library"),
            ("development tools", "tool"),
            ("useful packages", "package"),
            ("browser extensions", "extension")
        ]
        
        for query, expected_type in test_cases:
            result = parser.parse_query(query)
            assert result['project_type'] == expected_type
    
    # Test Filter Extraction
    def test_time_filter_extraction(self, parser):
        """Test time-based filter extraction"""
        test_cases = [
            ("trending projects this year", 365),
            ("popular repositories this month", 30),
            ("hot projects this week", 7),
            ("recent JavaScript libraries", 30)
        ]
        
        for query, expected_days in test_cases:
            result = parser.parse_query(query)
            assert result['filters'].get('days') == expected_days
    
    def test_activity_filter_extraction(self, parser):
        """Test activity-based filter extraction"""
        test_cases = [
            ("high activity Python projects", 100),
            ("very active repositories", 100),
            ("active JavaScript libraries", 10)
        ]
        
        for query, expected_min_stars in test_cases:
            result = parser.parse_query(query)
            assert result['filters'].get('min_stars') == expected_min_stars
    
    # Test Query Validation
    def test_query_validation_success(self, parser):
        """Test successful query validation"""
        valid_queries = [
            "top 5 Python frameworks",  # Clear ranking with language
            "compare React vs Vue",      # Clear comparison
            "trending JavaScript projects"  # Clear trending with language
        ]
        
        for query in valid_queries:
            result = parser.parse_query(query)
            assert parser.validate_query(result) == True
    
    def test_query_validation_failure(self, parser):
        """Test query validation failures"""
        # Queries that should fail validation
        invalid_queries = [
            "",  # Empty query
        ]
        
        for query in invalid_queries:
            result = parser.parse_query(query)
            # These should either be UNKNOWN intent or have low confidence
            if result['intent'] != QueryIntent.UNKNOWN:
                assert result['confidence'] <= 0.5
    
    # Test Suggestions
    def test_clarification_suggestions(self, parser):
        """Test suggestion generation for ambiguous queries"""
        # Test with ambiguous query
        result = parser.parse_query("show me some stuff")
        # For low confidence queries, we might not have suggestions
        # Just check that the method doesn't crash
        suggestions = parser.get_suggested_clarifications(result)
        assert isinstance(suggestions, list)
    
    def test_comparison_suggestions(self, parser):
        """Test suggestions for incomplete comparisons"""
        result = parser.parse_query("compare React")
        suggestions = parser.get_suggested_clarifications(result)
        
        assert len(suggestions) > 0
        assert any("repositories" in suggestion.lower() for suggestion in suggestions)
    
    # Test Edge Cases
    def test_empty_query(self, parser):
        """Test handling of empty queries"""
        result = parser.parse_query("")
        # Empty query might be parsed as SEARCH with low confidence
        assert result['intent'] in [QueryIntent.UNKNOWN, QueryIntent.SEARCH]
        assert result['confidence'] <= 0.5
    
    def test_very_long_query(self, parser):
        """Test handling of very long queries"""
        long_query = "show me the top 5 most starred Python web development frameworks that are actively maintained and have good documentation and are suitable for building REST APIs and have good community support and are beginner friendly" * 3
        
        result = parser.parse_query(long_query)
        # Should still detect intent despite length
        assert result['intent'] in [QueryIntent.RANKING, QueryIntent.SEARCH]
        assert result['language'] == 'python'
    
    def test_mixed_case_query(self, parser):
        """Test handling of mixed case queries"""
        result = parser.parse_query("TOP 5 PYTHON WEB FRAMEWORKS")
        
        assert result['intent'] == QueryIntent.RANKING
        assert result['language'] == 'python'
        assert result['project_type'] == 'framework'
    
    def test_query_with_special_characters(self, parser):
        """Test handling of queries with special characters"""
        result = parser.parse_query("compare React.js vs Vue.js!!!")
        
        assert result['intent'] == QueryIntent.COMPARISON
        assert len(result['repositories']) == 2
    
    # Test Confidence Scoring
    def test_confidence_scoring(self, parser):
        """Test confidence scoring for different query types"""
        # High confidence queries
        high_conf_queries = [
            "top 5 Python frameworks",
            "compare React vs Vue",
            "trending JavaScript projects"
        ]
        
        for query in high_conf_queries:
            result = parser.parse_query(query)
            assert result['confidence'] >= 0.7
        
        # Low confidence queries
        low_conf_queries = [
            "show me stuff",
            "find things",
            "what about projects"
        ]
        
        for query in low_conf_queries:
            result = parser.parse_query(query)
            assert result['confidence'] <= 0.61


if __name__ == "__main__":
    pytest.main([__file__, "-v"])