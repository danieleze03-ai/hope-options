# ============================================================
# HOPE OPTIONS — Data Fetcher
# Fetches live candle data using yfinance (no API key needed)
# ============================================================

import yfinance as yf
import pandas as pd
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PAIRS, CANDLE_LOOKBACK


def get_candles(pair_name: str, timeframe: str, lookback: int = CANDLE_LOOKBACK) -> pd.DataFrame:
    """
    Fetch OHLCV candles for a given pair and timeframe.

    pair_name: e.g. "EURUSD"
    timeframe: "1m", "5m", "15m"
    Returns: DataFrame with columns [open, high, low, close, volume]
    """
    ticker = PAIRS.get(pair_name)
    if not ticker:
        print(f"[DataFetcher] Unknown pair: {pair_name}")
        return pd.DataFrame()

    # Set period based on timeframe
    period_map = {
        "1m":  "1d",
        "5m":  "5d",
        "15m": "5d",
        "1h":  "30d",
    }
    period = period_map.get(timeframe, "5d")

    try:
        df = yf.download(
            tickers=ticker,
            period=period,
            interval=timeframe,
            auto_adjust=True,
            progress=False,
            multi_level_index=False
        )

        if df is None or df.empty:
            print(f"[DataFetcher] No data returned for {pair_name} {timeframe}")
            return pd.DataFrame()

        # Standardise column names to lowercase
        df.columns = [c.lower() for c in df.columns]

        # Keep only what we need
        df = df[["open", "high", "low", "close", "volume"]].copy()

        # Drop NaN rows
        df.dropna(inplace=True)

        # Return last N candles
        return df.tail(lookback)

    except Exception as e:
        print(f"[DataFetcher] Error fetching {pair_name} {timeframe}: {e}")
        return pd.DataFrame()


def get_current_price(pair_name: str) -> float:
    """
    Get the current live price of a pair.
    Used by result tracker to verify win/loss.
    """
    ticker = PAIRS.get(pair_name)
    if not ticker:
        return 0.0

    try:
        data = yf.download(
            tickers=ticker,
            period="1d",
            interval="1m",
            auto_adjust=True,
            progress=False,
            multi_level_index=False
        )
        if data is None or data.empty:
            return 0.0

        return float(data["Close"].iloc[-1])

    except Exception as e:
        print(f"[DataFetcher] Error getting price for {pair_name}: {e}")
        return 0.0


def test_data_fetcher():
    """Quick test to verify data fetching works."""
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