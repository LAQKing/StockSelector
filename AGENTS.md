# AGENTS.md - StockSelector Agent Guidelines

## Project Overview

Python-based A股智能选股系统 (A-share stock selector) using AkShare for data. Provides both CLI and web interface for stock screening based on technical and fundamental analysis.

## Build & Run Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# Web interface (Flask)
python app.py
# Then access http://localhost:5000

# CLI mode
python main.py

# With custom parameters
python main.py --top 30 --min-score 60 --tech-weight 0.7 --fund-weight 0.3

# Test AkShare data connectivity
python test_akshare.py
```

### Running Tests
This project does NOT have a formal test framework. `test_akshare.py` is a manual script.
```bash
# Manual test only
python test_akshare.py

# No pytest configured - do NOT use pytest commands
```

### Linting & Type Checking
No linting or type checking tools configured. Code uses basic Python practices.

## Code Style Guidelines

### Naming Conventions
- **Functions/variables**: snake_case (e.g., `get_stock_list`, `tech_weight`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `CONFIG_FILE`)
- **Classes**: PascalCase (not heavily used in this project)

### Type Hints
- **NOT required** in this codebase - see existing code for reference
- Use type hints for new public APIs if desired: `def run_selection(top_n: int = None) -> pd.DataFrame:`

### Imports
- Standard library first, then third-party
- Group by: stdlib, external libs (akshare, pandas, etc.), local modules
- Example:
```python
import os
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from data_fetcher import get_stock_list
```

### Error Handling
- Use try/except with specific exception types
- Return empty DataFrame or None on failure
- Log errors with print statements (no logging module)
- Example pattern:
```python
try:
    df = ak.stock_info_a_code_name()
    return df
except Exception as e:
    if attempt < 2:
        time.sleep(2)
    else:
        raise e
```

### Documentation
- Chinese comments used throughout codebase
- Docstrings for public functions (Google-style or simple description)
- Example:
```python
def get_stock_list() -> pd.DataFrame:
    """获取 A 股全部股票列表"""
```

### Formatting
- 4 spaces for indentation
- Max line length ~120 characters
- No enforced formatter - use reasonable spacing
- Use f-strings for string formatting

### Data Handling
- Use pandas DataFrames as primary data structure
- Handle missing/invalid data with `pd.to_numeric(..., errors="coerce").fillna(0)`
- Return empty DataFrame (`pd.DataFrame()`) for no-data cases

### Concurrency
- Use `concurrent.futures.ThreadPoolExecutor` for parallel operations
- Thread-safe operations only (no shared mutable state in threads)

### File Structure
```
stock_selector/
├── app.py              # Flask web server
├── main.py             # CLI entry point
├── selector.py         # Core selection logic
├── data_fetcher.py     # AkShare data fetching
├── indicators.py       # Technical indicators
├── fundamental.py      # Fundamental analysis
├── config.json         # Configuration file
├── templates/
│   └── index.html      # Web frontend
└── requirements.txt
```

### Key Patterns

1. **Configuration**: JSON file (`config.json`) with defaults in code
2. **Caching**: In-memory caching for historical data (`_history_cache`)
3. **Fallbacks**: Multiple data sources (EastMoney → Sina → historical)
4. **Filtering**: ST stocks, low market cap, banks removed

### Configuration Options (config.json)
- `top`: Number of stocks to return
- `min_score`: Minimum score threshold
- `tech_weight`: Technical analysis weight (0-1)
- `fund_weight`: Fundamental analysis weight (0-1)
- `max_stocks`: Maximum stocks to process
- `max_analyze`: Analyze top N by turnover
- `max_workers`: Thread pool size

### Important Notes for Agents

1. **AkShare dependencies**: Data comes from external APIs; network failures are common
2. **Rate limiting**: Add delays between API calls to avoid blocking
3. **First run**: Full market scan takes 5-10 minutes
4. **Windows compatibility**: Uses PowerShell-style commands
5. **No testing framework**: Test_akshare.py is manual; do NOT run pytest
6. **Chinese output**: All user-facing messages in Chinese

### What NOT to Do
- Do NOT use pytest - no test framework configured
- Do NOT add type hints to existing functions (not in style)
- Do NOT add logging module - uses print statements
- Do NOT create new test files without confirmation
- Do NOT modify data source APIs without fallback logic
