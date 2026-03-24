"""
data_fetcher.py - AkShare 数据获取模块（支持东方财富/新浪财经）
"""
import akshare as ak
import pandas as pd
import json
import os
import time
import requests
from datetime import datetime, timedelta
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

_session = requests.Session()
_session.mount("http://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1)))
_session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1)))

_data_source = "eastmoney"  # eastmoney or sina


def get_stock_list() -> pd.DataFrame:
    """获取 A 股全部股票列表"""
    for attempt in range(3):
        try:
            df = ak.stock_info_a_code_name()
            df.columns = ["code", "name"]
            return df
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                raise e
    return pd.DataFrame()


def get_daily_history(code: str, days: int = 120) -> pd.DataFrame:
    """
    获取单只股票日线历史数据
    :param code: 股票代码，如 '000001'
    :param days: 获取最近 N 天
    :return: DataFrame，含 date/open/high/low/close/volume/turnover
    """
    # Try East Money first
    df = _get_daily_history_eastmoney(code, days)
    if df.empty:
        # Fallback to Sina
        df = _get_daily_history_sina(code, days)
    return df


def _get_daily_history_eastmoney(code: str, days: int = 120) -> pd.DataFrame:
    end = datetime.today().strftime("%Y%m%d")
    start = (datetime.today() - timedelta(days=days)).strftime("%Y%m%d")
    for attempt in range(3):
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start,
                end_date=end,
                adjust="qfq",
            )
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "turnover",
                "换手率": "turnover_rate",
            })
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            return df
        except Exception:
            if attempt < 2:
                time.sleep(2)
    return pd.DataFrame()


def _get_daily_history_sina(code: str, days: int = 120) -> pd.DataFrame:
    """使用新浪财经接口获取历史数据"""
    try:
        if code.startswith("6"):
            sina_code = f"sh{code}"
        else:
            sina_code = f"sz{code}"
        
        url = f"https://quotes.sina.cn/cn/api/jsonp.php/var%20_{code}=/CN_MarketDataService.getKLineData?symbol={sina_code}&scale=240&ma=5&datalen={days}"
        resp = requests.get(url, timeout=10)
        text = resp.text
        if not text or "null" in text:
            return pd.DataFrame()
        
        import re
        match = re.search(r'\[.*\]', text)
        if not match:
            return pd.DataFrame()
        
        import json as json_lib
        data = json_lib.loads(match.group())
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df = df.rename(columns={
            "day": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        df["turnover"] = 0
        df["turnover_rate"] = 0
        return df
    except Exception:
        return pd.DataFrame()


def get_realtime_quotes(codes: list, max_workers: int = 8) -> pd.DataFrame:
    """
    获取多只股票实时行情（并发版）
    :param codes: 股票代码列表
    :param max_workers: 并发线程数
    :return: DataFrame
    """
    from tqdm import tqdm
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _fetch_via_spot():
        """Use EastMoney spot API"""
        try:
            df = ak.stock_zh_a_spot_em()
            if not df.empty:
                df = df[df["代码"].isin(codes)]
                return df.rename(columns={
                    "代码": "code",
                    "名称": "name",
                    "最新价": "price",
                    "涨跌幅": "pct_change",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "振幅": "amplitude",
                    "最高": "high",
                    "最低": "low",
                    "今开": "open",
                    "昨收": "pre_close",
                    "量比": "volume_ratio",
                    "换手率": "turnover_rate",
                    "市盈率-动态": "pe",
                    "市净率": "pb",
                })
        except Exception as e:
            print(f"Spot API error: {e}")
        return pd.DataFrame()

    def _fetch_via_sina(codes: list) -> pd.DataFrame:
        """Use Sina财经 API"""
        try:
            results = []
            for code in codes[:100]:  # Sina一次最多100只
                if code.startswith("6"):
                    sina_code = f"sh{code}"
                else:
                    sina_code = f"sz{code}"
                url = f"https://hq.sinajs.cn/list={sina_code}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    text = resp.text
                    if text and "=" in text:
                        parts = text.split("=")[1].split(",")
                        if len(parts) > 30:
                            try:
                                price = float(parts[0]) if parts[0] else 0
                                pct = 0
                                if len(parts) > 30:
                                    pre_close = float(parts[2]) if parts[2] else 0
                                    if pre_close > 0:
                                        pct = (price - pre_close) / pre_close * 100
                                results.append({
                                    "code": code,
                                    "name": _STOCK_MAPPING.get(code, code),
                                    "price": price,
                                    "pct_change": pct,
                                    "volume": 0,
                                    "turnover": 0,
                                    "turnover_rate": 0,
                                    "pe": 0,
                                    "pb": 0,
                                    "market_cap": 0,
                                    "float_cap": 0,
                                })
                            except:
                                pass
            return pd.DataFrame(results)
        except Exception as e:
            print(f"Sina API error: {e}")
        return pd.DataFrame()

    def _fetch_one(code):
        for attempt in range(3):
            try:
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=(datetime.today() - timedelta(days=10)).strftime("%Y%m%d"),
                    end_date=datetime.today().strftime("%Y%m%d"),
                    adjust="qfq",
                )
                if df.empty:
                    return None
                latest = df.iloc[-1]
                return {
                    "code":         code,
                    "name":         _STOCK_MAPPING.get(code, code),
                    "price":        latest.get("收盘", 0),
                    "pct_change":   latest.get("涨跌幅", 0),
                    "volume":       latest.get("成交量", 0),
                    "turnover":     latest.get("成交额", 0),
                    "turnover_rate": latest.get("换手率", 0),
                    "pe":           0,
                    "pb":           0,
                    "market_cap":   0,
                    "float_cap":    latest.get("成交额", 0) * 100,
                }
            except Exception:
                if attempt < 2:
                    time.sleep(1)
                else:
                    return None
        return None

    # Try spot API first
    print(f"   Trying spot API...")
    df_spot = _fetch_via_spot()
    if not df_spot.empty:
        df_spot["price"] = pd.to_numeric(df_spot["price"], errors="coerce").fillna(0)
        df_spot["pct_change"] = pd.to_numeric(df_spot["pct_change"], errors="coerce").fillna(0)
        df_spot["volume"] = pd.to_numeric(df_spot["volume"], errors="coerce").fillna(0)
        df_spot["turnover"] = pd.to_numeric(df_spot["turnover"], errors="coerce").fillna(0)
        df_spot["turnover_rate"] = pd.to_numeric(df_spot["turnover_rate"], errors="coerce").fillna(0)
        df_spot["pe"] = pd.to_numeric(df_spot["pe"], errors="coerce").fillna(0)
        df_spot["pb"] = pd.to_numeric(df_spot["pb"], errors="coerce").fillna(0)
        print(f"   Got {len(df_spot)} stocks via spot API")
        return df_spot

    # Try Sina API
    print(f"   Trying Sina API...")
    df_sina = _fetch_via_sina(codes)
    if not df_sina.empty:
        print(f"   Got {len(df_sina)} stocks via Sina API")
        return df_sina

    # Last fallback: historical API
    target_codes = codes[:500]
    print(f"   Fallback: fetching quotes ({len(target_codes)} stocks, {max_workers} threads)...")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_one, code): code for code in target_codes}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching quotes"):
            result = future.result()
            if result is not None:
                results.append(result)

    return pd.DataFrame(results)


def get_financial_indicator(code: str) -> dict:
    """
    获取股票基本面财务指标（最新一期）
    :param code: 股票代码
    :return: dict，含 roe/eps/revenue_growth 等
    """
    try:
        df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2023")
        if df.empty:
            return {}
        latest = df.iloc[0]
        return {
            "roe": _safe_float(latest.get("净资产收益率(%)")),
            "eps": _safe_float(latest.get("基本每股收益(元)")),
            "gross_margin": _safe_float(latest.get("销售毛利率(%)")),
        }
    except Exception:
        return {}


def _safe_float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return float("nan")
