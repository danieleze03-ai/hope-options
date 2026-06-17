# ============================================================
# HOPE OPTIONS — Data Fetcher
# Fetches live candle data using yfinance (no API key needed)
# ============================================================

import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PAIRS, CANDLE_LOOKBACK


def _download_with_retry(ticker: str, period: str, interval: str, retries: int = 3) -> pd.DataFrame:
    """
    Wraps yf.download with retry + exponential backoff.
    Handles YFRateLimitError automatically.
    """
    for attempt in range(retries):
        try:
            df = yf.download(
                tickers=ticker,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                multi_level_index=False
            )
            return df
        except Exception as e:
            error = str(e)
            if "Rate limit" in error or "Too Many Requests" in error:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s
                print(f"[DataFetcher] Rate limited. Waiting {wait}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait)
            else:
                print(f"[DataFetcher] Download error: {e}")
                return pd.DataFrame()

    print(f"[DataFetcher] All {retries} retries failed for {ticker}")
    return pd.DataFrame()


def get_candles(pair_name: str, timeframe: str, lookback: int = CANDLE_LOOKBACK) -> pd.DataFrame:
    ticker = PAIRS.get(pair_name)
    if not ticker:
        print(f"[DataFetcher] Unknown pair: {pair_name}")
        return pd.DataFrame()

    period_map = {
        "1m":  "1d",
        "5m":  "5d",
        "15m": "5d",
        "1h":  "30d",
    }
    period = period_map.get(timeframe, "5d")

    df = _download_with_retry(ticker, period, timeframe)

    if df is None or df.empty:
        print(f"[DataFetcher] No data returned for {pair_name} {timeframe}")
        return pd.DataFrame()

    df.columns = [c.lower() for c in df.columns]
    df = df[["open", "high", "low", "close", "volume"]].copy()
    df.dropna(inplace=True)

    return df.tail(lookback)


def get_current_price(pair_name: str) -> float:
    ticker = PAIRS.get(pair_name)
    if not ticker:
        return 0.0

    df = _download_with_retry(ticker, "1d", "1m")

    if df is None or df.empty:
        return 0.0

    try:
        return float(df["Close"].iloc[-1])
    except Exception as e:
        print(f"[DataFetcher] Error reading price for {pair_name}: {e}")
        return 0.0


def test_data_fetcher():
    print("Testing data fetcher...")

    for pair in ["EURUSD", "GBPUSD"]:
        df = get_candles(pair, "5m", lookback=10)
        if not df.empty:
            print(f"✅ {pair} 5m — {len(df)} candles fetched. Latest close: {df['close'].iloc[-1]:.5f}")
        else:
            print(f"❌ {pair} 5m — Failed to fetch data")

    price = get_current_price("EURUSD")
    print(f"✅ EURUSD current price: {price:.5f}" if price > 0 else "❌ Price fetch failed")


if __name__ == "__main__":
    test_data_fetcher()