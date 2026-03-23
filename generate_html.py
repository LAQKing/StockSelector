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
    <title>智能选股结果</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; padding: 20px; }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header .time { opacity: 0.8; font-size: 14px; }
        .header .count { background: rgba(255,255,255,0.2); padding: 8px 20px; border-radius: 20px; display: inline-block; margin-top: 15px; }
        .stock-card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
        .stock-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .stock-name { font-size: 20px; font-weight: bold; color: #333; }
        .stock-code { background: #f0f0f0; padding: 4px 10px; border-radius: 6px; font-size: 12px; color: #666; }
        .price-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 15px; }
        .price { font-size: 28px; font-weight: bold; }
        .price-up { color: #e53935; }
        .price-down { color: #43a047; }
        .pct { font-size: 18px; font-weight: 500; }
        .scores { display: flex; background: #f8f9fa; border-radius: 12px; padding: 15px; }
        .score-item { flex: 1; text-align: center; border-right: 1px solid #e0e0e0; }
        .score-item:last-child { border-right: none; }
        .score-value { font-size: 22px; font-weight: bold; }
        .score-value.tech { color: #1976d2; }
        .score-value.fund { color: #f57c00; }
        .score-value.total { color: #388e3c; }
        .score-label { font-size: 12px; color: #999; margin-top: 5px; }
        .rank { position: absolute; top: -10px; left: -10px; width: 30px; height: 30px; background: #667eea; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .card-wrap { position: relative; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>智能选股结果</h1>
            <p class="time">更新时间: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
            <p class="count">共选出 ''' + str(len(df)) + ''' 只股票</p>
        </div>
'''

for idx, row in df.iterrows():
    pct = row.get('pct_change', 0)
    price_class = 'price-up' if pct > 0 else 'price-down'
    pct_str = f'+{pct:.2f}%' if pct >= 0 else f'{pct:.2f}%'
    
    html += f'''
        <div class="card-wrap">
            <div class="stock-card">
                <div class="stock-header">
                    <span class="stock-name">{row.get('name', '')}</span>
                    <span class="stock-code">{row.get('code', '')}</span>
                </div>
                <div class="price-row">
                    <span class="price {price_class}">¥{row.get('price', 0):.2f}</span>
                    <span class="pct {price_class}">{pct_str}</span>
                </div>
                <div class="scores">
                    <div class="score-item">
                        <div class="score-value tech">{row.get('tech_score', 0):.0f}</div>
                        <div class="score-label">技术得分</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value fund">{row.get('fund_score', 0):.0f}</div>
                        <div class="score-label">基本面</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value total">{row.get('total_score', 0):.1f}</div>
                        <div class="score-label">综合得分</div>
                    </div>
                </div>
            </div>
        </div>
'''

html += '''
    </div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML generated: {len(df)} stocks')
