# GitHub Repository Analysis Agent - Test Cases

## Core Requirements Test Cases

Replace `YOUR_GITHUB_TOKEN` and `YOUR_OPENAI_KEY` with your actual tokens.

### Test 1: Top 5 most starred Python web frameworks
```bash
python3 main.py --openai-key YOUR_OPENAI_KEY --query "What are the top 5 most starred Python web frameworks?"
```

### Test 2: React vs Vue activity comparison (with GitHub token)
```bash
python3 main.py --token YOUR_GITHUB_TOKEN --openai-key YOUR_OPENAI_KEY --query "How active is the React repository compared to Vue?"
```

### Test 3: Most popular Python frameworks this year
```bash
python3 main.py --openai-key YOUR_OPENAI_KEY --query "What are the most popular Python frameworks this year?"
```

### Test 4: Trending JavaScript projects with high activity (with GitHub token)
```bash
python3 main.py --token YOUR_GITHUB_TOKEN --openai-key YOUR_OPENAI_KEY --query "Show me trending JavaScript projects with high activity"
```

### Test 5: Compare React vs Vue.js based on recent repository activity
```bash
python3 main.py --openai-key YOUR_OPENAI_KEY --query "Compare React vs Vue.js based on recent repository activity"
```

## Additional Test Cases

### Test with complete mode (OpenAI responses)
```bash
python3 main.py --token YOUR_GITHUB_TOKEN --openai-key YOUR_OPENAI_KEY --complete --query "find two trending machine learning projects"
```

### Test without GitHub token (rate limited)
```bash
python3 main.py --openai-key YOUR_OPENAI_KEY --query "top 3 Go web frameworks"
```

### Test with JSON output
```bash
python3 main.py --token YOUR_GITHUB_TOKEN --openai-key YOUR_OPENAI_KEY --json --query "compare Django vs Flask"
```

## Expected Results

- All queries should return properly formatted results
- Queries with GitHub token should show real data
- Queries without GitHub token may fall back to mock data
- Comparison queries should automatically map repository names (React → facebook/react)
- OpenAI integration should work for query parsing and --complete mode responses