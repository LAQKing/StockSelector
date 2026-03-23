import pandas as pd
import os
from datetime import datetime

csv_files = [f for f in os.listdir('.') if f.startswith('result_') and f.endswith('.csv')]
if not csv_files:
    print('No result files found')
    exit(1)

latest = sorted(csv_files)[-1]
df = pd.read_csv(latest)

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A股智能选股系统</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 15px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 13px; }
        .header .update-time {
            margin-top: 10px;
            font-size: 12px;
            opacity: 0.8;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        .summary-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .summary-card .label {
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 5px;
        }
        .summary-card .value {
            font-size: 20px;
            font-weight: 700;
            color: #667eea;
        }
        .results { padding: 20px; }
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .results-header h2 { color: #212529; font-size: 18px; }
        .timestamp {
            color: #6c757d;
            font-size: 13px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        thead {
            background: #f8f9fa;
        }
        th, td {
            padding: 12px 10px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
            font-size: 13px;
        }
        th {
            font-weight: 600;
            color: #495057;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }
        td { color: #212529; }
        tr:hover { background: #f8f9fa; }
        .rank {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            font-weight: bold;
            font-size: 12px;
        }
        .rank.top-3 {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .code {
            background: #e9ecef;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            color: #6c757d;
        }
        .name {
            font-weight: 600;
            max-width: 80px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .price {
            font-weight: 600;
            white-space: nowrap;
        }
        .pct-up { color: #dc3545; font-weight: 600; }
        .pct-down { color: #28a745; font-weight: 600; }
        .score {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 11px;
            text-align: center;
            min-width: 32px;
        }
        .score-high { background: #d4edda; color: #155724; }
        .score-mid { background: #fff3cd; color: #856404; }
        .score-low { background: #f8d7da; color: #721c24; }
        .empty {
            text-align: center;
            padding: 60px;
            color: #6c757d;
        }
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 12px;
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            .header h1 { font-size: 20px; }
            .summary { grid-template-columns: repeat(2, 1fr); padding: 15px; gap: 10px; }
            .summary-card { padding: 12px; }
            .summary-card .value { font-size: 18px; }
            .results { padding: 15px; }
            .results-header h2 { font-size: 16px; }
            table { display: block; overflow-x: auto; }
            th, td { padding: 10px 8px; font-size: 12px; }
            .name { max-width: 60px; }
            .score { font-size: 10px; padding: 2px 6px; min-width: 28px; }
            .hide-mobile { display: none; }
        }
        @media (max-width: 480px) {
            .header { padding: 20px 15px; }
            .header h1 { font-size: 18px; }
            .summary { grid-template-columns: 1fr 1fr; }
            .hide-small { display: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>A股智能选股系统</h1>
            <p>技术面 + 基本面综合评分</p>
            <p class="update-time">更新时间: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="label">选出股票</div>
                <div class="value">''' + str(len(df)) + ''' 只</div>
            </div>
            <div class="summary-card">
                <div class="label">平均涨幅</div>
                <div class="value">''' + f"{(df['pct_change'].mean() if 'pct_change' in df.columns else 0):.2f}%" + '''</div>
            </div>
            <div class="summary-card">
                <div class="label">最高涨幅</div>
                <div class="value">''' + f"{(df['pct_change'].max() if 'pct_change' in df.columns else 0):.2f}%" + '''</div>
            </div>
            <div class="summary-card">
                <div class="label">平均综合分</div>
                <div class="value">''' + f"{(df['total_score'].mean() if 'total_score' in df.columns else 0):.1f}" + '''</div>
            </div>
        </div>

        <div class="results">
            <div class="results-header">
                <h2>选股结果</h2>
                <div class="timestamp">共 ''' + str(len(df)) + ''' 只股票</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>代码</th>
                        <th>名称</th>
                        <th>价格</th>
                        <th>涨跌幅</th>
                        <th class="hide-mobile">市盈率</th>
                        <th class="hide-small hide-mobile">市净率</th>
                        <th>技术分</th>
                        <th>基本分</th>
                        <th>综合分</th>
                    </tr>
                </thead>
                <tbody>
'''

for idx, row in df.iterrows():
    rank_class = 'top-3' if idx < 3 else ''
    pct = row.get('pct_change', 0)
    pct_class = 'pct-up' if pct > 0 else 'pct-down'
    pct_str = f'+{pct:.2f}%' if pct >= 0 else f'{pct:.2f}%'
    
    tech_score = row.get('tech_score', 0)
    fund_score = row.get('fund_score', 0)
    total_score = row.get('total_score', 0)
    
    tech_cls = 'score-high' if tech_score >= 70 else 'score-mid' if tech_score >= 50 else 'score-low'
    fund_cls = 'score-high' if fund_score >= 70 else 'score-mid' if fund_score >= 50 else 'score-low'
    total_cls = 'score-high' if total_score >= 70 else 'score-mid' if total_score >= 50 else 'score-low'
    
    html += f'''
                    <tr>
                        <td><span class="rank {rank_class}">{idx + 1}</span></td>
                        <td><span class="code">{row.get('code', '')}</span></td>
                        <td><span class="name">{row.get('name', '')}</span></td>
                        <td class="price">¥{row.get('price', 0):.2f}</td>
                        <td class="{pct_class}">{pct_str}</td>
                        <td class="hide-mobile">{row.get('pe', '-'):.2f if isinstance(row.get('pe'), (int, float)) else '-'}</td>
                        <td class="hide-small hide-mobile">{row.get('pb', '-'):.2f if isinstance(row.get('pb'), (int, float)) else '-'}</td>
                        <td><span class="score {tech_cls}">{tech_score:.0f}</span></td>
                        <td><span class="score {fund_cls}">{fund_score:.0f}</span></td>
                        <td><span class="score {total_cls}">{total_score:.1f}</span></td>
                    </tr>
'''

html += '''
                </tbody>
            </table>
        </div>

        <div class="footer">
            智能选股系统 · 数据每日自动更新
        </div>
    </div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML generated: {len(df)} stocks')
