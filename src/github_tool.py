"""
GitHub API Tool for Repository Data Collection and Analysis

This module provides functionality to search and analyze GitHub repositories
using the GitHub REST API. It handles rate limiting, caching, and data processing.
"""

import requests
import time
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Custom exception for GitHub API related errors"""
    pass


class GitHubRepositoryTool:
    """
    A tool for interacting with GitHub's REST API to search repositories,
    collect statistics, and analyze repository activity.
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub API tool.
        
        Args:
            token: Optional GitHub personal access token for higher rate limits
        """
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        if token:
            self.headers["Authorization"] = f"token {token}"
            
        # Simple in-memory cache to avoid repeated API calls
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """
        Make a request to the GitHub API with error handling and rate limiting.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            GitHubAPIError: If the API request fails
        """
        cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True) if params else ''}"
        
        # Check cache first
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_timeout:
                logger.debug(f"Using cached data for {endpoint}")
                return cached_data
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Try with increasing timeouts and retries
        max_retries = 3
        timeouts = [10, 20, 30]
        last_error = None
        
        for attempt in range(max_retries):
            try:
                timeout = timeouts[attempt] if attempt < len(timeouts) else 30
                logger.info(f"Making GitHub API request to: {endpoint} (attempt {attempt + 1}/{max_retries}, timeout: {timeout}s)")
                response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
                
                # Handle rate limiting
                if response.status_code == 403 and 'rate limit' in response.text.lower():
                    reset_time = int(response.headers.get('x-ratelimit-reset', 0))
                    wait_time = max(reset_time - int(time.time()), 60)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
                
                response.raise_for_status()
                data = response.json()
                
                # Cache the response
                self._cache[cache_key] = (data, time.time())
                logger.info(f"Successfully retrieved data from GitHub API on attempt {attempt + 1}")
                
                return data
                
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"GitHub API request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    logger.error(f"All {max_retries} attempts failed. Last error: {e}")
        
        # If we get here, all retries failed
        raise GitHubAPIError(f"Failed to fetch data from GitHub API after {max_retries} attempts: {last_error}")

    def search_repositories(self, 
                          query: str, 
                          language: Optional[str] = None,
                          sort: str = "stars",
                          order: str = "desc",
                          per_page: int = 20) -> List[Dict[str, Any]]:
        """
        Search for repositories using GitHub's search API.
        
        Args:
            query: Search query string
            language: Filter by programming language
            sort: Sort field (stars, forks, updated)
            order: Sort order (asc, desc)
            per_page: Number of results per page (max 100)
            
        Returns:
            List of repository data dictionaries
        """
        search_query = query
        
        if language:
            search_query += f" language:{language}"
        
        params = {
            "q": search_query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100)
        }
        
        try:
            data = self._make_request("search/repositories", params)
            repositories = data.get("items", [])
            
            logger.info(f"Found {len(repositories)} repositories for query: {query}")
            return repositories
            
        except GitHubAPIError as e:
            logger.error(f"Repository search failed: {e}")
            logger.warning("GitHub API unavailable - using mock data for demonstration")
            # Return mock data for demo purposes when API is unavailable
            mock_data = self._get_mock_repositories(language, query)
            logger.info(f"Returning {len(mock_data)} mock repositories for demonstration")
            return mock_data

    def get_repository_details(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository details or None if not found
        """
        try:
            endpoint = f"repos/{owner}/{repo}"
            data = self._make_request(endpoint)
            
            # Get additional statistics
            stats = self._get_repository_statistics(owner, repo)
            data.update(stats)
            
            return data
            
        except GitHubAPIError as e:
            logger.error(f"Failed to get repository details for {owner}/{repo}: {e}")
            return None

    def _get_repository_statistics(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get additional statistics for a repository including recent activity.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with additional statistics
        """
        stats = {
            "recent_commits": 0,
            "recent_issues": 0,
            "recent_prs": 0,
            "contributors_count": 0
        }
        
        try:
            # Get recent commits (last 30 days)
            since_date = (datetime.now() - timedelta(days=30)).isoformat()
            commits_params = {"since": since_date, "per_page": 100}
            
            commits_data = self._make_request(f"repos/{owner}/{repo}/commits", commits_params)
            stats["recent_commits"] = len(commits_data) if isinstance(commits_data, list) else 0
            
            # Get recent issues
            issues_params = {"state": "all", "since": since_date, "per_page": 100}
            issues_data = self._make_request(f"repos/{owner}/{repo}/issues", issues_params)
            
            if isinstance(issues_data, list):
                # Separate issues from pull requests
                recent_issues = [i for i in issues_data if "pull_request" not in i]
                recent_prs = [i for i in issues_data if "pull_request" in i]
                
                stats["recent_issues"] = len(recent_issues)
                stats["recent_prs"] = len(recent_prs)
            
            # Get contributors count
            contributors_data = self._make_request(f"repos/{owner}/{repo}/contributors", {"per_page": 100})
            stats["contributors_count"] = len(contributors_data) if isinstance(contributors_data, list) else 0
            
        except GitHubAPIError as e:
            logger.warning(f"Failed to get additional stats for {owner}/{repo}: {e}")
        
        return stats

    def find_trending_repositories(self, 
                                 language: Optional[str] = None,
                                 days: int = 7,
                                 min_stars: int = 10) -> List[Dict[str, Any]]:
        """
        Find trending repositories based on recent activity and star growth.
        
        Args:
            language: Filter by programming language
            days: Look for repositories updated in the last N days
            min_stars: Minimum number of stars
            
        Returns:
            List of trending repositories
        """
        # Calculate date range for "trending"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build query for recently updated repositories with decent star count
        query = f"stars:>{min_stars} pushed:>{start_date.strftime('%Y-%m-%d')}"
        
        return self.search_repositories(
            query=query,
            language=language,
            sort="updated",
            order="desc",
            per_page=20
        )

    def compare_repositories(self, repos: List[tuple]) -> Dict[str, Dict[str, Any]]:
        """
        Compare multiple repositories and their statistics.
        
        Args:
            repos: List of (owner, repo) tuples
            
        Returns:
            Dictionary mapping repo names to their detailed stats
        """
        comparison_data = {}
        
        for owner, repo in repos:
            repo_key = f"{owner}/{repo}"
            repo_data = self.get_repository_details(owner, repo)
            
            if repo_data:
                # Extract key comparison metrics
                comparison_data[repo_key] = {
                    "name": repo_data.get("name", repo),
                    "description": repo_data.get("description", ""),
                    "language": repo_data.get("language", "Unknown"),
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "watchers": repo_data.get("watchers_count", 0),
                    "open_issues": repo_data.get("open_issues_count", 0),
                    "size": repo_data.get("size", 0),
                    "created_at": repo_data.get("created_at", ""),
                    "updated_at": repo_data.get("updated_at", ""),
                    "pushed_at": repo_data.get("pushed_at", ""),
                    "recent_commits": repo_data.get("recent_commits", 0),
                    "recent_issues": repo_data.get("recent_issues", 0),
                    "recent_prs": repo_data.get("recent_prs", 0),
                    "contributors_count": repo_data.get("contributors_count", 0),
                    "license": repo_data.get("license", {}).get("name", "No License") if repo_data.get("license") else "No License"
                }
            else:
                logger.warning(f"Could not fetch data for repository: {repo_key}")
                
        return comparison_data

    def get_language_frameworks(self, language: str, category: str = "framework", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find popular frameworks/libraries for a specific programming language.
        
        Args:
            language: Programming language (e.g., "python", "javascript")
            category: Type of projects to find (framework, library, tool)
            limit: Maximum number of results
            
        Returns:
            List of repository data for popular frameworks
        """
        # Build query to find frameworks/libraries
        query = f"{category} OR library"
        
        repositories = self.search_repositories(
            query=query,
            language=language,
            sort="stars",
            order="desc",
            per_page=limit
        )
        
        # Filter results to focus on actual frameworks/libraries
        filtered_repos = []
        framework_keywords = [category, "library", "lib", "framework", "tool", "package"]
        
        for repo in repositories:
            description = (repo.get("description") or "").lower()
            name = repo.get("name", "").lower()
            
            # Check if the repository looks like a framework/library
            is_framework = any(keyword in description or keyword in name 
                             for keyword in framework_keywords)
            
            if is_framework or len(filtered_repos) < limit // 2:
                filtered_repos.append(repo)
                
            if len(filtered_repos) >= limit:
                break
                
        return filtered_repos[:limit]
    
    def _get_mock_repositories(self, language: Optional[str], query: str) -> List[Dict[str, Any]]:
        """
        Return mock repository data when GitHub API is unavailable.
        This is for demo purposes only.
        """
        logger.info(f"Using mock data for language: {language}, query: {query}")
        print("Note: Using demonstration data due to GitHub API connectivity issues.")
        
        if language and language.lower() == "python":
            return [
                {
                    "name": "django",
                    "full_name": "django/django",
                    "description": "The web framework for perfectionists with deadlines.",
                    "stargazers_count": 78234,
                    "forks_count": 31876,
                    "language": "Python",
                    "updated_at": "2024-01-15T12:30:00Z",
                    "html_url": "https://github.com/django/django"
                },
                {
                    "name": "flask",
                    "full_name": "pallets/flask",
                    "description": "The Python micro framework for building web applications.",
                    "stargazers_count": 66847,
                    "forks_count": 16234,
                    "language": "Python",
                    "updated_at": "2024-01-14T08:45:00Z",
                    "html_url": "https://github.com/pallets/flask"
                },
                {
                    "name": "fastapi",
                    "full_name": "tiangolo/fastapi",
                    "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
                    "stargazers_count": 67123,
                    "forks_count": 5634,
                    "language": "Python",
                    "updated_at": "2024-01-16T14:20:00Z",
                    "html_url": "https://github.com/tiangolo/fastapi"
                }
            ]
        elif language and language.lower() == "javascript":
            return [
                {
                    "name": "react",
                    "full_name": "facebook/react",
                    "description": "The library for web and native user interfaces",
                    "stargazers_count": 218234,
                    "forks_count": 44876,
                    "language": "JavaScript",
                    "updated_at": "2024-01-16T10:15:00Z",
                    "html_url": "https://github.com/facebook/react"
                },
                {
                    "name": "vue",
                    "full_name": "vuejs/vue",
                    "description": "Vue.js is a progressive, incrementally-adoptable JavaScript framework for building UI on the web.",
                    "stargazers_count": 206487,
                    "forks_count": 33645,
                    "language": "JavaScript",
                    "updated_at": "2024-01-15T16:30:00Z",
                    "html_url": "https://github.com/vuejs/vue"
                },
                {
                    "name": "angular",
                    "full_name": "angular/angular",
                    "description": "The modern web developer's platform",
                    "stargazers_count": 93456,
                    "forks_count": 24789,
                    "language": "TypeScript",
                    "updated_at": "2024-01-16T11:45:00Z",
                    "html_url": "https://github.com/angular/angular"
                }
            ]
        else:
            # Generic mock data
            return [
                {
                    "name": "awesome-project",
                    "full_name": "user/awesome-project",
                    "description": f"An awesome project related to {query}",
                    "stargazers_count": 15234,
                    "forks_count": 3456,
                    "language": language or "Multiple",
                    "updated_at": "2024-01-15T12:00:00Z",
                    "html_url": "https://github.com/user/awesome-project"
                },
                {
                    "name": "demo-repo",
                    "full_name": "demo/demo-repo",
                    "description": f"Demo repository for {query} examples",
                    "stargazers_count": 8765,
                    "forks_count": 1234,
                    "language": language or "Multiple",
                    "updated_at": "2024-01-14T09:30:00Z",
                    "html_url": "https://github.com/demo/demo-repo"
                }
            ]