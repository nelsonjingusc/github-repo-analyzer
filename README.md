# GitHub Repository Analysis Agent

An intelligent AI agent that analyzes GitHub repository data to answer questions about code trends, project activity, and repository comparisons using natural language queries.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Features

- **Natural Language Queries**: Ask questions in plain English about GitHub repositories
- **Repository Rankings**: Find top repositories by stars, forks, or activity
- **Trend Analysis**: Discover trending projects and emerging technologies
- **Repository Comparisons**: Compare multiple repositories across various metrics
- **Smart Search**: Find repositories by language, topic, or keywords
- **Interactive CLI**: Beautiful command-line interface with rich formatting
- **Free & Open Source**: Uses only free APIs and local processing

## Sample Interactions

```bash
Ask me about repositories: What are the top 5 most starred Python web frameworks?

Analysis Result (Intent: ranking)
┌─────────────────────────────────────────────────────────────────┐
│ Here are the top 5 most starred Python web frameworks:         │
│                                                                 │
│ 1. **django/django** 75,234 stars                               │
│    A high-level Python web framework that encourages rapid...  │
│                                                                 │
│ 2. **pallets/flask** 65,847 stars                               │
│    A lightweight WSGI web application framework for Python...  │
│                                                                 │
│ 3. **tornadoweb/tornado** 21,456 stars                          │
│    Tornado is a Python web framework and asynchronous...       │
│                                                                 │
│ 4. **bottlepy/bottle** 8,234 stars                              │
│    bottle.py is a fast and simple micro-framework for...       │
│                                                                 │
│ 5. **webpy/webpy** 5,876 stars                                  │
│    web.py is a web framework for Python that is as...          │
└─────────────────────────────────────────────────────────────────┘
```

```bash
Ask me about repositories: Compare React vs Vue.js activity

Analysis Result (Intent: comparison)
┌─────────────────────────────────────────────────────────────────┐
│ ## Repository Comparison                                        │
│                                                                 │
│ ### facebook/react                                              │
│ - Stars: 218,234                                                │
│ - Forks: 44,876                                                 │
│ - Language: JavaScript                                           │
│ - Recent Commits: 156                                            │
│ - Contributors: 1,234                                            │
│ - Last Updated: 2024-01-15                                       │
│                                                                 │
│ ### vuejs/vue                                                   │
│ - Stars: 206,487                                                │
│ - Forks: 33,645                                                 │
│ - Language: JavaScript                                           │
│ - Recent Commits: 89                                             │
│ - Contributors: 876                                              │
│ - Last Updated: 2024-01-14                                       │
│                                                                 │
│ **Analysis**: React has more stars and recent activity,         │
│ while Vue shows strong community engagement.                    │
└─────────────────────────────────────────────────────────────────┘
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Internet connection for GitHub API access

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/github-repo-analyzer.git
   cd github-repo-analyzer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up GitHub token (recommended)**
   ```bash
   # Get a token from: https://github.com/settings/tokens
   export GITHUB_TOKEN=your_github_token_here
   ```

4. **Run the agent**
   ```bash
   python main.py
   ```

### Alternative Installation Methods

#### Using pip (if published to PyPI)
```bash
pip install github-repo-analyzer
github-analyzer
```

#### Using setup.py
```bash
pip install -e .
repo-analyzer
```

## Usage

### Interactive Mode
```bash
python main.py
```

### Single Query Mode
```bash
python main.py --query "top 10 Python machine learning libraries"
```

### JSON Output
```bash
python main.py --query "trending JavaScript projects" --json
```

### Debug Mode
```bash
python main.py --debug
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token (highly recommended)
  - Get yours at: https://github.com/settings/tokens
  - Increases API rate limits from 60 to 5,000 requests per hour

### Command Line Options

```bash
usage: main.py [-h] [--token TOKEN] [--query QUERY] [--json] [--debug] [--version]

GitHub Repository Analysis Agent

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN, -t TOKEN
                        GitHub personal access token
  --query QUERY, -q QUERY
                        Execute a single query and exit
  --json, -j            Output results in JSON format
  --debug, -d           Enable debug logging and verbose output
  --version, -v         show program's version number and exit
```

## 🎓 Query Examples

### Repository Rankings
- "What are the top 5 most starred Python frameworks?"
- "Show me the 10 most forked JavaScript projects"
- "Most active Go repositories this year"
- "Best machine learning libraries in Python"

### Trend Analysis
- "What are trending JavaScript projects this week?"
- "Show me rising Python data science projects"
- "Find popular React libraries from this month"
- "Trending artificial intelligence repositories"

### Repository Comparisons
- "Compare React vs Vue.js vs Angular"
- "How does TensorFlow compare to PyTorch?"
- "Django vs Flask vs FastAPI comparison"
- "Compare Kubernetes vs Docker Swarm activity"

### Smart Search
- "Find beginner-friendly machine learning projects"
- "Show me Python web scraping libraries"
- "Search for blockchain projects in Go"
- "Find mobile app development frameworks"

## 🏗 Architecture

### Core Components

```
github-repo-analyzer/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── ai_agent.py          # Main AI agent orchestration
│   ├── github_tool.py       # GitHub API integration
│   ├── query_parser.py      # Natural language understanding
│   └── cli.py               # Command-line interface
├── main.py                  # Application entry point
├── requirements.txt         # Dependencies
├── setup.py                 # Package configuration
└── README.md               # This file
```

### Key Classes

1. **`GitHubAnalysisAgent`**: Main orchestrator that combines all components
2. **`GitHubRepositoryTool`**: Handles all GitHub API interactions with caching
3. **`QueryParser`**: Understands natural language and extracts intent
4. **`LLMProvider`**: Manages response generation with fallback mechanisms
5. **`CLIInterface`**: Provides beautiful interactive command-line experience

### Data Flow

```
User Query → Query Parser → Intent Detection → GitHub API → Data Processing → Response Generation → CLI Display
```

## AI Capabilities

### Natural Language Understanding
The agent can understand various query patterns:
- **Ranking queries**: "top N", "best", "most popular"
- **Comparison queries**: "compare X vs Y", "difference between"
- **Trending queries**: "trending", "hot", "rising"
- **Search queries**: "find", "show me", "projects about"

### Response Generation
- **Local LLM Support**: Uses Ollama when available for intelligent responses
- **Template Fallback**: Smart template-based responses when LLM unavailable
- **Rich Formatting**: Beautiful CLI output with tables, panels, and markdown

### Caching & Performance
- **API Caching**: 5-minute cache for GitHub API responses
- **Rate Limit Handling**: Automatic retry with exponential backoff
- **Async Processing**: Concurrent API requests for faster responses

## Security & Privacy

- **No Data Collection**: All processing happens locally
- **Token Security**: GitHub tokens are handled securely and never logged
- **Rate Limit Compliance**: Respects GitHub API rate limits
- **Error Handling**: Comprehensive error handling prevents crashes

## Future Improvements

Key areas for enhancement:

### Scalability & Performance
- Add database persistence for caching across restarts
- Implement distributed architecture with Redis
- Add horizontal scaling support

### Enhanced AI Capabilities  
- Integrate with advanced NLP libraries (spaCy/NLTK)
- Add conversation memory across sessions
- Implement learning from user interactions

### Data Coverage
- Add support for GitLab and Bitbucket APIs
- Integrate package registry data (PyPI, NPM)
- Include code quality metrics from analysis tools

### User Interface
- Build web dashboard with visualizations
- Add REST API for third-party integrations
- Create mobile app version

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/your-username/github-repo-analyzer.git
cd github-repo-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
flake8 src/

# Type checking
mypy src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built by Nelson Jing