"""
stock_analyzer.py - 个股深度分析模块
"""
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from data_fetcher import get_daily_history, get_financial_indicator, _STOCK_MAPPING, get_stock_realtime, get_financial_detail
from indicators import add_indicators, score_technical
from fundamental import score_fundamental
import akshare as ak


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _safe_float(v):
    """安全转换为浮点数"""
    import math
    try:
        f = float(v)
        return 0 if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return 0


def get_fund_flow(code: str) -> dict:
    """获取个股资金流向"""
    try:
        market = "sh" if code.startswith("6") else "sz"
        df = ak.stock_individual_fund_flow(stock=code, market=market)
        if df is None or df.empty:
            return {}
        
        # 取最近5日数据
        recent = df.head(5)
        main_net = 0
        super_net = 0
        large_net = 0
        mid_net = 0
        small_net = 0
        
        for _, row in recent.iterrows():
            main_net += _safe_float(row.get("主力净流入-净额", 0))
            super_net += _safe_float(row.get("超大单净流入-净额", 0))
            large_net += _safe_float(row.get("大单净流入-净额", 0))
            mid_net += _safe_float(row.get("中单净流入-净额", 0))
            small_net += _safe_float(row.get("小单净流入-净额", 0))
        
        return {
            "main_net": main_net,
            "super_net": super_net,
            "large_net": large_net,
            "mid_net": mid_net,
            "small_net": small_net,
            "days": len(recent),
        }
    except Exception as e:
        print(f"[WARN] 获取资金流向失败: {e}")
        return {}


def get_sector_heat(code: str) -> dict:
    """获取板块热度"""
    try:
        # 获取行业资金流
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
        if df is None or df.empty:
            return {}
        
        # 从板块名称匹配（简化版）
        sector_name = ""
        net_inflow = 0
        rank = 0
        
        # 取前20个板块
        for idx, row in df.head(20).iterrows():
            rank += 1
            sector_name = row.get("名称", "")
            net_inflow = _safe_float(row.get("主力净流入-净额", 0))
            break  # 返回第一个（今日资金流入最高）
        
        return {
            "top_sector": sector_name,
            "top_inflow": net_inflow,
            "rank": rank,
        }
    except Exception as e:
        print(f"[WARN] 获取板块热度失败: {e}")
        return {}


def predict_trend(hist: pd.DataFrame) -> dict:
    """预测未来三天趋势"""
    if len(hist) < 10:
        return {"short": "震荡", "mid": "震荡", "long": "震荡"}
    
    latest = hist.iloc[-1]
    ma5 = latest.get("ma5", 0)
    ma10 = latest.get("ma10", 0)
    ma20 = latest.get("ma20", 0)
    ma60 = latest.get("ma60", 0)
    close = latest.get("close", 0)
    
    # 短期趋势（3天内）
    if ma5 > ma10 > ma20 and close > ma5:
        short = "看涨"
    elif ma5 < ma10 < ma20 and close < ma5:
        short = "看跌"
    else:
        short = "震荡"
    
    # 中期趋势（5-10天）
    if ma10 > ma20 and ma20 > ma60:
        mid = "看涨"
    elif ma10 < ma20 and ma20 < ma60:
        mid = "看跌"
    else:
        mid = "震荡"
    
    # 长期趋势（10-20天）
    if ma5 > ma20:
        long = "看涨"
    elif ma5 < ma20:
        long = "看跌"
    else:
        long = "震荡"
    
    return {"short": short, "mid": mid, "long": long}


def generate_operation_advice(tech_score: dict, fund_score: dict, fund_flow: dict, trend: dict, signals: list) -> dict:
    """生成详细操作建议"""
    bullish_count = sum(1 for s in signals if s["type"] == "bullish")
    bearish_count = sum(1 for s in signals if s["type"] == "bearish")
    
    config = load_config()
    tech_weight = config.get("tech_weight", 0.6)
    fund_weight = config.get("fund_weight", 0.4)
    total = tech_score.get("total", 0) * tech_weight + fund_score.get("total", 0) * fund_weight
    
    # 资金面判断
    main_net = fund_flow.get("main_net", 0)
    if main_net > 100000000:
        flow_advice = "主力资金大幅流入，关注买入机会"
    elif main_net > 0:
        flow_advice = "主力资金小幅流入，可适度关注"
    elif main_net < -100000000:
        flow_advice = "主力资金大幅流出，建议观望或减仓"
    elif main_net < 0:
        flow_advice = "主力资金小幅流出，注意风险"
    else:
        flow_advice = "资金流向平稳"
    
    # 综合建议（与 recommendation 一致）
    if total >= 70 and bullish_count > bearish_count:
        action = "强烈买入"
        reason = "技术面、基本面、资金面三方共振"
    elif total >= 60 and bullish_count >= bearish_count:
        action = "买入"
        reason = "多项指标向好，可适当建仓"
    elif total >= 50:
        action = "持有"
        reason = "处于震荡整理阶段，建议观望"
    elif total >= 40:
        action = "观望"
        reason = "指标显示下行风险，建议观望"
    else:
        action = "卖出"
        reason = "多项指标显示下行趋势，建议离场"
    
    return {
        "action": action,
        "reason": reason,
        "flow_advice": flow_advice,
    }


def analyze_stock(code: str) -> dict:
    """
    深度分析单只股票
    :param code: 股票代码
    :return: 分析结果字典
    """
    result = {
        "code": code,
        "name": _STOCK_MAPPING.get(code, code),
        "success": False,
        "error": None,
        "basic_info": {},
        "technical": {},
        "fundamental": {},
        "price_data": [],
        "signals": [],
        "recommendation": "",
        "fund_flow": {},
        "sector_heat": {},
        "trend": {},
        "operation_advice": {},
    }

    try:
        time.sleep(0.5)  # 避免API调用过于频繁
        
        # 1. 获取历史数据
        hist = get_daily_history(code, days=120)
        if hist.empty or len(hist) < 60:
            result["error"] = "历史数据不足"
            return result

        # 2. 基本信息
        latest = hist.iloc[-1]
        prev_close = _safe_float(hist.iloc[-2]["close"])
        current_close = _safe_float(latest["close"])
        result["basic_info"] = {
            "price": current_close,
            "change": current_close - prev_close,
            "pct_change": ((current_close - prev_close) / prev_close * 100) if prev_close != 0 else 0,
            "volume": int(_safe_float(latest["volume"])),
            "turnover": _safe_float(latest["turnover"]),
            "turnover_rate": _safe_float(latest.get("turnover_rate", 0)),
            "high_52w": _safe_float(hist["high"].tail(250).max() if len(hist) >= 250 else hist["high"].max()),
            "low_52w": _safe_float(hist["low"].tail(250).min() if len(hist) >= 250 else hist["low"].max()),
        }

        # 3. 技术分析
        hist = add_indicators(hist)
        tech_score = score_technical(hist)

        latest_with_ind = hist.iloc[-1]
        result["technical"] = {
            "score": tech_score,
            "ma5": _safe_float(latest_with_ind.get("ma5", 0)),
            "ma10": _safe_float(latest_with_ind.get("ma10", 0)),
            "ma20": _safe_float(latest_with_ind.get("ma20", 0)),
            "ma60": _safe_float(latest_with_ind.get("ma60", 0)),
            "macd_dif": _safe_float(latest_with_ind.get("macd_dif", 0)),
            "macd_dea": _safe_float(latest_with_ind.get("macd_dea", 0)),
            "macd_bar": _safe_float(latest_with_ind.get("macd_bar", 0)),
            "rsi": _safe_float(latest_with_ind.get("rsi14", 0)),
            "kdj_k": _safe_float(latest_with_ind.get("kdj_k", 0)),
            "kdj_d": _safe_float(latest_with_ind.get("kdj_d", 0)),
            "kdj_j": _safe_float(latest_with_ind.get("kdj_j", 0)),
            "boll_upper": _safe_float(latest_with_ind.get("boll_upper", 0)),
            "boll_mid": _safe_float(latest_with_ind.get("boll_mid", 0)),
            "boll_lower": _safe_float(latest_with_ind.get("boll_lower", 0)),
        }

        # 4. 基本面分析
        financial = get_financial_indicator(code)
        
        # 尝试获取更详细的财务数据
        time.sleep(0.2)
        financial_detail = get_financial_detail(code)
        
        # 获取实时行情（包含PE/PB/市值等）
        time.sleep(0.2)
        realtime_data = get_stock_realtime(code)
        
        # 构建完整的 realtime_dict 用于基本面评分
        realtime_dict = {
            "pe": _safe_float(realtime_data.get("pe", 0)),
            "pb": _safe_float(realtime_data.get("pb", 0)),
            "market_cap": _safe_float(realtime_data.get("market_cap", 0)),
            "turnover_rate": _safe_float(result["basic_info"].get("turnover_rate", 0)),
            "pct_change": _safe_float(result["basic_info"].get("pct_change", 0)),
        }
        fund_score = score_fundamental(realtime_dict, financial)
        
        # 优先使用 financial_detail 中的数据，如果没有则用 financial
        roe = _safe_float(financial_detail.get("roe")) or _safe_float(financial.get("roe", 0))
        
        result["fundamental"] = {
            "score": fund_score,
            "roe": roe,
            "debt_ratio": _safe_float(financial.get("debt_ratio", 0)),
            "pe": _safe_float(realtime_data.get("pe", 0)),
            "pb": _safe_float(realtime_data.get("pb", 0)),
            "market_cap": _safe_float(realtime_data.get("market_cap", 0)),
            "turnover_rate": _safe_float(realtime_data.get("turnover_rate", 0)),
        }

        # 5. 资金流向
        time.sleep(0.3)
        result["fund_flow"] = get_fund_flow(code)

        # 6. 板块热度
        time.sleep(0.3)
        result["sector_heat"] = get_sector_heat(code)

        # 7. 趋势预测
        result["trend"] = predict_trend(hist)

        # 8. 价格数据（最近60天）
        recent = hist.tail(60)
        result["price_data"] = [
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
                "ma5": float(row.get("ma5", 0)),
                "ma10": float(row.get("ma10", 0)),
                "ma20": float(row.get("ma20", 0)),
            }
            for _, row in recent.iterrows()
        ]

        # 9. 交易信号
        signals = generate_signals(hist, tech_score, fund_score)
        result["signals"] = signals

        # 10. 操作建议
        result["operation_advice"] = generate_operation_advice(
            tech_score, fund_score, result["fund_flow"], result["trend"], signals
        )

        # 11. 投资建议
        config = load_config()
        tech_weight = config.get("tech_weight", 0.6)
        fund_weight = config.get("fund_weight", 0.4)
        total_score = tech_score["total"] * tech_weight + fund_score["total"] * fund_weight
        result["total_score"] = round(total_score, 1)
        result["tech_weight"] = tech_weight
        result["fund_weight"] = fund_weight
        result["recommendation"] = generate_recommendation(total_score, signals)

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def generate_signals(hist: pd.DataFrame, tech_score: dict, fund_score: dict) -> list:
    """生成交易信号"""
    signals = []
    latest = hist.iloc[-1]
    prev = hist.iloc[-2]

    # 均线信号
    if latest["ma5"] > latest["ma10"] > latest["ma20"]:
        signals.append({"type": "bullish", "signal": "多头排列", "desc": "短中长期均线呈多头排列"})
    elif latest["ma5"] < latest["ma10"] < latest["ma20"]:
        signals.append({"type": "bearish", "signal": "空头排列", "desc": "短中长期均线呈空头排列"})

    # MACD信号
    if latest["macd_bar"] > 0 and prev["macd_bar"] <= 0:
        signals.append({"type": "bullish", "signal": "MACD金叉", "desc": "MACD柱状图由负转正"})
    elif latest["macd_bar"] < 0 and prev["macd_bar"] >= 0:
        signals.append({"type": "bearish", "signal": "MACD死叉", "desc": "MACD柱状图由正转负"})

    # RSI信号
    rsi = latest.get("rsi14", 0)
    if rsi < 30:
        signals.append({"type": "bullish", "signal": "RSI超卖", "desc": f"RSI={rsi:.1f}，处于超卖区域"})
    elif rsi > 70:
        signals.append({"type": "bearish", "signal": "RSI超买", "desc": f"RSI={rsi:.1f}，处于超买区域"})

    # KDJ信号
    if latest["kdj_k"] < 20 and latest["kdj_d"] < 20:
        signals.append({"type": "bullish", "signal": "KDJ超卖", "desc": "KDJ指标处于超卖区域"})
    elif latest["kdj_k"] > 80 and latest["kdj_d"] > 80:
        signals.append({"type": "bearish", "signal": "KDJ超买", "desc": "KDJ指标处于超买区域"})

    # 布林带信号
    if latest["close"] < latest["boll_lower"]:
        signals.append({"type": "bullish", "signal": "触及下轨", "desc": "价格触及布林带下轨，可能反弹"})
    elif latest["close"] > latest["boll_upper"]:
        signals.append({"type": "bearish", "signal": "触及上轨", "desc": "价格触及布林带上轨，可能回调"})

    # 成交量信号
    avg_volume = hist["volume"].tail(20).mean()
    if latest["volume"] > avg_volume * 2:
        signals.append({"type": "neutral", "signal": "放量", "desc": "成交量显著放大"})

    return signals


def generate_recommendation(total_score: float, signals: list) -> str:
    """生成投资建议"""
    bullish_count = sum(1 for s in signals if s["type"] == "bullish")
    bearish_count = sum(1 for s in signals if s["type"] == "bearish")

    if total_score >= 70 and bullish_count > bearish_count:
        return "强烈推荐"
    elif total_score >= 60 and bullish_count >= bearish_count:
        return "推荐"
    elif total_score >= 40:
        return "观望"
    else:
        return "不推荐"


def batch_analyze(codes: list, max_count: int = 20) -> list:
    """批量分析股票"""
    results = []
    for code in codes[:max_count]:
        result = analyze_stock(code)
        if result["success"]:
            results.append(result)
    return results
