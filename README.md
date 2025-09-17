# GitHub Repository Analyzer

A command-line tool for analyzing GitHub repository data. Search for trending projects, compare repositories, and get insights about code trends through natural language queries.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Sample Interactions

### User: "What are the top 5 most starred Python web frameworks?"
**Agent**: Uses GitHub tool to search and analyze Python repos, returns ranked list

```bash
python3 main.py --query "What are the top 5 most starred Python web frameworks?"

Analysis Result (Intent: ranking)
┌─────────────────────────────────────────────────────────────────┐
│ Here are the top 5 most starred python repositories:           │
│                                                                 │
│  1 fastapi/fastapi 89,538 stars FastAPI framework, high        │
│    performance, easy to learn, fast to code, ready for         │
│    production                                                   │
│  2 django/django 85,008 stars The Web framework for            │
│    perfectionists with deadlines.                              │
│  3 pallets/flask 70,369 stars The Python micro framework for   │
│    building web applications.                                   │
│  4 scrapy/scrapy 58,255 stars Scrapy, a fast high-level web    │
│    crawling & scraping framework for Python.                   │
│  5 Textualize/textual 31,019 stars The lean application        │
│    framework for Python. Build sophisticated user interfaces   │
└─────────────────────────────────────────────────────────────────┘
```

### User: "How active is the React repository compared to Vue?"
**Agent**: Compares recent commit activity, issues, and community metrics

```bash
python3 main.py --query "How active is the React repository compared to Vue?"

Analysis Result (Intent: comparison)
┌─────────────────────────────────────────────────────────────────┐
│                     Repository Comparison                       │
│                                                                 │
│                      facebook/react                             │
│ • Stars: 238,944                                                │
│ • Forks: 49,344                                                 │
│ • Language: JavaScript                                          │
│ • Recent Commits: 100                                           │
│ • Contributors: 100                                             │
│ • Last Updated: 2025-09-17                                      │
│                                                                 │
│                        vuejs/vue                                │
│ • Stars: 209,422                                                │
│ • Forks: 33,763                                                 │
│ • Language: TypeScript                                          │
│ • Recent Commits: 0                                             │
│ • Contributors: 100                                             │
│ • Last Updated: 2025-09-17                                      │
│                                                                 │
│ Analysis: React shows more recent activity with higher          │
│ star count and active development.                              │
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

### Basic Query
```bash
python3 main.py --query "top 5 Python web frameworks"
```

### With GitHub Token (Recommended)
```bash
# Set token as environment variable
export GITHUB_TOKEN=your_github_token_here
python3 main.py --query "trending Python projects"

# Or provide token directly
python3 main.py --token your_github_token_here --query "compare React vs Vue"
```

### With OpenAI Enhancement
```bash
# Basic mode: fast template responses
python3 main.py --openai-key YOUR_KEY --query "top 5 Python web frameworks"

# Complete mode: natural language responses
python3 main.py --openai-key YOUR_KEY --complete --query "compare Django vs Flask"
```

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token (highly recommended)
  - Get yours at: https://github.com/settings/tokens
  - Increases API rate limits from 60 to 5,000 requests per hour

- `OPENAI_API_KEY`: OpenAI API key for advanced AI features (optional)
  - Get yours at: https://platform.openai.com/account/api-keys
  - Enables intelligent query parsing and natural language responses

### Command Line Options

```bash
usage: main.py [-h] [--token TOKEN] [--openai-key OPENAI_KEY] --query QUERY [--complete]

options:
  -h, --help            show this help message and exit
  --token TOKEN, -t TOKEN
                        GitHub personal access token (or set GITHUB_TOKEN env var)
  --openai-key OPENAI_KEY, -o OPENAI_KEY
                        OpenAI API key for advanced query parsing (or set OPENAI_API_KEY env var)
  --query QUERY, -q QUERY
                        Repository analysis query (required)
  --complete, -c        Use OpenAI for natural language responses (requires --openai-key)
```

## Architecture

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

## Security & Privacy

- **No Data Collection**: All processing happens locally
- **Token Security**: GitHub tokens are handled securely and never logged
- **Rate Limit Compliance**: Respects GitHub API rate limits
- **Error Handling**: Proper error handling prevents crashes

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