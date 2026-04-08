# AGENTS.md - StockSelector Agent Guidelines

## Project Overview

Python-based A股智能选股系统 (A-share stock selector) using AkShare for data. Provides both CLI and web interface for stock screening based on technical and fundamental analysis. Now includes Vue3+Vite+ElementPlus frontend.

## Build & Run Commands

### Backend Installation
```bash
pip install -r requirements.txt
```

### Frontend Installation
```bash
cd frontend && npm install
```

### Running the Application

#### Development Mode (Recommended)
```bash
# Terminal 1: Flask backend (http://localhost:5001)
python app.py

# Terminal 2: Vite dev server (http://localhost:3000)
cd frontend && npm run dev
```

#### Production Mode
```bash
cd frontend && npm run build && python app.py
```

#### CLI Mode
```bash
python main.py --top 30 --min-score 60 --tech-weight 0.7 --fund-weight 0.3
```

### Linting & Type Checking
- **Python**: No formal linter. Manual code review recommended.
- **Frontend**: No lint/typecheck scripts configured. Use `npm run build` to verify.

### Running a Single Test
No formal test framework. Use the manual test script:
```bash
python test_akshare.py
```

## Data Flow
1. Frontend first tries `/data/stocks.json` (static JSON file)
2. Falls back to `/api/cache` API endpoint if JSON not found
3. After running selection, data saved to memory cache and JSON file

## File Structure
```
stock_selector/
├── app.py                  # Flask web server (saves JSON to frontend/public/data)
├── main.py                 # CLI entry point
├── selector.py            # Core selection logic
├── data_fetcher.py        # AkShare data fetching
├── indicators.py          # Technical indicators
├── fundamental.py         # Fundamental analysis
├── config.json            # Configuration file
├── requirements.txt
└── frontend/              # Vue3 frontend
    ├── package.json
    ├── vite.config.js
    ├── public/data/       # Generated JSON files
    └── src/
        ├── main.js
        ├── App.vue
        └── api/index.js  # API calls (JSON first, then API fallback)
```

## Code Style Guidelines

### Backend (Python)
- **Naming**: snake_case for functions/variables, UPPER_SNAKE_CASE for constants
- **Type hints**: NOT required (follow existing style)
- **Imports**: stdlib → third-party → local modules (see below)
- **Error handling**: try/except, return empty DataFrame/None on failure
- **Logging**: print statements (no logging module)
- **Documentation**: Chinese comments, simple docstrings

#### Import Order (Python)
```python
# 1. Standard library
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor

# 2. Third-party
import akshare as ak
import pandas as pd
import numpy as np
from flask import Flask, jsonify

# 3. Local modules
from data_fetcher import fetch_stock_data
from indicators import calculate_ma
from selector import filter_stocks
```

#### Error Handling Patterns
```python
# Data fetching - return None or empty DataFrame
def fetch_data(code):
    try:
        df = ak.stock_zh_a_hist(symbol=code)
        return df
    except Exception as e:
        print(f"获取数据失败: {code}, {e}")
        return pd.DataFrame()

# API endpoints - return error response
@app.route('/api/stocks')
def get_stocks():
    try:
        stocks = selector.select_stocks()
        return jsonify(stocks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Frontend (Vue3 + ElementPlus)
- Use Composition API with `<script setup>`
- ElementPlus components for UI (el-table, el-form, el-button, etc.)
- Responsive: PC shows table, mobile shows card-list
- CSS media queries at 768px breakpoint

### Configuration Options (config.json)
```json
{
  "top": 10,
  "min_score": 20,
  "tech_weight": 0.6,
  "fund_weight": 0.4,
  "max_stocks": 5000,
  "max_analyze": 500,
  "max_workers": 16,
  "interval_minutes": 60,
  "github": {
    "auto_commit": true,
    "commit_message": "Auto update stock selection results"
  }
}
```

## Key Patterns
1. **JSON caching**: Backend saves results to `frontend/public/data/stocks.json`
2. **Fallback logic**: Frontend tries JSON first, then API
3. **Data sources**: EastMoney → Sina → historical (fallback chain)

## Important Notes for Agents
1. **AkShare dependencies**: External APIs; network failures common
2. **Rate limiting**: Add `time.sleep(0.5)` between API calls
3. **First run**: Full market scan takes 5-10 minutes
4. **Chinese output**: All user-facing messages in Chinese
5. **Flask debug**: Set `FLASK_DEBUG=1` for auto-reload

## What NOT to Do
- Do NOT use pytest (not configured)
- Do NOT add type hints to existing Python functions
- Do NOT add logging module (use print)
- Do NOT modify data source APIs without fallback logic
- Do NOT create test files without confirmation
