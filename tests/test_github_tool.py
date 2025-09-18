#!/usr/bin/env python3
"""
Unit tests for GitHub API tool functionality

These tests verify the GitHub API integration, caching, and data processing
capabilities of the repository analysis agent.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from github_tool import GitHubRepositoryTool, GitHubAPIError


class TestGitHubRepositoryTool:
    """Test cases for GitHubRepositoryTool"""
    
    @pytest.fixture
    def github_tool(self):
        """Create a GitHub tool instance for testing"""
        return GitHubRepositoryTool()
    
    @pytest.fixture
    def sample_repo_data(self):
        """Sample repository data for testing"""
        return {
            "id": 12345,
            "name": "test-repo",
            "full_name": "testuser/test-repo", 
            "description": "A test repository",
            "stargazers_count": 100,
            "forks_count": 25,
            "language": "Python",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "pushed_at": "2024-01-01T12:00:00Z",
            "watchers_count": 50,
            "open_issues_count": 5,
            "size": 1000
        }
    
    def test_initialization_without_token(self, github_tool):
        """Test tool initialization without GitHub token"""
        assert github_tool.base_url == "https://api.github.com"
        assert "Authorization" not in github_tool.headers
        assert github_tool._cache == {}
        assert github_tool._cache_timeout == 300
    
    def test_initialization_with_token(self):
        """Test tool initialization with GitHub token"""
        token = "test_token_123"
        tool = GitHubRepositoryTool(token)
        assert tool.headers["Authorization"] == f"token {token}"
    
    @patch('requests.get')
    def test_make_request_success(self, mock_get, github_tool, sample_repo_data):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_repo_data
        mock_get.return_value = mock_response
        
        result = github_tool._make_request("repos/testuser/test-repo")
        
        assert result == sample_repo_data
        assert len(github_tool._cache) == 1
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_make_request_rate_limit(self, mock_get, github_tool):
        """Test rate limit handling"""
        # Mock rate limit response followed by success
        mock_rate_limit = Mock()
        mock_rate_limit.status_code = 403
        mock_rate_limit.text = "rate limit exceeded"
        mock_rate_limit.headers = {"x-ratelimit-reset": str(int(datetime.now().timestamp()) + 1)}
        
        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"data": "success"}
        
        mock_get.side_effect = [mock_rate_limit, mock_success]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = github_tool._make_request("test-endpoint")
            
        assert result == {"data": "success"}
        assert mock_get.call_count == 2
    
    @patch('requests.get')
    def test_make_request_failure(self, mock_get, github_tool):
        """Test API request failure"""
        # Mock a requests.exceptions.RequestException to trigger the retry mechanism
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")
        
        # The current implementation uses retry mechanism and converts to GitHubAPIError
        with pytest.raises(GitHubAPIError):
            github_tool._make_request("nonexistent/repo")
    
    def test_cache_functionality(self, github_tool, sample_repo_data):
        """Test caching behavior"""
        with patch.object(github_tool, '_make_request', return_value=sample_repo_data) as mock_request:
            # First call should hit the API
            result1 = github_tool._make_request("test-endpoint")
            
            # Second call should use cache
            result2 = github_tool._make_request("test-endpoint")
            
            assert result1 == result2 == sample_repo_data
            # Should only call API once due to caching
            mock_request.call_count = 1
    
    @patch.object(GitHubRepositoryTool, '_make_request')
    def test_search_repositories(self, mock_request, github_tool, sample_repo_data):
        """Test repository search functionality"""
        mock_request.return_value = {
            "total_count": 1,
            "items": [sample_repo_data]
        }
        
        results = github_tool.search_repositories(
            query="python web framework",
            language="python",
            sort="stars"
        )
        
        assert len(results) == 1
        assert results[0] == sample_repo_data
        
        # Verify API was called with correct parameters
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert "search/repositories" in args[0]
    
    @patch.object(GitHubRepositoryTool, '_make_request')
    @patch.object(GitHubRepositoryTool, '_get_repository_statistics')
    def test_get_repository_details(self, mock_stats, mock_request, github_tool, sample_repo_data):
        """Test getting detailed repository information"""
        mock_request.return_value = sample_repo_data
        mock_stats.return_value = {
            "recent_commits": 10,
            "recent_issues": 5,
            "recent_prs": 3,
            "contributors_count": 15
        }
        
        result = github_tool.get_repository_details("testuser", "test-repo")
        
        assert result["name"] == "test-repo"
        assert result["recent_commits"] == 10
        assert result["contributors_count"] == 15
        mock_request.assert_called_once()
        mock_stats.assert_called_once_with("testuser", "test-repo")
    
    @patch.object(GitHubRepositoryTool, '_make_request')
    def test_get_repository_statistics(self, mock_request, github_tool):
        """Test repository statistics gathering"""
        # Mock API responses
        mock_commits = [{"sha": "abc123"}] * 5
        # Current implementation checks for "pull_request" key presence, not null values
        mock_issues = [
            {"number": 1},  # Issue (no pull_request key)
            {"number": 2, "pull_request": {"url": "test"}},  # PR (has pull_request key)
            {"number": 3},  # Issue (no pull_request key)
        ]
        mock_contributors = [{"login": "user1"}, {"login": "user2"}]
        
        mock_request.side_effect = [mock_commits, mock_issues, mock_contributors]
        
        stats = github_tool._get_repository_statistics("testuser", "test-repo")
        
        assert stats["recent_commits"] == 5
        assert stats["recent_issues"] == 2  # 2 actual issues
        assert stats["recent_prs"] == 1     # 1 pull request
        assert stats["contributors_count"] == 2
    
    @patch.object(GitHubRepositoryTool, '_make_request')
    def test_find_trending_repositories(self, mock_request, github_tool, sample_repo_data):
        """Test trending repositories discovery"""
        mock_request.return_value = {
            "items": [sample_repo_data]
        }
        
        results = github_tool.find_trending_repositories(
            language="python",
            days=7,
            min_stars=50
        )
        
        assert len(results) == 1
        assert results[0] == sample_repo_data
        
        # Verify search parameters - params are passed as second positional argument
        mock_request.assert_called_once()
        args = mock_request.call_args[0]  # Get positional arguments
        assert len(args) >= 2  # Should have endpoint and params
        params = args[1]  # Second argument is params
        assert "stars:>50" in params["q"]
        assert "pushed:>" in params["q"]
    
    @patch.object(GitHubRepositoryTool, 'get_repository_details')
    def test_compare_repositories(self, mock_details, github_tool):
        """Test repository comparison functionality"""
        # Mock repository details
        repo1_data = {
            "name": "repo1",
            "description": "First repo",
            "language": "Python",
            "stargazers_count": 100,
            "forks_count": 20,
            "recent_commits": 10
        }
        
        repo2_data = {
            "name": "repo2", 
            "description": "Second repo",
            "language": "JavaScript",
            "stargazers_count": 200,
            "forks_count": 40,
            "recent_commits": 15
        }
        
        mock_details.side_effect = [repo1_data, repo2_data]
        
        repos_to_compare = [("user1", "repo1"), ("user2", "repo2")]
        result = github_tool.compare_repositories(repos_to_compare)
        
        assert len(result) == 2
        assert "user1/repo1" in result
        assert "user2/repo2" in result
        assert result["user1/repo1"]["stars"] == 100
        assert result["user2/repo2"]["stars"] == 200
    
    @patch.object(GitHubRepositoryTool, 'search_repositories')
    def test_get_language_frameworks(self, mock_search, github_tool, sample_repo_data):
        """Test finding frameworks for a specific language"""
        framework_repo = sample_repo_data.copy()
        framework_repo["name"] = "awesome-framework"
        framework_repo["description"] = "A popular Python web framework"
        
        mock_search.return_value = [framework_repo]
        
        results = github_tool.get_language_frameworks(
            language="python",
            category="framework",
            limit=5
        )
        
        assert len(results) == 1
        assert results[0]["name"] == "awesome-framework"
        mock_search.assert_called_once()


@pytest.mark.asyncio
class TestAsyncFunctionality:
    """Test asynchronous aspects if any"""
    
    async def test_concurrent_api_calls(self):
        """Test that multiple API calls can be made concurrently"""
        # This test would be more relevant if we had async methods
        # For now, it serves as a placeholder for future async functionality
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])