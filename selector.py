"""
selector.py - 智能选股核心逻辑（多线程并发版）
"""
import os
import json
import time
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_fetcher import (
    get_stock_list,
    get_daily_history,
    get_realtime_quotes,
    get_financial_indicator,
)
from indicators import add_indicators, score_technical
from fundamental import score_fundamental
from stock_analyzer import generate_signals, generate_recommendation
from indicators import add_indicators, score_technical
from fundamental import score_fundamental, filter_basic

stop_flag = False


def set_stop_flag():
    """设置停止标志"""
    global stop_flag
    stop_flag = True


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _analyze_single(code, realtime_dict, tech_weight, fund_weight, min_score):
    """分析单只股票，返回结果字典或 None（线程安全）"""
    try:
        hist = get_daily_history(code, days=60)
        if hist.empty or len(hist) < 30:
            return None

        hist = add_indicators(hist)
        tech = score_technical(hist)

        financial = {}
        fund = score_fundamental(realtime_dict, financial)

        total = tech["total"] * tech_weight + fund["total"] * fund_weight
        if total < min_score:
            return None

        signals = generate_signals(hist, tech, fund)
        recommendation = generate_recommendation(total, signals)

        code_full = f"{code}.SZ" if not code.startswith("6") else f"{code}.SH"
        return {
            "code":           code_full,
            "name":           realtime_dict.get("name", ""),
            "price":          realtime_dict.get("price"),
            "pct_change":     realtime_dict.get("pct_change"),
            "pe":             realtime_dict.get("pe"),
            "pb":             realtime_dict.get("pb"),
            "market_cap":     realtime_dict.get("market_cap"),
            "turnover_rate":  realtime_dict.get("turnover_rate"),
            "tech_score":     round(tech["total"], 1),
            "tech_trend":     tech["trend"],
            "tech_momentum":  tech["momentum"],
            "tech_volume":    tech["volume"],
            "fund_score":     round(fund["total"], 1),
            "fund_valuation": fund["valuation"],
            "fund_profit":    fund["profitability"],
            "fund_growth":    fund["growth"],
            "fund_liquidity": fund["liquidity"],
            "total_score":    round(total, 1),
            "signals":        signals,
            "recommendation": recommendation,
        }
    except Exception:
        return None


def run_selection(
    top_n: int = None,
    tech_weight: float = None,
    fund_weight: float = None,
    min_score: float = None,
    max_workers: int = None,
    max_analyze: int = None,
) -> pd.DataFrame:
    """
    执行智能选股（多线程并发版）
    :param top_n: 返回前 N 只股票
    :param tech_weight: 技术面权重
    :param fund_weight: 基本面权重
    :param min_score: 最低综合得分阈值
    :param max_workers: 并发线程数
    :param max_analyze: 分析的股票数量（按成交额排序）
    :return: 选股结果 DataFrame
    """
    cfg = load_config()
    top_n = top_n or cfg.get("top", 10)
    tech_weight = tech_weight or cfg.get("tech_weight", 0.6)
    fund_weight = fund_weight or cfg.get("fund_weight", 0.4)
    min_score = min_score if min_score is not None else cfg.get("min_score", 0)
    max_workers = max_workers or cfg.get("max_workers", 8)
    max_analyze = max_analyze or cfg.get("max_analyze", 500)
    print("[INFO] Getting stock list...")
    stock_list = get_stock_list()

    print("[INFO] Getting realtime quotes...")
    all_codes = stock_list["code"].tolist()
    df_realtime = get_realtime_quotes(all_codes, max_workers=max_workers)

    print(f"   Fetched {len(df_realtime)} records")
    if not df_realtime.empty:
        print(f"   Columns: {df_realtime.columns.tolist()}")

    print("[INFO] Filtering stocks (remove ST, low cap, etc)...")
    df_realtime = filter_basic(df_realtime)

    if df_realtime.empty:
        print("[WARNING] No stocks left after filtering")
        return pd.DataFrame()

    if "code" not in df_realtime.columns:
        print(f"[WARNING] DataFrame missing 'code' column: {df_realtime.columns.tolist()}")
        return pd.DataFrame()

    # 过滤条件
    df_realtime = df_realtime.copy()
    
    # 过滤银行股（通过名称判断）
    if "name" in df_realtime.columns:
        df_realtime = df_realtime[~df_realtime["name"].str.contains("银行", na=False)]
    
    # 过滤市值超过1000亿的股票
    if "market_cap" in df_realtime.columns:
        market_cap = pd.to_numeric(df_realtime["market_cap"], errors="coerce").fillna(0)
        df_realtime = df_realtime[market_cap <= 2e11]
    
    if df_realtime.empty:
        print("[WARNING] No stocks left after filtering banks and large cap")
        return pd.DataFrame()
    
    # 按成交额降序排序，取成交额最大的前N只（市场关注度高）
    df_realtime["_turnover"] = pd.to_numeric(df_realtime["turnover"], errors="coerce").fillna(0)
    df_realtime = df_realtime.sort_values("_turnover", ascending=False)
    
    if len(df_realtime) > max_analyze:
        df_realtime = df_realtime.head(max_analyze)
        print(f"   {len(df_realtime)} stocks remaining (top by turnover)")
    else:
        print(f"   {len(df_realtime)} stocks remaining")
    
    filtered_codes = df_realtime["code"].tolist()

    realtime_map = {row["code"]: row.to_dict() for _, row in df_realtime.iterrows()}

    results = []
    print(f"[INFO] Analyzing stocks ({max_workers} threads)...")
    start_time = time.time()
    
    global stop_flag
    stop_flag = False

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _analyze_single,
                code,
                realtime_map[code],
                tech_weight,
                fund_weight,
                min_score,
            ): code
            for code in filtered_codes
            if code in realtime_map
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="分析进度"):
            if stop_flag:
                print("[INFO] 用户请求停止，终止分析")
                break
            try:
                result = future.result(timeout=30)
            except Exception:
                continue
            if result is not None:
                results.append(result)

    elapsed = time.time() - start_time
    print(f"[INFO] Analysis completed in {elapsed:.1f} seconds")

    if not results:
        print("[WARNING] No stocks met the min score requirement")
        return pd.DataFrame()

    df_result = (
        pd.DataFrame(results)
        .sort_values("total_score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    df_result.index += 1
    return df_result
